# scrcpy-py-ddlx

纯 Python 实现的 scrcpy 客户端，支持 MCP 服务器，用于 Android 设备镜像和控制。

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 快速开始

### 1. 创建工作目录并克隆项目

```bash
# 创建工作目录
mkdir ddlx
cd ddlx

# 克隆项目
git clone https://github.com/AIddlx/scrcpy_py_ddlx.git
```

### 2. 创建虚拟环境

```bash
# 在工作目录中创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate
```

### 3. 安装依赖

```bash
# 进入项目目录
cd scrcpy-py-ddlx

# 安装依赖
pip install -r requirements.txt
```

### 4. 运行测试

```bash
python tests_gui/test_direct.py
```

详细步骤请参考：[测试指南](docs/SETUP_GUIDE.md)

---

## 使用模式

| 模式 | 命令 | 说明 |
|------|------|------|
| **Python API** | `from scrcpy_py_ddlx import ScrcpyClient` | 作为 Python 库使用 |
| **HTTP MCP** | `python scrcpy_http_mcp_server.py --audio` | HTTP MCP 服务器 |
| **Direct Test** | `python tests_gui/test_direct.py` | 快速测试（带视频窗口） |

---

## Python API 示例

```python
from scrcpy_py_ddlx import ScrcpyClient, ClientConfig

config = ClientConfig(
    show_window=True,
    audio=True,
)

client = ScrcpyClient(config)
client.connect()

# 控制设备
client.tap(500, 1000)
client.home()
client.text("Hello World")

client.disconnect()
```

---

## 功能特性

- 🎥 **视频流** - 支持 H.264/H.265 编解码器，GPU 加速渲染
- 🔊 **音频流** - OPUS 编码，支持播放和录制
- 📊 **码率监控** - 实时监控视频传输码率
- 📋 **剪贴板同步** - PC 与设备自动同步
- 📱 **应用列表获取** - 获取设备已安装应用
- 🖱️ **完整控制** - 触摸、键盘、滚动、文字输入
- 🌐 **无线 ADB** - 无需 USB 连接，支持自动发现
- 🤖 **MCP 服务器** - Claude Code / 阶跃桌面助手集成

### GPU 渲染支持

启用 OpenGL GPU 加速可将视频码率从 3.7 Mbps 提升到 7.0+ Mbps。

```bash
pip install PyOpenGL PyOpenGL_accelerate
```

---

## 阶跃桌面助手集成

支持在阶跃桌面助手中添加 MCP 工具，实现 AI 直接控制 Android 设备。

详细步骤：[阶跃桌面助手 MCP 集成指南](docs/JUMPY_ASSISTANT_MCP_SETUP.md)

---

## 文档

| 文档 | 说明 |
|------|------|
| [测试指南](docs/SETUP_GUIDE.md) | 完整的测试环境搭建流程 |
| [阶跃桌面助手集成](docs/JUMPY_ASSISTANT_MCP_SETUP.md) | 在阶跃助手中添加 MCP 工具 |
| [协作规范](CLAUDE.md) | 开发协作规范 |

---

## 系统要求

- Python 3.10+
- Android 设备（API 21+）
- ADB（Android SDK Platform Tools）

### Python 依赖

#### 核心依赖（必需）

- `av` - 视频/音频编解码
- `numpy` - 数组操作

#### 可选依赖（按需安装）

- `PySide6` - Qt6 GUI
- `PyOpenGL` - GPU 加速渲染
- `PyOpenGL_accelerate` - OpenGL 加速
- `sounddevice` - 音频播放
- `starlette` / `uvicorn` - HTTP MCP 服务器

#### 一键安装所有依赖

```bash
pip install -r requirements.txt
```

---

## 项目结构

```
scrcpy-py-ddlx/
├── scrcpy_py_ddlx/          # Python 包
│   ├── client/              # 客户端核心
│   ├── core/                # 核心功能（解码、渲染）
│   └── mcp_server.py        # MCP 服务器
├── scrcpy-server            # 预编译 server
├── scrcpy_http_mcp_server.py # HTTP MCP 服务器
├── tests_gui/               # 测试脚本
├── docs/                    # 文档
└── image/                   # 截图和说明图片
```

---

## 许可证

MIT License

---

## 参考资料

- **[官方 scrcpy](https://github.com/Genymobile/scrcpy)** - Android 镜像与控制工具（原项目）
- **[本仓库](https://github.com/AIddlx/scrcpy_py_ddlx)** - Python 客户端实现
