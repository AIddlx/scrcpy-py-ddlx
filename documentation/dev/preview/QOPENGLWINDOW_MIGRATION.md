# QOpenGLWindow 迁移经验

## 背景

为了降低预览窗口的 CPU 使用率，将渲染组件从 `QOpenGLWidget` 迁移到 `QOpenGLWindow`。

## 性能对比

| 组件 | CPU 使用率 (Windows) | 原理 |
|------|---------------------|------|
| QOpenGLWidget | ~6-7% | FBO 离屏渲染，需要额外的合成 |
| QOpenGLWindow | ~0.5% | 直接渲染到窗口表面 |

## 关键技术点

### 1. QOpenGLWindow vs QOpenGLWidget

```python
# QOpenGLWidget: QWidget 子类，可直接作为中央部件
class MyWidget(QOpenGLWidget):
    pass
window.setCentralWidget(MyWidget())

# QOpenGLWindow: QWindow 子类，需要容器包装
class MyWindow(QOpenGLWindow):
    pass
gl_window = MyWindow()
container = QWidget.createWindowContainer(gl_window)
window.setCentralWidget(container)
```

### 2. 事件处理差异

**鼠标事件**：`createWindowContainer()` 创建的容器会拦截鼠标事件，需要在容器层面处理。

```python
class GLWindowContainer(QWidget):
    """自定义容器，转发鼠标/键盘事件"""

    def __init__(self, gl_window, main_window):
        super().__init__()
        self._gl_window = gl_window
        self._container = QWidget.createWindowContainer(gl_window, self)
        # 容器不拦截焦点
        self._container.setFocusPolicy(Qt.NoFocus)

    def mousePressEvent(self, event):
        # 在容器层面处理触摸事件
        ...
```

**键盘事件**：需要在 `QMainWindow` 级别使用事件过滤器捕获。

```python
class PreviewWindow(QMainWindow):
    def __init__(self):
        # 安装应用程序级别的事件过滤器
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if self.isActiveWindow():
                # 处理键盘事件
                ...
```

### 3. 控制事件队列

预览窗口在独立进程中运行，控制事件通过 `multiprocessing.Queue` 传递：

```python
# 预览进程发送
control_queue.put(('touch_down', x, y))
control_queue.put(('text', char))
control_queue.put(('key', 'back'))

# 主进程接收并执行
events = preview_manager.get_control_events()
for event in events:
    handle_control_event(event)
```

### 4. Direct SHM 模式的控制事件读取

当使用 Direct SHM 模式（GPU NV12 直接渲染）时，`_start_frame_sender()` 不会被调用，但控制事件仍需读取。

**解决方案**：创建独立的控制事件读取线程。

```python
def _start_control_event_reader(self):
    """独立线程读取控制事件（Direct SHM 模式）"""
    def control_reader_loop():
        while preview_manager.is_running:
            events = preview_manager.get_control_events()
            for event in events:
                handle_control_event(event)
            time.sleep(0.01)

    thread = threading.Thread(target=control_reader_loop, daemon=True)
    thread.start()
```

## 已知限制

### 1. 中文输入法不支持

Qt 在 Windows 上对 `QOpenGLWindow` 的 IME 支持有限，嵌入的窗口无法正确接收输入法事件。

**临时方案**：通过 MCP 工具 `input_text` 输入中文。

**可能方案**：
- 使用 Windows IMM32/TSF API 直接获取输入法输入
- 使用隐藏的文本输入控件（但效果不稳定）

### 2. Qt 键常量差异

不同版本的 PySide6/Qt 可能缺少某些键常量：

```python
# 不存在的键（会导致 AttributeError）
Qt.Key_Mute
Qt.Key_MediaPlayPause
Qt.Key_NumLock  # 某些版本
Qt.Key_ScrollLock  # 某些版本

# 解决方案：只使用确认存在的键
key_map = {
    Qt.Key_VolumeUp: 'volume_up',
    Qt.Key_VolumeDown: 'volume_down',
    Qt.Key_VolumeMute: 'volume_mute',
    # ...
}
```

### 3. OpenGL 上下文问题

