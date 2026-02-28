# ScreenshotCapture

> **文件**: `video/ScreenshotCapture.java`
> **定位**: 截图专用组件，用于 video=false 模式

---

## 概述

ScreenshotCapture 是一个独立的截图组件，在 `video=false` 模式下创建 VirtualDisplay 用于截图。

**核心特点**：
- 不依赖编码器（MediaCodec）
- 直接从 VirtualDisplay 获取帧
- 延迟低（~70-120ms）

---

## 架构

```
ScreenshotCapture
│
├── ImageReader          # 接收帧数据
│   └── Surface          # VirtualDisplay 的输出目标
│
├── VirtualDisplay       # 屏幕镜像（SurfaceControl API）
│   ├── createDisplay()  # 创建虚拟显示
│   └── setDisplaySurface() # 设置输出 Surface
│
└── 帧处理
    ├── onImageAvailable() # 帧到达回调
    └── imageToBitmap()    # 转换为 Bitmap
```

---

## 初始化流程

```java
public void init() throws ConfigurationException {
    // 1. 创建 ImageReader
    imageReader = ImageReader.newInstance(width, height, RGBA_8888, 2);

    // 2. 设置帧回调
    imageReader.setOnImageAvailableListener(listener, handler);

    // 3. 创建 VirtualDisplay (使用 SurfaceControl API)
    display = SurfaceControl.createDisplay("scrcpy_screenshot", false);

    // 4. 配置 VirtualDisplay (必须在 Transaction 中)
    SurfaceControl.openTransaction();
    try {
        SurfaceControl.setDisplaySurface(display, surface);
        SurfaceControl.setDisplayLayerStack(display, layerStack);
        SurfaceControl.setDisplayProjection(display, 0, deviceRect, displayRect);
    } finally {
        SurfaceControl.closeTransaction();
    }
}
```

---

## 关键技术点

### 1. SurfaceControl API 选择

| API | 权限要求 | 可用性 |
|-----|---------|--------|
| 公开 API + AUTO_MIRROR | 需要 CAPTURE_VIDEO_OUTPUT | ❌ shell 无权限 |
| 隐藏 API createVirtualDisplay() | 无额外权限 | ❌ 某些版本不存在 |
| **SurfaceControl API** | 无额外权限 | ✅ 可用 |

### 2. Transaction 必须性

所有 SurfaceControl 操作**必须**在 Transaction 中调用：

```java
// ❌ 错误：不在 Transaction 中
SurfaceControl.setDisplaySurface(display, surface);

// ✅ 正确：在 Transaction 中
SurfaceControl.openTransaction();
try {
    SurfaceControl.setDisplaySurface(display, surface);
} finally {
    SurfaceControl.closeTransaction();
}
```

否则会抛出 `NullPointerException`。

---

## 截图流程

```java
public Bitmap captureScreenshot(long timeoutMs) {
    // 1. 等待帧
    frameLock.lock();
    try {
        while (!frameReady && pendingFrame == null) {
            frameCondition.await(timeoutMs, TimeUnit.MILLISECONDS);
        }

        // 2. 转换为 Bitmap
        Bitmap bitmap = imageToBitmap(pendingFrame, width, height);
        return bitmap;

    } finally {
        frameLock.unlock();
    }
}
```

---

## 与其他组件的关系

```
Server.java
    │
    ├── video=true
    │   └── SurfaceEncoder (编码器)
    │
    └── video=false + 网络模式
        └── ScreenshotCapture (截图组件)
            │
            └── Controller.takeScreenshot()
                └── captureScreenshot() → Bitmap → JPEG
```

---

## 性能指标

| 指标 | 值 |
|------|---|
| 初始化时间 | ~50-100ms |
| 截图延迟 | ~70-120ms |
| 内存占用 | ~10-20MB |
| 截图大小 | 80KB-330KB (取决于分辨率) |

---

## 与编码器截图对比

| 方案 | 流程 | 延迟 | 复杂度 |
|------|------|------|--------|
| 编码器 | VirtualDisplay → MediaCodec → H.264 → 解码 | ~200-500ms | 高 |
| **ScreenshotCapture** | VirtualDisplay → ImageReader → JPEG | ~70-120ms | 低 |

---

## 使用场景

- `--push` 模式（video=false + 网络模式）
- 需要截图但不需要视频流
- 低延迟截图需求

---

## 相关文档

- [Controller.md](Controller.md) - 控制消息处理
- [Server.md](Server.md) - 服务入口
- [SurfaceControl 截图限制](../../../development/known_issues/surfacecontrol_screenshot_limitation.md)

---

*此文档记录 ScreenshotCapture 组件的实现细节*
