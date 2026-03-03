# stream.py

> **文件**: `core/stream.py`
> **功能**: TCP 视频流解析器

---

## 概述

`stream.py` 实现 scrcpy TCP 模式的视频流解析，包括包头解析和配置包合并。

---

## 数据类

### PacketHeader

```python
@dataclass
class PacketHeader:
    pts_flags: int      # 原始 PTS + 标志
    pts: int            # 显示时间戳
    size: int           # 负载大小
    is_config: bool     # 是否配置包
    is_key_frame: bool  # 是否关键帧
```

### VideoPacket

```python
@dataclass
class VideoPacket:
    header: PacketHeader
    data: bytes         # 负载数据
    codec_id: int       # 编解码器 ID
    packet_id: int      # 延迟追踪 ID
    send_time_ns: int   # 发送时间 (E2E 延迟)
```

---

## PacketMerger 类

合并 H.264/H.265 的配置包与媒体包。

### 原理

```
配置包 (SPS/PPS) + 媒体包 (I/P 帧) = 完整可解码帧
```

### 使用

```python
merger = PacketMerger()

for packet in packets:
    packet = merger.merge(packet)
    if not packet.header.is_config:
        # 媒体包已合并配置，可解码
        decode(packet)

# 清除缓冲
merger.clear()
```

---

## StreamParser 类

### 主要方法

```python
class StreamParser:
    # 解析编解码器 ID
    def parse_codec_id(self, data: bytes) -> Tuple[int, bytes]

    # 解析视频尺寸
    def parse_video_size(self, data: bytes) -> Tuple[int, int, bytes]

    # 解析包头
    def parse_packet_header(self, data: bytes) -> Tuple[PacketHeader, bytes]

    # 解析完整包
    def parse_packet(self, data: bytes, codec_id: int) -> Tuple[VideoPacket, bytes]

    # 重置合并器
    def reset_merger(self) -> None
```

### 使用流程

```python
parser = StreamParser()

# 1. 解析编解码器
codec_id, data = parser.parse_codec_id(raw_data)

# 2. 解析视频尺寸
width, height, data = parser.parse_video_size(data)

# 3. 循环解析包
while data:
    packet, data = parser.parse_packet(data, codec_id)
    if packet:
        process_packet(packet)
```

---

## DataBuffer 类

TCP 流缓冲区管理。

```python
buffer = DataBuffer()

# 添加数据
buffer.feed(socket.recv(4096))

# 消费数据
data = buffer.consume(12)  # 读取 12 字节

# 查看数据 (不移除)
peek_data = buffer.peek(4)

# 获取大小
size = buffer.size

# 清除
buffer.clear()
```

---

## NALU 类型解析

### H.264

```python
def parse_h264_nalu_type(data: bytes) -> int:
    """
    返回 NALU 类型 (1-31):
    - 1: 非 IDR 切片
    - 5: IDR 切片 (关键帧)
    - 7: SPS
    - 8: PPS
    """
```

### H.265

```python
def parse_h265_nalu_type(data: bytes) -> int:
    """
    返回 NALU 类型 (0-63):
    - 19: IDR_W_RADL (关键帧)
    - 20: IDR_N_LP
    - 32: VPS
    - 33: SPS
    - 34: PPS
    """
```

---

## TCP 包格式

```
┌─────────────────────────────────────────────────────────────┐
│                     Packet Header (12 bytes)                │
├───────────────────────────────┬─────────────────────────────┤
│     PTS + Flags (8 bytes)     │     Size (4 bytes)          │
│  ┌─────────────────────────┐  │                             │
│  │CK...... ........ ...... │  │  Payload size in bytes      │
│  │^^<--------------------->│  │                             │
│  │||    PTS (62 bits)      │  │                             │
│  │|`- key frame (bit 62)   │  │                             │
│  │`-- config (bit 63)      │  │                             │
│  └─────────────────────────┘  │                             │
├───────────────────────────────┴─────────────────────────────┤
│                    Payload (N bytes)                        │
│                 H.264 / H.265 / AV1 数据                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 相关文档

- [protocol.md](protocol.md) - 协议常量
- [video_decoder.md](video_decoder.md) - 视频解码
- [udp_video_demuxer.md](udp_video_demuxer.md) - UDP 解复用
