# Android 11+ 音频捕获锁屏限制

## 问题描述

在 Android 11+ 设备上，如果设备处于锁屏状态时启动 scrcpy，音频捕获会失败。

## 原因

Android 11+ 的安全限制要求：
- **音频捕获必须在设备解锁（前台）状态下启动**
- 这是 `AudioRecord` API 的系统级限制

## 行为说明

| 场景 | 行为 |
|------|------|
| 启动时设备已解锁 | 音频正常启动 ✓ |
| 启动时设备锁屏 | 音频启动失败，每 3 秒重试一次 |
| 启动成功后锁屏 | **音频继续正常工作** ✓ |
| 60 秒内解锁 | 重试成功，音频恢复 ✓ |
| 超过 60 秒未解锁 | 音频被禁用，本次会话无法恢复 |

## 技术细节

1. **AudioRecord 权限机制**：
   - 一旦 AudioRecord 成功启动，就获得了系统权限
   - 即使之后锁屏，音频流也会继续工作

2. **重试机制**（服务端实现）：
   - 音频启动失败后，每 3 秒重试一次
   - 最多重试 20 次（共 60 秒）
   - 重试成功后立即恢复正常工作

3. **服务端日志示例**：
   ```
   E scrcpy: Failed to start audio capture
   E scrcpy: On Android 11, audio capture must be started in the foreground
   W scrcpy: Audio capture failed (attempt 1/20): null
   W scrcpy: Audio capture failed (attempt 2/20): null
   I scrcpy: Audio capture started successfully after 2 retry(es)
   ```

## 解决方案

### 方案 1：启动前解锁设备（推荐）
在启动 scrcpy 前确保设备已解锁。

### 方案 2：60 秒内解锁
如果启动时设备锁屏，在 60 秒内解锁设备，音频会自动恢复。

### 方案 3：仅使用视频模式
如果不需要音频，使用 `--usb` 或 `--usb-video` 模式。

## 代码实现

- 服务端重试逻辑：`scrcpy/server/.../audio/AudioEncoder.java`
- 重试间隔：3 秒
- 最大重试次数：20 次

## 相关链接

- [Android 11 音频捕获限制](https://developer.android.com/about/versions/11/privacy/foreground-service-permissions)
- [scrcpy 音频问题讨论](https://github.com/Genymobile/scrcpy/issues/4380)

---

**状态**: 已知限制，有缓解措施
**影响版本**: Android 11+
**创建日期**: 2026-02-28
