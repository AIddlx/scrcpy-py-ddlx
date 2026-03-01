# 音频管道

> 音频流的解复用、解码、播放和录制

---

## 概述

音频管道负责将 Android 端编码的 OPUS 音频流解码并播放。

## 管道阶段

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ 网络接收 │───►│ 解复用   │───►│ 解码    │───►│ 播放    │
│ (UDP/TCP)│    │ Demuxer │    │ Decoder │    │ Player  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

---

## 1. 解复用 (Demuxer)

### TCP 模式

| 文件 | `core/demuxer/audio.py` |
|------|--------------------------|

### UDP 模式

| 文件 | `core/demuxer/udp_audio.py` |
|------|------------------------------|

### 帧格式

```
[类型:1字节] [PTS:8字节] [包大小:4字节] [OPUS 负载]
```

---

## 2. 解码 (Decoder)

| 文件 | `core/audio/decoder.py` |
|------|--------------------------|

### 编解码器

| 编解码器 | 说明 |
|---------|------|
| OPUS | 主要支持 |
| AAC | 计划中 |
| RAW | 透传模式 |

### 输出格式

- 采样率: 48000 Hz
- 声道: 立体声
- 格式: 16-bit PCM

---

## 3. 播放 (Player)

### SoundDevice 播放器

| 文件 | `core/audio/sounddevice_player.py` |
|------|-------------------------------------|

- 低延迟播放
- 回调驱动
- 默认播放器

### Qt 播放器

| 文件 | 说明 |
|------|------|
| `qt_opus_player.py` | QMediaPlayer (实验性) |
| `qt_push_player.py` | QAudioSink 推送模式 |

---

## 4. 同步 (Sync)

| 文件 | `core/audio/sync.py` |
|------|-----------------------|

### A/V 同步策略

1. **基于 PTS**: 使用音频 PTS 调整播放速度
2. **丢帧策略**: 音频严重滞后时丢弃
3. **延迟调整**: 动态调整缓冲区

---

## 5. 录制 (Recording)

### WAV 录制

| 文件 | `core/audio/recorder.py` |
|------|---------------------------|

```python
# 录制为 WAV 文件
client.start_audio_recording("output.wav")
# ...
client.stop_audio_recording()
```

### 透传录制

| 文件 | `core/audio/passthrough_recorder.py` |
|------|----------------------------------------|

```python
# 直接保存 OPUS 流，无需解码
client.start_audio_recording("output.opus", passthrough=True)
```

---

## 编解码器定义

| 文件 | `core/audio/codecs/` |
|------|----------------------|

```
codecs/
├── __init__.py
└── base.py          # 编解码器基类和常量
```

---

## 相关文档

- [音视频管道](../../../development/VIDEO_AUDIO_PIPELINE.md)
