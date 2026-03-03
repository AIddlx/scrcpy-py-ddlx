# scrcpy-py-ddlx 协议交互流程详解

> **版本**: 1.3
> **最后更新**: 2026-02-23
> **基于**: PROTOCOL_SPEC.md v1.3

本文档详细描述客户端和服务端之间的协议交互流程，包括消息格式定义和时序图。

---

## 目录

1. [协议层概述](#1-协议层概述)
2. [连接建立流程](#2-连接建立流程)
3. [TCP 控制通道消息格式](#3-tcp-控制通道消息格式)
4. [UDP 视频流协议头](#4-udp-视频流协议头)
5. [能力协商流程](#5-能力协商流程)
6. [心跳机制](#6-心跳机制)
7. [PLI 请求机制](#7-pli-请求机制)
8. [FEC 协议扩展](#8-fec-协议扩展)

---

## 1. 协议层概述

### 1.1 双通道架构

```
+------------------+                    +------------------+
|     Client       |                    |     Server       |
|    (Python)      |                    |    (Android)     |
+--------+---------+                    +--------+---------+
         |                                       |
         |  ┌─────────────────────────────────┐  |
         |  │       TCP Control Channel       │  |
         |  │   - 控制消息 (触摸/键盘等)        │  |
         |  │   - 设备消息 (剪贴板/截图等)      │  |
         |  │   - 心跳 (PING/PONG)            │  |
         |  └─────────────────────────────────┘  |
         |                                       |
         |  ┌─────────────────────────────────┐  |
         |  │       UDP Media Channel         │  |
         |  │   - 视频流 (H.264/H.265/AV1)    │  |
         |  │   - 音频流 (OPUS/FLAC/AAC)      │  |
         |  │   - FEC 数据包 (可选)            │  |
         |  └─────────────────────────────────┘  |
         |                                       |
+--------+---------------------------------------+---------+
```

### 1.2 端口分配（网络 UDP 模式）

| 端口 | 用途 | 协议 |
|------|------|------|
| 27183 | UDP 发现 (Wake-on-LAN) | UDP |
| 27184 | TCP 控制通道 | TCP |
| 27185 | UDP 视频流 | UDP |
| 27186 | UDP 音频流 | UDP |

---

## 2. 连接建立流程

### 2.1 网络 UDP 模式（带能力协商）

```
┌─────────────┐                    ┌─────────────┐
│   客户端     │                    │   服务端     │
└──────┬──────┘                    └──────┬──────┘
       │                                  │
       │  1. 绑定 UDP 视频/音频端口        │
       │  (等待接收)                       │
       │                                  │
       │  2. 连接 TCP 控制端口             │
       │─────────────────────────────────>│
       │                                  │
       │  3. 接收 dummy byte (1字节)       │
       │<─────────────────────────────────│
       │     0x00                          │
       │                                  │
       │  4. 接收设备名 (64字节, TCP)       │
       │<─────────────────────────────────│
       │     UTF-8 字符串, 空字节填充       │
       │                                  │
       │  5. 接收设备能力信息 (TCP)         │
       │<─────────────────────────────────│
       │     见 5.1 设备能力格式            │
       │                                  │
       │  6. 发送客户端配置 (TCP)           │
       │─────────────────────────────────>│
       │     见 5.2 客户端配置格式          │
       │                                  │
       │  7. 接收视频配置包 (UDP)           │
       │  [UDP头24B] [scrcpy头12B] [配置]  │
       │<─────────────────────────────────│
       │                                  │
       │  8. 开始接收视频帧 (UDP)           │
       │<─────────────────────────────────│
       │                                  │
       │  9. 启动心跳线程                   │
       │  (每2秒发送 PING)                 │
       │                                  │
```

### 2.2 ADB 隧道模式

```
┌─────────────┐                    ┌─────────────┐
│   客户端     │                    │   服务端     │
└──────┬──────┘                    └──────┬──────┘
       │                                  │
       │  1. adb forward 创建隧道          │
       │─────────────────────────────────>│
       │                                  │
       │  2. 连接到本地转发端口             │
       │─────────────────────────────────>│
       │                                  │
       │  3. 接收 dummy byte (1字节)       │
       │<─────────────────────────────────│
       │                                  │
       │  4. 接收设备名 (64字节)            │
       │<─────────────────────────────────│
       │                                  │
       │  5. 接收 codec_id (4字节, 原始)   │
       │<─────────────────────────────────│
       │     注意：无 scrcpy 头部!          │
       │                                  │
       │  6. 接收视频尺寸 (8字节, 原始)     │
       │<─────────────────────────────────│
       │     width: 4B, height: 4B        │
       │                                  │
       │  7. 开始接收视频帧 (带 scrcpy 头部) │
       │<─────────────────────────────────│
       │                                  │
```

**关键差异**: ADB 模式下，`codec_id` 和视频尺寸是**原始字节**，没有 scrcpy 头部！

---

## 3. TCP 控制通道消息格式

### 3.1 控制消息通用格式

所有控制消息以类型字节开头：

```
+--------+--------+--------+--------+--------+--------+
| Type   | Length (可选)    | Data (可选)              |
| 1 byte | 4 bytes (BE)     | N bytes                  |
+--------+--------+--------+--------+--------+--------+
```

### 3.2 客户端 -> 服务端 消息类型

| 类型值 | 名称 | 数据格式 | 说明 |
|--------|------|----------|------|
| 0x00 | INJECT_KEYCODE | `action:1 keycode:4 repeat:4 metastate:4` | 键盘事件 |
| 0x01 | INJECT_TEXT | `length:4 text:N` | 文本输入 |
| 0x02 | INJECT_TOUCH_EVENT | 见下方详细格式 | 触摸事件 |
| 0x03 | INJECT_SCROLL_EVENT | `x:4 y:4 w:2 h:2 hscroll:2 vscroll:2 buttons:4` | 滚轮事件 |
| 0x04 | BACK_OR_SCREEN_ON | `action:1` | 返回键/唤醒 |
| 0x05 | EXPAND_NOTIFICATION_PANEL | 无 | 展开通知 |
| 0x06 | EXPAND_SETTINGS_PANEL | 无 | 展开设置 |
| 0x07 | COLLAPSE_PANELS | 无 | 收起面板 |
| 0x08 | GET_CLIPBOARD | `copy_key:1` | 获取剪贴板 |
| 0x09 | SET_CLIPBOARD | `seq:8 paste:1 length:4 text:N` | 设置剪贴板 |
| 0x0A | SET_DISPLAY_POWER | `on:1` | 屏幕电源 |
| 0x0B | ROTATE_DEVICE | 无 | 旋转设备 |
| 0x0C-0x0E | UHID_* | `id:2 ...` | UHID 操作 |
| 0x0F | OPEN_HARD_KEYBOARD_SETTINGS | 无 | 打开硬键盘设置 |
| 0x10 | START_APP | `length:1 name:N` | 启动应用 |
| 0x11 | RESET_VIDEO | 无 | 重置视频/PLI |
| 0x12 | SCREENSHOT | 无 | 截图请求 |
| 0x13 | GET_APP_LIST | 无 | 获取应用列表 |
| 0x14-0x18 | *_VIDEO/AUDIO | 无 | 媒体流控制 |
| **0x19** | **PING** | `timestamp:8` | **心跳请求** |

### 3.3 触摸事件详细格式

```
INJECT_TOUCH_EVENT (type=0x02):
+------+------+------+------+------+------+------+------+------+------+
|Type  |Action|Pointer ID    |X     |Y     |W     |H     |Press |ABtn  |Btns  |
|1     |1     |8             |4     |4     |2     |2     |2     |4     |4     |
+------+------+------+------+------+------+------+------+------+------+

Action: 0=DOWN, 1=UP, 2=MOVE, 3=CANCEL, ...
Pointer ID: 特殊值 -1=鼠标, -2=通用手指, -3=虚拟手指
Pressure: 0.0-1.0 编码为 0-65536 的 uint16 定点数
```

### 3.4 服务端 -> 客户端 消息类型

| 类型值 | 名称 | 数据格式 | 说明 |
|--------|------|----------|------|
| 0x00 | CLIPBOARD | `length:4 text:N` | 剪贴板内容 |
| 0x01 | ACK_CLIPBOARD | `sequence:8` | 剪贴板确认 |
| 0x02 | UHID_OUTPUT | `id:2 size:2 data:N` | UHID 输出 |
| 0x03 | APP_LIST | 应用列表数据 | 应用列表 |
| 0x04 | SCREENSHOT | `length:4 data:N` | JPEG 截图数据 |
| **0x05** | **PONG** | `timestamp:8` | **心跳响应** |

---

## 4. UDP 视频流协议头

### 4.1 UDP 头部格式（24 字节）

```
偏移量   字段          大小    类型      描述
------   ----          ----    ----      ----
0        sequence      4       uint32    包序列号（big-endian）
4        timestamp     8       int64     PTS 时间戳（big-endian）
12       flags         4       uint32    标志位（big-endian）
16       send_time_ns  8       int64     设备发送时间（big-endian）
```

### 4.2 flags 字段位定义

```
位 0:    KEY_FRAME    - 1 表示关键帧
位 1:    CONFIG       - 1 表示配置包
位 2:    FEC_DATA     - 1 表示 FEC 数据包
位 3:    FEC_PARITY   - 1 表示 FEC 校验包
位 4-30: RESERVED     - 保留，设为 0
位 31:   FRAGMENTED   - 1 表示分片包
```

### 4.3 完整 UDP 数据包结构

```
普通包:
+------------------+------------------+------------------+------------------+
| UDP Header (24B) | Scrcpy Header    | Payload          |
| seq|ts|flags|ns  | pts_flags|size   | H.264/H.265 data |
+------------------+------------------+------------------+------------------+

分片包:
+------------------+------------+------------------+
| UDP Header (24B) | frag_idx   | Fragment data    |
|                  | 4 bytes    | up to ~65KB      |
+------------------+------------+------------------+

FEC 数据包:
+------------------+----------------+------------------+------------------+
| UDP Header (24B) | FEC Header (7B)| Scrcpy Header    | Payload          |
|                  | gid|idx|K|M|sz|                  |                  |
+------------------+----------------+------------------+------------------+

FEC 校验包:
+------------------+------------------+------------------+
| UDP Header (24B) | FEC Parity Hdr   | Parity data      |
|                  | gid|idx|K|M (5B) |                  |
+------------------+------------------+------------------+
```

### 4.4 Scrcpy 标准数据包头部（12 字节）

```
偏移量   字段          大小    类型      描述
------   ----          ----    ----      ----
0        pts_flags     8       uint64    PTS + 标志位（big-endian）
8        size          4       uint32    负载大小（big-endian）

pts_flags 字段位定义:
  位 63: CONFIG 标志    - 1 表示配置包
  位 62: KEY_FRAME 标志 - 1 表示关键帧
  位 0-61: PTS 值       - 演示时间戳（微秒）
```

---

## 5. 能力协商流程

### 5.1 设备能力信息格式

服务端通过 TCP 控制通道发送：

```
偏移量   字段                    大小      类型      描述
------   ----                    ----      ----      ----
0        screen_width            4        uint32    屏幕宽度（BE）
4        screen_height           4        uint32    屏幕高度（BE）
8        video_encoder_count     1        uint8     视频编码器数量
9        video_encoders          N*12     bytes     视频编码器列表
         - codec_id              4        uint32    编码器ID
         - flags                 4        uint32    标志位 (bit0=硬件)
         - priority              4        uint32    推荐优先级
9+N*12   audio_encoder_count     1        uint8     音频编码器数量
10+N*12  audio_encoders          M*12     bytes     音频编码器列表
```

**编码器 ID 对照表**:
```
视频: h264=0x68323634, h265=0x68323635, av1=0x00617631
音频: opus=0x6f707573, aac=0x00000003, flac=0x00000004
```

### 5.2 客户端配置格式

客户端选择配置后发送（32 字节）：

```
偏移量   字段                    大小      类型      描述
------   ----                    ----      ----      ----
0        video_codec_id          4        uint32    选择的视频编码器
4        audio_codec_id          4        uint32    选择的音频编码器
8        video_bitrate           4        uint32    视频码率 (bps)
12       audio_bitrate           4        uint32    音频码率 (bps)
16       max_fps                 4        uint32    最大帧率
20       config_flags            4        uint32    配置标志位
24       reserved                4        uint32    保留（填0）
28       i_frame_interval        4        float     I帧间隔（秒，IEEE754 BE）
```

**config_flags 定义**:
```
bit 0: 启用音频
bit 1: 启用视频
bit 2: CBR 模式 (0=VBR)
bit 3: 启用视频 FEC
bit 4: 启用音频 FEC
```

### 5.3 编码器选择策略

```python
def select_best_video_codec(capabilities):
    """
    优先级: AV1 > H.265 > H.264
    优先选择硬件编码器
    """
    priority_order = [AV1, H265, H264]

    for codec in priority_order:
        # 优先硬件编码器
        for encoder in capabilities.video_encoders:
            if encoder.codec_id == codec and encoder.is_hardware():
                return codec
        # 其次软件编码器
        for encoder in capabilities.video_encoders:
            if encoder.codec_id == codec:
                return codec

    return H264  # 默认
```

---

## 6. 心跳机制

### 6.1 心跳时序图

```
┌─────────────────┐                    ┌─────────────────┐
│    客户端        │                    │    服务端        │
└────────┬────────┘                    └────────┬────────┘
         │                                      │
         │  ──── PING (每2秒) ─────────────────>│
         │      type: 0x19 (25)                 │
         │      timestamp: 当前时间(微秒)        │
         │                                      │
         │                      处理 PING        │
         │                      Controller.java  │
         │                      handlePing()     │
         │                                      │
         │  <─── PONG (立即响应) ────────────────│
         │      type: 0x05 (5)                  │
         │      timestamp: 回显                 │
         │                                      │
         │  如果 5 秒无 PONG 响应：              │
         │  → 断开连接                          │
         │                                      │
```

### 6.2 PING 消息格式

```
客户端 -> 服务端:
+--------+--------+--------+--------+--------+--------+--------+--------+--------+
| Type   | Timestamp (8 bytes, big-endian, microseconds)                            |
| 0x19   |                                                                          |
+--------+--------+--------+--------+--------+--------+--------+--------+--------+

总大小: 9 字节
```

### 6.3 PONG 消息格式

```
服务端 -> 客户端:
+--------+--------+--------+--------+--------+--------+--------+--------+--------+
| Type   | Timestamp (8 bytes, big-endian, 回显 PING 的时间戳)                      |
| 0x05   |                                                                          |
+--------+--------+--------+--------+--------+--------+--------+--------+--------+

总大小: 9 字节
```

### 6.4 超时参数

| 参数 | 值 | 说明 |
|------|---|------|
| PING_INTERVAL | 2.0 秒 | PING 发送间隔 |
| TIMEOUT | 5.0 秒 | 无 PONG 响应超时时间 |

### 6.5 实现位置

| 组件 | 文件 |
|------|------|
| 服务端 PING 处理 | `Controller.java` - `handlePing()` |
| 服务端 PONG 发送 | `DeviceMessage.java` - `createPong()` |
| 客户端心跳管理器 | `heartbeat.py` - `HeartbeatManager` |
| 客户端 PING 发送 | `control.py` - `set_ping()` |
| 客户端 PONG 接收 | `device_msg.py` - `_process_pong()` |

---

## 7. PLI 请求机制

### 7.1 PLI 触发条件

| 条件 | 描述 |
|------|------|
| 连续丢包 >= N | `consecutive_drops >= pli_threshold` (默认 10) |
| 关键帧丢失 | 检测到 KEY_FRAME 包丢失 |
| FEC 恢复失败 | FEC 组内丢失包数 > 冗余度 |
| 分片丢失 | 关键帧的分片 0 丢失 |

### 7.2 PLI 请求流程

```
┌─────────────────┐                    ┌─────────────────┐
│    客户端        │                    │    服务端        │
│ UdpVideoDemuxer │                    │   Controller    │
└────────┬────────┘                    └────────┬────────┘
         │                                      │
         │  检测到连续丢包 >= 10                 │
         │                                      │
         │  ──── RESET_VIDEO ──────────────────>│
         │      type: 0x11 (17)                 │
         │      (仅 1 字节)                      │
         │                                      │
         │                      处理 RESET_VIDEO │
         │                      resetVideo()     │
         │                      requestSyncFrame()│
         │                                      │
         │  <─── 新的关键帧 (UDP) ───────────────│
         │      flags |= KEY_FRAME              │
         │                                      │
```

### 7.3 PLI 配置参数

```python
DEFAULT_PLI_THRESHOLD = 10    # 连续丢包多少次后发送 PLI
DEFAULT_PLI_COOLDOWN = 1.0    # PLI 请求冷却时间（秒）
```

---

## 8. FEC 协议扩展

### 8.1 FEC 组概念

```
FEC Group (组):
├── Data Packet 0  [seq=N+0, ts=T, flags=FEC_DATA]
├── Data Packet 1  [seq=N+1, ts=T, flags=FEC_DATA]
├── Data Packet 2  [seq=N+2, ts=T, flags=FEC_DATA]
├── Data Packet 3  [seq=N+3, ts=T, flags=FEC_DATA]
├── Parity Packet 0 [seq=N+4, ts=T, flags=FEC_PARITY]  # XOR of 0-3
└── Parity Packet 1 [seq=N+5, ts=T, flags=FEC_PARITY]  # 可选

参数:
- K = 4 (数据包数)
- M = 2 (校验包数)
- 可恢复任意 min(M, K) 个丢失包
```

### 8.2 FEC 数据包格式

```
[UDP Header: 24B] [FEC Header: 7B] [Scrcpy Header: 12B] [Payload: NB]

FEC Header (7 bytes):
  group_id: 2B (uint16, BE) - 组标识
  frame_idx: 1B (uint8) - 帧索引 (0 到 K-1)
  total_frames: 1B (uint8) - K
  total_parity: 1B (uint8) - M
  original_size: 2B (uint16, BE) - 原始大小
```

### 8.3 FEC 校验包格式

```
[UDP Header: 24B] [FEC Parity Header: 5B] [Parity Data: NB]

FEC Parity Header (5 bytes):
  group_id: 2B (uint16, BE) - 组标识
  parity_idx: 1B (uint8) - 校验包索引 (0 到 M-1)
  total_data: 1B (uint8) - K
  total_parity: 1B (uint8) - M
```

### 8.4 FEC 恢复流程

```
客户端收到:
  Data[0] ✓, Data[1] ✗, Data[2] ✓, Data[3] ✓, Parity[0] ✓

恢复算法:
  Data[1] = Data[0] XOR Data[2] XOR Data[3] XOR Parity[0]
```

---

## 附录 A: 消息类型快速参考

### A.1 控制消息 (Client -> Server)

```
0x00 INJECT_KEYCODE
0x01 INJECT_TEXT
0x02 INJECT_TOUCH_EVENT
0x03 INJECT_SCROLL_EVENT
0x04 BACK_OR_SCREEN_ON
0x05 EXPAND_NOTIFICATION_PANEL
0x06 EXPAND_SETTINGS_PANEL
0x07 COLLAPSE_PANELS
0x08 GET_CLIPBOARD
0x09 SET_CLIPBOARD
0x0A SET_DISPLAY_POWER
0x0B ROTATE_DEVICE
0x0C UHID_CREATE
0x0D UHID_INPUT
0x0E UHID_DESTROY
0x0F OPEN_HARD_KEYBOARD_SETTINGS
0x10 START_APP
0x11 RESET_VIDEO (PLI)
0x12 SCREENSHOT
0x13 GET_APP_LIST
0x14 REQUEST_VIDEO_FRAME
0x15 START_VIDEO
0x16 STOP_VIDEO
0x17 START_AUDIO
0x18 STOP_AUDIO
0x19 PING (Heartbeat)
```

### A.2 设备消息 (Server -> Client)

```
0x00 CLIPBOARD
0x01 ACK_CLIPBOARD
0x02 UHID_OUTPUT
0x03 APP_LIST
0x04 SCREENSHOT
0x05 PONG (Heartbeat)
```

---

## 附录 B: 关键文件位置

### B.1 服务端

| 功能 | 文件 |
|------|------|
| 控制消息定义 | `ControlMessage.java` |
| 设备消息定义 | `DeviceMessage.java` |
| 控制器 | `Controller.java` |
| UDP 发送器 | `udp/UdpMediaSender.java` |
| FEC 编码器 | `udp/SimpleXorFecEncoder.java` |
| 能力协商 | `device/CapabilityNegotiation.java` |

### B.2 客户端

| 功能 | 文件 |
|------|------|
| 协议常量 | `core/protocol.py` |
| 控制消息 | `core/control.py` |
| 设备消息 | `core/device_msg.py` |
| 心跳管理 | `core/heartbeat.py` |
| 能力协商 | `core/negotiation.py` |
| UDP 视频解复用 | `core/demuxer/udp_video.py` |

---

**文档维护者**: Claude AI
**确认状态**: 基于代码分析完成
