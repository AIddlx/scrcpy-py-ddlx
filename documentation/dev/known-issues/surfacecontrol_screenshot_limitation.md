# SurfaceControl 截图限制与解决方案

## 状态: ✅ 已解决

## 问题描述

在 `--push` 模式（`video=false` + 网络模式）下，使用 TCP SCREENSHOT 控制消息截图时：

1. **第一次截图成功**（某些设备）
2. **后续截图失败**，返回空数据

## 错误日志

```
SurfaceFlinger: FB is protected: PERMISSION_DENIED
SurfaceFlinger: captureScreen failed to readInt32: -1
SurfaceControl: Failed to take screenshot
```

## 根本原因

1. **权限限制**：`SurfaceControl.screenshot()` 需要系统权限
   - `android:sharedUserId="android.uid.system"` + platform 签名
   - 或 `android.permission.READ_FRAME_BUFFER` 权限

2. **scrcpy 运行身份**：服务器以 **shell 用户**运行，没有系统权限

3. **帧缓冲区保护**：某些设备/情况下，帧缓冲区被标记为"受保护"状态
   - 第一次截图可能成功
   - 后续截图被拒绝（`FB is protected`）

---

## 尝试过的方案

### 方案 1: SurfaceControl.screenshot() ❌

```java
Bitmap bitmap = SurfaceControl.screenshot(width, height);
```

**结果**：权限不足，"FB is protected"

### 方案 2: ImageReader + 公开 VirtualDisplay API ❌

```java
// 使用公开 API
DisplayManager.createVirtualDisplay(name, width, height, dpi, surface,
    VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR);
```

**结果**：
```
Requires CAPTURE_VIDEO_OUTPUT or CAPTURE_SECURE_VIDEO_OUTPUT permission
```

### 方案 3: DisplayManager 隐藏 API ❌

```java
// 反射调用隐藏 API
DisplayManager.createVirtualDisplay(name, width, height, displayId, surface);
```

**结果**：
```
NoSuchMethodException: android.hardware.display.DisplayManager.createVirtualDisplay
[class java.lang.String, int, int, int, class android.view.Surface]
```

隐藏 API 在某些 Android 版本上不存在。

---

## 最终解决方案: ScreenshotCapture ✅

### 设计思路

在 `video=false` 时也创建 VirtualDisplay，但**不经过编码器**：

```
VirtualDisplay → ImageReader → Bitmap → JPEG → 客户端
```

### 关键技术点

1. **使用 SurfaceControl API 创建 VirtualDisplay**（与 ScreenCapture 相同）

2. **必须在 Transaction 中调用**：
```java
SurfaceControl.openTransaction();
try {
    SurfaceControl.setDisplaySurface(display, surface);
    SurfaceControl.setDisplayLayerStack(display, layerStack);
    SurfaceControl.setDisplayProjection(display, 0, deviceRect, displayRect);
} finally {
    SurfaceControl.closeTransaction();
}
```

3. **使用 ImageReader 接收帧**：
```java
ImageReader imageReader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 2);
// VirtualDisplay 输出到 imageReader.getSurface()
```

### 实现文件

| 文件 | 说明 |
|------|------|
| `ScreenshotCapture.java` | 独立的截图组件，使用 VirtualDisplay + ImageReader |
| `Server.java` | 在 `video=false` 时也创建 ScreenshotCapture |
| `Controller.java` | 优先使用 ScreenshotCapture 截图 |

### 架构

```
video=false + 网络模式启动:
│
├── Server.java 检测 video=false
│   └── 创建 ScreenshotCapture
│       ├── ImageReader (接收帧)
│       └── VirtualDisplay (SurfaceControl API)
│
截图请求:
│
├── Controller.takeScreenshot()
│   └── ScreenshotCapture.captureScreenshot()
│       ├── 从 ImageReader 获取帧
│       └── 转换为 Bitmap
├── Bitmap → JPEG (动态质量压缩)
└── 通过 DeviceMessage 返回客户端
```

### 性能

| 指标 | 值 |
|------|---|
| 延迟 | ~70-120ms |
| 内存占用 | ~10-20MB (ImageReader buffer) |
| 截图大小 | 80KB-330KB (取决于分辨率和质量) |

---

## 经验教训

### 1. VirtualDisplay API 选择

| API | 权限要求 | 可用性 |
|-----|---------|--------|
| 公开 API + AUTO_MIRROR | 需要 CAPTURE_VIDEO_OUTPUT | ❌ shell 用户无权限 |
| 隐藏 API createVirtualDisplay() | 无额外权限 | ❌ 某些版本不存在 |
| SurfaceControl API | 无额外权限 | ✅ 可用 |

### 2. SurfaceControl Transaction

所有 SurfaceControl 操作（setDisplaySurface, setDisplayLayerStack, setDisplayProjection）**必须**在 `openTransaction()` 和 `closeTransaction()` 之间调用，否则会抛出 NullPointerException。

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

### 3. 与编码器方案对比

