# GUI Overview (客户端)

> **目录**: `gui/`
> **文件**: 6 个 Python 文件
> **功能**: Qt 图形界面

---

## 文件清单

| 文件 | 职责 |
|------|------|
| `__main__.py` | GUI 入口 |
| `main_window.py` | 主窗口 |
| `preview_window.py` | 预览窗口 |
| `mcp_manager.py` | MCP 服务器管理 |
| `config_manager.py` | 配置管理 |
| `__init__.py` | 模块导出 |

---

## GUI 入口

### __main__.py

```python
"""
GUI 模块入口。

可通过 python -m scrcpy_py_ddlx.gui 启动。
"""

def main():
    """启动 GUI 应用。"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
```

---

## MainWindow

主窗口，包含设备列表和连接控制。

```python
class MainWindow(QMainWindow):
    """
    主窗口。

    功能:
    - 设备发现和列表
    - 连接参数配置
    - 启动预览窗口
    - MCP 服务器管理
    """

    def __init__(self):
        self._device_list: QListWidget
        self._connect_button: QPushButton
        self._config_panel: ConfigPanel

    def refresh_devices(self) -> None:
        """刷新设备列表。"""

    def connect_device(self, device: DeviceInfo) -> None:
        """连接设备。"""

    def open_preview(self, connection: Connection) -> None:
        """打开预览窗口。"""
```

### UI 布局

```
┌─────────────────────────────────────────────────────┐
│  工具栏: [刷新设备] [连接] [设置] [MCP]             │
├─────────────────────┬───────────────────────────────┤
│                     │                               │
│   设备列表          │   配置面板                    │
│   ┌───────────┐     │   ┌─────────────────────┐    │
│   │ Device 1  │     │   │ 视频编解码器: [  ]  │    │
│   │ Device 2  │     │   │ 码率: [      ]      │    │
│   │ ...       │     │   │ FEC: [ ]            │    │
│   └───────────┘     │   └─────────────────────┘    │
│                     │                               │
├─────────────────────┴───────────────────────────────┤
│  状态栏: 已连接 | 192.168.1.100:27185              │
└─────────────────────────────────────────────────────┘
```

---

## PreviewWindow

预览窗口，显示设备屏幕。

```python
class PreviewWindow(QMainWindow):
    """
    预览窗口。

    功能:
    - 视频显示 (QOpenGLWidget)
    - 触摸/按键事件转发
    - 窗口大小自适应
    - 截图/录制
    """

    # 信号
    frame_received = pyqtSignal(np.ndarray)
    connection_lost = pyqtSignal()

    def __init__(self, connection: Connection, config: Config):
        self._video_widget: QOpenGLWidget
        self._control_sender: ControlSender
        self._stats_label: QLabel

    def set_frame(self, frame: np.ndarray) -> None:
        """设置视频帧 (线程安全)。"""

    def send_touch_event(self, event: QTouchEvent) -> None:
        """发送触摸事件。"""

    def send_key_event(self, event: QKeyEvent) -> None:
        """发送按键事件。"""

    def take_screenshot(self) -> None:
        """截图。"""

    def toggle_recording(self) -> None:
        """切换录制状态。"""
```

### OpenGL 渲染

```python
class VideoWidget(QOpenGLWidget):
    """
    OpenGL 视频渲染组件。

    支持:
    - NV12/YUV420P/BGR 格式
    - 硬件加速渲染
    - 宽高比保持
    """

    def initializeGL(self) -> None:
        """初始化 OpenGL。"""
        # 创建纹理
        # 编译着色器

    def paintGL(self) -> None:
        """渲染帧。"""
        # 更新纹理
        # 绘制四边形

    def resizeGL(self, w: int, h: int) -> None:
        """调整大小。"""
        # 更新视口
        # 计算缩放
```

### 事件处理

