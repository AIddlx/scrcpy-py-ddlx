# 技术债务清单

> **更新时间**: 2026-02-26
> **严重程度**: Critical > Major > Minor

---

## Critical (必须尽快处理)

### TD-001: CPU 模式 GIL 竞争

**位置**: `scrcpy_py_ddlx/core/decoder/video.py`

**问题**:
- `frame.reformat("rgb24")` 持有 GIL 10-50ms
- 阻塞 UDP 接收线程
- 延迟累积到数秒

**当前状态**: 部分修复（GPU 模式可用）

**解决方案**:
1. 短期：CPU 模式码率/帧率限制
2. 长期：多进程架构

**影响**: CPU 模式基本不可用

---

### TD-002: 多进程解码器 UV 异常

**位置**: `scrcpy_py_ddlx/core/decoder/decoder_process.py`

**问题**:
- 多进程模式 UV 数据右侧 30% 为零
- 解码器创建方式不一致

**当前状态**: 弃用

**解决方案**:
- 使用 HWAccel 替代直接 cuvid
- 添加输出格式验证

**影响**: 无法使用多进程降低 GIL 竞争

---

## Major (影响用户体验)

### TD-003: 单帧缓冲架构

**位置**: `scrcpy_py_ddlx/core/decoder/delay_buffer.py`

**问题**:
- 只能存储 1 帧
- 任何消费延迟都导致帧丢失
- 无背压机制

**当前状态**: 部分修复（事件驱动渲染）

**解决方案**:
- 多帧缓冲（建议 3 帧）
- 生产消费协调

**影响**: Frame Skip，窗口拖动丢帧

---

### TD-004: 硬件解码器缓冲

**位置**: `scrcpy_py_ddlx/core/decoder/video.py`

**问题**:
- NVIDIA 解码器默认 3-5 帧缓冲
- 低帧率时延迟被放大

**当前状态**: 已优化

**解决方案**:
- `surfaces=2` 配置
- `LOW_DELAY` 标志

**影响**: VBR 低帧率场景 300-500ms 延迟

---

### TD-005: 带音频视频录制失败

**位置**: `scrcpy_py_ddlx/core/recorder/`

**问题**:
- 录制文件无法正常播放
- 音视频同步问题

**当前状态**: 已隐藏功能

**解决方案**: 待重新设计

**影响**: 无法录制带音频的视频

---

## Minor (可延后处理)

### TD-006: paintGL 空转

**位置**: `scrcpy_py_ddlx/core/player/video/opengl_window.py`

**问题**:
- 60fps 调用，30fps 消费
- 50% 空转

**当前状态**: 已优化（事件驱动）

**解决方案**: 事件驱动渲染

**影响**: CPU 资源浪费

---

### TD-007: I-frame 间隔不稳定

**位置**: 服务端 `ScreenEncoder.java`

**问题**:
- `KEY_I_FRAME_INTERVAL` 参数不可靠
- 静止场景 I-frame 间隔过大

**当前状态**: 已知问题

**解决方案**: 服务端修改

**影响**: 静止画面后恢复慢

---

### TD-008: 录音时长问题

**位置**: `scrcpy_py_ddlx/core/audio/recorder.py`

**问题**:
- 录音时长可能少于设定时间
- 缓冲区数据未完全写入

**当前状态**: 已知限制

**解决方案**: 添加缓冲区刷新

**影响**: 录音末尾丢失

---

## 待排查

### TD-009: 音频解码 GIL 风险

**位置**: `scrcpy_py_ddlx/core/decoder/audio.py`

**状态**: 待排查

**风险**: 音频处理可能持有 GIL

---

### TD-010: 控制命令 GIL 风险

**位置**: `scrcpy_py_ddlx/client/control.py`

**状态**: 待排查

**风险**: 控制命令编码可能持有 GIL

---

## 统计

| 严重程度 | 数量 | 已修复 | 待处理 |
|----------|------|--------|--------|
| Critical | 2 | 0 | 2 |
| Major | 3 | 1 | 2 |
| Minor | 3 | 1 | 2 |
| 待排查 | 2 | 0 | 2 |
| **总计** | **10** | **2** | **8** |

---

## 处理优先级

1. TD-001 (Critical) - CPU 模式限制
2. TD-003 (Major) - 多帧缓冲
3. TD-009/010 - GIL 风险排查
4. TD-002 (Critical) - 多进程修复
5. TD-005 (Major) - 录制功能

---

## 相关文档

- [优化路线图](OPTIMIZATION_ROADMAP.md)
- [已知问题](development/known_issues/README.md)
- [GIL 竞争问题](GIL_COMPETITION_ISSUE.md)