| 方案 | 流程 | 延迟 | 复杂度 |
|------|------|------|--------|
| 编码器 | VirtualDisplay → MediaCodec → H.264 → 网络 → 解码 | ~200-500ms | 高 |
| **ScreenshotCapture** | VirtualDisplay → ImageReader → JPEG | ~70-120ms | 低 |

ScreenshotCapture 不需要编码器、不需要客户端解码，直接在服务端获取 Bitmap 并压缩为 JPEG。

---

## 代码审查与改进建议

> **审查日期**: 2026-02-28
> **审查范围**: ScreenshotCapture.java, Server.java, Controller.java

---

### 1. 资源泄漏问题 🔴 高风险

**问题描述**：

`ScreenshotCapture` 创建后未被加入 `asyncProcessors` 管理列表，导致在会话结束时资源不会被显式释放。

**代码位置**：`Server.java` 第 382-396 行

```java
} else if (networkMode && control) {
    try {
        ScreenshotCapture screenshotCapture = new ScreenshotCapture(options);
        screenshotCapture.init();
        // ⚠️ screenshotCapture 未被加入 asyncProcessors 列表！
        if (controller != null) {
            controller.setScreenshotCapture(screenshotCapture);
        }
    } catch (Exception e) {
        Ln.e("Failed to initialize ScreenshotCapture: " + e.getMessage());
    }
}
```

**后果**：

- VirtualDisplay 泄漏 → 占用系统资源
- ImageReader 泄漏 → 持续占用 10-20MB 内存
- 可能导致后续连接失败

**修复建议**：

方案 A：在 Controller 中添加显式释放

```java
// Controller.java
public void release() {
    if (screenshotCapture != null) {
        screenshotCapture.release();
        screenshotCapture = null;
    }
}
```

方案 B：让 ScreenshotCapture 实现 AsyncProcessor 接口

```java
public class ScreenshotCapture implements AsyncProcessor {
    @Override
    public void start(TerminationListener listener) { /* 初始化逻辑 */ }
    
    @Override
    public void stop() { release(); }
    
    @Override
    public void join() { /* 无需等待 */ }
}

// Server.java
asyncProcessors.add(screenshotCapture);
```

---

### 2. Image 资源未关闭 🟡 中风险

**问题描述**：

`captureScreenshot()` 中获取的 `Image` 对象在转换为 Bitmap 后未被关闭。虽然 `onImageAvailable` 回调会在下一帧到达时关闭旧帧，但如果长时间没有新帧或会话结束，最后一个 Image 对象会泄漏。

**代码位置**：`ScreenshotCapture.java` 第 134-167 行

**修复建议**：

```java
public Bitmap captureScreenshot(long timeoutMs) {
    frameLock.lock();
    try {
        // ... 等待帧 ...
        
        if (pendingFrame == null) {
            return null;
        }
        
        Bitmap bitmap = imageToBitmap(pendingFrame, videoSize.getWidth(), videoSize.getHeight());
        
        // ✅ 关闭已使用的 Image
        pendingFrame.close();
        pendingFrame = null;
        frameReady = false;
        
        return bitmap;
    } finally {
        frameLock.unlock();
    }
}
```

---

### 3. 并发逻辑可简化 🟢 低风险

**问题描述**：

`frameReady` 和 `pendingFrame` 是两个独立变量，虽然当前实现正确，但逻辑复杂，维护困难。

**当前实现**：

```java
// 等待条件
while (!frameReady && pendingFrame == null) { ... }

// 回调设置
pendingFrame = reader.acquireLatestImage();
frameReady = true;
```

**建议简化**：仅使用 `pendingFrame` 作为条件

```java
// 等待条件
while (pendingFrame == null) { ... }

// 回调设置（先关闭旧帧）
if (pendingFrame != null) {
    pendingFrame.close();
}
pendingFrame = reader.acquireLatestImage();
frameCondition.signalAll();
```

这样 `frameReady` 标志可以移除，逻辑更清晰。

---

### 4. 延迟初始化考虑 💡 优化建议

**当前行为**：`ScreenshotCapture` 在服务启动时立即创建。

**潜在优化**：按需延迟初始化

```java
// Controller.java
private void takeScreenshot(int quality) {
    // 延迟初始化
    if (screenshotCapture == null && needScreenshotCapture) {
        screenshotCapture = new ScreenshotCapture(options);
        screenshotCapture.init();
    }
    // ... 现有逻辑
}
```

**优点**：

- 无截图请求时不占用资源
- 减少启动时间

**缺点**：

- 第一次截图有初始化延迟 (~100ms)

---

### 总结

| 问题 | 风险等级 | 状态 | 建议
|------|---------|------|------
| 资源泄漏 | 🔴 高 | ✅ 已修复 | Controller.stop() 中释放
| Image 未关闭 | 🟡 中 | ✅ 已修复 | captureScreenshot() 后关闭
| 并发逻辑复杂 | 🟢 低 | 可选 | 简化条件判断
| 延迟初始化 | 💡 优化 | 可选 | 按需创建

---

## 日期

- 2026-02-27: 问题确认，尝试多种方案
- 2026-02-28: 实现 ScreenshotCapture 方案，问题解决
- 2026-02-28: 代码审查，发现潜在资源泄漏问题
