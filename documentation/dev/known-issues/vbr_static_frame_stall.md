# VBR 模式静止画面导致编码器停止输出

## 问题描述

在网络模式下使用 VBR（可变码率）编码时，如果设备画面长时间静止，编码器可能停止输出帧数据，导致客户端画面卡死。

### 现象

- 客户端正常接收帧数据，E2E 延迟正常（7-17ms）
- 画面静止后，UDP 数据流突然中断
- 客户端检测到 3 秒无数据后断开连接
- TCP 心跳正常（PING/PONG 持续响应）
- E2E 延迟暴增到 4000ms+ 直到断开

## 问题原因

### 1. VBR 编码模式特性

```
VBR (Variable Bitrate) 模式：
┌─────────────────────────────────────────────────────────┐
│  画面变化大 → 高码率 → 编码器频繁输出                      │
│  画面变化小 → 低码率 → 编码器减少输出                      │
│  画面静止   → 极低码率 → 编码器可能停止输出  ← 问题所在     │
└─────────────────────────────────────────────────────────┘
```

**关键理解**：这不是 bug，是 VBR 的预期行为。画面静止时编码器不输出是正常的，画面恢复活动后会立即恢复输出。

### 2. 客户端错误处理

原来的客户端代码错误地将 UDP 超时视为断开：

```python
# 错误的处理
except socket.timeout:
    self._consecutive_timeouts += 1
    if self._consecutive_timeouts >= 3:
        logger.error("Server disconnect detected")
        break  # 错误地断开！
```

### 3. REPEAT_PREVIOUS_FRAME_AFTER 参数失效

```java
format.setLong(MediaFormat.KEY_REPEAT_PREVIOUS_FRAME_AFTER, 100_000); // 100ms
```

此参数理论上应该在静止时每 100ms 重复发送上一帧，但：
- Qualcomm HEVC 硬件编码器**忽略此参数**
- 其他厂商的编码器也可能不支持
- 结果：静止时编码器完全不输出

## 正确的架构设计

### 网络模式 vs ADB 隧道模式

| 模式 | 数据通道 | 断开判断依据 | 原因 |
|------|----------|-------------|------|
| **网络模式** | TCP 控制 + UDP 视频/音频 | **仅 TCP 心跳** | UDP 超时可能是画面静止 |
| **ADB 隧道** | 单一 socket | Socket 错误/不完整读取 | 单通道，超时无特殊含义 |

### 网络模式架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Android 设备                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ TCP 控制    │    │ UDP 视频    │    │ UDP 音频    │     │
│  │ (心跳+控制) │    │ (数据流)    │    │ (数据流)    │     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                         客户端                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  连接状态判断：                                       │   │
│  │  - TCP 心跳超时 → 断开连接                           │   │
│  │  - UDP 超时 → 仅记录日志，不影响连接状态             │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 状态

- **优先级**: 高
- **状态**: ✅ 已修复（客户端兼容）
- **服务端修复**: 不需要（VBR 静止不输出是预期行为）
- **最后修复日期**: 2026-02-26（代码与文档对齐，修复了两个相关问题）

## 相关问题

同一天修复的另一个相关问题：
- [预览窗口启动黑屏问题](preview_black_screen_fix.md) - VBR 静止画面导致共享内存无帧

## 实现的修复

### 1. UDP 视频接收 (`udp_video.py`)

**修复前**：
```python
except socket.timeout:
    self._consecutive_timeouts += 1
    if self._consecutive_timeouts >= MAX_CONSECUTIVE_TIMEOUTS:
        logger.error("Server disconnect detected")
        break  # 错误地断开
```

**修复后**：
```python
except socket.timeout:
    # UDP timeout - this is NORMAL in network mode
    # Disconnect detection is handled by TCP heartbeat
    self._consecutive_timeouts += 1
    if self._consecutive_timeouts % 10 == 0:
        logger.info(f"No video data - static screen or network issue")
    continue  # 继续等待，不触发断开
```

### 2. UDP 音频接收 (`udp_audio.py`)

同样的修复逻辑。

### 3. ADB 隧道模式 (无需修改)

ADB 隧道模式使用的 `StreamingDemuxerBase` 本来就正确处理超时：

```python
except socket.timeout:
    continue  # 本来就正确
```

## 测试验证

### 网络模式测试

```
测试命令: python scrcpy_http_mcp_server.py --network-push 192.168.5.4

结果：
- 运行时间: 约 15 秒
- 帧数: 300 帧
- E2E 延迟: 大部分 8-100ms
- 状态: ✅ 画面静止后不断开，恢复活动后继续
```

### ADB 隧道模式测试

```
测试命令: python scrcpy_http_mcp_server.py --connect --preview

结果：
- 运行时间: 约 24 秒
- 帧数: 420 帧
- E2E 延迟: 11-69ms
- 状态: ✅ 本来就正常
```

## 相关文件

| 文件 | 说明 |
|------|------|
| `scrcpy_py_ddlx/core/demuxer/udp_video.py` | UDP 视频接收（已修复） |
| `scrcpy_py_ddlx/core/demuxer/udp_audio.py` | UDP 音频接收（已修复） |
| `scrcpy_py_ddlx/core/demuxer/base.py` | ADB 隧道基类（无需修改） |
| `scrcpy_py_ddlx/core/heartbeat.py` | TCP 心跳管理 |
| `scrcpy/server/.../video/SurfaceEncoder.java` | 服务端编码器（无需修改） |
