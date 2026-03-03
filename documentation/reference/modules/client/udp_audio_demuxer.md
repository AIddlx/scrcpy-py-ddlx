# UdpAudioDemuxer - UDP 音频解复用器

> **路径**: `scrcpy_py_ddlx/core/demuxer/udp_audio.py`
> **职责**: UDP 网络模式音频流解复用

---

## 类定义

### UdpAudioPacketHeader (dataclass)

**职责**: 解析后的 UDP 音频包头部

| 字段 | 类型 | 说明 |
|------|------|------|
| `sequence` | int | 包序号 |
| `timestamp` | int | 时间戳 |
| `flags` | int | 标志位 |
| `send_time_ns` | int | 发送时间戳 (v1.2) |

**属性**:
- `is_config`: 是否为配置包
- `is_fec_data`: 是否为 FEC 数据包
- `is_fec_parity`: 是否为 FEC 校验包

---

### UdpAudioStats (dataclass)

**职责**: UDP 音频统计信息

| 字段 | 类型 | 说明 |
|------|------|------|
| `packets_received` | int | 接收包数 |
| `bytes_received` | int | 接收字节数 |
| `packets_lost` | int | 丢包数 |
| `config_packets` | int | 配置包数 |
| `audio_packets` | int | 音频包数 |
| `fec_recoveries` | int | FEC 恢复数 |
| `parse_errors` | int | 解析错误数 |

---

### UdpAudioDemuxer

**职责**: UDP 音频解复用器

**线程**: 独立接收线程

**对比视频解复用器**:
- 音频包通常较小（无需分片）
- 无 PLI 机制（音频解码器更好处理间隙）
- 延迟要求更低

---

## 常量

| 常量 | 值 | 说明 |
|------|-----|------|
| `MAX_UDP_PACKET` | 65507 | 最大 UDP 包大小 |
| `MAX_CONSECUTIVE_TIMEOUTS` | 3 | 断连检测超时次数 |
| `SOCKET_TIMEOUT` | 1.5s | Socket 超时时间 |

---

## 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `_socket` | socket | UDP socket |
| `_packet_queue` | Queue | 音频包队列 |
| `_codec_id` | int | 编解码器 ID |
| `_fec_decoder` | FecDecoder | FEC 解码器 (可选) |
| `_expected_seq` | int | 期望的下一个序号 |
| `_seq_initialized` | bool | 序号是否已初始化 |
| `_config_received` | bool | 是否收到配置 |

---

## 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `start` | - | - | 启动解复用线程 |
| `stop` | - | - | 停止解复用器 |
| `get_stats` | - | UdpAudioStats | 获取统计信息 |
| `settimeout` | timeout | - | 设置 socket 超时 |
| `pause` | - | - | 暂停 (lazy decode) |
| `resume` | - | - | 恢复 (lazy decode) |

---

## 数据包格式

### UDP 包结构

```
[UDP Header: 24B] [Scrcpy Header: 12B] [Audio Payload: NB]
```

### UDP Header (24 字节 v1.2)

```
sequence:     4B (uint32, big-endian)
timestamp:    8B (int64, big-endian)
flags:        4B (uint32, big-endian)
send_time_ns: 8B (int64, big-endian)
```

### Scrcpy Header (12 字节)

```
pts_flags: 8B (PTS + flags)
size:      4B (payload size)
```

---

## 处理流程

```
[UDP Socket]
    │
    ▼
recvfrom() ──→ [packet]
    │
    ▼
_parse_udp_header() ──→ [UdpAudioPacketHeader]
    │
    ├─→ is_config? ──→ _handle_config_packet()
    │
    ├─→ is_fec_parity? ──→ _handle_fec_parity()
    │
    ├─→ is_fec_data? ──→ _handle_fec_data()
    │
    └─→ normal ──→ _handle_normal_packet()
                         │
                         ▼
                   [_packet_queue.put(opus_data)]
```

---

## 配置包处理

### 简单格式 (首包)

```python
# 只有 4 字节 codec_id
if len(payload) == 4:
    codec_id = struct.unpack('>I', payload)[0]
    # OPUS = 0x4f505553
```

### 完整格式 (后续配置)

```
[Scrcpy Header: 12B] [codec_id: 4B] [config_data: NB]
```

**注意**: OPUS 解码器不需要配置包，仅用于编解码器识别。

---

## 丢包检测

```python
def _detect_loss(seq):
    if seq < expected_seq:
        return  # 乱序包

    gap = seq - expected_seq
    if gap > 0:
        stats.packets_lost += gap
        logger.debug(f"Audio packet loss: {gap} packets")
```

---

## FEC 恢复流程

### FEC 数据包格式 (7 字节头)

```
group_id:     2B (uint16)
packet_idx:   1B (uint8)
total_data:   1B (uint8)
total_parity: 1B (uint8)
original_size:2B (uint16)
```

### FEC 校验包格式 (5 字节头)

```
group_id:     2B (uint16)
parity_idx:   1B (uint8)
total_data:   1B (uint8)
total_parity: 1B (uint8)
```

### 恢复流程

```python
# FEC 数据包
result = fec_decoder.add_data_packet(...)
if result:
    _process_recovered_packets(result)

# FEC 校验包
result = fec_decoder.add_parity_packet(...)
if result:
    _process_recovered_packets(result)
```

---

## 断连检测

```python
# 1.5s 超时 * 3 次 = 4.5s 最大等待
consecutive_timeouts = 0

while running:
    try:
        packet = socket.recvfrom()
        consecutive_timeouts = 0  # 重置
    except socket.timeout:
        consecutive_timeouts += 1
        if consecutive_timeouts >= 3:
            logger.error("Server disconnect detected")
            break
```

---

## 依赖关系

```
UdpAudioDemuxer
    │
    ├──→ socket (UDP)
    │
    ├──→ Queue (音频包队列)
    │
    ├──→ FecDecoder (可选)
    │
    └──→ protocol.py (常量)
```

**被依赖**:
- components.py (创建)
- AudioDecoder (消费队列)

---

## 工厂函数

### create_udp_audio_demuxer()

```python
def create_udp_audio_demuxer(
    udp_socket,
    audio_codec=0x4f505553,  # OPUS
    queue_size=30,
    fec_decoder=None,
) -> tuple[UdpAudioDemuxer, Queue]:
    """创建 UDP 音频解复用器和包队列"""
```

---

*此文档基于代码分析生成*
