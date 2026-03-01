# AudioDecoder - 音频解码器

> **路径**: `scrcpy_py_ddlx/core/audio/decoder.py`
> **职责**: 多线程音频解码器包装器

---

## 类定义

### AudioDecoder

**职责**: 音频解码线程管理

**线程**: 解码线程 (后台)

**依赖**: audio.codecs.base, audio.sync

---

## 编解码器常量

| 常量 | 值 | 说明 |
|------|-----|------|
| `RAW` | 0 | RAW 未压缩 |
| `OPUS` | 1 | Opus 编码 |
| `AAC` | 2 | AAC 编码 |
| `FDK_AAC` | 3 | FDK-AAC 编码 |
| `FLAC` | 4 | FLAC 编码 |

---

## 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `_sample_rate` | int | 采样率 (48000) |
| `_channels` | int | 声道数 (2) |
| `_audio_codec` | int | 编解码器类型 |
| `_codec` | AudioCodecBase | 编解码器实现 |
| `_frame_sink` | FrameSink | 输出目标 |
| `_packet_queue` | Queue | 输入队列 |
| `_running` | bool | 运行状态 |
| `_paused` | bool | 暂停状态 |

---

## 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `start` | - | - | 启动解码线程 |
| `stop` | - | - | 停止解码 |
| `push` | packet | - | 推送音频包 |
| `pause` | - | - | 暂停解码 |
| `resume` | - | - | 恢复解码 |
| `sync_with_video` | video_pts | - | 音视频同步 |
| `set_frame_sink` | sink | - | 设置输出目标 |

---

## 解码流程

```
[AudioPacket] ──→ push() ──→ [_packet_queue]
                                   │
                                   ▼
                        [_decode_loop 线程]
                                   │
                                   ▼
                        [_codec.decode()]
                                   │
                                   ▼
                        [FrameSink.push()]
```

---

## 音视频同步

```python
def sync_with_video(video_pts):
    """
    根据视频 PTS 调整音频播放

    - 如果音频超前: 等待
    - 如果音频落后: 跳过部分帧
    """
```

**组件**:
- `PTSComparator`: PTS 比较器
- `AudioDelayAdjuster`: 延迟调整器

---

## 编解码器实现

| 编解码器 | 实现方式 |
|----------|----------|
| RAW | 直接透传 |
| OPUS | PyAV av.decode() |
| AAC | PyAV av.decode() |
| FLAC | PyAV av.decode() |

---

## 依赖关系

```
AudioDecoder
    │
    ├──→ audio.codecs.base (编解码器)
    │
    ├──→ audio.sync (同步)
    │
    ├──→ Queue (包队列)
    │
    └──→ FrameSink (输出)
```

**被依赖**:
- components.py (创建)
- client.py (使用)

---

*此文档基于代码分析生成*
