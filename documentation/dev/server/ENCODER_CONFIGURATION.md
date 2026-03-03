# 服务端视频编码器配置详解

本文档详细分析 scrcpy 服务端视频编码器的完整配置机制。

## 1. 概述

scrcpy 使用 Android `MediaCodec` API 进行硬件视频编码。编码器配置主要通过 `SurfaceEncoder.java` 类实现。

### 核心类
- `SurfaceEncoder.java` - 视频编码器主类
- `VideoCodec.java` - 支持的视频编解码器枚举
- `Options.java` - 编码器配置选项
- `CodecOption.java` - 自定义编解码器选项
- `CodecUtils.java` - 编解码器工具类

### 支持的编码格式
| 编码格式 | MIME Type | 标识符 |
|---------|-----------|--------|
| H.264 (AVC) | `video/avc` | 0x68323634 |
| H.265 (HEVC) | `video/hevc` | 0x68323635 |
| AV1 | `video/av1` | 0x00617631 |

---

## 2. MediaFormat 配置参数详解

### 2.1 基础配置参数

| 参数 | KEY 常量 | 类型 | 默认值 | 说明 |
|------|----------|------|--------|------|
| MIME 类型 | `KEY_MIME` | String | - | 视频编码格式（如 `video/avc`） |
| 宽度 | `KEY_WIDTH` | int | 动态 | 视频宽度（像素） |
| 高度 | `KEY_HEIGHT` | int | 动态 | 视频高度（像素） |
| 码率 | `KEY_BIT_RATE` | int | 8000000 | 目标码率（bps） |
| 帧率 | `KEY_FRAME_RATE` | int | 60 | 配置帧率（不控制实际帧率） |

### 2.2 码率控制参数

| 参数 | KEY 常量 | 类型 | 默认值 | 最低 API | 说明 |
|------|----------|------|--------|----------|------|
| 码率模式 | `KEY_BITRATE_MODE` | int | VBR | API 26 | CBR 或 VBR 模式 |
| I 帧间隔 | `KEY_I_FRAME_INTERVAL` | float | 10.0 | - | 关键帧间隔（秒） |
| 重复帧延迟 | `KEY_REPEAT_PREVIOUS_FRAME_AFTER` | long | 100000 | - | 无新帧时重复显示延迟（μs） |

**码率模式详解：**

| 模式 | 常量值 | 特点 | 适用场景 |
|------|--------|------|----------|
| CBR (Constant Bitrate) | `BITRATE_MODE_CBR` | 固定码率，带宽稳定 | 网络传输、实时流 |
| VBR (Variable Bitrate) | `BITRATE_MODE_VBR` | 可变码率，质量优先 | 本地录制、存储 |
| CQ (Constant Quality) | `BITRATE_MODE_CQ` | 恒定质量，不控制码率 | 高质量录制 |

### 2.3 颜色格式参数

| 参数 | KEY 常量 | 类型 | 默认值 | 最低 API | 说明 |
|------|----------|------|--------|----------|------|
| 颜色格式 | `KEY_COLOR_FORMAT` | int | COLOR_FormatSurface | - | Surface 输入格式 |
| 颜色范围 | `KEY_COLOR_RANGE` | int | COLOR_RANGE_LIMITED | API 24 | 颜色范围（Limited/Full） |

### 2.4 低延迟优化参数

| 参数 | KEY 常量 | 类型 | 默认值 | 最低 API | 说明 |
|------|----------|------|--------|----------|------|
| 低延迟模式 | `KEY_LOW_LATENCY` | int | 0 | API 30 | 启用低延迟编码（Android 11+） |
| B 帧数量 | `KEY_MAX_B_FRAMES` | int | 0 | - | 最大 B 帧数量 |
| 最大 FPS | `KEY_MAX_FPS_TO_ENCODER` | float | 0 | 私有/10 | 限制编码器输入帧率 |

---

## 3. scrcpy 扩展配置选项

### 3.1 命令行参数映射

| 命令行参数 | Options 字段 | 说明 |
|-----------|--------------|------|
| `--video-bit-rate` | `videoBitRate` | 视频码率（默认 8Mbps） |
| `--max-fps` | `maxFps` | 最大帧率 |
| `--video-codec` | `videoCodec` | 视频编解码器 |
| `--video-codec-options` | `videoCodecOptions` | 自定义编码器选项 |
| `--video-encoder` | `videoEncoder` | 指定编码器名称 |
| `--bitrate-mode` | `bitrateMode` | CBR/VBR 模式 |
| `--i-frame-interval` | `iFrameInterval` | I 帧间隔 |
| `--low-latency` | `lowLatency` | 启用低延迟模式 |
| `--encoder-priority` | `encoderPriority` | 编码线程优先级 |
| `--encoder-buffer` | `encoderBuffer` | 编码缓冲区配置 |
| `--skip-frames` | `skipFrames` | 跳帧策略 |

### 3.2 编码线程优先级

