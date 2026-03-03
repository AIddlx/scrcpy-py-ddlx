# 依赖清单

> scrcpy_http_mcp_server.py 运行所需的全部依赖

---

## 系统依赖

### ADB (Android Debug Bridge)

| 属性 | 值 |
|------|-----|
| **用途** | 设备通信和服务端启动 |
| **最低版本** | 1.0.40 |
| **必需** | ✅ 是 |

---

## Python 依赖

### 核心 Web 框架

| 包名 | 用途 | 必需 |
|------|------|------|
| `starlette` | ASGI Web 框架 | ✅ |
| `uvicorn` | ASGI 服务器 | ✅ |

### MCP 协议

| 包名 | 用途 | 必需 |
|------|------|------|
| `mcp` | MCP SDK | ✅ |

### 音视频处理

| 包名 | 用途 | 必需 |
|------|------|------|
| `numpy` | 图像处理 | ✅ |
| `av` (PyAV) | 视频解码 | ✅ |

### 标准库

| 模块 | 用途 |
|------|------|
| `sys` | 系统接口 |
| `json` | JSON 处理 |
| `logging` | 日志 |
| `asyncio` | 异步 |
| `threading` | 多线程 |
| `subprocess` | 进程调用 |
| `urllib.request` | HTTP 请求 |
| `os` | 环境变量 |
| `socket` | 网络操作 |
| `select` | I/O 多路复用 |
| `datetime` | 时间处理 |
| `pathlib` | 路径处理 |
| `typing` | 类型提示 |

---

## 项目内部依赖

### 客户端模块

```python
from scrcpy_py_ddlx.client import ScrcpyClient, ClientConfig
from scrcpy_py_ddlx.client.config import ConnectionMode
from scrcpy_py_ddlx.core.control import ControlMessage
from scrcpy_py_ddlx.core.auth import generate_auth_key, save_auth_key, load_auth_key
from scrcpy_py_ddlx.core.logging_config import setup_logging, get_cache_dir
```

| 模块 | 用途 |
|------|------|
| `client.client` | 主客户端类 |
| `client.config` | 配置管理 |
| `core.control` | 控制消息 |
| `core.auth` | 认证 |
| `core.logging_config` | 日志配置 |

---

## 安装命令

```bash
# 核心依赖
pip install starlette uvicorn mcp numpy av

# 完整依赖
pip install -r requirements.txt

# uvicorn 标准扩展 (推荐)
pip install uvicorn[standard]
```

---

## 可选依赖

### 性能优化

```bash
pip install uvloop httptools watchfiles
```

### 音频支持

```bash
pip install sounddevice pyaudio
```

---

## 依赖检查

```python
# 检查 Starlette
try:
    from starlette.applications import Starlette
    STARLETTE_AVAILABLE = True
except ImportError:
    STARLETTE_AVAILABLE = False

# 检查 uvicorn
import uvicorn
print(f"uvicorn: {uvicorn.__version__}")
```

---

## 相关文档

- [tools/overview.md](tools/overview.md) - 工具总览
- [usage.md](usage.md) - 使用说明