`resizeGL` 中调用 OpenGL 函数可能失败（上下文不当前）：

```python
def resizeGL(self, w, h):
    try:
        glViewport(0, 0, w, h)
    except Exception:
        pass  # 忽略上下文错误
```

## 键盘映射

### 支持的控制键

| Qt 键 | Android 动作 | 说明 |
|-------|-------------|------|
| Escape | back | 返回 |
| Enter/Return | enter | 确认 |
| 方向键 | dpad_* | 导航 |
| F1-F12 | f1-f12 | 功能键 |
| Tab | tab | 制表符 |
| Delete/Backspace | del | 删除 |
| Insert | insert | 插入 |
| PageUp/PageDown | page_* | 翻页 |
| VolumeUp/Down/Mute | volume_* | 音量 |
| CapsLock | caps_lock | 大写锁定 |

### 文本输入

- 英文字符：直接通过 `inject_text` 发送
- 中文：暂不支持，使用 MCP 工具

## 架构说明

项目中有两处使用 `QOpenGLWindow` 进行渲染：

### 1. MCP 预览窗口（跨进程）

```
scrcpy_http_mcp_server.py
    └── PreviewManager.start()
        └── preview_process.py (独立进程)
            └── PreviewWindow(QMainWindow)
                └── GLWindowContainer(QWidget)
                    └── OpenGLPreviewWidget(QOpenGLWindow)
```

**特点**：
- 预览窗口运行在独立进程中
- 通过 `multiprocessing.Queue` 传递控制事件
- 需要单独的控制事件读取线程（Direct SHM 模式）

### 2. test_network_direct.py（同进程）

```
test_network_direct.py
    └── ScrcpyClient.run_with_qt()
        └── ComponentFactory.create_video_window()
            └── factory.create_video_window(use_opengl=True)
                └── OpenGLVideoWindow(QMainWindow)
                    └── OpenGLVideoRenderer(QOpenGLWindow)
                        └── QWidget.createWindowContainer()
```

**日志验证** (`test_logs/scrcpy_network_test_20260224_123329.log`):
```
[OPENGL_WINDOW] Using QOpenGLWindow-based renderer (low CPU mode)  ← video_window.py
[OPENGL_WINDOW] Event-driven rendering enabled                       ← opengl_window.py
OpenGLVideoWindow shown, geometry=...                                ← video_window.py
Initializing OpenGL (QOpenGLWindow)...                               ← opengl_window.py
OpenGL (QOpenGLWindow) initialized successfully                      ← opengl_window.py
```

**特点**：
- 与客户端运行在同一进程
- 使用事件驱动渲染（Signal 机制）
- 通过 `DelayBuffer` 直接消费帧

### 关键文件对照

| 场景 | 窗口类 | 渲染类 | 基类 | 文件 |
|------|--------|--------|------|------|
| MCP 预览 | `PreviewWindow` | `OpenGLPreviewWidget` | `QOpenGLWindow` | `preview_process.py` |
| 网络测试 | `OpenGLVideoWindow` | `OpenGLVideoRenderer` | `QOpenGLWindow` | `video_window.py` + `opengl_window.py` |

**注意**：两者都通过 `QWidget.createWindowContainer()` 嵌入，因此中文输入法面临相同的 Qt 限制。

## 文件修改清单

| 文件 | 修改 |
|------|------|
| `preview_process.py` | QOpenGLWindow 迁移、事件处理、控制事件发送 |
| `scrcpy_http_mcp_server.py` | 控制事件读取线程、事件处理 |
| `opengl_window.py` | QOpenGLWindow 渲染器实现 |
| `video_window.py` | OpenGLVideoWindow 封装 |

## 测试命令

```bash
# ADB 隧道模式
python scrcpy_http_mcp_server.py --connect --preview

# 网络模式
python scrcpy_http_mcp_server.py --network-push 192.168.x.x
```

## 参考资料

- [Qt QOpenGLWindow 文档](https://doc.qt.io/qt-6/qopenglwindow.html)
- [Qt Event Filters](https://doc.qt.io/qt-6/eventsandfilters.html)
- [Android KeyEvent](https://developer.android.com/reference/android/view/KeyEvent)
