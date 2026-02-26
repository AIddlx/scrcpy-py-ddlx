# 预览窗口启动时黑屏问题

## 问题描述

预览窗口启动后长时间黑屏，需要用户点击设备屏幕才会显示画面。

### 现象

- 预览窗口启动正常，但画面一直黑屏
- 用户点击设备屏幕后，画面立即显示
- 越早点击，画面显示越早

## 问题原因

### 根本原因

**解码器在 `start_preview` 之前就开始工作，早期帧写入 DelayBuffer 而不是共享内存。**

### 时间线分析

```
修复前：
T+0s   解码器开始解码帧 → 写入 DelayBuffer（shm_writer=None）
T+1s   start_preview 被调用 → SimpleSHMWriter 创建
T+1s   decoder._shm_writer = shm_writer ← 这时才设置
T+1s   但此时画面静止，VBR 不输出新帧
T+2s   预览进程启动 → 读取共享内存 → counter=0 → 无帧！
T+?s   用户点击 → 画面变化 → 新帧 → 写入共享内存 → 显示
```

### 问题链

```
1. 解码器在 start_preview 之前就开始工作
2. 早期帧被写入 DelayBuffer（shm_writer 还是 None）
3. start_preview 创建共享内存，设置 shm_writer
4. VBR 模式下静止画面不输出新帧
5. 共享内存 counter=0，没有帧数据
6. 预览进程读取失败，窗口黑屏
7. 用户点击 → 画面变化 → 编码器输出新帧 → 显示
```

## 状态

- **优先级**: 高
- **状态**: ✅ 已修复
- **修复日期**: 2026-02-26

## 解决方案

在设置 `shm_writer` 后，立即请求一个关键帧来触发编码器输出：

```python
# scrcpy_http_mcp_server.py

shm_writer = self._preview_manager.get_shm_writer()
if shm_writer is not None:
    decoder._shm_writer = shm_writer
    decoder._output_nv12 = True
    logger.info("Direct SHM mode enabled: GPU NV12 rendering")

    # CRITICAL: Request a new keyframe after setting shm_writer
    # This ensures a frame is written to shared memory immediately,
    # preventing black screen when VBR mode has paused output due to static screen.
    if hasattr(self._client, 'reset_video'):
        self._client.reset_video()
        logger.info("Preview: Requested keyframe after shm_writer setup")
```

## 修复效果

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| 首帧显示时间 | 22秒后（需点击） | 立即（第一个 timer tick） |
| counter 值 | 0（无帧） | 4+（已有帧） |
| TRUE_E2E | - | 82ms → 10-30ms |

### 修复后日志

```
20:24:21.147 | Direct SHM mode enabled: GPU NV12 rendering
20:24:21.148 | Preview: Requested keyframe after shm_writer setup
...
20:24:21.607 | [TIMER_TICK] #1
20:24:21.610 | [SHM_TIMING] counter=4  ← 共享内存已有帧！
20:24:21.610 | [PREVIEW_PTS] First frame received  ← 立即显示！
```

## 相关问题

- [VBR 静止画面断开问题](vbr_static_frame_stall.md) - 同一次修复中的另一个问题

## 相关文件

| 文件 | 说明 |
|------|------|
| `scrcpy_http_mcp_server.py` | MCP 服务器，修复点 |
| `scrcpy_py_ddlx/core/decoder/video.py` | 视频解码器 |
| `scrcpy_py_ddlx/simple_shm.py` | 共享内存读写 |
| `scrcpy_py_ddlx/preview_process.py` | 预览进程 |

## 经验教训

1. **理解数据流时序** - 解码器可能在其他组件初始化之前就开始工作
2. **VBR 模式特性** - 静止画面时不输出帧是预期行为，需要主动触发
3. **共享内存初始化** - 创建共享内存不等于有数据，需要确保写入端已就绪
4. **关键帧请求** - 在需要立即显示时，请求关键帧是最可靠的方式
