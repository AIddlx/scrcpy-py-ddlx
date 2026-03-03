# UDP 媒体发送 (UdpMediaSender.java)

> UDP 视频音频数据发送，支持 FEC

---

## 文件位置

```
scrcpy/server/src/main/java/com/genymobile/scrcpy/udp/UdpMediaSender.java
```

---

## 概述

`UdpMediaSender` 负责通过 UDP 发送视频和音频数据到客户端。

---

## UDP Header 格式 (24 字节)

```
┌──────────┬──────────┬──────────┬──────────┐
│ seq (4)  │ pts (8)  │ flags(4) │ send_ns(8)│
└──────────┴──────────┴──────────┴──────────┘

seq:     包序号 (递增)
pts:     显示时间戳 (纳秒)
flags:   标志位
send_ns: 发送时间 (纳秒，用于 E2E 延迟追踪)
```

---

## 标志位定义

```java
public static final long FLAG_KEY_FRAME = 1L << 0;   // 关键帧
public static final long FLAG_CONFIG = 1L << 1;      // 配置帧 (SPS/PPS)
public static final long FLAG_FEC_DATA = 1L << 2;    // FEC 数据包
public static final long FLAG_FEC_PARITY = 1L << 3;  // FEC 校验包
```

---

## 核心方法

### 发送数据包

```java
public void sendPacket(ByteBuffer data, long timestamp,
                       boolean config, boolean keyFrame) throws IOException
```

### 启用 FEC

```java
public void enableFec(int groupSize, int parityCount, String fecMode)
```

---

## 大帧分片

当数据超过 UDP 最大载荷时自动分片：

```
原始帧: 100KB
分片后: ~70 个 UDP 包 (每个 ~1400 字节)
```

---

## FEC 集成

```java
if (fecEnabled) {
    ByteBuffer fecPacket = fecEncoder.addPacket(packet);
    if (fecPacket != null) {
        sendFecPacket(fecPacket, timestamp);
    }
}
```

---

## 相关文档

- [FEC 编码器](fec_encoder.md)
- [协议规范](../../../PROTOCOL_SPEC.md)
