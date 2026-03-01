# QOpenGLWindow 输入控制修复经验

## 问题描述

预览窗口从 `QOpenGLWidget` 迁移到 `QOpenGLWindow` 后，出现以下问题：
1. 触摸/鼠标控制失效
2. 键盘控制失效
3. 英文字符输入失效

## 根本原因

### 1. 鼠标事件被容器拦截

`QOpenGLWindow` 是 `QWindow`，不是 `QWidget`。使用 `QWidget.createWindowContainer()` 嵌入时，鼠标事件被容器 widget 拦截，不会传递到 `QOpenGLWindow`。

**解决方案**：创建 `GLWindowContainer` 类，在容器级别处理鼠标事件。

### 2. 键盘事件需要事件过滤器

键盘事件需要通过 `QApplication.instance().installEventFilter()` 在应用程序级别捕获，而不是仅依赖 `keyPressEvent`。

### 3. Direct SHM 模式缺少控制事件读取

使用 Direct SHM 模式时，`_start_frame_sender()` 不会被调用，但该方法原本负责读取控制事件。需要单独启动 `_start_control_event_reader()`。

### 4. Qt 键常量不存在

PySide6 中部分 Qt.Key 常量不存在：
- `Qt.Key_Mute` - 不存在
- `Qt.Key_MediaPlayPause` - 不存在
- `Qt.Key_NumLock` - 不存在
- `Qt.Key_ScrollLock` - 不存在
- `Qt.Key_Camera` - 不存在

需要移除这些键映射。

### 5. 空格键冲突

`Qt.Key_Space` 被映射为 `'dpad_center'`，导致空格无法作为文本字符输入。需要移除此映射。

## 修复方案

### 1. GLWindowContainer 类

```python
class GLWindowContainer(QWidget):
    """容器 widget，处理鼠标和键盘事件"""

    def __init__(self, gl_window, main_window, parent=None):
        super().__init__(parent)
        self._gl_window = gl_window
        self._main_window = main_window
        self.setMouseTracking(True)

        # 内部容器（不获取焦点）
        self._container = QWidget.createWindowContainer(gl_window, self)
        self._container.setFocusPolicy(Qt.NoFocus)

    def mousePressEvent(self, event):
        # 处理鼠标按下，发送 touch_down 事件

    def mouseMoveEvent(self, event):
        # 处理鼠标移动，发送 touch_move 事件

    def mouseReleaseEvent(self, event):
        # 处理鼠标释放，发送 touch_up 事件
```

### 2. 应用程序级别事件过滤器

```python
def eventFilter(self, obj, event):
    if event.type() == QEvent.Type.KeyPress:
        if self.isActiveWindow():
            key = event.key()
            text = event.text()

            # 检查控制键映射
            action = key_map.get(key)
            if action:
                control_queue.put(('key', action), timeout=0.1)
                return True

            # 文本输入
            if text and text[0].isprintable():
                control_queue.put(('text', text[0]), timeout=0.1)
                return True

    return super().eventFilter(obj, event)
```

### 3. 窗口显示时获取焦点

```python
def showEvent(self, event):
    super().showEvent(event)
    self.activateWindow()
    self.raise_()
    self.setFocus()
```

### 4. Direct SHM 模式的控制事件读取

```python
def _start_control_event_reader(self):
    """单独的控制事件读取线程"""
    def control_reader_loop():
        while self._preview_manager.is_running:
            events = self._preview_manager.get_control_events()
            for event in events:
                self._handle_preview_control_event(event)
            time.sleep(0.01)

    threading.Thread(target=control_reader_loop, daemon=True).start()
```

## 最终支持的按键

### 控制键
| 按键 | 动作 |
|------|------|
| ESC | back |
| Enter/Return | enter |
| Backspace/Delete | del |
| Tab | tab |
| 方向键 | dpad_up/down/left/right |
| F1-F12 | f1-f12 |
| Page Up/Down | page_up/page_down |
| Insert | insert |
| CapsLock | caps_lock |
| 音量键 | volume_up/down/mute |

### 文本输入
- 所有可打印 ASCII 字符
- 空格

## 已知限制

1. **中文输入法不支持**：Qt 在 Windows 上对嵌入的 QOpenGLWindow 的 IME 支持有问题，需要通过 MCP 工具 `input_text` 输入中文

2. **OpenGL resizeGL 错误**：`glViewport` 可能在上下文不正确时失败，需要用 try/except 包裹

## 文件修改清单

| 文件 | 修改内容 |
|------|----------|
| `scrcpy_py_ddlx/preview_process.py` | GLWindowContainer、eventFilter、showEvent |
| `scrcpy_http_mcp_server.py` | _start_control_event_reader、_handle_preview_control_event |

## 测试验证

```bash
python scrcpy_http_mcp_server.py --network-push 192.168.5.4
```

验证：
1. 鼠标点击/滑动设备响应
2. ESC 键返回
3. 英文字符输入
4. 方向键滚动
