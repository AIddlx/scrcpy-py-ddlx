# 服务端VBR编码机制分析

## 概述

本文档分析Android服务端的VBR（Variable Bitrate）编码机制，帮助理解为什么不同内容会产生不同的帧率和延迟特性。

## 核心配置

### 编码器创建 (`SurfaceEncoder.java`)

```java
// 关键常量
private static final int DEFAULT_I_FRAME_INTERVAL = 10; // 秒
private static final int REPEAT_FRAME_DELAY_US = 100_000; // 100ms

// 编码格式配置
MediaFormat format = new MediaFormat();
format.setInteger(MediaFormat.KEY_BIT_RATE, bitRate);
format.setInteger(MediaFormat.KEY_FRAME_RATE, 60);  // 名义帧率，实际可变
format.setFloat(MediaFormat.KEY_I_FRAME_INTERVAL, iFrameInterval);
format.setLong(MediaFormat.KEY_REPEAT_PREVIOUS_FRAME_AFTER, 100_000); // µs
```

### VBR vs CBR

```java
if (cbrMode) {
    format.setInteger(MediaFormat.KEY_BITRATE_MODE,
        MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_CBR);
} else {
    format.setInteger(MediaFormat.KEY_BITRATE_MODE,
        MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_VBR);
}
```

## VBR模式行为

### 码率控制

| 模式 | 行为 | 特点 |
|------|------|------|
| **VBR** (默认) | 根据内容动态调整 | 静态场景省带宽，动态场景高质量 |
| **CBR** | 固定码率 | 稳定带宽，但可能浪费或质量不足 |

**重要**：许多硬件编码器（如Qualcomm）在VBR模式下会**忽略**KEY_BIT_RATE设置，自行决定码率。

### 帧率控制

```
KEY_FRAME_RATE = 60  // 名义帧率
KEY_MAX_FPS_TO_ENCODER = maxFps  // 实际最大帧率限制
```

**注意**：`KEY_FRAME_RATE` "does not impact the actual frame rate, which is variable"。

### 帧重复机制

```java
KEY_REPEAT_PREVIOUS_FRAME_AFTER = 100_000 µs = 100ms
```

- 如果100ms内没有新帧产生，编码器会**重复上一帧**
- 这确保了即使静态内容，也有帧输出
- 但重复帧的PTS相同，客户端可能认为没有新内容

## VBR对静态内容的影响

### 机制分析

```
静态内容（如时钟动画）：
1. 内容变化少 → 编码器检测到低复杂度
2. 降低码率 → 减少数据量
3. 可能降低帧率 → 节省带宽
4. 100ms后重复帧 → 保持连接活跃
```

### 实测数据

| 内容类型 | 帧率 | Key Frame大小 | PTS间隔 |
|----------|------|---------------|---------|
| JS网页时钟 | 10-20fps | 81KB | 50-100ms |
| 本地App | ~60fps | 19KB | 16-50ms |
| 游戏画面 | ~60fps | 正常 | ~16ms |

### 关键发现

1. **JS网页时钟**：
   - 帧率降低到10-20fps
   - Key Frame异常大（81KB vs 19KB）
   - PTS间隔出现100ms的规律跳跃

2. **本地App**：
   - 保持60fps
   - Key Frame正常（19KB）
   - PTS间隔稳定

## 编码循环分析

```java
// 编码循环 (SurfaceEncoder.java:247-323)
final long DEQUEUE_TIMEOUT_US = 100000; // 100ms timeout

do {
    int outputBufferId = codec.dequeueOutputBuffer(bufferInfo, DEQUEUE_TIMEOUT_US);
    if (outputBufferId < 0) {
        // INFO_TRY_AGAIN_LATER - 没有帧可用
        consecutiveTimeouts++;
        continue;
    }
    // 处理帧...
} while (!eos);
```

**关键点**：
- 编码器每100ms检查一次输出
- 如果没有帧（静态内容），会等待
- 这可能导致帧间隔增大

## 低延迟选项

### KEY_LOW_LATENCY (Android 11+)

```java
if (lowLatency && Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
    format.setInteger(MediaFormat.KEY_LOW_LATENCY, 1);
}
```

**效果**：
- 优化编码器响应时间
- 可能增加码率
- 但**与VBR的帧率调整行为无关**

### KEY_MAX_B_FRAMES

```java
if (encoderBuffer > 0) {
    format.setInteger(MediaFormat.KEY_MAX_B_FRAMES, 0);
}
```

**效果**：
- 禁用B帧
- 减少编码延迟
- 但不改变帧率

### 编码线程优先级

```java
switch (encoderPriority) {
    case 2: priority = THREAD_PRIORITY_URGENT_DISPLAY; break;
    case 1: priority = THREAD_PRIORITY_URGENT_AUDIO; break;
    default: priority = THREAD_PRIORITY_DEFAULT; break;
}
```

## 对客户端的影响

### 时间跳跃问题

VBR + 静态内容 → 低帧率 → 大PTS间隔 → 客户端看到"时间跳跃"

```
服务端：[帧A] --100ms-- [帧A'] --100ms-- [帧B]
        ↑                           ↑
      时钟12:00:00              时钟12:00:01

客户端收到：
        [A(12:00:00)] --跳跃-- [B(12:00:01)]
        视觉上：时钟直接跳了1秒
```

### 解决方向

1. **服务端**：使用CBR强制固定帧率（增加带宽）
2. **客户端**：时间补偿（平滑处理跳跃）
3. **协议层**：传递更多时间信息

## 相关配置参数

| 参数 | 默认值 | 作用 |
|------|--------|------|
| `bitrate_mode` | VBR | 码率控制模式 |
| `video_bit_rate` | 2.5Mbps | 目标码率（VBR可能忽略） |
| `max_fps` | 60 | 最大帧率限制 |
| `i_frame_interval` | 10s | 关键帧间隔 |
| `low_latency` | false | 低延迟模式 |
| `encoder_buffer` | 0 | 编码缓冲（0=auto, 1=禁用B帧） |
| `encoder_priority` | 1 | 编码线程优先级 |

## 相关文件

- `scrcpy/server/src/main/java/com/genymobile/scrcpy/video/SurfaceEncoder.java`
- `scrcpy_py_ddlx/client/config.py` - 客户端配置
- `docs/development/known_issues/VBR_LATENCY_ISSUE.md` - VBR延迟问题

## 参考资料

- [Android MediaFormat](https://developer.android.com/reference/android/media/MediaFormat)
- [MediaCodec API](https://developer.android.com/reference/android/media/MediaCodec)
- [scrcpy issue #488](https://github.com/Genymobile/scrcpy/issues/488) - max-fps-to-encoder
