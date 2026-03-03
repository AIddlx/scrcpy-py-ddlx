# Decoder (客户端)

> **目录**: `core/decoder/`, `core/audio/`
> **文件**: 6 个 Python 文件
> **功能**: 视频/音频解码

---

## 文件清单

| 文件 | 职责 |
|------|------|
| `decoder/video.py` | 视频解码器 (H.264/H.265/AV1) |
| `decoder/audio.py` | 音频解码器 (已移动) |
| `decoder/decoder_process.py` | 多进程解码器 |
| `decoder/delay_buffer.py` | 延迟缓冲 |
| `decoder/exceptions.py` | 解码异常 |
| `audio/decoder.py` | 音频解码器 (新位置) |

---

## VideoDecoder

### 支持的编解码器

| 编解码器 | MIME 类型 | 硬件加速 |
|----------|-----------|----------|
| H.264 | video/avc | CUVID, QSV, D3D11VA |
| H.265 | video/hevc | CUVID, QSV, D3D11VA |
| AV1 | video/av01 | CUVID (RTX 30+) |

### 硬件加速检测

```python
def _detect_best_hw_device_type() -> Optional[str]:
    """
    自动检测最佳硬件设备类型。

    Returns:
        "cuda" - NVIDIA GPU
        "qsv" - Intel Quick Sync
        "d3d11va" - DirectX 11
        "vaapi" - Linux VAAPI
        "videotoolbox" - macOS
        None - 软解码
    """
```

### 核心类

```python
class VideoDecoder:
    def __init__(
        self,
        codec_id: CodecId,
        hw_accel: bool = True,
        thread_safe: bool = True
    ):
        """
        初始化视频解码器。

        Args:
            codec_id: 编解码器 ID
            hw_accel: 启用硬件加速
            thread_safe: 线程安全模式
        """

    def decode(self, packet: VideoPacket) -> Optional[np.ndarray]:
        """
        解码视频包。

        Args:
            packet: 视频包对象

        Returns:
            BGR 格式的 numpy 数组，或 None
        """

    def get_video_size(self) -> Tuple[int, int]:
        """获取视频尺寸 (width, height)。"""

    def flush(self) -> None:
        """刷新解码器缓冲区。"""

    def release(self) -> None:
        """释放资源。"""
```

### 使用示例

```python
from scrcpy_py_ddlx.core.decoder.video import VideoDecoder
from scrcpy_py_ddlx.core.protocol import CodecId

# 创建解码器
decoder = VideoDecoder(CodecId.H264, hw_accel=True)

# 解码循环
for packet in video_packets:
    frame = decoder.decode(packet)
    if frame is not None:
        # frame 是 BGR 格式的 numpy 数组
        cv2.imshow("Video", frame)

# 释放
decoder.release()
```

### SimpleDecoder

简化版解码器（用于录制）。

```python
class SimpleDecoder:
    """
    简化的解码器，用于录制。

    不关心帧内容，只用于获取编解码器参数。
    """

    def get_extradata(self) -> Optional[bytes]:
        """获取编解码器额外数据 (SPS/PPS)。"""
```

---

## AudioDecoder

### 支持的编解码器

| 编解码器 | MIME 类型 | 采样率 |
|----------|-----------|--------|
| OPUS | audio/opus | 48000 |
| AAC | audio/mp4a-latm | 48000 |
| FLAC | audio/flac | 48000 |
| RAW | audio/raw | 48000 |

### 核心类

```python
class AudioDecoder:
    def __init__(self, codec_id: CodecId):
        """
        初始化音频解码器。

        Args:
            codec_id: 音频编解码器 ID
        """

    def decode(self, packet) -> Optional[np.ndarray]:
        """
        解码音频包。

        Returns:
            float32 PCM 数据 (channels, samples)
        """
```

---

## DelayBuffer

延迟缓冲，用于音视频同步。

```python
class DelayBuffer:
    """
    延迟缓冲器。

    用于平滑解码输出，减少抖动。
    """

    def __init__(self, delay_ms: int = 0, max_size: int = 10):
        """
        Args:
            delay_ms: 目标延迟 (毫秒)
            max_size: 最大缓冲帧数
        """

    def put(self, frame, pts: int) -> None:
        """添加帧到缓冲区。"""

    def get(self) -> Optional[Tuple[Any, int]]:
        """获取帧和 PTS。"""

    def clear(self) -> None:
        """清空缓冲区。"""

    def get_delay(self) -> float:
        """获取当前延迟 (毫秒)。"""
```

---

## DecoderProcess

多进程解码器，解决 GIL 问题。

```python
class DecoderProcess:
    """
    多进程解码器。

    在独立进程中运行解码，避免 GIL 阻塞。
    """

    def __init__(self, codec_id: CodecId, hw_accel: bool = True):
        self._process: Optional[multiprocessing.Process] = None
        self._frame_queue: multiprocessing.Queue = None

    def start(self) -> None:
        """启动解码进程。"""

    def decode(self, packet: VideoPacket) -> None:
        """发送包到解码进程 (非阻塞)。"""

    def get_frame(self, timeout: float = 0.1) -> Optional[np.ndarray]:
        """获取解码后的帧。"""

    def stop(self) -> None:
        """停止解码进程。"""
```

### 进程间通信

```
主进程                      解码进程
  │                           │
  │ packet_queue              │ frame_queue
  │ ───────────────────────> │
  │                           │ (解码)
  │ <─────────────────────── │
  │                           │
```

---

## 异常类型

```python
class CodecNotSupportedError(DecodeError):
    """编解码器不支持"""

class DecoderInitializationError(DecodeError):
    """解码器初始化失败"""

class DecodeError(Exception):
    """解码错误基类"""
```

---

## 性能优化

### 硬件加速

| GPU | 推荐设备类型 | 备注 |
|-----|-------------|------|
| NVIDIA | cuda | 最佳性能 |
| Intel | qsv | 低功耗 |
| AMD | d3d11va | Windows |
| Apple | videotoolbox | macOS |

### 零拷贝模式 (实验性)

```bash
# 启用 GPU 零拷贝
export SCRCPY_ZERO_COPY_GPU=1
```

### 线程安全

```python
# 线程安全模式 (默认)
decoder = VideoDecoder(codec_id, thread_safe=True)

# 非线程安全 (稍快，但需要外部同步)
decoder = VideoDecoder(codec_id, thread_safe=False)
```

---

## 相关文档

- [video_decoder.md](video_decoder.md) - 视频解码详解
- [audio_decoder.md](audio_decoder.md) - 音频解码详解
- [Demuxer.md](Demuxer.md) - 解复用器
- [stream.md](stream.md) - 流解析
