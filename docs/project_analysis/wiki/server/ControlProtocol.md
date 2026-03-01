# ControlProtocol (服务端)

> **目录**: `control/`
> **文件**: 8 个 Java 文件
> **功能**: 控制消息处理

---

## 文件清单

| 文件 | 职责 |
|------|------|
| `Controller.java` | 控制消息处理器 |
| `ControlMessage.java` | 控制消息定义 |
| `ControlMessageReader.java` | 消息解析 |
| `DeviceMessage.java` | 设备消息定义 |
| `DeviceMessageWriter.java` | 消息序列化 |
| `ControlChannel.java` | 控制通道 |
| `ControlProtocolException.java` | 协议异常 |
| `PointersState.java` | 多点触控状态 |

---

## 控制消息类型

### Client → Server

| 类型 | 值 | 说明 |
|------|-----|------|
| INJECT_KEYCODE | 0 | 按键事件 |
| INJECT_TEXT | 1 | 文字输入 |
| INJECT_TOUCH_EVENT | 2 | 触摸事件 |
| INJECT_SCROLL_EVENT | 3 | 滚动事件 |
| BACK_OR_SCREEN_ON | 4 | 返回/唤醒 |
| EXPAND_NOTIFICATION_PANEL | 5 | 展开通知 |
| COLLAPSE_PANELS | 7 | 收起面板 |
| GET_CLIPBOARD | 8 | 获取剪贴板 |
| SET_CLIPBOARD | 9 | 设置剪贴板 |
| ROTATE_DEVICE | 11 | 旋转设备 |
| UHID_CREATE | 12 | 创建 HID 设备 |
| UHID_INPUT | 13 | HID 输入 |
| UHID_DESTROY | 14 | 销毁 HID |
| RESET_VIDEO | 17 | PLI 请求 |
| SCREENSHOT | 18 | 截图 |
| PING | 25 | 心跳请求 |

### Server → Client

| 类型 | 值 | 说明 |
|------|-----|------|
| CLIPBOARD | 0 | 剪贴板内容 |
| ACK_CLIPBOARD | 1 | 剪贴板确认 |
| UHID_OUTPUT | 2 | HID 输出 |
| APP_LIST | 3 | 应用列表 |
| SCREENSHOT | 4 | 截图数据 |
| PONG | 5 | 心跳响应 |
| FILE_CHANNEL_INFO | 6 | 文件通道信息 |

---

## ControlMessageReader

解析客户端发送的控制消息。

```java
public class ControlMessageReader {
    public ControlMessage parse(byte[] buffer) {
        ByteBuffer bb = ByteBuffer.wrap(buffer);
        int type = bb.get() & 0xFF;

        switch (type) {
            case ControlMessage.TYPE_INJECT_KEYCODE:
                return parseInjectKeycode(bb);
            case ControlMessage.TYPE_INJECT_TOUCH_EVENT:
                return parseInjectTouchEvent(bb);
            case ControlMessage.TYPE_SET_CLIPBOARD:
                return parseSetClipboard(bb);
            // ...
        }
    }
}
```

---

## Controller

处理控制消息并注入系统。

```java
public class Controller {
    public void control(ControlMessage msg) {
        switch (msg.getType()) {
            case TYPE_INJECT_KEYCODE:
                injectKeycode(msg);
                break;
            case TYPE_INJECT_TOUCH_EVENT:
                injectTouch(msg);
                break;
            case TYPE_SET_CLIPBOARD:
                setClipboard(msg);
                break;
            // ...
        }
    }
}
```

---

## 消息格式

### 按键事件

```
[type: 1B][action: 1B][keycode: 4B][metastate: 4B]

action: 0=DOWN, 1=UP
keycode: Android KeyEvent.KEYCODE_*
metastate: 修饰键状态
```

### 触摸事件

```
[type: 1B][action: 1B][pointer_id: 8B][position: 8B]
       [pressure: 4B][buttons: 4B]

action: 0=DOWN, 1=UP, 2=MOVE
pointer_id: 触点 ID
position: (x: 4B, y: 4B)
pressure: 0.0-1.0 (乘以 65536)
```

### 剪贴板

```
[type: 1B][sequence: 4B][length: 4B][text: NB]
```

---

## PointersState

多点触控状态管理。

```java
public class PointersState {
    private final Pointer[] pointers;

    // 获取触点
    public Pointer get(int index);

    // 查找触点
    public int indexOf(long pointerId);

    // 添加触点
    public int add(long pointerId);
}
```

---

## 相关文档

- [control.md](../client/control.md) - 客户端控制
- [device_msg.md](../client/device_msg.md) - 设备消息
- [tcp_messages.md](../protocol/tcp_messages.md) - TCP 消息格式
