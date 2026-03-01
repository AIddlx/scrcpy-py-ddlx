# Direct SHM 模式截图功能修复

## 状态: ✅ 已修复

## 问题描述

在 Direct SHM 模式（网络模式预览窗口）下，截图功能无法正常工作：
1. 初始几次截图可能成功
2. 之后一直返回 "No frame available"
3. 截图可能返回第一帧而不是最新帧

## 问题根因

在 Direct SHM 模式下，帧数据流如下：

```
解码器 → _frame_to_nv12() → NV12 bytes → SHM Writer → GPU 渲染
                                    ↓
                            DelayBuffer → 截图
```

**问题代码** (`video.py`):

```python
if self._shm_writer is not None:
    if self._output_nv12 and frame_data is not None:
        self._shm_writer.write_nv12_frame(frame_data, ...)
        # 问题：帧只写入 SHM，不推入 DelayBuffer
        # 所以截图从 DelayBuffer 获取的是旧帧
```

## 修复方案

### video.py - 同时推入 DelayBuffer 和写入 SHM

```python
# Push to DelayBuffer for screenshot support (always, even with SHM)
if self._output_nv12 and frame_data is not None:
    # For Direct SHM mode: frame_data is bytes, wrap in dict for screenshot conversion
    if isinstance(frame_data, bytes):
        screenshot_frame = {
            'nv12_bytes': frame_data,
            'width': frame_w,
            'height': frame_h
        }
        self._frame_buffer.push(screenshot_frame, ...)
    else:
        # Already dict format (Y/U/V planes or GPU dict)
        self._frame_buffer.push(frame_data, ...)

# If shm_writer is set, also write directly to SHM for preview window
if self._shm_writer is not None:
    if self._output_nv12 and frame_data is not None:
        self._shm_writer.write_nv12_frame(frame_data, ...)
```

## 验证结果

**测试日期**: 2026-02-27

**测试日志**: `session_20260227_184726.log`

```
18:47:50 - screenshot_20260227_184750_028.jpg (7.1ms) ✅
18:47:54 - screenshot_20260227_184754_483.jpg (7.8ms) ✅
18:47:58 - screenshot_20260227_184758_243.jpg (7.8ms) ✅
18:48:17 - screenshot_20260227_184817_653.jpg (6.4ms) ✅
18:48:21 - screenshot_20260227_184821_274.jpg (9.1ms) ✅
```

每次截图都有不同的时间戳，证明截图是实时的，不再是同一张旧图。

## 涉及文件

| 文件 | 修改内容 |
|------|----------|
| `scrcpy_py_ddlx/core/decoder/video.py` | 同时推入 DelayBuffer 和写入 SHM，封装 NV12 bytes 为 dict 格式 |
| `scrcpy_py_ddlx/client/client.py` | `_nv12_dict_to_bgr()` 支持 NV12 bytes 格式 |
| `scrcpy_py_ddlx/mcp_server.py` | 同上 |

## 经验教训

1. **类型检查要匹配实际数据**：Direct SHM 模式下 `frame_data` 是 bytes，需要封装为 dict
2. **数据流追踪要完整**：从生产者到消费者的每一步都要验证数据格式
3. **不同模式可能有不同的数据格式**：Direct SHM 模式使用 bytes 格式优化性能，但截图需要兼容处理
4. **代码重构时注意保留修复**：此问题在 2026-02-24 已修复，但代码重构时丢失了修复

## 日期

- 首次修复: 2026-02-24
- 问题复发: 2026-02-27
- 再次修复: 2026-02-27
