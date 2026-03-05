# scrcpy-py-ddlx

基于 [scrcpy](https://github.com/Genymobile/scrcpy) 协议的纯 Python 客户端实现，让你在电脑上高清镜像和控制 Android 设备。内置 MCP 服务器，可与 [阶跃桌面助手](https://www.stepfun.com/download) 等 AI 工具无缝集成，适用于自动化测试、远程控制、AI 辅助操作等场景。

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/) [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE) [![Platform](https://img.shields.io/badge/Platform-Windows_10/11-blue)](https://www.microsoft.com/windows) [![Platform](https://img.shields.io/badge/Platform-Linux/macOS-orange)]()

[English](README_EN.md) | 中文

---

## 功能特性

- 🎥 **高清投屏** - H.264/H.265 编解码，4K 60fps，GPU 加速渲染
- 🔊 **音频流** - OPUS 编解码，支持播放和录制
- 🌐 **多连接模式** - USB / WiFi / 网络直连 (TCP/UDP)
- 🤖 **AI 操控** - MCP 服务器，支持 [阶跃桌面助手](https://www.stepfun.com/download)
- 📋 **剪贴板同步** - PC 与设备双向同步
- 📁 **文件传输** - 设备与 PC 间快速传输
- 🖱️ **完整控制** - 触摸、键盘、滚动、文字输入

---



## 阶跃桌面助手

[阶跃桌面助手](https://www.stepfun.com/download) 是阶跃星辰推出的国产桌面 AI Agent。

### 核心能力

| 功能 | 说明 |
|------|------|
| **自然语言操控** | 用说话的方式操控电脑，自动执行复杂任务 |
| **本地文件操作** | 智能命名、分类、整理文件 |
| **网页浏览** | 自主访问网站、提取信息、生成报告 |
| **MCP 协议** | 调用 Excel、飞书、邮箱等 16+ 款工具 |
| **妙计系统** | 保存常用指令，一键复用，社区分享 |

### 与本项目的集成

本项目提供 MCP 服务器，安装阶跃桌面助手后，配置 MCP 即可让 AI 自动操作手机：

```
AI 发送指令 → MCP 服务器 → scrcpy-py-ddlx → Android 设备
```

**可实现**：
- 截图识别屏幕内容
- 自动点击、滑动操作
- 文件传输管理
- 应用启动与控制

### 下载安装

- **官网**：https://www.stepfun.com/download
- **支持**：Windows / macOS
- **费用**：免费使用

---

**快速导航**：[快速开始](#快速开始) · [入口脚本](#入口脚本) · [预编译文件](#预编译文件) · [依赖说明](#依赖说明) · [阶跃桌面助手](#阶跃桌面助手) · [文档](#文档) · [AI 助手集成](#ai-助手集成)

---

## 快速开始

### 系统要求

| 项目 | 要求 |
|------|------|
| **操作系统** | Windows 10/11 ✅ / Linux / macOS (理论上支持，暂未适配) |
| **Python** | 3.10 或更高版本 |
| **Android** | API 21+ (Android 5.0+) |
| **ADB** | Android SDK Platform Tools |

> **平台兼容性说明**：本项目在 Windows 10/11 环境下充分测试。Linux 和 macOS 理论上可以运行（核心功能使用跨平台库），但由于缺少测试硬件，暂未进行适配和验证。欢迎社区贡献其他平台的支持。

### 安装步骤

```bash
# 1. 创建并进入目录
mkdir ddlx
cd ddlx

# 2. 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 3. 克隆项目
git clone https://github.com/AIddlx/scrcpy-py-ddlx.git .

# 4. 安装依赖
pip install -r requirements.txt
```

### 运行测试

```bash
# USB 模式 - 最简单的方式
python tests_gui/test_direct.py

# 网络模式 - 支持 WiFi
python tests_gui/test_network_direct.py

# MCP 服务器 - AI 操控
python scrcpy_http_mcp_server.py
```

---

## 入口脚本

本项目提供三个主要入口脚本：

| 脚本 | 用途 | 连接方式 |
|------|------|----------|
| `tests_gui/test_direct.py` | 快速测试 / 开发调试 | USB (ADB) |
| `tests_gui/test_network_direct.py` | 无线投屏 / 远程控制 | WiFi (TCP/UDP) |
| `scrcpy_http_mcp_server.py` | AI 操控服务 | USB / WiFi |

### test_direct.py - USB 模式

纯 USB 模式，最稳定的连接方式：

```bash
# 基本用法
python tests_gui/test_direct.py

# 调试模式
python tests_gui/test_direct.py --log-level DEBUG
```

**特点：**
- 自动检测 USB 连接的设备
- 自动推送服务端到设备
- 显示视频窗口，支持音频和剪贴板

### test_network_direct.py - 网络模式

支持 WiFi 无线连接：

```bash
# 一次性模式 (服务端随客户端退出)
python tests_gui/test_network_direct.py

# 驻留模式 (服务端保持运行)
python tests_gui/test_network_direct.py --stay-alive

# FEC 纠错 (弱网环境)
python tests_gui/test_network_direct.py --fec frame --fec-k 8 --fec-m 2
```

### scrcpy_http_mcp_server.py - MCP 服务器

HTTP MCP 服务器，供 AI 助手调用：

```bash
# 一次性模式 (USB)
python scrcpy_http_mcp_server.py

# 一次性模式 (网络)
python scrcpy_http_mcp_server.py --net

# 驻留模式 (网络，服务端保持运行)
python scrcpy_http_mcp_server.py --net --stay-alive

# 指定端口
python scrcpy_http_mcp_server.py --port 3359

# 终止远程服务端 (IP 可选，不填则自动发现)
python scrcpy_http_mcp_server.py --stop-server
python scrcpy_http_mcp_server.py --stop-server 192.168.1.100
```

**MCP 工具列表：**

| 工具 | 功能 |
|------|------|
| `screenshot` | 获取屏幕截图 |
| `tap` | 点击指定坐标 |
| `swipe` | 滑动操作 |
| `type_text` | 输入文字 |
| `press_key` | 按键 (HOME/BACK/等) |
| `get_device_info` | 获取设备信息 |
| `list_apps` | 获取应用列表 |
| `start_app` | 启动应用 |
| `push_file` | 推送文件到设备 |
| `pull_file` | 从设备拉取文件 |

---

## 预编译文件

项目包含预编译文件，**无需自行编译**：

| 文件 | 说明 |
|------|------|
| `scrcpy-server` | Android 服务端 (~90KB)，自动推送到设备 |
| `scrcpy-companion.apk` | **手机端管理工具**，用于网络模式 |

### scrcpy-companion.apk

安装到手机后，提供以下功能：

| 功能 | 说明 |
|------|------|
| **快捷开关** | 下拉通知栏快速终止服务端 |
| **状态查看** | 查看服务端运行状态、端口、PID |
| **日志查看** | 实时查看服务端日志 |

**使用场景**：
- 网络模式下，先通过 USB 推送驻留服务端（`--stay-alive`），之后断开 USB，手机端用 companion 查看状态或终止服务
- 远程控制时，无需物理连接手机即可管理服务端

**安装**：
```bash
adb install scrcpy/companion/scrcpy-companion.apk
```

如需自行编译服务端，请参考 [安装指南](documentation/user/installation.md)。

---

## 项目结构

```
scrcpy-py-ddlx/
├── scrcpy_py_ddlx/           # Python 客户端包
│   ├── client/               # 连接、配置、组件
│   ├── core/                 # 核心功能
│   │   ├── decoder/          # 视频/音频解码
│   │   ├── demuxer/          # 数据包解析
│   │   ├── audio/            # 音频处理
│   │   └── file/             # 文件传输
│   ├── gui/                  # Qt GUI 组件
│   └── mcp_server.py         # MCP 服务实现
├── scrcpy/server/            # Java 服务端源码
├── scrcpy-server             # 预编译服务端
├── scrcpy_http_mcp_server.py # MCP 服务器入口
├── tests_gui/                # 测试脚本
│   ├── test_direct.py        # USB 模式测试
│   └── test_network_direct.py # 网络模式测试
├── documentation/            # 文档
│   ├── user/                 # 用户指南
│   ├── api/                  # API 参考
│   └── dev/                  # 开发文档
└── requirements.txt          # Python 依赖
```

---

## 依赖说明

### 核心依赖 (必需)

```
av>=13.0.0        # 视频/音频编解码 (PyAV)
numpy>=1.24.0     # 数组操作
```

### GUI 依赖

```
PySide6           # Qt6 GUI 框架
PyOpenGL          # GPU 加速渲染
```

### MCP 服务器

```
starlette         # HTTP 框架
uvicorn           # ASGI 服务器
```

### 音频播放

```
sounddevice       # 音频输出
```

### Windows 剪贴板

```
pywin32           # Windows API
pyperclip         # 剪贴板操作
```

---

## 文档

| 文档 | 说明 |
|------|------|
| [快速开始](documentation/user/quickstart.md) | 5 分钟上手指南 |
| [安装指南](documentation/user/installation.md) | 完整安装说明 |
| [MCP 服务器指南](documentation/user/mcp-server-guide.md) | 服务器参数详解 |
| [API 参考](documentation/api/control.md) | 控制方法文档 |
| [协议规范](documentation/dev/protocols/PROTOCOL_SPEC.md) | 通信协议详情 |
| [故障排除](documentation/user/troubleshooting.md) | 常见问题解决 |

---

## AI 助手集成

本项目支持 [阶跃AI桌面伙伴](https://www.stepfun.com/download) 进行 AI 操控。

下载安装后，配置 MCP 并启动MCP服务器即可让 AI 自动操作手机。

详见 [阶跃助手 MCP 集成指南](documentation/user/integrations/jumpy-assistant.md)。

---

## 致谢

- [scrcpy](https://github.com/Genymobile/scrcpy) - 原始 scrcpy 项目
- [PyAV](https://github.com/PyAV-Org/PyAV) - FFmpeg Python 绑定
- [PySide6](https://www.pyside.org/) - Qt for Python

---

## 许可证

MIT License

---

## 交流群

欢迎加入交流群讨论问题和分享经验：

| scrcpy-py-ddlx QQ 群 | 阶跃官方群 |
|:--------------------:|:----------:|
| <img src="image/scrcpy-py-ddlx的qq群.jpg" width="280"> | <img src="image/阶跃官方群.png" width="280"> |
