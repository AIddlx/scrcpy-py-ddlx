# UdpMediaSender.java - UDP 发送器

> **路径**: `scrcpy/server/src/main/java/com/genymobile/scrcpy/udp/UdpMediaSender.java`
> **职责**: UDP 媒体数据发送器，支持分片和 FEC

---

## 常量

### 包大小

| 常量 | 值 | 说明 |
|------|-----|------|
| `MAX_PACKET_SIZE` | 65507 | UDP 最大负载 |
| `HEADER_SIZE` | 24 | UDP 头大小 |

### 标志位

| 常量 | 值 | 说明 |
|------|-----|------|
| `FLAG_KEY_FRAME` | 1L << 0 | 关键帧 |
| `FLAG_CONFIG` | 1L << 1 | 配置包 |
| `FLAG_FEC_DATA` | 1L << 2 | FEC 数据包 |
| `FLAG_FEC_PARITY` | 1L << 3 | FEC 校验包 |

---

## UDP 包格式 (24字节头)

```
[seq:4B][timestamp:8B][flags:4B][send_time_ns:8B][data...]
```

| 偏移 | 大小 | 字段 | 说明 |
|------|------|------|------|
| 0 | 4 | seq | 序列号 (BE) |
| 4 | 8 | timestamp | 时间戳 (BE) |
| 12 | 4 | flags | 标志位 (BE) |
| 16 | 8 | send_time_ns | 发送时间纳秒 (BE) |
| 24 | N | data | 负载数据 |

---

## 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `sendPacket` | ByteBuffer, pts, keyFrame, config | void | 发送数据包 |
| `sendPacketWithFec` | ByteBuffer, pts, keyFrame, config | void | 带 FEC 发送 |
| `enableFec` | groupSize, parityCount, mode | void | 启用 FEC |
| `sendFecDataPacket` | ByteBuffer, pts, keyFrame | void | 发送 FEC 数据包 |
| `sendFecParityPacket` | ByteBuffer, pts | void | 发送 FEC 校验包 |

---

## 分片逻辑

```
if (dataSize > MAX_PACKET_SIZE - HEADER_SIZE) {
    // 分片发送
    for each fragment:
        sendFragment(fragment, fragmentIndex, totalFragments)
} else {
    // 单包发送
    sendSinglePacket(data)
}
```

---

## FEC 模式

### Frame Mode

```
每 K 帧生成 M 个校验包
适用于帧级别保护
```

### Fragment Mode

```
每 K 个分片生成 M 个校验包
适用于分片级别保护
```

---

## 依赖关系

```
UdpMediaSender
    │
    ├──→ DatagramSocket (UDP socket)
    │
    ├──→ SimpleXorFecEncoder (FEC 编码)
    │
    └──→ InetAddress (目标地址)
```

---

## 使用示例

```java
// 创建发送器
UdpMediaSender sender = new UdpMediaSender(socket, clientAddr, clientPort);

// 发送普通包
sender.sendPacket(buffer, pts, isKeyFrame, isConfig);

// 启用 FEC
sender.enableFec(4, 1, "frame");  // K=4, M=1

// 带 FEC 发送
sender.sendPacketWithFec(buffer, pts, isKeyFrame, isConfig);
```

---

*此文档基于服务端代码分析生成*
