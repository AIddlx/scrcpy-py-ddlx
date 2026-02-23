# 多进程解码器问题归档

## 状态

**暂时弃用** - 2026-02-23

## 问题描述

多进程模式下，画面右侧约1/3区域出现严重绿色变色。

## 症状

- 右侧区域UV数据约30%为零（`u_right_zeros=66832/216000 (30.9%)`）
- Y平面数据正常，只有UV（色度）平面受影响
- 单进程模式相同场景下UV数据正常（`U range: [26, 212]`，无零值）

## 根因分析

### 直接原因

子进程解码器输出的NV12格式UV数据右侧区域包含大量零值。

### 技术原因

**解码器创建方式不一致**：

| 模式 | 解码器创建方式 |
|------|---------------|
| 单进程 | `av.CodecContext.create('hevc', 'r', hwaccel=HWAccel(device_type="cuda"))` |
| 多进程 | `av.CodecContext.create('hevc_cuvid', 'r')` |

单进程使用 `HWAccel` 包装器，多进程直接使用 `hevc_cuvid` 解码器名称。这两种方式虽然都能解码H.265，但输出的NV12格式可能有细微差异（stride、对齐等）。

## 尝试的修复

1. **添加fast path** - 直接复制PyAV平面数据，避免numpy处理
2. **添加reading_buffer同步** - 防止SHM读写竞争
3. **使用HWAccel** - 改为与单进程相同的解码器创建方式（未完成测试）

## 数据流分析

```
[UDP接收] → [分片重组] → [解码] → [SHM写入] → [SHM读取] → [OpenGL渲染]
                                    ↑                    ↓
                              问题发生点            症状显现点
```

## 相关文件

- `scrcpy_py_ddlx/core/decoder/decoder_process.py` - 子进程解码器
- `scrcpy_py_ddlx/simple_shm.py` - 共享内存读写
- `scrcpy_py_ddlx/core/player/video/opengl_window.py` - NV12渲染

## 诊断日志

关键日志模式：
```
[SHM_DATA] u_right_zeros=66832/216000 (30.9%)  # 多进程，有问题
[PAINT_NV12] U range: [0, 212]                 # 多进程，最小值为0
[PAINT_NV12] U range: [26, 212]                # 单进程，最小值正常
```

## 后续工作

如果将来需要重新启用多进程模式：

1. 修改 `decoder_process.py` 使用 `HWAccel` 而非直接使用 cuvid 解码器名称
2. 添加解码器输出格式的验证（stride、alignment）
3. 考虑使用不同的IPC方式（如管道而非SHM）

## 相关文档

- [GIL竞争问题](GIL_COMPETITION_ISSUE.md)
- [Python GIL竞争风险](PYTHON_GIL_COMPETITION_RISKS.md)
