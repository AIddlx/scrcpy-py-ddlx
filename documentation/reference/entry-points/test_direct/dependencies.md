# 依赖清单

> test_direct.py 运行所需的全部依赖

---

## 系统依赖

### ADB (Android Debug Bridge)

| 属性 | 值 |
|------|-----|
| **用途** | 设备通信和服务端启动 |
| **最低版本** | 1.0.40 |
| **必需** | ✅ 是 |

```bash
# 验证安装
adb version
```

---

## Python 依赖

### 核心依赖

| 包名 | 用途 | 必需 |
|------|------|------|
| `numpy` | 视频帧数据处理 | ✅ |
| `av` (PyAV) | 视频/音频解码 | ✅ |
| `PySide6` | Qt GUI | ✅ |

### 标准库

| 模块 | 用途 |
|------|------|
| `sys` | 系统接口 |
| `logging` | 日志记录 |
| `time` | 时间操作 |
| `threading` | 多线程 |
| `subprocess` | 进程调用 (ADB) |
| `re` | 正则表达式 |
| `socket` | 网络扫描 |
| `pathlib` | 路径处理 |
| `datetime` | 时间戳 |
| `concurrent.futures` | 并发扫描 |

---

## 项目内部依赖

### 客户端模块

```python
from scrcpy_py_ddlx.client import ScrcpyClient, ClientConfig
from scrcpy_py_ddlx.core.player.video import create_video_window
from scrcpy_py_ddlx.core.file_pusher import init_file_pusher
```

| 模块 | 用途 |
|------|------|
| `client.client` | 主客户端类 |
| `client.config` | 配置定义 |
| `core.player.video` | 视频渲染窗口 |
| `core.file_pusher` | 文件传输 |

---

## 安装命令

```bash
# 核心依赖
pip install numpy av PySide6

# 可选: 音频录制格式支持
pip install pyaudio  # wav 格式
```

---

## 依赖检查

脚本启动时会自动检查依赖:

```python
# 检查 numpy
import numpy as np
print(f"[PASS] numpy: {np.__version__}")

# 检查 PySide6
from PySide6.QtWidgets import QApplication
print(f"[PASS] PySide6 已安装")

# 检查 PyAV
import av
print(f"[PASS] PyAV: {av.__version__}")

# 检查源码模块
from scrcpy_py_ddlx.client import ScrcpyClient, ClientConfig
print("[PASS] 源码模块导入成功")
```

---

## 相关文档

- [features.md](features.md) - 功能详解
- [usage.md](usage.md) - 使用说明