```java
// encoderPriority 值映射
switch (encoderPriority) {
    case 2:  // URGENT_DISPLAY (-8) - 实时优先级
        priority = android.os.Process.THREAD_PRIORITY_URGENT_DISPLAY;
        break;
    case 1:  // URGENT_AUDIO (-19) - 紧急优先级（默认）
        priority = android.os.Process.THREAD_PRIORITY_URGENT_AUDIO;
        break;
    default: // DEFAULT (0) - 普通优先级
        priority = android.os.Process.THREAD_PRIORITY_DEFAULT;
        break;
}
```

### 3.3 自定义编码器选项格式

格式：`key1:type1=value1,key2:type2=value2,...`

类型支持：
- `int` - 整数（默认）
- `long` - 长整数
- `float` - 浮点数
- `string` - 字符串

示例：
```
--video-codec-options=profile:int=8,level:int=512
```

---

## 4. 硬件平台差异

### 4.1 主要芯片厂商编码器特点

| 厂商 | 编码器名称前缀 | 特点 | 兼容性注意 |
|------|---------------|------|-----------|
| Qualcomm (高通) | `OMX.qcom.video.encoder.` | 性能优秀，功能完整 | 最广泛支持 |
| MediaTek (联发科) | `OMX.MTK.video.encoder.` | 低功耗，APU 加速 | 部分参数不支持 |
| Samsung Exynos | `OMX.Exynos.` | 性能良好 | Profile 设置可能被忽略 |
| HiSilicon (海思) | `OMX.hisi.video.encoder.` | 国产芯片 | 配置差异较大 |
| Android 软编 | `OMX.google.` | 兼容性好，性能差 | 作为后备方案 |

### 4.2 已知平台差异

#### Qualcomm 平台
- 完整支持 KEY_BITRATE_MODE 设置
- 支持所有标准 Profile 和 Level
- KEY_LOW_LATENCY 支持良好
- 支持动态码率调整

#### MediaTek 平台
- 部分设备忽略 KEY_BITRATE_MODE
- Profile 设置可能不生效（始终使用 Baseline）
- 低端设备编码速度较慢
- APU 可用于 AI 增强编码

#### Samsung Exynos 平台
- 功能支持介于高通和联发科之间
- 部分 Android 版本硬编码 Profile
- KEY_MAX_B_FRAMES 支持不稳定

#### 华为设备
- 特殊的 YUV 格式要求
- COLOR_Format 可能需要特殊处理
- 部分设备禁用屏幕录制

### 4.3 版本相关差异

| 参数 | 最低 API | 说明 |
|------|----------|------|
| `KEY_BITRATE_MODE` | API 26 (Android 8.0) | CBR/VBR 模式选择 |
| `KEY_COLOR_RANGE` | API 24 (Android 7.0) | 颜色范围控制 |
| `KEY_LOW_LATENCY` | API 30 (Android 11) | 低延迟模式 |
| `KEY_MAX_FPS_TO_ENCODER` | 私有 API (Android 10+) | 帧率限制 |

---

## 5. 延迟优化策略

### 5.1 编码端延迟组成

```
总延迟 = 采集延迟 + 编码缓冲 + 编码处理 + 网络传输 + 解码延迟 + 渲染延迟
```

**编码相关延迟：**
- **采集延迟**：VirtualDisplay 到 Surface 的延迟（通常 <5ms）
- **编码缓冲延迟**：编码器内部帧缓冲（6-8 帧，约 100-130ms @60fps）
- **编码处理延迟**：硬件编码处理时间（通常 <10ms）

### 5.2 低延迟优化配置

#### 推荐配置（低延迟优先）
```java
format.setInteger(MediaFormat.KEY_BIT_RATE, 4000000);  // 4Mbps
format.setFloat(MediaFormat.KEY_I_FRAME_INTERVAL, 1.0f); // 1秒 I 帧
format.setInteger(MediaFormat.KEY_MAX_B_FRAMES, 0);    // 禁用 B 帧
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
    format.setInteger(MediaFormat.KEY_LOW_LATENCY, 1); // Android 11+
}
```

#### 推荐配置（质量优先）
```java
format.setInteger(MediaFormat.KEY_BIT_RATE, 8000000);  // 8Mbps
format.setFloat(MediaFormat.KEY_I_FRAME_INTERVAL, 10.0f); // 10秒 I 帧
// 使用 VBR 模式获得更好质量
```

### 5.3 参数对延迟的影响

| 参数 | 降低延迟 | 提高质量 | 说明 |
|------|---------|---------|------|
| 码率 | ↓降低 | ↑提高 | 低码率减少传输延迟，但降低质量 |
| I 帧间隔 | ↓降低 | ↑提高 | 短间隔快速恢复，长间隔节省带宽 |
| B 帧 | ↓降低 | ↑提高 | 禁用 B 帧减少缓冲延迟 |
| LOW_LATENCY | ↓降低 | - | 硬件级低延迟优化 |
| CBR 模式 | ↓降低 | - | 稳定码率减少网络抖动 |

---

## 6. 错误处理机制

### 6.1 编码器初始化失败处理

```
初始化流程:
1. 尝试指定编码器 → 失败则尝试默认编码器
2. 配置 MediaFormat → 失败则抛出 ConfigurationException
3. 创建输入 Surface → 失败则重置编码器
```

