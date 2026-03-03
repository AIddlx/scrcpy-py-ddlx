# 服务端帧率控制机制分析

> **版本**: 1.0
> **创建日期**: 2026-02-23
> **相关文件**: `SurfaceEncoder.java`, `Options.java`

本文档深入分析 Android 服务端的帧率控制和 VBR/CBR 机制，帮助理解不同内容类型的帧率行为差异。

---

## 1. 核心配置参数

### 1.1 关键常量 (`SurfaceEncoder.java`)

```java
private static final int DEFAULT_I_FRAME_INTERVAL = 10;      // 关键帧间隔: 10秒
private static final int REPEAT_FRAME_DELAY_US = 100_000;    // 帧重复延迟: 100ms
private static final String KEY_MAX_FPS_TO_ENCODER = "max-fps-to-encoder";
```

### 1.2 可配置参数 (`Options.java`)

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `video_bit_rate` | 8,000,000 (8Mbps) | 目标码率 |
| `max_fps` | 0 (无限制) | 最大帧率限制 |
| `bitrate_mode` | "vbr" | 码率控制模式 |
| `i_frame_interval` | 10 | I帧间隔 (秒) |
| `low_latency` | false | 低延迟模式 (Android 11+) |
| `encoder_buffer` | 0 | 编码器缓冲 (0=auto, 1=禁用B帧) |
| `encoder_priority` | 1 | 编码线程优先级 |

---

## 2. 帧率控制机制详解

### 2.1 帧率配置层级

```
┌─────────────────────────────────────────────────────────┐
│                  MediaFormat 配置                        │
├─────────────────────────────────────────────────────────┤
│  KEY_FRAME_RATE = 60        (名义帧率，不控制实际帧率)    │
│  KEY_MAX_FPS_TO_ENCODER     (实际最大帧率限制)           │
│  KEY_REPEAT_PREVIOUS_FRAME_AFTER = 100ms (静态内容触发)  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              Android MediaCodec 编码器                   │
├─────────────────────────────────────────────────────────┤
│  - 根据内容复杂度动态调整实际帧率                         │
│  - VBR 模式: 内容变化少时自动降低帧率                     │
│  - CBR 模式: 尝试保持恒定帧率 (依赖硬件实现)              │
└─────────────────────────────────────────────────────────┘
```

### 2.2 `KEY_REPEAT_PREVIOUS_FRAME_AFTER` 行为

**设置值**: 100,000 微秒 = 100ms

**行为描述** (来自 Android 文档和代码分析):

```
屏幕内容变化检测流程:
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  屏幕有变化?  ─────────────────────────────────────────→ │ [编码新帧]
│       │                                                  │
│       ↓ 无变化                                           │
│                                                          │
│  等待 100ms                                              │
│       │                                                  │
│       ↓                                                  │
│                                                          │
│  [生成重复帧] ← 重复上一帧内容, PTS 相同                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**关键点**:
1. 新帧**只在屏幕内容变化时**产生
2. 如果屏幕静止超过 100ms，编码器会生成重复帧
3. 重复帧的 **PTS (时间戳) 与上一帧相同**
4. 这确保了即使静态内容，连接也不会超时

### 2.3 `max_fps` 参数的实际作用

```java
// SurfaceEncoder.java:387-391
if (maxFps > 0) {
    // 设置最大帧率限制 (非公开 API，Android 10+)
    format.setFloat(KEY_MAX_FPS_TO_ENCODER, maxFps);
}
```

**实际效果**:
- 仅在 `maxFps > 0` 时生效
- 这是**最大值**限制，不是目标帧率
- VBR 模式下，实际帧率仍可能低于此值
- 参考: [scrcpy issue #488](https://github.com/Genymobile/scrcpy/issues/488)

---

## 3. VBR vs CBR 模式对比

### 3.1 模式设置

```java
// SurfaceEncoder.java:365-373
if (Build.VERSION.SDK_INT >= AndroidVersions.API_26_ANDROID_8_0) {
    if (cbrMode) {
        format.setInteger(MediaFormat.KEY_BITRATE_MODE,
            MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_CBR);
    } else {
        format.setInteger(MediaFormat.KEY_BITRATE_MODE,
            MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_VBR);
    }
}
```

### 3.2 行为差异对比表

| 特性 | VBR (默认) | CBR |
|------|------------|-----|
| **码率策略** | 根据内容动态调整 | 恒定码率 |
| **静态场景** | 自动降低码率和帧率 | 保持较高码率 |
| **动态场景** | 增加码率保持质量 | 可能出现质量波动 |
| **带宽使用** | 不均匀，省带宽 | 持续占用带宽 |
| **延迟稳定性** | 随内容变化 | 较稳定 |
| **硬件支持** | 几乎所有编码器 | 部分硬件可能忽略 |

### 3.3 VBR 模式下的帧率动态调整

```
内容复杂度检测:
┌─────────────────────────────────────────────────────────────┐
│                    VBR 帧率调整逻辑                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  高运动/复杂内容 (游戏/视频)                                 │
│       │                                                     │
│       ├──→ 帧率: 50-60 fps                                  │
│       ├──→ 码率: 接近设定值                                  │
│       └──→ 帧间隔: 16-20ms                                   │
│                                                             │
│  中等变化 (UI 动画/滑动)                                     │
│       │                                                     │
│       ├──→ 帧率: 30-50 fps                                  │
│       ├──→ 码率: 中等                                        │
│       └──→ 帧间隔: 20-33ms                                   │
│                                                             │
│  低变化 (JS 时钟/静态页面)                                   │
│       │                                                     │
│       ├──→ 帧率: 10-20 fps  ⚠️                              │
│       ├──→ 码率: 大幅降低                                    │
│       └──→ 帧间隔: 50-100ms  ⚠️                              │
│                                                             │
│  完全静止                                                    │
│       │                                                     │
│       ├──→ 帧率: 10 fps (由 REPEAT_FRAME_AFTER 决定)        │
│       └──→ 发送重复帧 (每 100ms)                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 静态内容检测与帧率降低

