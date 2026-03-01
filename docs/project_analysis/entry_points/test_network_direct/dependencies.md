# 依赖清单

> test_network_direct.py 运行所需的全部依赖

---

## 系统依赖

### ADB (Android Debug Bridge)

| 属性 | 值 |
|------|-----|
| **用途** | 启动服务端 (仅启动时需要) |
| **最低版本** | 1.0.40 |
| **必需** | ✅ 启动时需要 |

```bash
# 验证安装
adb version
```

### 网络端口

| 端口 | 协议 | 用途 |
|------|------|------|
| 27183 | UDP | 设备发现 |
| 27184 | TCP | 控制通道 |
| 27185 | UDP | 视频流 |
| 27186 | UDP | 音频流 |
| 27187 | TCP | 文件传输 |

---

## Python 依赖

### 核心依赖

| 包名 | 用途 | 必需 |
|------|------|------|
| `numpy` | 视频帧处理 | ✅ |
| `av` (PyAV) | 视频解码 | ✅ |
| `PySide6` | Qt GUI | ✅ |

### 标准库

| 模块 | 用途 |
|------|------|
| `sys` | 系统接口 |
| `os` | 环境变量 |
| `logging` | 日志 |
| `subprocess` | ADB 调用 |
| `time` | 时间操作 |
| `argparse` | 命令行解析 |
| `re` | 正则表达式 |
| `pathlib` | 路径处理 |
| `datetime` | 时间戳 |

---

## 项目内部依赖

### 客户端模块

```python
from scrcpy_py_ddlx.client import ScrcpyClient, ClientConfig
from scrcpy_py_ddlx.client.config import ConnectionMode
from scrcpy_py_ddlx.core.negotiation import VideoCodecId, AudioCodecId
from scrcpy_py_ddlx.core.auth import (
    generate_auth_key, save_auth_key, load_auth_key
)
```

| 模块 | 用途 |
|------|------|
| `client.client` | 主客户端 |
| `client.config` | 配置和网络模式 |
| `core.negotiation` | 编解码器协商 |
| `core.auth` | 认证密钥管理 |

---

## 服务端依赖

### 运行在 Android 设备上

| 组件 | 路径 |
|------|------|
| 服务端 APK | `/data/local/tmp/scrcpy-server.apk` |
| 认证密钥 | `/data/local/tmp/scrcpy-auth.key` |

---

## 安装命令

```bash
# 核心依赖
pip install numpy av PySide6

# 完整依赖 (包含 MCP 相关)
pip install -r requirements.txt
```

---

## 依赖检查

脚本启动时自动检查:

```python
import numpy as np
print(f"[PASS] numpy: {np.__version__}")

from PySide6.QtWidgets import QApplication
print("[PASS] PySide6 installed")

import av
print(f"[PASS] PyAV: {av.__version__}")

from scrcpy_py_ddlx.client import ScrcpyClient, ClientConfig
from scrcpy_py_ddlx.client.config import ConnectionMode
print("[PASS] Source modules imported")
```

---

## 相关文档

- [features/overview.md](features/overview.md) - 功能概览
- [usage.md](usage.md) - 使用说明
