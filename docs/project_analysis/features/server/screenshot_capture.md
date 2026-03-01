# ScreenshotCapture

> **文件**: `video/ScreenshotCapture.java`
> **功能**: video=false 模式截图组件

---

## 概述

`ScreenshotCapture` 提供在禁用视频流时的截图功能，使用 SurfaceControl API 直接捕获屏幕。

---

## 使用场景

当客户端只需要截图而不需要实时视频时，可以使用 `video=false` 模式：

```bash
# 服务端启动参数
video=false screenshot=true
```

---

## 技术方案

### 方案对比

| 方案 | 延迟 | 可靠性 | 说明 |
|------|------|--------|------|
| SurfaceControl.screenshot() | ~50ms | ❌ 权限问题 | 直接调用受限 |
| 编码器方案 | ~200-500ms | ✅ 可靠 | 需要完整编码 |
| **ScreenshotCapture** | ~70-120ms | ✅ 可靠 | ImageReader 方案 |

### 实现原理

```
SurfaceControl.createDisplay()
       │
       ▼
VirtualDisplay
       │
       ▼
ImageReader.acquireLatestImage()
       │
       ▼
RGB/RGBA Bitmap
       │
       ▼
PNG/JPEG 编码
```

---

## 核心方法

```java
public class ScreenshotCapture {
    // 初始化
    public void start(int width, int height);

    // 截图
    public byte[] capture();

    // 释放资源
    public void stop();
}
```

---

## 关键技术点

### 1. SurfaceControl Transaction

```java
// 必须在 Transaction 中操作
SurfaceControl.Transaction t = new SurfaceControl.Transaction();
t.setBufferSize(surface, width, height);
t.apply();
```

### 2. ImageReader 回调

```java
imageReader.setOnImageAvailableListener(reader -> {
    Image image = reader.acquireLatestImage();
    // 处理图像
}, handler);
```

---

## 与 Controller 集成

```java
// Controller.java
private ScreenshotCapture screenshotCapture;

public void takeScreenshot() {
    if (screenshotCapture != null) {
        byte[] data = screenshotCapture.capture();
        sendScreenshot(data);
    }
}
```

---

## 延迟优化

| 操作 | 耗时 |
|------|------|
| ImageReader.acquireLatestImage() | ~20-40ms |
| YUV → RGB 转换 | ~20-40ms |
| PNG 编码 | ~30-40ms |
| **总计** | **~70-120ms** |

---

## 相关文档

- [Controller.md](../server/Controller.md) - 控制处理
- [screenshot](../mcp/tools.md) - 截图 MCP 工具
