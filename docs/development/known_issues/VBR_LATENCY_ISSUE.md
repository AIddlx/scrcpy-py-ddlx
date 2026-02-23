# VBR场景下的延迟问题分析

## 状态

**已优化** - 2026-02-23 - 四轮优化完成，滞后从 300-500ms 降至 ~111ms，内存带宽降低 51%（3纹理→2纹理）

## 问题描述

VBR 模式下，低帧率场景（如 JS 网页时钟）出现 300-500ms 滞后，而高帧率场景（60fps 游戏）只有 88-120ms。

**关键观察**：
- 60fps 时：滞后 ~100ms（约 6 帧）
- 10fps 时：滞后 300-500ms（约 3-5 帧）

**结论**：滞后是**固定帧数**，而非固定时间 → 说明有固定帧数的缓冲。

## 根因

**硬件解码器（NVIDIA cuvid/nvdec）默认有 3-5 帧的内部缓冲**，与帧率无关：
- 60fps: 5帧 × 16.67ms = 83ms
- 10fps: 5帧 × 100ms = 500ms

## 修复方案

### 第一轮：LOW_DELAY 标志

修改 `video.py`，为硬件解码器启用 `AV_CODEC_FLAG_LOW_DELAY` 标志：

```python
# 之前：只有软件解码器设置
if not self._using_hw_decoder:
    codec.flags |= 0x00080000

# 之后：所有解码器都设置
codec.flags |= 0x00080000  # 移到 if 外面
```

**效果**：滞后从 300-500ms 降至 115-200ms

### 第二轮：超低延迟配置

#### 1. 硬件解码器 surfaces 优化

```python
# NVIDIA cuvid/nvdec 默认使用 5+ surfaces
# 减少到 2 以最小化延迟
codec.options = {'surfaces': '2'}
```

#### 2. Packet Queue 大小优化

```python
# 之前：maxsize=3（可能缓冲 3 个包）
# 之后：maxsize=1（始终处理最新包）
self._packet_queue = Queue(maxsize=1)
```

**效果**：queue_wait 从 0.1-20ms 降至 0.72ms 平均

### 第三轮：事件驱动渲染

将 16ms Timer 轮询改为 Qt Signal 事件驱动：

```python
# DelayBuffer 添加信号支持
_frame_ready_signal = Signal()
delay_buffer.set_frame_ready_signal(self._frame_ready_signal)

# 帧到达时立即触发渲染
self._frame_ready_signal.connect(self._on_frame_ready)
```

**效果**：滞后稳定在 ~111ms，消除轮询延迟

### 第四轮：内存带宽优化（2 纹理方案）

使用 GL_RG 格式上传 UV 交错数据，完全消除 U/V plane 复制：

```python
# 之前：3 纹理方案（Y + U + V）
u_plane = uv_plane[:, 0::2].copy()  # ~0.65 MB 复制
v_plane = uv_plane[:, 1::2].copy()  # ~0.65 MB 复制
# 上传 3 个 GL_LUMINANCE 纹理

# 之后：2 纹理方案（Y + UV）
uv_plane = frame_array[height:, :]  # 零拷贝
# 上传 1 个 GL_LUMINANCE + 1 个 GL_RG 纹理
```

**Shader 变更**：
```glsl
// 之前：3 纹理
uniform sampler2D y_texture;
uniform sampler2D u_texture;
uniform sampler2D v_texture;

// 之后：2 纹理
uniform sampler2D y_texture;
uniform sampler2D uv_texture;  // RG 格式，R=U, G=V
float u = texture2D(uv_texture, coord).r;
float v = texture2D(uv_texture, coord).g;
```

**效果**：内存带宽从 ~7.6 MB/帧 降至 ~3.7 MB/帧（减少 51%）

## 完整低延迟配置

| 配置项 | 默认值 | 优化值 | 作用 |
|--------|--------|--------|------|
| `AV_CODEC_FLAG_LOW_DELAY` | 禁用 | 启用 | 减少帧重排序 |
| `surfaces` (cuvid) | 5+ | 2 | 减少硬件帧缓冲 |
| `Packet Queue` | maxsize=3 | maxsize=1 | 不累积旧包 |
| `DelayBuffer` | 1 帧 | 1 帧 | 必要的单帧缓冲 |
| **渲染模式** | 16ms 轮询 | **Signal 事件驱动** | 帧到达立即渲染 |

## 优化效果总结

| 指标 | 优化前 | 第一轮后 | 第二轮后 | 第三轮后 | 第四轮后 |
|------|--------|---------|---------|---------|---------|
| 滞后 | 300-500ms | 115-200ms | - | **~111ms** | ~111ms |
| 渲染模式 | 16ms 轮询 | 16ms 轮询 | 16ms 轮询 | **事件驱动** | 事件驱动 |
| GIL 调用(10fps) | 60次/秒 | 60次/秒 | 60次/秒 | **10次/秒** | 10次/秒 |
| 内存带宽 | ~7.6 MB/帧 | ~7.6 MB/帧 | ~7.6 MB/帧 | ~7.6 MB/帧 | **~3.7 MB/帧** |
| 纹理数量 | 3 | 3 | 3 | 3 | **2** |

## 关键经验

1. **硬件解码器有固定帧缓冲**：默认 3-5 帧，与帧率无关
2. **低帧率时缓冲延迟被放大**：5帧 × 100ms = 500ms
3. **`AV_CODEC_FLAG_LOW_DELAY` 对硬件解码器有效**
4. **`surfaces` 选项控制 NVIDIA 解码器缓冲**
5. **诊断关键**：滞后是"固定帧数"而非"固定时间"
6. **事件驱动渲染**：使用 Qt Signal 替代 Timer 轮询，减少 GIL 竞争
7. **GL_RG 双通道纹理**：使用 RG 格式上传 UV 交错数据，消除 U/V 分离复制

## 代码位置

- `scrcpy_py_ddlx/core/decoder/video.py` 第418行 - LOW_DELAY 标志
- `scrcpy_py_ddlx/core/decoder/video.py` 第438行 - surfaces 选项
- `scrcpy_py_ddlx/core/decoder/video.py` 第253行 - Packet Queue 大小
- `scrcpy_py_ddlx/core/decoder/delay_buffer.py` - 帧就绪信号
- `scrcpy_py_ddlx/core/player/video/opengl_window.py` 第107行 - 2纹理 shader (Y + UV)
- `scrcpy_py_ddlx/core/player/video/opengl_window.py` 第241行 - 2纹理初始化
- `scrcpy_py_ddlx/core/player/video/opengl_window.py` 第500行 - _paint_nv12 2纹理上传

## 参考资料

- [FFmpeg cuvid decoder options](https://ffmpeg.org/ffmpeg-codecs.html#cuvid)
- [PyNvVideoCodec API](https://docs.nvidia.com/video-technologies/pynvvideocodec/pynvc-api-prog-guide/index.html)

## 相关文档

- [多进程解码器问题](MULTIPROCESS_DECODER_ISSUE.md)
- [视频音频管道](../VIDEO_AUDIO_PIPELINE.md)
- [网络管道](../NETWORK_PIPELINE.md)
