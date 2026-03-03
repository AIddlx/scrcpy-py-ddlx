# Controller - 控制器

> **路径**: `scrcpy/server/src/main/java/com/genymobile/scrcpy/control/Controller.java`
> **职责**: 控制消息处理和事件注入

---

## 类定义

### Controller

**职责**: 接收客户端控制消息并执行相应操作

**实现**: AsyncProcessor, VirtualDisplayListener

**线程**: 独立控制线程 "control-recv"

---

## 内部类

### DisplayData

| 字段 | 类型 | 说明 |
|------|------|------|
| `virtualDisplayId` | int | 虚拟显示 ID |
| `positionMapper` | PositionMapper | 位置映射器 |

---

## 常量

| 常量 | 值 | 说明 |
|------|-----|------|
| `POINTER_ID_MOUSE` | -1 | 鼠标指针 ID |
| `DEFAULT_DEVICE_ID` | 0 | 默认设备 ID |

---

## 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `displayId` | int | 显示 ID |
| `controlChannel` | ControlChannel | 控制通道 |
| `sender` | DeviceMessageSender | 消息发送器 |
| `clipboardAutosync` | boolean | 剪贴板自动同步 |
| `powerOn` | boolean | 开机唤醒 |
| `surfaceCapture` | SurfaceCapture | 屏幕捕获 |
| `captureReset` | CaptureReset | 捕获重置 |
| `surfaceEncoder` | SurfaceEncoder | 视频编码器 |
| `audioEncoder` | AudioEncoder | 音频编码器 |
| `fileServer` | FileServer | 文件服务器 |
| `uhidManager` | UhidManager | UHID 管理器 |

---

## 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `start` | TerminationListener | void | 启动控制器 |
| `stop` | - | void | 停止控制器 |
| `join` | - | void | 等待线程结束 |
| `setSurfaceCapture` | SurfaceCapture | void | 设置屏幕捕获 |
| `setSurfaceEncoder` | SurfaceEncoder | void | 设置视频编码器 |
| `setAudioEncoder` | AudioEncoder | void | 设置音频编码器 |

---

## 控制消息类型处理

```java
boolean handleEvent() {
    ControlMessage msg = controlChannel.recv();

    switch (msg.getType()) {
        case TYPE_INJECT_KEYCODE:
            injectKeycode(msg.getAction(), msg.getKeycode(), ...);
            break;

        case TYPE_INJECT_TEXT:
            injectText(msg.getText());
            break;

        case TYPE_INJECT_TOUCH_EVENT:
            injectTouch(msg.getAction(), msg.getPointerId(), ...);
            break;

        case TYPE_INJECT_SCROLL_EVENT:
            injectScroll(msg.getPosition(), msg.getHScroll(), ...);
            break;

        case TYPE_SET_CLIPBOARD:
            setClipboard(msg.getText(), msg.getPaste(), ...);
            break;

        case TYPE_START_APP:
            startAppAsync(msg.getText());
            break;

        case TYPE_RESET_VIDEO:
            resetVideo();
            break;

        case TYPE_GET_APP_LIST:
            getAppListAsync();
            break;

        case TYPE_SCREENSHOT:
            takeScreenshotAsync();
            break;

        case TYPE_PING:
            handlePing(msg.getTimestamp());
            break;

        case TYPE_OPEN_FILE_CHANNEL:
            openFileChannel();
            break;

        // ... 更多消息类型
    }
}
```

---

## 触摸事件注入

```java
boolean injectTouch(int action, long pointerId, Position position,
                    float pressure, int actionButton, int buttons) {
    // 1. 获取事件坐标和显示 ID
    Pair<Point, Integer> pair = getEventPointAndDisplayId(position);

    // 2. 更新指针状态
    int pointerIndex = pointersState.getPointerIndex(pointerId);
    Pointer pointer = pointersState.get(pointerIndex);
    pointer.setPoint(point);
    pointer.setPressure(pressure);

    // 3. 确定输入源类型
    int source;
    if (pointerId == POINTER_ID_MOUSE && isMouseEvent) {
        source = InputDevice.SOURCE_MOUSE;
    } else {
        source = InputDevice.SOURCE_TOUCHSCREEN;
    }

    // 4. 构建 MotionEvent
    MotionEvent event = MotionEvent.obtain(...);
    return Device.injectEvent(event, targetDisplayId, INJECT_MODE_ASYNC);
}
```

---

## 滚动事件注入

```java
boolean injectScroll(Position position, float hScroll, float vScroll, int buttons) {
    Point point = getEventPointAndDisplayId(position).first;

    MotionEvent.PointerCoords coords = pointerCoords[0];
    coords.x = point.getX();
    coords.y = point.getY();
    coords.setAxisValue(MotionEvent.AXIS_HSCROLL, hScroll);
    coords.setAxisValue(MotionEvent.AXIS_VSCROLL, vScroll);

    MotionEvent event = MotionEvent.obtain(..., MotionEvent.ACTION_SCROLL, ...);
    return Device.injectEvent(event, targetDisplayId, INJECT_MODE_ASYNC);
}
```

