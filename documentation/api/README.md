# API 参考

面向开发者的 API 文档。

---

## 文档

| 文档 | 说明 |
|------|------|
| [控制方法](control.md) | 所有控制命令及示例 |
| [协议参数](protocol.md) | 协议格式和参数 |
| [功能状态](status.md) | 各功能支持情况 |

---

## 快速参考

### 控制命令分类

- **触摸**: tap, swipe, long_press
- **按键**: key, text
- **屏幕**: screenshot, rotate
- **应用**: start_app, install_apk
- **文件**: list_files, push_file, pull_file
- **剪贴板**: get_clipboard, set_clipboard

### 连接模式

- **ADB Tunnel**: USB 连接，安全稳定
- **Network**: TCP 控制 + UDP 媒体，无线自由