```python
def mousePressEvent(self, event: QMouseEvent) -> None:
    """鼠标按下 → 触摸 DOWN。"""
    x, y = self._screen_to_device(event.pos())
    self._control_sender.send_touch(TOUCH_DOWN, x, y)

def mouseMoveEvent(self, event: QMouseEvent) -> None:
    """鼠标移动 → 触摸 MOVE。"""
    x, y = self._screen_to_device(event.pos())
    self._control_sender.send_touch(TOUCH_MOVE, x, y)

def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    """鼠标释放 → 触摸 UP。"""
    self._control_sender.send_touch(TOUCH_UP, 0, 0)

def keyPressEvent(self, event: QKeyEvent) -> None:
    """键盘按下 → 按键事件。"""
    keycode = self._qt_key_to_android(event.key())
    self._control_sender.send_key(KEY_DOWN, keycode)
```

---

## McpManager

MCP 服务器管理器。

```python
class McpManager(QObject):
    """
    MCP 服务器管理器。

    功能:
    - 启动/停止 MCP 服务器
    - HTTP 和 STDIO 模式
    - 连接状态管理
    """

    server_started = pyqtSignal(int)  # port
    server_stopped = pyqtSignal()
    client_connected = pyqtSignal()

    def __init__(self):
        self._http_server: Optional[ThreadingHTTPServer] = None
        self._stdio_process: Optional[subprocess.Popen] = None

    def start_http_server(self, port: int = 8765) -> None:
        """启动 HTTP MCP 服务器。"""

    def stop_http_server(self) -> None:
        """停止 HTTP MCP 服务器。"""

    def get_mcp_status(self) -> dict:
        """获取 MCP 状态。"""
```

---

## ConfigManager

配置管理器。

```python
class ConfigManager:
    """
    配置管理器。

    功能:
    - 保存/加载配置
    - 默认配置
    - 配置验证
    """

    DEFAULT_CONFIG = {
        "video_codec": "h264",
        "video_bit_rate": 8000000,
        "audio_codec": "opus",
        "audio_bit_rate": 128000,
        "max_fps": 60,
        "fec_enabled": False,
        "fec_group_size": 4,
        "fec_parity_count": 1,
    }

    def __init__(self, config_path: str = None):
        self._config = self.DEFAULT_CONFIG.copy()
        if config_path:
            self.load(config_path)

    def load(self, path: str) -> None:
        """从文件加载配置。"""

    def save(self, path: str) -> None:
        """保存配置到文件。"""

    def get(self, key: str, default=None) -> Any:
        """获取配置项。"""

    def set(self, key: str, value: Any) -> None:
        """设置配置项。"""
```

---

## 跨进程通信

预览窗口可能运行在独立进程中。

```python
class PreviewProcess:
    """
    预览进程管理。

    解决 GIL 竞争问题:
    - 解码在子进程
    - 渲染在子进程
    - 通过 SharedMemory 传输
    """

    def __init__(self, connection_info: dict):
        self._process: Optional[multiprocessing.Process] = None
        self._shared_memory: Optional[SharedMemory] = None
        self._frame_event: Event = Event()

    def start(self) -> None:
        """启动预览进程。"""

    def stop(self) -> None:
        """停止预览进程。"""

    def get_frame(self) -> Optional[np.ndarray]:
        """从共享内存读取帧。"""
```

---

## 样式表

```python
# 暗色主题
DARK_STYLE = """
QMainWindow {
    background-color: #1e1e1e;
}
QPushButton {
    background-color: #3c3c3c;
    color: white;
    border: 1px solid #555;
    padding: 5px 10px;
}
QPushButton:hover {
    background-color: #4a4a4a;
}
QListWidget {
    background-color: #2d2d2d;
    color: white;
}
"""
```

---

## 相关文档

- [preview_process.md](preview_process.md) - 预览进程详解
- [mcp_server.md](mcp_server.md) - MCP 服务器
- [features/gui/overview.md](../../features/gui/overview.md) - GUI 功能