### 6.2 运行时错误处理

#### 尺寸降级机制
当编码器不支持当前分辨率时，自动降级：
```java
private static final int[] MAX_SIZE_FALLBACK = {2560, 1920, 1600, 1280, 1024, 800};
```

**降级条件：**
1. 仅在首帧发送前触发
2. `downsizeOnError` 选项启用
3. 按顺序尝试更小分辨率

#### 连续错误限制
```java
private static final int MAX_CONSECUTIVE_ERRORS = 3;
```
首帧发送后，连续错误 3 次则终止编码。

### 6.3 编码器停转检测

```java
// 100ms 超时检测
final long DEQUEUE_TIMEOUT_US = 100000;
// 10 秒无输出判定为停转
if (consecutiveTimeouts >= 100) {
    Ln.w("Encoder stall detected: no output for 10 seconds");
}
```

---

## 7. 实际配置示例

### 7.1 标准配置（默认）

```java
MediaFormat format = new MediaFormat();
format.setString(MediaFormat.KEY_MIME, "video/avc");
format.setInteger(MediaFormat.KEY_BIT_RATE, 8000000);
format.setInteger(MediaFormat.KEY_FRAME_RATE, 60);
format.setInteger(MediaFormat.KEY_COLOR_FORMAT,
    MediaCodecInfo.CodecCapabilities.COLOR_FormatSurface);
format.setFloat(MediaFormat.KEY_I_FRAME_INTERVAL, 10.0f);
format.setLong(MediaFormat.KEY_REPEAT_PREVIOUS_FRAME_AFTER, 100000);

// API 26+
format.setInteger(MediaFormat.KEY_BITRATE_MODE,
    MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_VBR);

// API 24+
format.setInteger(MediaFormat.KEY_COLOR_RANGE,
    MediaFormat.COLOR_RANGE_LIMITED);
```

### 7.2 低延迟配置

```java
MediaFormat format = createBaseFormat();

// 低码率 CBR
format.setInteger(MediaFormat.KEY_BIT_RATE, 4000000);
format.setInteger(MediaFormat.KEY_BITRATE_MODE,
    MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_CBR);

// 频繁 I 帧
format.setFloat(MediaFormat.KEY_I_FRAME_INTERVAL, 1.0f);

// 禁用 B 帧
format.setInteger(MediaFormat.KEY_MAX_B_FRAMES, 0);

// Android 11+ 低延迟
if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
    format.setInteger(MediaFormat.KEY_LOW_LATENCY, 1);
}
```

### 7.3 高质量配置

```java
MediaFormat format = createBaseFormat();

// 高码率
format.setInteger(MediaFormat.KEY_BIT_RATE, 16000000);

// VBR 模式
format.setInteger(MediaFormat.KEY_BITRATE_MODE,
    MediaCodecInfo.EncoderCapabilities.BITRATE_MODE_VBR);

// 长时间 I 帧
format.setFloat(MediaFormat.KEY_I_FRAME_INTERVAL, 10.0f);

// H.265 编码（如果支持）
format.setString(MediaFormat.KEY_MIME, "video/hevc");
```

---

## 8. 调试建议

### 8.1 查看可用编码器

```java
MediaCodecList codecList = new MediaCodecList(REGULAR_CODECS);
for (MediaCodecInfo info : codecList.getCodecInfos()) {
    if (info.isEncoder()) {
        Log.d(TAG, "Encoder: " + info.getName());
        for (String type : info.getSupportedTypes()) {
            Log.d(TAG, "  Type: " + type);
        }
    }
}
```

### 8.2 检查编码器能力

```java
MediaCodecInfo.CodecCapabilities caps =
    codecInfo.getCapabilitiesForType("video/avc");

// 检查支持的 Profile
for (int profile : caps.profileLevels) {
    Log.d(TAG, "Profile: " + profile);
}

// 检查码率模式支持
EncoderCapabilities encoderCaps = caps.getEncoderCapabilities();
boolean supportsCBR = encoderCaps.isBitrateModeSupported(
    EncoderCapabilities.BITRATE_MODE_CBR);
```

### 8.3 日志关键点

```java
// SurfaceEncoder.java 关键日志
Ln.i("SurfaceEncoder initialized: videoBitRate=" + videoBitRate +
     ", maxFps=" + maxFps + ", cbrMode=" + cbrMode);

Ln.i("Using CBR mode for bitrate control"); // 或 VBR

Ln.i("Low latency mode enabled (KEY_LOW_LATENCY=1)");

Ln.d("Encoder configured and started, entering encode loop");
```

---

## 9. 参考资料

- [Android MediaCodec API 文档](https://developer.android.com/reference/android/media/MediaCodec)
- [Android MediaFormat 文档](https://developer.android.com/reference/android/media/MediaFormat)
- [Android 视频编码最佳实践](https://developer.android.com/media/optimize/sharing)
- [scrcpy 官方文档](https://github.com/Genymobile/scrcpy)

---

**文档版本**: 1.0
**创建日期**: 2026-02-23
**维护者**: scrcpy-py-ddlx 开发团队
