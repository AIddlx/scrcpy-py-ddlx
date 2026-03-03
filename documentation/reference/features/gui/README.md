# GUI 模块

> PyQt6 桌面应用界面

---

## 功能清单

| 组件 | 文件 | 说明 | 状态 |
|------|------|------|------|
| 主窗口 | `gui/main_window.py` | 应用主界面 | ✅ |
| 预览窗口 | `gui/preview_window.py` | 独立预览窗口 | ✅ |
| MCP 管理器 | `gui/mcp_manager.py` | MCP 服务管理 | ✅ |
| 配置管理 | `gui/config_manager.py` | 用户配置 | ✅ |
| 连接面板 | `gui/panels/connection_panel.py` | 连接设置 | ✅ |
| 设备面板 | `gui/panels/device_panel.py` | 设备信息 | ✅ |
| 媒体面板 | `gui/panels/media_panel.py` | 媒体控制 | ✅ |
| 日志面板 | `gui/panels/log_panel.py` | 日志显示 | ✅ |

---

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                        MainWindow                            │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│ Connection  │   Device    │   Media     │      Log          │
│   Panel     │   Panel     │   Panel     │     Panel         │
└─────────────┴─────────────┴─────────────┴───────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ PreviewWindow   │
                    │ (独立进程)       │
                    └─────────────────┘
```

---

## 启动方式

```bash
# 命令行启动
python -m scrcpy_py_ddlx.gui

# 或
python scrcpy_mcp_gui.py
```

---

## 主要功能

### 连接管理

- 设备列表显示
- USB/网络模式切换
- 自动发现设备

### 预览窗口

- 独立进程运行
- 支持多设备预览
- 跨进程共享内存

### MCP 服务管理

- 启动/停止 MCP 服务
- 状态监控
- 日志输出

---

## 文件结构

```
gui/
├── __init__.py
├── __main__.py          # 入口点
├── main_window.py       # 主窗口
├── preview_window.py    # 预览窗口
├── mcp_manager.py       # MCP 管理
├── config_manager.py    # 配置管理
└── panels/
    ├── __init__.py
    ├── connection_panel.py
    ├── device_panel.py
    ├── media_panel.py
    └── log_panel.py
```

---

## 依赖

- PyQt6
- qt-material (主题)

---

## 注意事项

1. **GUI 线程安全**: 所有 GUI 操作必须在主线程
2. **信号槽**: 使用 Qt 信号槽进行跨线程通信
3. **独立进程**: 预览窗口使用多进程避免 GIL
