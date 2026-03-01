# Streamer - 流发送器

> **路径**: `scrcpy/server/src/main/java/com/genymobile/scrcpy/device/Streamer.java`
> **职责**: 媒体流数据发送

---

## 类定义

### Streamer

**职责**: 将编码后的视频/音频数据发送到客户端

**支持模式**:
- ADB 隧道模式 (FileDescriptor)
- TCP 网络模式 (OutputStream)
- UDP 网络模式 (UdpMediaSender)

---

## 常量

| 常量 | 值 | 说明 |
|------|-----|------|
| `PACKET_FLAG_CONFIG` | 1L << 63 | 配置包标志 |
| `PACKET_FLAG_KEY_FRAME` | 1L << 62 | 关键帧标志 |

---

## 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `fd` | FileDescriptor | ADB 模式文件描述符 |
| `codec` | Codec | 编解码器信息 |
| `sendCodecMeta` | boolean | 是否发送编解码器元数据 |
| `sendFrameMeta` | boolean | 是否发送帧元数据 |
| `outputStream` | OutputStream | TCP 模式输出流 |
| `udpSender` | UdpMediaSender | UDP 发送器 |
| `networkMode` | boolean | 是否网络模式 |

---

## 构造函数

### ADB 隧道模式

```java
Streamer(FileDescriptor fd, Codec codec,
         boolean sendCodecMeta, boolean sendFrameMeta)
```

### TCP 网络模式

```java
Streamer(OutputStream outputStream, Codec codec,
         boolean sendCodecMeta, boolean sendFrameMeta)
```

### UDP 网络模式

```java
Streamer(UdpMediaSender udpSender, Codec codec,
         boolean sendCodecMeta, boolean sendFrameMeta)
```

---

## 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `getCodec` | - | Codec | 获取编解码器 |
| `writeAudioHeader` | - | void | 写音频头 |
| `writeVideoHeader` | Size | void | 写视频头 |
| `writeDisableStream` | boolean error | void | 禁用流 |
| `writePacket` | ByteBuffer, long pts, boolean config, boolean keyFrame | void | 写数据包 |

---

## 数据包格式

### Scrcpy Header (12 字节)

```
pts_flags: 8B (PTS + flags)
    - bit 63: config flag
    - bit 62: keyframe flag
    - bits 0-61: PTS
size:      4B (payload size)
```

### UDP 模式完整包

```
[UDP Header: 24B] [Scrcpy Header: 12B] [Payload: NB]
```

---

## 写包流程

### ADB 模式

```java
void writePacket(ByteBuffer buffer, long pts, boolean config, boolean keyFrame) {
    if (sendFrameMeta) {
        writeFrameMeta(fd, buffer.remaining(), pts, config, keyFrame);
    }
    IO.writeFully(fd, buffer);
}
```

### TCP 模式

```java
void writePacket(ByteBuffer buffer, long pts, boolean config, boolean keyFrame) {
    if (sendFrameMeta) {
        writeFrameMetaNetwork(outputStream, buffer.remaining(), pts, config, keyFrame);
    }
    byte[] data = new byte[buffer.remaining()];
    buffer.get(data);
    outputStream.write(data);
}
```

### UDP 模式

```java
void writePacket(ByteBuffer buffer, long pts, boolean config, boolean keyFrame) {
    int dataSize = buffer.remaining();
    ByteBuffer packet = ByteBuffer.allocate(12 + dataSize);

    // 构建 scrcpy header
    long ptsAndFlags = config ? PACKET_FLAG_CONFIG : pts;
    if (keyFrame) ptsAndFlags |= PACKET_FLAG_KEY_FRAME;

    packet.putLong(ptsAndFlags);
    packet.putInt(dataSize);
    packet.put(buffer);
    packet.flip();

    // 发送
    if (udpSender.isFecEnabled()) {
        udpSender.sendPacketWithFec(packet, pts, config, keyFrame);
    } else {
        udpSender.sendPacket(packet, pts, config, keyFrame);
    }
}
```

---

## 视频头格式

```java
void writeVideoHeader(Size videoSize) {
    // 编解码器元数据: codec_id + width + height = 12 字节
    ByteBuffer payload = ByteBuffer.allocate(12);
    payload.putInt(codec.getId());
    payload.putInt(videoSize.getWidth());
    payload.putInt(videoSize.getHeight());

    // UDP 模式: 包装 scrcpy header
    if (udpSender != null) {
        ByteBuffer packet = ByteBuffer.allocate(12 + payload.remaining());
        packet.putLong(PACKET_FLAG_CONFIG);  // pts=0, config=true
        packet.putInt(payload.remaining());
        packet.put(payload);
        packet.flip();
        udpSender.sendPacket(packet, 0, true, false);
    }
}
```

---

## 音频头格式

```java
void writeAudioHeader() {
    ByteBuffer buffer = ByteBuffer.allocate(4);
    buffer.putInt(codec.getId());  // 'OPUS' = 0x4f505553
    buffer.flip();

    if (udpSender != null) {
        udpSender.sendPacket(buffer, 0, true, false);
    }
}
```

---

## 禁用流

```java
void writeDisableStream(boolean error) {
    byte[] code = new byte[4];
    if (error) code[3] = 1;  // code 1 = 配置错误

    if (udpSender != null) {
        udpSender.sendPacket(ByteBuffer.wrap(code), 0, true, false);
    }
}
```

**错误码**:
- 0: 显式禁用流 (无音频捕获，继续视频)
- 1: 配置错误，必须停止

---

## OPUS 配置包修复

```java
void fixOpusConfigPacket(ByteBuffer buffer) {
    // Android MediaCodec OPUS 配置包格式:
    // [AOPUSHDR: 8B] [size: 8B native] [OpusHead: NB] ...
    // 需要提取 OpusHead 部分作为 extradata

    byte[] idBuffer = new byte[8];
    buffer.get(idBuffer);  // "AOPUSHDR"

    long size = buffer.getLong();  // native byte-order
    buffer.limit(buffer.position() + (int)size);
}
```

---

## FLAC 配置包修复

```java
void fixFlacConfigPacket(ByteBuffer buffer) {
    // FLAC 配置包格式:
    // [fLaC: 4B] [size: 4B big-endian] [streaminfo: NB]

    buffer.order(ByteOrder.BIG_ENDIAN);
    int size = buffer.getInt();
    buffer.limit(buffer.position() + size);
}
```

---

## 依赖关系

```
Streamer
    │
    ├──→ Codec (编解码器信息)
    │
    ├──→ UdpMediaSender (UDP 发送)
    │
    ├──→ IO (文件操作)
    │
    └──→ AudioCodec (OPUS/FLAC 修复)
```

**被依赖**:
- ScreenEncoder (视频流)
- AudioEncoder (音频流)

---

*此文档基于代码分析生成*
