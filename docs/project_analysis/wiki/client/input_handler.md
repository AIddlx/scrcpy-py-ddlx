# InputHandler - 输入处理器

> **路径**: `scrcpy_py_ddlx/core/player/video/input_handler.py`
> **职责**: 鼠标和键盘事件处理

---

## 类定义

### InputHandler

**职责**: 视频组件输入处理基类

**设计参考**: 官方 scrcpy `input_manager.c` 和 `mouse_sdk.c`

---

## 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `_mouse_buttons_state` | int | 鼠标按钮状态位掩码 |
| `_last_position` | Tuple[int, int] | 最后位置 |
| `_device_size` | Tuple[int, int] | 设备屏幕尺寸 |
| `_control_queue` | ControlMessageQueue | 控制消息队列 |
| `_mouse_hover` | bool | 是否发送 hover 事件 |

---

## 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `set_control_queue` | queue | - | 设置控制队列 |
| `set_device_size` | width, height | - | 设置设备尺寸 |
| `_send_touch_event` | action, pointer_id, ... | - | 发送触摸事件 |
| `_send_scroll_event` | x, y, hscroll, vscroll | - | 发送滚动事件 |
| `_send_keycode_event` | keycode, action, repeat | - | 发送按键事件 |

---

## Qt 到 Android 按钮映射

```python
def _qt_button_to_android(qt_button):
    mapping = {
        Qt.LeftButton:   AndroidMotionEventButtons.PRIMARY,    # 0x01
        Qt.RightButton:  AndroidMotionEventButtons.SECONDARY,  # 0x02
        Qt.MiddleButton: AndroidMotionEventButtons.TERTIARY,   # 0x04
        Qt.BackButton:   AndroidMotionEventButtons.BACK,       # 0x08
        Qt.ForwardButton:AndroidMotionEventButtons.FORWARD,    # 0x10
    }
    return mapping.get(qt_button, 0)
```

---

## 鼠标状态管理

```python
def _update_mouse_button_state(button, pressed):
    android_button = _qt_button_to_android(button)
    if pressed:
        _mouse_buttons_state |= android_button   # 设置位
    else:
        _mouse_buttons_state &= ~android_button  # 清除位
```

---

## 触摸事件发送

```python
def _send_touch_event(action, pointer_id, position_x, position_y,
                      pressure=1.0, action_button=0):
    msg = ControlMessage(ControlMessageType.INJECT_TOUCH_EVENT)
    msg.set_touch_event(
        action=action,
        pointer_id=pointer_id,
        position_x=position_x,
        position_y=position_y,
        screen_width=_device_size[0],
        screen_height=_device_size[1],
        pressure=pressure,
        action_button=action_button,
        buttons=_mouse_buttons_state,
    )
    _control_queue.put(msg)
```

---

## 滚动事件发送

```python
def _send_scroll_event(position_x, position_y, hscroll, vscroll):
    msg = ControlMessage(ControlMessageType.INJECT_SCROLL_EVENT)
    msg.set_scroll_event(
        position_x=position_x,
        position_y=position_y,
        screen_width=_device_size[0],
        screen_height=_device_size[1],
        hscroll=hscroll,  # -1.0 到 1.0
        vscroll=vscroll,  # -1.0 到 1.0
        buttons=_mouse_buttons_state,
    )
    _control_queue.put(msg)
```

---

## 按键事件发送

```python
def _send_keycode_event(keycode, action, repeat=0):
    msg = ControlMessage(ControlMessageType.INJECT_KEYCODE)
    msg.set_keycode(action, keycode, repeat, metastate=0)
    _control_queue.put(msg)
```

---

## CoordinateMapper 类

**职责**: 窗口坐标到设备坐标映射

---

## CoordinateMapper 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `_frame_width` | int | 帧宽度 |
| `_frame_height` | int | 帧高度 |
| `_device_size` | Tuple[int, int] | 设备尺寸 |

---

## 坐标映射算法

### 渲染区域计算

```python
def _get_render_rect(widget_width, widget_height):
    # 保持宽高比缩放
    scale_x = widget_width / frame_width
    scale_y = widget_height / frame_height
    scale = min(scale_x, scale_y)  # 适应窗口

    render_w = int(frame_width * scale)
    render_h = int(frame_height * scale)

    # 居中
    x = (widget_width - render_w) // 2
    y = (widget_height - render_h) // 2

    return x, y, render_w, render_h
```

### 坐标转换

```python
def map_to_device_coords(widget_x, widget_y, widget_width, widget_height):
    render_x, render_y, render_w, render_h = _get_render_rect(...)

    # 检查是否在渲染区域内
    if not (render_x <= widget_x < render_x + render_w and
            render_y <= widget_y < render_y + render_h):
        return -1, -1  # 区域外

    # 映射到设备坐标
    device_x = (widget_x - render_x) * device_width // render_w
    device_y = (widget_y - render_y) * device_height // render_h

    # 边界裁剪
    device_x = max(0, min(device_x, device_width - 1))
    device_y = max(0, min(device_y, device_height - 1))

    return device_x, device_y
```

---

## 坐标映射示意图

```
┌─────────────────────────────────────┐
│           Widget (窗口)              │
│                                     │
│    ┌─────────────────────┐          │
│    │                     │          │
│    │    Render Area      │          │
│    │    (保持宽高比)      │          │
│    │                     │          │
│    │  (x,y) ────→ (device_x, device_y)
│    │                     │          │
│    └─────────────────────┘          │
│                                     │
└─────────────────────────────────────┘
```

---

## 使用示例

```python
class OpenGLVideoRenderer(QOpenGLWindow, InputHandler, CoordinateMapper):
    def mousePressEvent(self, event):
        # 坐标映射
        device_x, device_y = self.map_to_device_coords(
            event.x(), event.y(),
            self.width(), self.height()
        )

        # 更新按钮状态
        self._update_mouse_button_state(event.button(), True)

        # 发送触摸事件
        self._send_touch_event(
            action=AndroidMotionEventAction.DOWN,
            pointer_id=POINTER_ID_MOUSE,
            position_x=device_x,
            position_y=device_y,
        )
```

---

## 依赖关系

```
InputHandler
    │
    ├──→ protocol.py (常量)
    │
    └──→ ControlMessage, ControlMessageQueue

CoordinateMapper
    │
    └──→ (无外部依赖)
```

**被依赖**:
- opengl_window.py (继承)

---

*此文档基于代码分析生成*