### 4.1 检测机制

Android 的 `VirtualDisplay` 和 `MediaCodec` 配合工作:

1. **VirtualDisplay** 将屏幕内容渲染到 Surface
2. **只有当 Surface 内容变化时**，才会触发编码
3. 编码器内部会分析帧间差异

### 4.2 静态内容的帧率行为

```
时间线示例 (JS 网页时钟):
┌────────────────────────────────────────────────────────────────┐
│ T=0ms    T=100ms   T=200ms   T=300ms   T=400ms   T=500ms       │
│   │        │        │        │        │        │              │
│   ▼        ▼        ▼        ▼        ▼        ▼              │
│ [帧1]───[重复]───[帧2]───[重复]───[帧3]───[重复]              │
│  新帧    帧1'    新帧    帧2'    新帧    帧3'                  │
│  81KB            80KB            81KB                          │
│                                                                │
│ 帧间隔: 100ms (远大于期望的 16ms)                              │
│ 实际帧率: ~10 fps                                              │
└────────────────────────────────────────────────────────────────┘
```

### 4.3 不同内容类型的预期行为

| 内容类型 | 变化程度 | 预期帧率 | 预期间隔 | Key Frame 大小 |
|----------|----------|----------|----------|----------------|
| 3D 游戏 | 高 | 50-60 fps | 16-20ms | 正常 (~20KB) |
| 视频播放 | 高 | 50-60 fps | 16-20ms | 正常 |
| UI 滑动 | 中 | 30-50 fps | 20-33ms | 正常 |
| 简单动画 | 中-低 | 20-40 fps | 25-50ms | 中等 |
| **JS 网页时钟** | 低 | **10-20 fps** | **50-100ms** | **大 (~80KB)** |
| 静态页面 | 极低 | 10 fps | 100ms | 正常 |

**JS 网页时钟的特殊性**:
- 内容变化少但必须精确同步
- 每帧都是"关键帧"（显示新时间）
- 低帧率 = 任何延迟都会放大视觉跳跃

---

## 5. 编码循环时序分析

### 5.1 编码循环流程

```java
// SurfaceEncoder.java:254-323
final long DEQUEUE_TIMEOUT_US = 100000; // 100ms timeout

do {
    // 检查待机模式
    if (standby.get() && !singleFrameMode) {
        singleFrameMode = waitInStandby();
        // ...
    }

    // 尝试获取编码输出
    int outputBufferId = codec.dequeueOutputBuffer(bufferInfo, DEQUEUE_TIMEOUT_US);

    if (outputBufferId < 0) {
        // INFO_TRY_AGAIN_LATER - 没有帧可用
        consecutiveTimeouts++;
        continue;  // 继续等待
    }

    // 有帧可用，处理并发送
    // ...

} while (!eos);
```

### 5.2 时序图

```
编码循环时序:
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│ 时间轴 ─────────────────────────────────────────────────────────→   │
│                                                                     │
│ [dequeueOutputBuffer(100ms timeout)]                               │
│         │                                                           │
│         ├──→ 有输出 ──→ [处理帧] ──→ [发送] ──→ [释放buffer]        │
│         │                                                           │
│         └──→ 超时 ──→ [consecutiveTimeouts++] ──→ [继续循环]         │
│                                                                     │
│ 如果连续 100 次超时 (10秒) ──→ [警告: 编码器可能卡死]               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.3 关键时间参数

| 参数 | 值 | 影响 |
|------|-----|------|
| `DEQUEUE_TIMEOUT_US` | 100,000 (100ms) | 编码输出等待超时 |
| `REPEAT_FRAME_DELAY_US` | 100,000 (100ms) | 静态内容帧重复间隔 |
| `DEFAULT_I_FRAME_INTERVAL` | 10 (秒) | 关键帧间隔 |

---

## 6. 对客户端延迟的影响分析

### 6.1 延迟传递链

```
服务端:
┌────────────────────────────────────────────────────────────────┐
│ [屏幕捕获] → [MediaCodec编码] → [UDP发送]                       │
│    ~10-20ms     ~50-100ms         ~1-5ms                       │
└────────────────────────────────────────────────────────────────┘
                            ↓
