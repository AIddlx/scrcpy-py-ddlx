# VideoDecoder - 视频解码器

> **路径**: `scrcpy_py_ddlx/core/decoder/video.py`
> **职责**: 使用 PyAV (FFmpeg) 进行视频解码，支持硬件加速

---

## 类定义

### VideoDecoder

**职责**: 多线程视频解码器

**线程**: 解码线程 (后台)

**依赖**: PyAV, numpy, DelayBuffer, protocol

---

## 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `_width` | int | 视频宽度 |
| `_height` | int | 视频高度 |
| `_codec_id` | int | 编解码器ID |
| `_hw_accel` | bool | 硬件加速标志 |
| `_output_nv12` | bool | NV12输出模式 |
| `_packet_queue` | Queue | 输入包队列 |
| `_frame_buffer` | DelayBuffer | 输出缓冲区 |
| `_codec` | CodecContext | PyAV 解码器 |

---

## 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `start` | - | - | 启动解码线程 |
| `stop` | - | - | 停止解码 |
| `push` | packet | - | 推送视频包 |
| `pause` | - | - | 暂停解码 |
| `resume` | - | - | 恢复解码 |
| `get_frame` | timeout | np.ndarray | 获取解码帧 |
| `set_frame_size_changed_callback` | callback | - | 设置尺寸变化回调 |
| `configure_content_detection` | ... | - | 配置内容检测 |

---

## 内部方法

| 方法 | 说明 |
|------|------|
| `_decode_loop` | 解码主循环 |
| `_decode_packet` | 解码单个包 |
| `_frame_to_bgr` | 转换为RGB格式 |
| `_frame_to_nv12` | 转换为NV12格式 |
| `_frame_to_nv12_dict` | 转换为NV12字典 |
| `_init_hw_decoder` | 初始化硬件解码器 |

---

## 硬件加速

### 支持的硬件解码器

| 类型 | 说明 |
|------|------|
| `cuda` | NVIDIA NVDEC |
| `cuvid` | NVIDIA CUVID |
| `qsv` | Intel Quick Sync |
| `d3d11va` | DirectX 11 |
| `videotoolbox` | macOS |

### 低延迟配置

```python
# LOW_DELAY 标志
codec.flags |= 0x00080000

# NVIDIA surfaces 配置
codec.options = {'surfaces': '2'}

# Packet Queue 大小
self._packet_queue = Queue(maxsize=1)
```

---

## 输出格式

### RGB 模式 (CPU)

```python
frame_bgr = frame.reformat(format="rgb24")
# GIL 持有时间: 10-50ms
# 不推荐使用
```

### NV12 模式 (GPU)

```python
frame_nv12 = frame.reformat(format="nv12")
# GIL 持有时间: 1-5ms
# 推荐使用
```

---

## 依赖关系

```
VideoDecoder
    │
    ├──→ av (PyAV)
    │
    ├──→ numpy
    │
    ├──→ DelayBuffer (输出)
    │
    └──→ protocol.py (常量)
```

---

*此文档基于客户端代码分析生成*
