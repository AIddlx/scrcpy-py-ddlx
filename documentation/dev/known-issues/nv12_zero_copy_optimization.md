# NV12 Semi-planar 零拷贝优化（待实现）

## 现状

`test_network_direct.py` 即使使用 `--quiet --no-tracker` 仍有最高 3% 的 CPU 峰值占用。

## 原因分析

### 两条渲染路径对比

| 路径 | 使用场景 | 数据格式 | CPU 开销 |
|------|----------|----------|----------|
| SHM 路径 | MCP 预览窗口 | semi-planar bytes | ~1.5%（零拷贝）|
| DelayBuffer 路径 | test_network_direct.py | dict (Y/U/V 分离) | ~3-4%（有拷贝）|

### 问题根源

在 `video.py` 第 909-914 行：

```python
elif self._shm_writer is not None:
    # For SHM: return bytes format (semi-planar, 零拷贝)
    frame_data, frame_w, frame_h = self._frame_to_nv12(frame)
else:
    # For DelayBuffer: return dict with separate Y/U/V planes (需要 UV 转换)
    frame_data, frame_w, frame_h = self._frame_to_nv12_dict(frame)
```

**DelayBuffer 路径**返回 dict 格式（分离的 Y/U/V plane），导致 `opengl_window.py` 每帧需要做 UV interleaved 转换：

```python
# opengl_window.py 第 554-556 行
uv_plane = np.empty((uv_height, uv_width * 2), dtype=np.uint8)  # 分配 ~1.2MB
uv_plane[:, 0::2] = u_plane  # 复制 ~0.6MB
uv_plane[:, 1::2] = v_plane  # 复制 ~0.6MB
```

对于 1080x2400 分辨率，每帧需要额外处理 **~2.4MB** 数据！

## 优化方案

让 `_frame_to_nv12_dict` 返回 numpy 数组格式的 semi-planar NV12 数据：
- 格式：`np.array` 形状为 `(height * 3 // 2, width)`，即 `[Y plane; UV plane interleaved]`
- `opengl_window.py` 中使用 view 零拷贝提取 Y 和 UV plane

### 预期效果

| 场景 | 优化前 | 优化后 |
|------|--------|--------|
| test_network_direct.py 快速滑动 | ~3-4% | ~1.5-2% |

### 需要修改的文件

1. `scrcpy_py_ddlx/core/decoder/video.py`
   - 修改 `_frame_to_nv12_dict` 返回 semi-planar numpy 数组

2. `scrcpy_py_ddlx/core/player/video/opengl_window.py`
   - 添加处理 numpy 数组格式的逻辑（参考现有的 semi-planar 路径）

## 状态

⏳ **待实现**（优先级：中）

## 相关文档

- [CPU_OPTIMIZATION_RESEARCH.md](../CPU_OPTIMIZATION_RESEARCH.md)
- [WINDOW_RESIZE_FIXES_PREVIEW.md](../WINDOW_RESIZE_FIXES_PREVIEW.md) - #17 glTexImage2D vs glTexSubImage2D

---

**创建日期**: 2026-03-01
