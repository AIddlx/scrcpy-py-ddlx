# fec.py (FEC Decoder)

> **文件**: `core/demuxer/fec.py`
> **功能**: FEC 前向纠错解码器

---

## 概述

`FecDecoder` 实现客户端 FEC 解码，与 `SimpleXorFecEncoder.java` 配合恢复丢失的包。

---

## FEC 组结构

```
数据包:   [D0] [D1] [D2] [D3] ... [DK-1]
校验包:   [P0] [P1] ... [PM-1]

恢复: 如果丢失 N 个包且 M >= N，可以通过 XOR 恢复
```

---

## FecGroupBuffer 数据类

```python
@dataclass
class FecGroupBuffer:
    group_id: int                    # 组 ID
    total_data_packets: int          # K
    total_parity_packets: int        # M
    created_at: float                # 创建时间

    data_packets: Dict[int, bytes]   # 已收到的数据包
    parity_packets: Dict[int, bytes] # 已收到的校验包
    original_sizes: Dict[int, int]   # 原始大小

    @property
    def is_complete(self) -> bool    # 是否收齐所有数据包
    @property
    def missing_count(self) -> int   # 缺失包数量
    @property
    def can_recover(self) -> bool    # 是否可以恢复
```

---

## FecDecoder 类

```python
class FecDecoder:
    def __init__(self, group_size: int = 4, parity_count: int = 1)

    # 处理 UDP 包
    def process_packet(self, packet: bytes) -> List[bytes]

    # 重置状态
    def reset(self) -> None

    # 统计信息
    @property
    def stats(self) -> dict
```

---

## FEC Header 格式

### 数据包 Header (7 bytes)

```
[group_id: 2B][packet_idx: 1B][total_data: 1B][total_parity: 1B][original_size: 2B]

group_id: 组 ID
packet_idx: 组内索引 (0 到 K-1)
total_data: K
total_parity: M
original_size: 原始负载大小
```

### 校验包 Header (5 bytes)

```
[group_id: 2B][parity_idx: 1B][total_data: 1B][total_parity: 1B]
```

---

## 恢复算法

```python
def recover_missing(self, group: FecGroupBuffer) -> List[bytes]:
    """
    使用 XOR 恢复缺失的包

    D_missing = D0 ⊕ D1 ⊕ ... ⊕ P0
    """
    missing_indices = group.get_missing_indices()
    recovered = []

    for idx in missing_indices:
        # XOR 所有已知数据包和校验包
        result = bytearray()
        for i, pkt in group.data_packets.items():
            xor_into(result, pkt)
        for i, pkt in group.parity_packets.items():
            xor_into(result, pkt)

        # 截断到原始大小
        original_size = group.original_sizes.get(idx, len(result))
        recovered.append(bytes(result[:original_size]))

    return recovered
```

---

## 使用示例

```python
from scrcpy_py_ddlx.core.demuxer.fec import FecDecoder

decoder = FecDecoder(group_size=4, parity_count=1)

# 处理每个 UDP 包
for packet in udp_packets:
    frames = decoder.process_packet(packet)
    for frame in frames:
        # 处理恢复的视频帧
        decode_video(frame)
```

---

## 统计信息

```python
stats = decoder.stats
# {
#     "groups_processed": 100,
#     "packets_recovered": 5,
#     "groups_complete": 95,
#     "groups_unrecoverable": 0
# }
```

---

## 相关文档

- [SimpleXorFecEncoder.md](../server/SimpleXorFecEncoder.md) - 服务端编码器
- [FEC_PLI_PROTOCOL_SPEC.md](../../../FEC_PLI_PROTOCOL_SPEC.md) - 协议规范
