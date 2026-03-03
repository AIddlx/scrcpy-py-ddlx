# UDP 传输机制详解

> **版本**: 1.2
> **最后更新**: 2026-02-23
> **状态**: 实现完成

本文档详细分析 scrcpy-py-ddlx 项目中服务端的 UDP 网络传输机制，包括数据包格式、分片机制、FEC 实现等。

---

## 目录

1. [架构概述](#1-架构概述)
2. [数据包格式](#2-数据包格式)
3. [发送流程](#3-发送流程)
4. [分片机制](#4-分片机制)
5. [FEC 前向纠错](#5-fec-前向纠错)
6. [流量控制](#6-流量控制)
7. [关键代码位置](#7-关键代码位置)

---

## 1. 架构概述

### 1.1 传输层架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           服务端发送架构                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐    │
│  │ MediaCodec   │────>│   Streamer   │────>│     UdpMediaSender       │    │
│  │ (编码器)      │     │  (流处理器)   │     │     (UDP 发送器)          │    │
│  └──────────────┘     └──────────────┘     │                          │    │
│                             │               │  ┌────────────────────┐  │    │
│                             │               │  │ SimpleXorFecEncoder│  │    │
│                             │               │  │   (FEC 编码器)      │  │    │
│                             │               │  └────────────────────┘  │    │
│                             │               └───────────┬──────────────┘    │
│                             │                           │                   │
│                             │                           ▼                   │
│                             │               ┌──────────────────────────┐   │
│                             │               │      DatagramSocket      │   │
│                             │               │        (UDP Socket)       │   │
│                             │               └──────────────────────────┘   │
│                             │                           │                   │
│                             ▼                           ▼                   │
│                    ┌──────────────┐          ┌──────────────────────────┐  │
│                    │   TCP 控制    │          │      网络传输 (WiFi)      │  │
│                    │    通道       │          └──────────────────────────┘  │
│                    └──────────────┘                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 核心类关系

```
Streamer
  ├── 持有 UdpMediaSender (UDP 模式)
  ├── 持有 OutputStream (TCP 模式)
  └── 持有 FileDescriptor (ADB 模式)

UdpMediaSender
  ├── 持有 DatagramSocket
  ├── 持有 SimpleXorFecEncoder (可选)
  └── 管理包序列号

SimpleXorFecEncoder
  ├── 管理 FEC 组状态
  └── 生成 XOR 校验包
```

### 1.3 数据流

```
屏幕帧 → MediaCodec 编码 → Streamer 封装 → UdpMediaSender 发送 → 网络

                              │
                              ▼
                      [Scrcpy Header]
                      pts_flags: 8B
                      size: 4B
                              │
                              ▼
                      [UDP Header]
                      seq: 4B
                      timestamp: 8B
                      flags: 4B
                      send_time_ns: 8B
                              │
                              ▼
                      (可选 FEC Header)
                              │
                              ▼
                      UDP Socket 发送
```

---

## 2. 数据包格式

### 2.1 UDP 头部结构 (24 字节)

**文件**: `UdpMediaSender.java:14`

```java
private static final int HEADER_SIZE = 24; // seq(4) + timestamp(8) + flags(4) + send_time_ns(8)
```

```
偏移量   字段          大小    类型      描述
------   ----          ----    ----      ----
0        sequence      4       uint32    包序列号（big-endian，递增）
4        timestamp     8       int64     时间戳 / PTS（big-endian，微秒）
12       flags         4       uint32    标志位（big-endian）
16       send_time_ns  8       int64     设备发送时间（纳秒，big-endian）[v1.2]
```

**字段详解**:

| 字段 | 用途 | 备注 |
|------|------|------|
| `sequence` | 包序号 | 用于丢包检测、乱序重组 |
| `timestamp` | PTS 时间戳 | 帧的演示时间，同一帧的所有包相同 |
| `flags` | 包类型标志 | 见下方标志位定义 |
| `send_time_ns` | 发送时间 | 用于 E2E 延迟计算 (v1.2 新增) |

### 2.2 FLAGS 标志位定义

**文件**: `UdpMediaSender.java:16-19`

```java
public static final long FLAG_KEY_FRAME = 1L << 0;     // bit 0: 关键帧
public static final long FLAG_CONFIG = 1L << 1;        // bit 1: 配置包
public static final long FLAG_FEC_DATA = 1L << 2;      // bit 2: FEC 数据包
public static final long FLAG_FEC_PARITY = 1L << 3;    // bit 3: FEC 校验包
// bit 31: 分片标志 (在 sendFragmented 中设置)
```

| Bit | 名称 | 值 | 描述 |
|-----|------|-----|------|
| 0 | KEY_FRAME | 0x00000001 | 关键帧（I帧） |
| 1 | CONFIG | 0x00000002 | 配置包（SPS/PPS, codec header） |
| 2 | FEC_DATA | 0x00000004 | FEC 数据包 |
| 3 | FEC_PARITY | 0x00000008 | FEC 校验包 |
| 4-30 | RESERVED | - | 保留 |
| 31 | FRAGMENTED | 0x80000000 | 分片包 |

### 2.3 完整 UDP 包结构

#### 2.3.1 普通包（非分片、无 FEC）

```
┌────────────────────────────────────────────────────────────────────────┐
│                         UDP Header (24 bytes)                          │
├────────────────────────────────────────────────────────────────────────┤
│  sequence (4B)  │  timestamp (8B)  │  flags (4B)  │  send_time_ns (8B) │
├────────────────────────────────────────────────────────────────────────┤
│                        Scrcpy Header (12 bytes)                        │
├────────────────────────────────────────────────────────────────────────┤
│                    pts_flags (8B)        │       size (4B)             │
├────────────────────────────────────────────────────────────────────────┤
│                            Payload (N bytes)                           │
│                          (视频/音频编码数据)                              │
└────────────────────────────────────────────────────────────────────────┘
```

#### 2.3.2 分片包

```
┌────────────────────────────────────────────────────────────────────────┐
│                         UDP Header (24 bytes)                          │
│              flags bit 31 = 1 (FRAGMENTED)                             │
├────────────────────────────────────────────────────────────────────────┤
│                        Fragment Index (4 bytes)                        │
│                     分片索引 (0, 1, 2, ...)                            │
├────────────────────────────────────────────────────────────────────────┤
│                        Fragment Data (N bytes)                         │
│             第一个分片包含 Scrcpy Header，后续分片只有数据               │
└────────────────────────────────────────────────────────────────────────┘
```

#### 2.3.3 FEC 数据包

```
┌────────────────────────────────────────────────────────────────────────┐
│                         UDP Header (24 bytes)                          │
│              flags bit 2 = 1 (FEC_DATA)                                │
├────────────────────────────────────────────────────────────────────────┤
│                       FEC Data Header (7 bytes)                        │
│  group_id (2B) │ frame_idx (1B) │ total_frames (1B) │ parity (1B) │ size (2B) │
├────────────────────────────────────────────────────────────────────────┤
│                            Payload (N bytes)                           │
└────────────────────────────────────────────────────────────────────────┘
```

#### 2.3.4 FEC 校验包

```
┌────────────────────────────────────────────────────────────────────────┐
│                         UDP Header (24 bytes)                          │
│              flags bit 3 = 1 (FEC_PARITY)                              │
├────────────────────────────────────────────────────────────────────────┤
│                      FEC Parity Header (5 bytes)                       │
│       group_id (2B) │ parity_idx (1B) │ total_frames (1B) │ total_parity (1B) │
├────────────────────────────────────────────────────────────────────────┤
│                          Parity Data (N bytes)                         │
│                    (XOR 结果数据)                                       │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 发送流程

### 3.1 整体发送流程时序图

```
┌─────────────┐                    ┌─────────────┐                    ┌─────────────┐
│ MediaCodec  │                    │   Streamer  │                    │UdpMediaSender│
└──────┬──────┘                    └──────┬──────┘                    └──────┬──────┘
       │                                  │                                  │
       │  encode() 完成                    │                                  │
       │  BufferInfo                       │                                  │
       │─────────────────────────────────>│                                  │
       │                                  │                                  │
       │                                  │  writePacket(buffer, bufferInfo) │
       │                                  │─────────────────────────────────>│
       │                                  │                                  │
       │                                  │                    构建 UDP 包    │
       │                                  │                    添加头部      │
       │                                  │                    [可选] FEC    │
       │                                  │                                  │
       │                                  │                    socket.send() │
       │                                  │─────────────────────────────────>│ 网络
       │                                  │                                  │
```

### 3.2 发送入口：Streamer.writePacket()

**文件**: `Streamer.java:147-203`

```java
public void writePacket(ByteBuffer buffer, long pts, boolean config, boolean keyFrame)
        throws IOException {
    // ... 配置包特殊处理 ...

    if (networkMode) {
        if (udpSender != null) {
            // UDP 模式: 始终添加 scrcpy 头部
            int dataSize = buffer.remaining();
            ByteBuffer packet = ByteBuffer.allocate(12 + dataSize);

            // 构建 scrcpy 头部
            long ptsAndFlags;
            if (config) {
                ptsAndFlags = PACKET_FLAG_CONFIG;
            } else {
                ptsAndFlags = pts;
                if (keyFrame) {
                    ptsAndFlags |= PACKET_FLAG_KEY_FRAME;
                }
            }
            packet.putLong(ptsAndFlags);
            packet.putInt(dataSize);
            packet.put(buffer);
            packet.flip();

            // 选择发送方式
            if (udpSender.isFecEnabled()) {
                udpSender.sendPacketWithFec(packet, pts, config, keyFrame);
            } else {
                udpSender.sendPacket(packet, pts, config, keyFrame);
            }
        }
    }
}
```

### 3.3 单包发送：sendSinglePacket()

**文件**: `UdpMediaSender.java:88-118`

```java
private void sendSinglePacket(ByteBuffer data, long timestamp, long flags)
        throws IOException {
    int dataSize = data.remaining();
    long sendTimeNs = System.nanoTime();  // 记录发送时间

    // 分配缓冲区: UDP 头部 (24B) + 数据
    ByteBuffer packet = ByteBuffer.allocate(HEADER_SIZE + dataSize);

    // 写入 UDP 头部
    packet.putInt(sequence++);            // 序列号递增
    packet.putLong(timestamp);            // PTS 时间戳
    packet.putInt((int) flags);           // 标志位
    packet.putLong(sendTimeNs);           // 发送时间 (E2E 延迟追踪)
    packet.put(data);                     // 负载数据

    packet.flip();

    // 发送 UDP 包
    DatagramPacket dp = new DatagramPacket(
        packet.array(),
        packet.remaining(),
        clientAddress,
        clientPort
    );
    socket.send(dp);
}
```

### 3.4 发送决策流程

```
                    sendPacket(data, timestamp, config, keyFrame)
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │ dataSize == 0 ?     │
                            └──────────┬──────────┘
                                       │
                        ┌──────────────┴──────────────┐
                        │ YES                         │ NO
                        ▼                             ▼
                   跳过 (空包)              ┌─────────────────────┐
                                          │ dataSize + HEADER    │
                                          │ <= MAX_PACKET_SIZE ? │
                                          └──────────┬───────────┘
                                                     │
                                      ┌──────────────┴──────────────┐
                                      │ YES                         │ NO
                                      ▼                             ▼
                             sendSinglePacket()         sendFragmented()
                             (单包发送)                  (分片发送)
```

---

## 4. 分片机制

### 4.1 为什么需要分片

UDP 协议限制单个数据包最大为 65507 字节（IPv4）。当视频帧超过此限制时（如高分辨率 I 帧），需要分片发送。

### 4.2 分片参数

**文件**: `UdpMediaSender.java:127`

```java
int maxFragmentData = MAX_PACKET_SIZE - HEADER_SIZE - 4;  // 减去 4 字节分片索引
// 实际: 65507 - 24 - 4 = 65479 字节
```

### 4.3 分片发送流程

**文件**: `UdpMediaSender.java:120-171`

```java
private void sendFragmented(ByteBuffer data, long timestamp, long flags)
        throws IOException {
    long sendTimeNs = System.nanoTime();
    int fragmentIndex = 0;
    int maxFragmentData = MAX_PACKET_SIZE - HEADER_SIZE - 4;

    // 第一个分片
    int firstChunkSize = Math.min(totalData, maxFragmentData);
    ByteBuffer firstChunk = ByteBuffer.allocate(HEADER_SIZE + 4 + firstChunkSize);

    firstChunk.putInt(sequence++);
    firstChunk.putLong(timestamp);
    long fragFlags = flags | (1L << 31);  // 设置分片标志
    firstChunk.putInt((int) fragFlags);
    firstChunk.putLong(sendTimeNs);
    firstChunk.putInt(fragmentIndex++);   // 分片索引

    // 复制数据（包含 scrcpy 头部）
    byte[] temp = new byte[firstChunkSize];
    data.get(temp);
    firstChunk.put(temp);

    firstChunk.flip();
    socket.send(new DatagramPacket(firstChunk.array(), ...));

    // 后续分片
    while (data.hasRemaining()) {
        int chunkSize = Math.min(data.remaining(), maxFragmentData);
        ByteBuffer chunk = ByteBuffer.allocate(HEADER_SIZE + 4 + chunkSize);

        // ... 同样的头部构建 ...

        socket.send(...);
    }
}
```

### 4.4 分片格式图示

```
原始帧 (100KB):
┌────────────────────────────────────────────────────────────────────┐
│ Scrcpy Header (12B) │              Frame Data (100KB)              │
└────────────────────────────────────────────────────────────────────┘

分片后:

Fragment 0:
┌─────────────────────────────────────────────────────────────────────┐
│ UDP Header (24B) │ FragIdx (4B) │ Scrcpy (12B) │ Data (65467B)     │
│ flags=0x80000001 │ idx=0        │              │                   │
└─────────────────────────────────────────────────────────────────────┘

Fragment 1:
┌─────────────────────────────────────────────────────────────────────┐
│ UDP Header (24B) │ FragIdx (4B) │ Data (65479B)                     │
│ flags=0x80000001 │ idx=1        │                                   │
└─────────────────────────────────────────────────────────────────────┘

Fragment 2:
┌─────────────────────────────────────────────────────────────────────┐
│ UDP Header (24B) │ FragIdx (4B) │ Data (剩余字节)                    │
│ flags=0x80000001 │ idx=2        │                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.5 客户端重组逻辑

**文件**: `udp_packet_reader.py:261-326`

客户端通过 `timestamp` 分组，按 `frag_idx` 排序重组：

```python
def _reassemble_fragment(self, timestamp, flags, frag_idx, data):
    # 获取或创建分片缓冲区
    if timestamp not in self._fragment_buffers:
        self._fragment_buffers[timestamp] = FragmentBuffer(...)

    frag_buf = self._fragment_buffers[timestamp]
    frag_buf.fragments[frag_idx] = data

    # 从第一个分片提取预期大小
    if frag_idx == 0 and len(data) >= 12:
        _, expected_payload_size = struct.unpack('>QI', data[:12])
        frag_buf.expected_size = 12 + expected_payload_size

    # 检查是否接收完整
    if frag_buf.total_size >= frag_buf.expected_size:
        # 按顺序重组
        reassembled = b''
        for i in sorted(frag_buf.fragments.keys()):
            reassembled += frag_buf.fragments[i]
        return reassembled
```

---

## 5. FEC 前向纠错

### 5.1 FEC 原理

FEC (Forward Error Correction) 通过发送冗余数据，在丢包时无需重传即可恢复数据。

本项目采用简单的 XOR 方式：
- 将 K 个数据包分为一组
- 对 K 个包进行 XOR 运算生成 M 个校验包
- 可恢复最多 M 个丢失的数据包

```
原始数据:
  D0, D1, D2, D3 (K=4)

生成校验:
  P0 = D0 XOR D1 XOR D2 XOR D3

发送:
  D0, D1, D2, D3, P0 (5 个包)

如果 D1 丢失:
  D1 = D0 XOR D2 XOR D3 XOR P0
```

### 5.2 SimpleXorFecEncoder 类

**文件**: `SimpleXorFecEncoder.java`

```java
public class SimpleXorFecEncoder {
    private final int groupSize;      // K: 每组帧数
    private final int parityCount;    // M: 校验包数
    private int currentGroupId = 0;   // 当前组 ID
    private int currentFrameIdx = 0;  // 当前帧索引 (0 到 K-1)

    // 累积当前帧的所有数据包
    private ByteArrayOutputStream currentFrameStream = null;

    // 已完成的帧数据列表
    private final List<byte[]> frameDataList = new ArrayList<>();
}
```

### 5.3 FEC 发送流程

**文件**: `UdpMediaSender.java:308-355`

```java
public void sendPacketWithFec(ByteBuffer data, long timestamp,
                               boolean config, boolean keyFrame) throws IOException {
    // 配置包不使用 FEC
    if (config) {
        sendPacket(data, timestamp, config, keyFrame);
        return;
    }

    // 检测新帧
    boolean isNewFrame = (lastTimestamp != timestamp);
    if (isNewFrame) {
        // 标记上一帧完成
        if (fecEncoder.hasIncompleteGroup()) {
            fecEncoder.frameComplete();
        }
        lastTimestamp = timestamp;
    }

    // 发送数据包 (带 FEC 头部)
    ByteBuffer fecWrapped = fecEncoder.addPacket(data);
    sendFecDataPacket(fecWrapped, timestamp, keyFrame);

    // 检查是否完成一个 FEC 组
    if (fecEncoder.shouldFinalizeGroup()) {
        // 生成并发送校验包
        List<ByteBuffer> parityPackets = fecEncoder.generateParityPackets();
        for (ByteBuffer parity : parityPackets) {
            sendFecParityPacket(parity, timestamp);
        }
    }
}
```

### 5.4 FEC 组时序图

```
时间 ─────────────────────────────────────────────────────────────────────>

Frame 0     Frame 1     Frame 2     Frame 3     Frame 4     Frame 5
    │           │           │           │           │           │
    ▼           ▼           ▼           ▼           ▼           ▼
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│FEC_DATA│  │FEC_DATA│  │FEC_DATA│  │FEC_DATA│  │FEC_DATA│  │FEC_DATA│
│group=0 │  │group=0 │  │group=0 │  │group=0 │  │group=1 │  │group=1 │
│idx=0   │  │idx=1   │  │idx=2   │  │idx=3   │  │idx=0   │  │idx=1   │
└────────┘  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘
                                        │
                                        ▼
                                   ┌─────────┐
                                   │FEC_PARITY│  <- 组 0 完成后发送
                                   │group=0  │
                                   └─────────┘
```

### 5.5 FEC 头部格式

#### 数据包头部 (7 字节)

```
偏移量   字段           大小    描述
------   ----           ----    ----
0        group_id       2       组标识 (uint16, big-endian)
2        frame_idx      1       帧索引 (0 到 K-1)
3        total_frames   1       总帧数 (K)
4        total_parity   1       校验包数 (M)
5        original_size  2       原始数据大小 (用于恢复)
```

#### 校验包头部 (5 字节)

```
偏移量   字段           大小    描述
------   ----           ----    ----
0        group_id       2       组标识 (uint16, big-endian)
2        parity_idx     1       校验包索引 (0 到 M-1)
3        total_frames   1       总帧数 (K)
4        total_parity   1       校验包数 (M)
```

### 5.6 大帧 FEC 分片

当校验数据超过 UDP MTU 时，需要分片发送：

**文件**: `UdpMediaSender.java:260-296`

```java
private void sendFragmentedFecParityPacket(ByteBuffer fecParity, long timestamp)
        throws IOException {
    long flags = FLAG_FEC_PARITY | (1L << 31);  // FEC + 分片标志
    int maxFragmentData = MAX_PACKET_SIZE - HEADER_SIZE - 5 - 4;  // FEC 头 + 分片索引

    while (fecParity.hasRemaining()) {
        int chunkSize = Math.min(fecParity.remaining(), maxFragmentData);

        ByteBuffer packet = ByteBuffer.allocate(HEADER_SIZE + chunkSize + 4);
        packet.putInt(sequence++);
        packet.putLong(timestamp);
        packet.putInt((int) flags);
        packet.putLong(sendTimeNs);
        packet.putInt(fragmentIndex);  // 分片索引

        // 复制校验数据片段
        byte[] temp = new byte[chunkSize];
        fecParity.get(temp);
        packet.put(temp);

        socket.send(...);
        fragmentIndex++;
    }
}
```

---

## 6. 流量控制

### 6.1 当前实现特点

当前实现**没有显式的流量控制**，依赖以下机制：

| 机制 | 说明 |
|------|------|
| UDP 无阻塞 | 发送即忘，不等待确认 |
| 客户端缓冲 | 客户端使用小缓冲 (1-2 帧) |
| 丢包容忍 | 丢包则等待下一关键帧 |

### 6.2 潜在问题

1. **网络拥塞**: 高码率 + 弱网 = 大量丢包
2. **缓冲溢出**: 客户端处理慢于发送速度
3. **延迟累积**: 队列增长导致延迟增加

### 6.3 改进方向 (未来)

```
┌─────────────────────────────────────────────────────────────────┐
│                     流量控制改进方案                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 基于丢包率的自适应码率                                       │
│     - 客户端统计丢包率                                           │
│     - 通过控制通道反馈给服务端                                    │
│     - 服务端动态调整 MediaCodec 码率                              │
│                                                                 │
│  2. 接收端缓冲反馈                                               │
│     - 客户端定期报告缓冲状态                                      │
│     - 服务端根据反馈调整发送速率                                  │
│                                                                 │
│  3. 拥塞控制算法                                                 │
│     - 类似 GCC (Google Congestion Control)                       │
│     - 基于延迟梯度和丢包率                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. 关键代码位置

### 7.1 服务端代码

| 功能 | 文件 | 关键方法/常量 |
|------|------|--------------|
| UDP 发送器 | `udp/UdpMediaSender.java` | `sendPacket()`, `sendFragmented()`, `sendPacketWithFec()` |
| UDP 头部常量 | `udp/UdpMediaSender.java:14` | `HEADER_SIZE = 24` |
| UDP 标志位 | `udp/UdpMediaSender.java:16-19` | `FLAG_*` |
| FEC 编码器 | `udp/SimpleXorFecEncoder.java` | `addPacket()`, `generateParityPackets()` |
| 流处理器 | `device/Streamer.java` | `writePacket()` |
| 视频编码器 | `video/SurfaceEncoder.java` | `encode()` |

### 7.2 客户端代码

| 功能 | 文件 | 关键方法/常量 |
|------|------|--------------|
| UDP 包读取器 | `client/udp_packet_reader.py` | `recv()`, `_receive_packet()`, `_reassemble_fragment()` |
| 协议常量 | `core/protocol.py` | `UDP_HEADER_SIZE`, `UDP_FLAG_*` |
| UDP 头部大小 | `core/protocol.py:280` | `UDP_HEADER_SIZE = 24` |

### 7.3 关键常量对照表

| 常量 | 服务端 (Java) | 客户端 (Python) |
|------|--------------|-----------------|
| UDP 头部大小 | `HEADER_SIZE = 24` | `UDP_HEADER_SIZE = 24` |
| 关键帧标志 | `FLAG_KEY_FRAME = 1L << 0` | `UDP_FLAG_KEY_FRAME = 1 << 0` |
| 配置包标志 | `FLAG_CONFIG = 1L << 1` | `UDP_FLAG_CONFIG = 1 << 1` |
| FEC 数据标志 | `FLAG_FEC_DATA = 1L << 2` | `UDP_FLAG_FEC_DATA = 1 << 2` |
| FEC 校验标志 | `FLAG_FEC_PARITY = 1L << 3` | `UDP_FLAG_FEC_PARITY = 1 << 3` |
| 分片标志 | `1L << 31` | `UDP_FLAG_FRAGMENTED = 1 << 31` |
| 最大 UDP 包 | `MAX_PACKET_SIZE = 65507` | `MAX_UDP_PACKET = 65507` |

---

## 附录 A: 调试日志示例

### A.1 正常包发送日志

```
D/UDP: UDP packet #1: size=52, ts=0, flags=0x2, send_ns=1234567890123456, hex=8000000000000000000000c683236340000078000000438
D/UDP: UDP sent: 52 bytes to 192.168.1.100:27185
```

### A.2 分片包发送日志

```
D/UDP: Fragmenting large frame: total=100000 bytes
D/UDP: Sent fragment 0: 65479 bytes
D/UDP: Sent fragment 1: 34521 bytes
```

### A.3 FEC 发送日志

```
D/FEC: FEC encoder initialized: K=4, M=1 (optimized frame-level FEC)
D/FEC: FEC data sent: 1234 bytes, keyFrame=true
D/FEC: FEC group complete: sent 1 parity for 4 frames
D/FEC: FEC parity sent: 71293 bytes
```

---

## 附录 B: 常见问题排查

### B.1 包解析错误

**症状**: `Payload size 2897478176 exceeds maximum`

**可能原因**:
1. 客户端 UDP_HEADER_SIZE 与服务端不一致
2. 分片包重组失败
3. 第一个配置包未正确处理

**排查步骤**:
1. 检查客户端 `protocol.py` 的 `UDP_HEADER_SIZE` 是否为 24
2. 查看客户端日志中的 hex dump
3. 对比服务端日志中的发送数据

### B.2 丢包严重

**症状**: 视频花屏、卡顿

**可能原因**:
1. WiFi 信号弱
2. 码率过高
3. 分片过多导致丢失概率增加

**排查步骤**:
1. 检查丢包统计
2. 降低视频码率
3. 启用 FEC

### B.3 延迟高

**症状**: 画面明显滞后

**可能原因**:
1. 客户端解码慢
2. 网络拥塞
3. 缓冲过多

**排查步骤**:
1. 检查 E2E 延迟统计（send_time_ns）
2. 检查客户端 CPU 占用
3. 减少客户端缓冲区大小

---

**文档维护者**: Claude AI
**参考文档**:
- [PROTOCOL_SPEC.md](../PROTOCOL_SPEC.md) - 完整协议规范
- [FEC_PLI_PROTOCOL_SPEC.md](../FEC_PLI_PROTOCOL_SPEC.md) - FEC/PLI 扩展规范
