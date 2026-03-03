# SimpleXorFecEncoder

> **文件**: `udp/SimpleXorFecEncoder.java`
> **功能**: XOR 前向纠错编码器

---

## 概述

`SimpleXorFecEncoder` 实现基于 XOR 的前向纠错编码，每 K 帧生成 M 个校验帧。

---

## 参数

| 参数 | 变量名 | 默认值 | 说明 |
|------|--------|--------|------|
| 组大小 | `groupSize` (K) | 4 | 每组数据帧数 |
| 校验数 | `parityCount` (M) | 1 | 每组校验帧数 |

---

## 编码原理

### XOR 校验生成

```
帧 0: [D0] ─────────┐
帧 1: [D1] ─────────┼───► XOR ───► [P0]
帧 2: [D2] ─────────┤
帧 3: [D3] ─────────┘

P0 = D0 ⊕ D1 ⊕ D2 ⊕ D3
```

### 丢包恢复

```
已知: D0, D1, D3, P0
丢失: D2

恢复:
D2 = D0 ⊕ D1 ⊕ D3 ⊕ P0
```

---

## 核心方法

```java
public class SimpleXorFecEncoder {
    // 构造函数
    public SimpleXorFecEncoder(int groupSize, int parityCount);
    public SimpleXorFecEncoder();  // 默认 K=4, M=1

    // 添加数据包 (返回 null 或校验包)
    public ByteBuffer addPacket(ByteBuffer dataPacket);

    // 检查是否需要生成校验
    public boolean shouldFinalizeGroup();

    // 获取当前帧索引
    public int getCurrentFrameIdx();

    // 获取组大小
    public int getGroupSize();
}
```

---

## FEC Header 格式

### 数据包 Header (7 bytes)

```
[group_id: 2B][packet_idx: 1B][total_data: 1B][total_parity: 1B][original_size: 2B]

group_id: 组 ID (递增)
packet_idx: 组内索引 (0 到 K-1)
total_data: K
total_parity: M
original_size: 原始负载大小
```

### 校验包 Header (5 bytes)

```
[group_id: 2B][parity_idx: 1B][total_data: 1B][total_parity: 1B]

parity_idx: 校验索引 (0 到 M-1)
```

---

## 使用示例

```java
// 创建编码器
SimpleXorFecEncoder encoder = new SimpleXorFecEncoder(4, 1);

// 处理每个数据包
for (ByteBuffer packet : packets) {
    ByteBuffer fecPacket = encoder.addPacket(packet);
    if (fecPacket != null) {
        // 发送 FEC 校验包
        sendFecPacket(fecPacket);
    }
}
```

---

## 优化

- 使用 `ByteArrayOutputStream` 避免重复内存分配
- 延迟初始化缓冲区
- 支持帧级和分片级 FEC

---

## 相关文档

- [UdpMediaSender.md](UdpMediaSender.md) - UDP 发送器集成
- [fec_decoder.md](../../client/fec_decoder.md) - 客户端解码器
- [FEC_PLI_PROTOCOL_SPEC.md](../../../../FEC_PLI_PROTOCOL_SPEC.md) - 协议规范
