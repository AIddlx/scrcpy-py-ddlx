# VideoPipeline (服务端)

> **目录**: `video/`
> **文件**: 14 个 Java 文件
> **功能**: 视频捕获和编码

---

## 文件清单

| 文件 | 职责 |
|------|------|
| `SurfaceEncoder.java` | MediaCodec 硬件编码 |
| `ScreenCapture.java` | 屏幕捕获 (VirtualDisplay) |
| `SurfaceCapture.java` | 捕获基类 |
| `VideoCodec.java` | 编解码器定义 (H.264/H.265/AV1) |
| `VideoSource.java` | 视频源管理 |
| `VideoFilter.java` | 视频滤镜 (OpenGL) |
| `ScreenshotCapture.java` | 截图组件 (video=false) |
| `CameraCapture.java` | 摄像头捕获 |
| `NewDisplayCapture.java` | 虚拟显示器捕获 |
| `DisplaySizeMonitor.java` | 分辨率监控 |
| `CaptureReset.java` | 捕获重置处理 |
| `VirtualDisplayListener.java` | 虚拟显示监听器 |
| `CameraAspectRatio.java` | 摄像头宽高比 |
| `CameraFacing.java` | 摄像头朝向 |

---

## 核心流程

```
┌─────────────────┐
│  ScreenCapture  │  屏幕捕获
│  (VirtualDisplay)│
└────────┬────────┘
         │ Surface
         ▼
┌─────────────────┐
│ SurfaceEncoder  │  MediaCodec 编码
│ (H.264/H.265)   │
└────────┬────────┘
         │ ByteBuffer
         ▼
┌─────────────────┐
│    Streamer     │  分发
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
 TCP      UDP Sender
(USB)    (Network)
```

---

## SurfaceEncoder

### 核心参数

| 参数 | 说明 |
|------|------|
| `video_codec` | h264/h265/av1 |
| `video_bit_rate` | 码率 (bps) |
| `max_fps` | 最大帧率 |
| `i_frame_interval` | 关键帧间隔 (秒) |
| `bitrate_mode` | CBR/VBR |
| `low_latency` | 低延迟模式 |

### 编码流程

```java
// 1. 创建 MediaCodec
MediaCodec encoder = MediaCodec.createEncoderByType(mimeType);

// 2. 配置
encoder.configure(format, null, null, CONFIGURE_FLAG_ENCODE);

// 3. 设置 Surface
Surface surface = encoder.createInputSurface();
virtualDisplay.setSurface(surface);

// 4. 循环编码
while (running) {
    int index = encoder.dequeueOutputBuffer(bufferInfo, timeout);
    if (index >= 0) {
        ByteBuffer buffer = encoder.getOutputBuffer(index);
        sendFrame(buffer, bufferInfo);
        encoder.releaseOutputBuffer(index, false);
    }
}
```

---

## VideoCodec

```java
public enum VideoCodec {
    H264("h264", "video/avc"),
    H265("h265", "video/hevc"),
    AV1("av1", "video/av01");

    public final String name;
    public final String mimeType;
}
```

---

## ScreenCapture

### VirtualDisplay 创建

```java
VirtualDisplay display = mediaProjection.createVirtualDisplay(
    "scrcpy",
    width, height, dpi,
    DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
    surface, null, null
);
```

---

## ScreenshotCapture

video=false 模式的截图方案。

### 方案对比

| 方案 | 延迟 | 可靠性 |
|------|------|--------|
| 编码器方案 | 200-500ms | ✅ |
| ImageReader | 70-120ms | ✅ |

详见 [ScreenshotCapture.md](ScreenshotCapture.md)。

---

## 相关文档

- [UdpMediaSender.md](UdpMediaSender.md) - UDP 发送
- [Streamer.md](Streamer.md) - 流分发
- [video_decoder.md](../client/video_decoder.md) - 客户端解码
