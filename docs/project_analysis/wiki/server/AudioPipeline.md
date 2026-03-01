# AudioPipeline (服务端)

> **目录**: `audio/`
> **文件**: 10 个 Java 文件
> **功能**: 音频捕获和编码

---

## 文件清单

| 文件 | 职责 |
|------|------|
| `AudioEncoder.java` | OPUS 编码器 |
| `AudioCapture.java` | 音频捕获接口 |
| `AudioDirectCapture.java` | 直接捕获 (Android 10+) |
| `AudioPlaybackCapture.java` | 播放捕获 (Android 10+) |
| `AudioRawRecorder.java` | 原始音频录制 |
| `AudioRecordReader.java` | AudioRecord 读取 |
| `AudioSource.java` | 音频源定义 |
| `AudioCodec.java` | 编解码器定义 |
| `AudioConfig.java` | 音频配置 |
| `AudioCaptureException.java` | 捕获异常 |

---

## 核心流程

```
┌─────────────────────┐
│   AudioCapture      │  音频捕获
│ (AudioRecord/API)   │
└──────────┬──────────┘
           │ PCM 数据
           ▼
┌─────────────────────┐
│   AudioEncoder      │  OPUS 编码
│   (MediaCodec)      │
└──────────┬──────────┘
           │ ByteBuffer
           ▼
┌─────────────────────┐
│     Streamer        │  分发
└──────────┬──────────┘
           │
      ┌────┴────┐
      ▼         ▼
    TCP      UDP Sender
   (USB)    (Network)
```

---

## AudioSource

```java
public enum AudioSource {
    OUTPUT("output"),      // 设备输出 (默认)
    PLAYBACK("playback");  // 播放捕获 (dup 模式)
}
```

---

## AudioCodec

```java
public enum AudioCodec {
    OPUS("opus", "audio/opus", 48000, 2),
    AAC("aac", "audio/mp4a-latm", 48000, 2),
    FLAC("flac", "audio/flac", 48000, 2),
    RAW("raw", "audio/raw", 48000, 2);

    public final String name;
    public final String mimeType;
    public final int sampleRate;
    public final int channels;
}
```

---

## AudioDirectCapture

Android 10+ 的直接音频捕获。

```java
// 创建 AudioRecord
AudioRecord record = new AudioRecord(
    MediaRecorder.AudioSource.DEFAULT,
    SAMPLE_RATE,
    CHANNEL_CONFIG,
    AUDIO_FORMAT,
    bufferSize
);

// 读取数据
int bytesRead = record.read(buffer, 0, bufferSize);
```

---

## AudioPlaybackCapture

Android 10+ 的播放音频捕获 (audio_dup 模式)。

```java
// 捕获播放中的音频
AudioPlaybackCaptureConfiguration config =
    new AudioPlaybackCaptureConfiguration.Builder(mediaProjection)
        .addMatchingUsage(AudioAttributes.USAGE_MEDIA)
        .build();

AudioRecord record = new AudioRecord.Builder()
    .setAudioPlaybackCaptureConfig(config)
    .build();
```

---

## AudioEncoder

### 核心参数

| 参数 | 说明 |
|------|------|
| `audio_codec` | opus/aac/flac/raw |
| `audio_bit_rate` | 码率 (bps) |

### 编码流程

```java
// 1. 创建编码器
MediaCodec encoder = MediaCodec.createEncoderByType("audio/opus");

// 2. 配置
MediaFormat format = MediaFormat.createAudioFormat("audio/opus", 48000, 2);
format.setInteger(MediaFormat.KEY_BIT_RATE, bitRate);
encoder.configure(format, null, null, CONFIGURE_FLAG_ENCODE);

// 3. 启动
encoder.start();

// 4. 编码循环
while (running) {
    // 输入 PCM
    int inputIndex = encoder.dequeueInputBuffer(timeout);
    if (inputIndex >= 0) {
        ByteBuffer inputBuffer = encoder.getInputBuffer(inputIndex);
        inputBuffer.put(pcmData);
        encoder.queueInputBuffer(inputIndex, 0, pcmData.length, pts, 0);
    }

    // 输出 OPUS
    int outputIndex = encoder.dequeueOutputBuffer(bufferInfo, timeout);
    if (outputIndex >= 0) {
        ByteBuffer outputBuffer = encoder.getOutputBuffer(outputIndex);
        sendAudio(outputBuffer, bufferInfo);
        encoder.releaseOutputBuffer(outputIndex, false);
    }
}
```

---

## 相关文档

- [Streamer.md](Streamer.md) - 流分发
- [audio_decoder.md](../client/audio_decoder.md) - 客户端解码
