# UDP Header 格式

> **版本**: v1.2 (2026-02-20)
> **大小**: 24 字节
> **字节序**: Big-endian

---

## 概述

UDP 数据包在有效载荷前包含 24 字节的头部，用于：
- 流类型区分（视频/音频）
- 序列号追踪
- 分片重组
- FEC 纠错
- E2E 延迟追踪

---

## 头部格式

```
偏移   大小   字段                    说明
────────────────────────────────────────────────────────────
0      1      stream_type            流类型 (0=视频, 1=音频)
1      1      flags                  标志位
2      4      sequence               序列号 (big-endian)
6      4      pts                    显示时间戳 (big-endian)
10     4      total_size             总大小 (big-endian)
14     2      fragment_index         分片索引 (big-endian)
16     2      fragment_count         分片总数 (big-endian)
18     4      fec_group_id           FEC 组 ID (big-endian)
22     2      send_time_ns_low       发送时间低 16 位 (big-endian)
────────────────────────────────────────────────────────────
总大小: 24 字节
```

---

## 字段详解

### stream_type (1字节)

| 值 | 说明 |
|-----|------|
| 0 | 视频流 |
| 1 | 音频流 |

### flags (1字节)

| 位 | 说明 |
|-----|------|
| 0 | CONFIG: 配置包 |
| 1 | KEY_FRAME: 关键帧 |
| 2-7 | 保留 |

### sequence (4字节)

- 包序列号
- 每个流独立计数
- 用于检测丢包和排序

### pts (4字节)

- 显示时间戳
- 单位：微秒
- 用于音视频同步

### total_size (4字节)

- 完整帧的总大小
- 用于分片重组验证

### fragment_index (2字节)

- 当前分片索引 (0-based)
- 用于分片重组

### fragment_count (2字节)

- 总分片数量
- 用于判断是否接收完整

### fec_group_id (4字节)

- FEC 组标识
- 用于关联数据包和校验包

### send_time_ns_low (2字节)

- 发送时间的低 16 位
- 结合 pts 计算 E2E 延迟

---

## 分片重组逻辑

```python
def reassemble_packet(fragments):
    """
    分片重组流程:
    1. 按 fragment_index 排序
    2. 验证 fragment_count 一致
    3. 拼接所有 payload
    4. 验证 total_size
    """
    # 排序
    fragments.sort(key=lambda f: f.fragment_index)

    # 拼接
    payload = b''.join(f.payload for f in fragments)

    # 验证
    if len(payload) == fragments[0].total_size:
        return payload
    else:
        raise ReassemblyError("Size mismatch")
```

---

## E2E 延迟计算

```python
def calculate_e2e_latency(header, recv_time_ns):
    """
    E2E 延迟 = 接收时间 - 发送时间

    发送时间由两部分组成:
    - pts (高 48 位)
    - send_time_ns_low (低 16 位)
    """
    send_time_ns = (header.pts << 16) | header.send_time_ns_low
    e2e_ns = recv_time_ns - send_time_ns
    return e2e_ns / 1_000_000  # 转换为毫秒
```

---

## 相关代码

| 文件 | 说明 |
|------|------|
| `core/demuxer/udp_video.py` | 视频包头解析 |
| `core/demuxer/udp_audio.py` | 音频包头解析 |
| `server/udp/UdpMediaSender.java` | 服务端包头构造 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | - | 初始 12 字节格式 |
| v1.1 | 2026-02-15 | 添加 FEC 支持 |
| v1.2 | 2026-02-20 | 扩展至 24 字节，添加 send_time_ns |

---

*此文档基于协议规范生成*