---

## 剪贴板处理

### 获取剪贴板

```java
void getClipboard(int copyKey) {
    // 按下 COPY/CUT 键 (Android >= 7)
    if (copyKey != COPY_KEY_NONE) {
        int key = (copyKey == COPY_KEY_COPY) ? KEYCODE_COPY : KEYCODE_CUT;
        pressReleaseKeycode(key, INJECT_MODE_WAIT_FOR_FINISH);
    }

    // 发送剪贴板内容
    if (!clipboardAutosync) {
        String text = Device.getClipboardText();
        sender.send(DeviceMessage.createClipboard(text));
    }
}
```

### 设置剪贴板

```java
boolean setClipboard(String text, boolean paste, long sequence) {
    isSettingClipboard.set(true);
    boolean ok = Device.setClipboardText(text);
    isSettingClipboard.set(false);

    // 按下 PASTE 键
    if (paste) {
        pressReleaseKeycode(KEYCODE_PASTE, INJECT_MODE_ASYNC);
    }

    // 发送确认
    if (sequence != SEQUENCE_INVALID) {
        sender.send(DeviceMessage.createAckClipboard(sequence));
    }

    return ok;
}
```

---

## 媒体流控制

### 启动/停止视频

```java
void startVideo() {
    if (surfaceEncoder != null) {
        surfaceEncoder.setStandby(false);
    }
}

void stopVideo() {
    if (surfaceEncoder != null) {
        surfaceEncoder.setStandby(true);
    }
}
```

### 启动/停止音频

```java
void startAudio() {
    if (audioEncoder != null) {
        audioEncoder.setStandby(false);
    }
}

void stopAudio() {
    if (audioEncoder != null) {
        audioEncoder.setStandby(true);
    }
}
```

---

## 心跳处理

```java
void handlePing(long timestamp) {
    // 立即回复 PONG，回显时间戳
    DeviceMessage pong = DeviceMessage.createPong(timestamp);
    sender.send(pong);
    Ln.d("Heartbeat: PING received, PONG sent (timestamp=" + timestamp + ")");
}
```

---

## 截图功能

```java
void takeScreenshot() {
    // 1. 获取显示信息
    DisplayInfo displayInfo = ServiceManager.getDisplayManager().getDisplayInfo(displayId);
    int width = displayInfo.getSize().getWidth();
    int height = displayInfo.getSize().getHeight();

    // 2. 使用 SurfaceControl 截图
    Bitmap bitmap = SurfaceControl.screenshot(width, height);

    // 3. 压缩为 JPEG
    ByteArrayOutputStream baos = new ByteArrayOutputStream();
    bitmap.compress(Bitmap.CompressFormat.JPEG, 85, baos);
    bitmap.recycle();

    // 4. 发送给客户端
    DeviceMessage msg = DeviceMessage.createScreenshot(baos.toByteArray());
    sender.send(msg);
}
```

---

## 应用列表

```java
void getAppList() {
    List<DeviceApp> apps = Device.listApps();
    DeviceMessage msg = DeviceMessage.createAppList(apps);
    sender.send(msg);
}
```

---

## 文件通道

```java
void openFileChannel() {
    if (fileServer == null) {
        fileServer = new FileServer();
    }
    int port = fileServer.start();
    int sessionId = fileServer.getSessionId();

    DeviceMessage msg = DeviceMessage.createFileChannelInfo(port, sessionId);
    sender.send(msg);
}
```

---

## 剪贴板自动同步

```java
// 监听剪贴板变化
ClipboardManager clipboardManager = ServiceManager.getClipboardManager();
clipboardManager.addPrimaryClipChangedListener(() -> {
    if (isSettingClipboard.get()) {
        return;  // 忽略自己设置的
    }
    String text = Device.getClipboardText();
    if (text != null) {
        sender.send(DeviceMessage.createClipboard(text));
    }
});
```

---

## 显示 ID 处理

```java
int getActionDisplayId() {
    if (displayId != Device.DISPLAY_ID_NONE) {
        return displayId;  // 真实屏幕
    }

    // 虚拟显示 (--new-display)
    DisplayData data = displayData.get();
    return (data != null) ? data.virtualDisplayId : 0;
}
```

---

## 依赖关系

```
Controller
    │
    ├──→ ControlChannel (接收消息)
    │
    ├──→ DeviceMessageSender (发送响应)
    │
    ├──→ Device (事件注入)
    │
    ├──→ SurfaceEncoder (视频控制)
    │
    ├──→ AudioEncoder (音频控制)
    │
    ├──→ FileServer (文件传输)
    │
    └──→ UhidManager (UHID 设备)
```

**被依赖**:
- Server.java (创建和管理)

---

*此文档基于代码分析生成*
