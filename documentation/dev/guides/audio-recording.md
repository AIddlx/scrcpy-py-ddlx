# 音频录制功能指南

## 概述

本文档记录了音频录制功能的实现细节、常见问题和解决方案。

---

## 录制模式

### 1. WAV 格式（推荐用于兼容性）

```bash
curl -X POST "http://localhost:3359/mcp" -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"record_audio\",\"arguments\":{\"filename\":\"test.wav\",\"duration\":10,\"format\":\"wav\"}}}"
```

**特点**：
- 无损 PCM 格式（float32 IEEE）
- 兼容性最好，所有播放器支持
- 文件较大（约 384 KB/秒，立体声 48kHz）

### 2. Opus 格式（推荐用于存储）

```bash
curl -X POST "http://localhost:3359/mcp" -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"record_audio\",\"arguments\":{\"filename\":\"test.opus\",\"duration\":10,\"format\":\"opus\"}}}"
```

**特点**：
- 高压缩比（约 10:1），128kbps
- OGG 容器封装
- 推荐播放器：VLC、Windows Media Player
- 文件扩展名：`.opus`

### 3. MP3 格式

```bash
curl -X POST "http://localhost:3359/mcp" -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"record_audio\",\"arguments\":{\"filename\":\"test.mp3\",\"duration\":10,\"format\":\"mp3\"}}}"
```

**特点**：
- 广泛支持的格式
- 192kbps 码率
- 兼容性好

---

## 技术实现

### 音频数据流

```
Android 服务端                    Python 客户端
┌──────────────┐                 ┌──────────────────────────────────────┐
│ AudioCapture │                 │                                      │
│   (PCM)      │                 │  UdpAudioDemuxer                     │
└──────┬───────┘                 │      ↓ OPUS packets                  │
       ↓                         │  AudioDecoder (PyAV)                 │
┌──────────────┐   UDP 网络      │      ↓ float32 PCM                   │
│ Opus Encoder │ ──────────────▶ │  TeeAudioRecorder                    │
│              │                 │      ├─→ 播放器 (实时播放)            │
└──────────────┘                 │      └─→ AudioRecorder (WAV 写入)    │
                                 │             ↓                        │
                                 │      close() 时转换为 Opus/MP3       │
                                 └──────────────────────────────────────┘
```

### 文件格式

| 格式 | 容器 | 编码 | 采样率 | 通道 |
|------|------|------|--------|------|
| WAV | RIFF/WAVE | PCM float32 | 48000 Hz | 立体声 |
| Opus | OGG | libopus | 48000 Hz | 立体声 |
| MP3 | RAW | libmp3lame | 48000 Hz | 立体声 |

---

## 常见问题

### 1. 转换失败，保留 .tmp.wav 文件

**现象**：录音结束后文件名是 `.tmp.wav` 而不是 `.opus`

**原因**：PyAV 的 `AudioCodecContext.channels` 属性是只读的，不能在创建后设置

**解决方案**：
```python
# 错误写法
output_stream = output.add_stream('libopus', rate=48000)
output_stream.channels = 2  # AttributeError!

# 正确写法
output_stream = output.add_stream('libopus', rate=48000)  # PyAV 自动配置 channels
output_stream.bit_rate = 128000
output_stream.format = 'flt'
```

### 2. PotPlayer 播放 Opus 音量跳变

**现象**：
- VLC 播放正常
- PotPlayer 播放到某个时刻音量突然变大
- 之后整个文件音量都变大

**原因**：PotPlayer 的"声音规格化"功能会动态调整音量

**解决方案**：
1. PotPlayer → 右键 → 选项 → 声音
2. 取消勾选"声音规格化"（或"音量标准化"）

**验证文件是否正常**：
```bash
# 检查整体音量
ffmpeg -i recording.opus -af "volumedetect" -f null /dev/null 2>&1 | grep volume

# 分段检查音量（前10秒 vs 后10秒）
ffmpeg -i recording.opus -ss 0 -t 10 -af "volumedetect" -f null /dev/null 2>&1 | grep volume
ffmpeg -i recording.opus -ss 10 -t 10 -af "volumedetect" -f null /dev/null 2>&1 | grep volume
```

### 3. 录音文件格式选择

| 场景 | 推荐格式 | 原因 |
|------|----------|------|
| 后期编辑处理 | WAV | 无损，质量最好 |
| 长时间存储 | Opus | 压缩率高，体积小 |
| 分享给他人 | MP3 | 兼容性最广 |
| 快速验证 | WAV | 无转换延迟 |

---

## 代码关键点

### PyAV Opus 编码器配置

```python
def _convert_to_opus(self):
    # 1. 打开输入 WAV
    input_ = av.open(wav_filename, 'r')
    input_stream = input_.streams.audio[0]

    # 2. 创建 OGG 容器
    output = av.open(opus_filename, 'w', format='ogg')

    # 3. 添加 Opus 流 - 不要传递 channels 参数
    output_stream = output.add_stream('libopus', rate=input_stream.rate)
    output_stream.bit_rate = 128000
    output_stream.format = 'flt'  # float32 格式匹配 WAV 输入

    # 4. 编码 - PyAV 自动处理格式匹配
    for frame in input_.decode(audio=0):
        for packet in output_stream.encode(frame):
            output.mux(packet)

    # 5. 刷新编码器
    for packet in output_stream.encode():
        output.mux(packet)
```

### 注意事项

1. **不要手动调用 `frame.reformat()`**：PyAV 会自动处理格式转换
2. **不要设置 `channels` 属性**：在 `add_stream()` 中也不要传递
3. **使用 `flt` 格式**：匹配 float32 WAV 输入，避免精度损失
4. **文件扩展名**：Opus 在 OGG 容器中使用 `.opus` 扩展名

---

## 日期

2026-02-24
