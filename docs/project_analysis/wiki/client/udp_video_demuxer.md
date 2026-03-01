# UdpVideoDemuxer - 视频解复用器

> **路径**: `scrcpy_py_ddlx/core/demuxer/udp_video.py`
> **职责**: UDP视频解复用器，处理分片重组、FEC、PLI请求

---

## 类定义

### UdpPacketHeader (dataclass)

**职责**: UDP包头解析结果

| 字段 | 类型 | 说明 |
|------|------|------|
| `sequence` | int | 序列号 |
| `timestamp` | int | 时间戳 |
| `flags` | int | 标志位 |
| `send_time_ns` | int | 发送时间(纳秒) |

**属性**:
- `is_key_frame` - 是否关键帧
- `is_config` - 是否配置包
- `is_fragmented` - 是否分片
- `is_fec_data` - 是否FEC数据
- `is_fec_parity` - 是否FEC校验

---

### FragmentBuffer (dataclass)

**职责**: 分片重组缓冲区

| 字段 | 类型 | 说明 |
|------|------|------|
| `timestamp` | int | 时间戳 |
| `flags` | int | 标志位 |
| `fragments` | dict | 分片字典 |
| `expected_size` | int | 预期大小 |
| `total_size` | int | 总大小 |

---

### UdpStats (dataclass)

**职责**: UDP统计信息

| 字段 | 说明 |
|------|------|
| `packets_received` | 接收包数 |
| `bytes_received` | 接收字节数 |
| `packets_lost` | 丢包数 |
| `fragments_reassembled` | 重组分片数 |
| `pli_requests_sent` | PLI请求数 |

---

### UdpVideoDemuxer

**职责**: UDP视频解复用器

**线程**: 解复用线程 (后台)

---

## 主要属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `_socket` | socket | UDP套接字 |
| `_packet_queue` | Queue | 输出队列 |
| `_fec_decoder` | FECDecoder | FEC解码器 |
| `_control_channel` | socket | 控制通道 |
| `_fragment_buffers` | dict | 分片缓冲区 |
| `_stats` | UdpStats | 统计信息 |

---

## 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `start` | - | - | 启动解复用线程 |
| `stop` | - | - | 停止 |
| `get_stats` | - | UdpStats | 获取统计 |
| `set_frame_size_changed_callback` | callback | - | 设置尺寸变化回调 |
| `set_control_channel` | socket | - | 设置控制通道 |

---

## 内部方法

| 方法 | 说明 |
|------|------|
| `_process_packet` | 处理UDP包 |
| `_handle_normal_packet` | 处理普通包 |
| `_handle_fragment` | 处理分片 |
| `_handle_fec_data` | 处理FEC数据 |
| `_handle_fec_parity` | 处理FEC校验 |
| `_reassemble_fragment` | 重组分片 |
| `_parse_scrcpy_packet` | 解析scrcpy包 |
| `_merge_config` | 合并配置包 |
| `_detect_loss` | 检测丢包 |
| `_send_pli` | 发送PLI请求 |

---

## 常量

| 常量 | 值 | 说明 |
|------|-----|------|
| `MAX_UDP_PACKET` | 65507 | 最大UDP包 |
| `MAX_PACKET_SIZE` | 16MB | 最大scrcpy包 |
| `FRAGMENT_TIMEOUT` | 2.0 | 分片超时(秒) |
| `MAX_CONSECUTIVE_TIMEOUTS` | 3 | 断连阈值 |

---

## 分片重组流程

```
1. 收到第一个分片 → 创建 FragmentBuffer
2. 收到后续分片 → 添加到 fragments dict
3. 检查是否完整 → 所有分片到齐
4. 重组 → 按索引排序，拼接
5. 输出 → 推送到 packet_queue
6. 清理 → 删除 FragmentBuffer
```

---

## PLI 请求

当检测到连续丢包时，发送 PLI (Picture Loss Indication) 请求关键帧：

```python
if consecutive_losses > threshold:
    self._send_pli()
```

---

## 依赖关系

```
UdpVideoDemuxer
    │
    ├──→ socket (UDP)
    │
    ├──→ protocol.py (常量)
    │
    ├──→ stream.py (解析)
    │
    └──→ fec.py (FEC解码)
```

---

*此文档基于客户端代码分析生成*