网络: ~5-20ms (WiFi)
                            ↓
客户端:
┌────────────────────────────────────────────────────────────────┐
│ [UDP接收] → [解码] → [渲染] → [显示]                            │
│   ~1-5ms     ~5ms    ~5ms    ~0-16ms                           │
└────────────────────────────────────────────────────────────────┘
```

### 6.2 VBR 静态内容的特殊影响

**问题**: 低帧率 + 时间敏感内容 = 视觉跳跃

```
正常内容 (60fps):
┌────────────────────────────────────────────────────────────────┐
│ [F1][F2][F3][F4][F5][F6]... 每帧 16ms                          │
│  ↓   ↓   ↓   ↓   ↓   ↓                                         │
│ 即使丢帧/延迟，影响有限 (最多跳 1-2 帧)                         │
└────────────────────────────────────────────────────────────────┘

静态内容 (10fps, JS时钟):
┌────────────────────────────────────────────────────────────────┐
│ [F1] ─── 100ms ─── [F2] ─── 100ms ─── [F3]                     │
│  ↓                  ↓                  ↓                        │
│ 每帧都是"关键帧"（显示新时间）                                  │
│ 任何延迟/丢帧 = 视觉上时间跳跃                                  │
└────────────────────────────────────────────────────────────────┘
```

### 6.3 延迟对比

| 场景 | 服务端帧率 | 服务端帧间隔 | 理论最小延迟 | 实测延迟 |
|------|-----------|-------------|-------------|----------|
| 3D 游戏 | 60 fps | 16ms | ~80ms | 88-120ms |
| 本地 App | 60 fps | 16ms | ~80ms | ~100ms |
| UI 滑动 | 40 fps | 25ms | ~90ms | ~120ms |
| **JS 时钟** | **10-20 fps** | **50-100ms** | ~130ms | **400ms+** |

**结论**: 静态内容场景下，服务端帧率降低是客户端延迟增大的主要原因之一。

---

## 7. 优化建议

### 7.1 服务端优化选项

| 选项 | 命令参数 | 效果 | 副作用 |
|------|----------|------|--------|
| CBR 模式 | `--bitrate-mode=cbr` | 更稳定的帧率 | 带宽增加 |
| 降低 I 帧间隔 | `--i-frame-interval=2` | 更快恢复 | 带宽增加 |
| 低延迟模式 | `--low-latency` | 减少编码缓冲 | 部分设备不兼容 |
| 限制帧率 | `--max-fps=30` | 更稳定的帧间隔 | 画面流畅度降低 |

### 7.2 客户端补偿策略

对于 VBR 静态内容场景，建议在客户端实现:

1. **PTS 时间跳跃检测**
   - 监控帧间隔变化
   - 当间隔 > 50ms 时标记为"跳跃帧"

2. **关键帧保护**
   - 检测到跳跃时，延长当前帧的显示优先级
   - 避免关键帧被后续帧覆盖

3. **时间补偿显示**
   - 根据 PTS 计算期望显示时间
   - 动态调整渲染节奏

---

## 8. 相关文件

- `scrcpy/server/src/main/java/com/genymobile/scrcpy/video/SurfaceEncoder.java` - 主编码器
- `scrcpy/server/src/main/java/com/genymobile/scrcpy/Options.java` - 配置解析
- `scrcpy/server/src/main/java/com/genymobile/scrcpy/video/ScreenCapture.java` - 屏幕捕获
- `scrcpy_py_ddlx/client/config.py` - 客户端配置

## 9. 相关文档

- [SERVER_VBR_MECHANISM.md](../SERVER_VBR_MECHANISM.md) - VBR 机制概述
- [VBR_LATENCY_ISSUE.md](../known_issues/VBR_LATENCY_ISSUE.md) - VBR 延迟问题
- [E2E_LATENCY_ANALYSIS.md](../E2E_LATENCY_ANALYSIS.md) - 端到端延迟分析
- [VIDEO_AUDIO_PIPELINE.md](../VIDEO_AUDIO_PIPELINE.md) - 音视频管道

---

## 10. 参考资料

- [Android MediaFormat.KEY_REPEAT_PREVIOUS_FRAME_AFTER](https://developer.android.com/reference/android/media/MediaFormat#KEY_REPEAT_PREVIOUS_FRAME_AFTER)
- [scrcpy issue #488 - max-fps-to-encoder](https://github.com/Genymobile/scrcpy/issues/488)
- [scrcpy develop.md - Video encoding](https://github.com/Genymobile/scrcpy/blob/master/doc/develop.md#video-encoding)
