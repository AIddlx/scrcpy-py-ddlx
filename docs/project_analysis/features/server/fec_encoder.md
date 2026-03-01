# FEC 编码器 (SimpleXorFecEncoder.java)

> XOR 前向纠错编码器

---

## 文件位置

```
scrcpy/server/src/main/java/com/genymobile/scrcpy/udp/SimpleXorFecEncoder.java
```

---

## 概述

使用简单 XOR 运算实现前向纠错，每 K 帧生成 M 个校验帧。

---

## 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `groupSize` (K) | 4 | 每组数据帧数 |
| `parityCount` (M) | 1 | 每组校验帧数 |

---

## 工作原理

### 编码过程

```
帧 1: [D1]
帧 2: [D2]
帧 3: [D3]
帧 4: [D4]
           ↓ XOR
校验: [P1 = D1 ⊕ D2 ⊕ D3 ⊕ D4]
```

### 解码过程 (丢失帧 3)

```
已知: D1, D2, D4, P1
恢复: D3 = D1 ⊕ D2 ⊕ D4 ⊕ P1
```

---

## 核心方法

### 添加数据包

```java
public ByteBuffer addPacket(ByteBuffer dataPacket)
```

返回值：
- `null`: 还未到生成校验帧的时机
- `ByteBuffer`: 校验帧数据

### 检查组完成

```java
public boolean shouldFinalizeGroup()
```

---

## 优化

- 使用 `ByteArrayOutputStream` 避免重复内存分配
- 延迟初始化缓冲区
- 支持帧级和分片级 FEC

---

## 相关文档

- [UDP 发送详解](udp_sender.md)
- [FEC 协议规范](../../../FEC_PLI_PROTOCOL_SPEC.md)
