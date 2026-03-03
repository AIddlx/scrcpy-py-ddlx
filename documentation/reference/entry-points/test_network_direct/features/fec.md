# FEC 前向纠错

> Forward Error Correction for UDP

---

## 概述

FEC (Forward Error Correction) 通过添加冗余校验包来恢复丢失的 UDP 包。

### 为什么需要 FEC

```
无 FEC:
  发送: D0 D1 D2 D3
  接收: D0 XX D2 D3  (D1 丢失)
  结果: 无法解码

有 FEC (K=4, M=1):
  发送: D0 D1 D2 D3 P0
  接收: D0 XX D2 D3 P0  (D1 丢失)
  恢复: D1 = P0 ⊕ D0 ⊕ D2 ⊕ D3
  结果: 完整解码
```

---

## FEC 模式

### 帧级 FEC (frame)

```
每 K 个完整帧生成 M 个校验帧

组结构:
  [Frame0] [Frame1] [Frame2] [Frame3] [Parity0]
   ↓         ↓        ↓        ↓         ↓
  数据帧    数据帧   数据帧   数据帧    校验帧

优点: 简单，开销固定
缺点: 大帧时延迟较高
```

### 片级 FEC (fragment)

```
每帧分成 K 个片段，生成 M 个校验片段

帧结构:
  [F0] [F1] [F2] [F3] [P0] [F4] [F5] [F6] [F7] [P1]
   ↓    ↓    ↓    ↓    ↓
  片段  片段 片段 片段 校验

优点: 延迟低，适合大帧
缺点: 实现复杂
```

---

## 参数配置

### 命令行

```bash
# 启用帧级 FEC (默认 K=4, M=1)
python test_network_direct.py --fec frame

# 启用片级 FEC
python test_network_direct.py --fec fragment

# 自定义 K 和 M
python test_network_direct.py --fec frame --fec-k 8 --fec-m 2

# 仅视频 FEC
python test_network_direct.py --video-fec frame

# 仅音频 FEC
python test_network_direct.py --audio-fec fragment
```

### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--fec-k` | 4 | 数据包数 (K) |
| `--fec-m` | 1 | 校验包数 (M) |
| `--fec` | - | 同时启用视频和音频 FEC |
| `--video-fec` | - | 仅视频 FEC |
| `--audio-fec` | - | 仅音频 FEC |

---

## 恢复能力

| K | M | 丢包容忍 | 开销 |
|---|---|---------|------|
| 4 | 1 | 1/5 (20%) | 25% |
| 8 | 2 | 2/10 (20%) | 25% |
| 4 | 2 | 2/6 (33%) | 50% |

### 计算公式

```
恢复能力 = M / (K + M)
开销 = M / K
```

---

## 实现

### 服务端 (SimpleXorFecEncoder)

```java
public class SimpleXorFecEncoder {
    // XOR 异或生成校验包
    public byte[] encode(byte[][] dataPackets) {
        byte[] parity = new byte[maxSize];
        for (byte[] packet : dataPackets) {
            for (int i = 0; i < packet.length; i++) {
                parity[i] ^= packet[i];
            }
        }
        return parity;
    }
}
```

### 客户端 (FecDecoder)

```python
class FecDecoder:
    def recover(self, group: FecGroup) -> List[bytes]:
        """恢复丢失的包"""
        if group.is_complete():
            return group.data_packets

        # XOR 恢复
        missing_index = group.find_missing()
        recovered = group.parity_packets[0]
        for i, packet in enumerate(group.data_packets):
            if i != missing_index:
                recovered = xor(recovered, packet)

        return recovered
```

---

## 推荐配置

| 网络条件 | K | M | 模式 |
|---------|---|---|------|
| 优质网络 | - | - | 不启用 |
| 一般网络 | 4 | 1 | frame |
| 较差网络 | 4 | 2 | frame |
| 高延迟 | 8 | 2 | fragment |

---

## 相关文档

- [network.md](network.md) - 网络模式
- [low_latency.md](low_latency.md) - 低延迟优化
