# 剪贴板同步使用轮询而非事件

## 现状

当前剪贴板同步使用 `pyperclip` 库，通过轮询检测剪贴板变化：

```
[I] 21:56:24 [CONN] [Clipboard Monitor] Poll #2050, current='...', last='...'
[I] 21:56:29 [CONN] [Clipboard Monitor] Poll #2060, current='...', last='...'
[I] 21:56:34 [CONN] [Clipboard Monitor] Poll #2070, current='...', last='...'
```

轮询间隔约 500ms，每秒 2 次检测。

## 问题

- **CPU 开销**: 持续轮询消耗 CPU 资源
- **延迟**: 最坏情况下延迟 500ms
- **日志噪音**: 大量 Poll 日志

## 原因

`pyperclip` 设计追求简单和跨平台，不依赖 GUI 事件循环：
- Windows: 需要窗口消息循环接收 `WM_CLIPBOARDUPDATE`
- macOS: 需要 Cocoa 事件循环监听 `NSPasteboard`
- Linux: 需要 X11 事件监听 Selection

## 改进方案

由于项目已使用 PySide6 (Qt)，可以使用 Qt 的事件驱动机制：

```python
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QClipboard

class ClipboardSync:
    def __init__(self):
        clipboard = QApplication.clipboard()
        clipboard.dataChanged.connect(self.on_clipboard_changed)

    def on_clipboard_changed(self):
        # 事件驱动，仅在剪贴板变化时触发
        text = QApplication.clipboard().text()
        # 同步到设备...
```

### 优势

- **零轮询开销**: 仅在变化时触发
- **即时响应**: 无延迟
- **无日志噪音**: 不需要 Poll 日志

### 挑战

- 需要 Qt 应用上下文 (QApplication)
- 需要重构现有剪贴板同步模块
- 需要处理 Qt 信号在非 GUI 线程的问题

## 优先级

**低** - 当前轮询方案功能正常，开销可接受

## 相关文件

- `scrcpy_py_ddlx/client/components/clipboard_sync.py`

## 参考

- [Qt QClipboard Documentation](https://doc.qt.io/qt-6/qclipboard.html)
- [pyperclip GitHub](https://github.com/asweigart/pyperclip)
