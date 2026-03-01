# 文件传输

> PC 与设备之间的文件传输功能

---

## 功能清单

| 功能 | 通道 | 文件 | 状态 |
|------|------|------|------|
| [ADB 文件操作](adb_file.md) | ADB | `core/file/file_ops.py` | ✅ |
| [网络文件通道](network_file.md) | TCP | `core/file/file_channel.py` | ✅ |
| 文件命令 | - | `core/file/file_commands.py` | ✅ |

---

## 通道对比

| 特性 | ADB 文件 | 网络文件 |
|------|---------|---------|
| 传输层 | ADB push/pull | 独立 TCP |
| 需要 USB | 是 (或 adb tcpip) | 否 |
| 速度 | 较快 | 快 |
| 断点续传 | 否 | 计划中 |
| 适用模式 | USB/网络 | 仅网络 |

---

## 使用方式

### Python API

```python
from scrcpy_py_ddlx import Client

client = Client(device="192.168.1.100:5555", network_mode=True)
client.start()

# 列出目录
files = client.list_dir("/sdcard/Download")

# 上传文件
client.push_file("local.txt", "/sdcard/Download/remote.txt")

# 下载文件
client.pull_file("/sdcard/Download/remote.txt", "local.txt")

# 删除文件
client.delete_file("/sdcard/Download/remote.txt")
```

### MCP 工具

```json
// 列出目录
{"tool": "list_dir", "arguments": {"path": "/sdcard/Download"}}

// 上传文件
{"tool": "push_file", "arguments": {"local": "local.txt", "remote": "/sdcard/Download/remote.txt"}}

// 下载文件
{"tool": "pull_file", "arguments": {"remote": "/sdcard/Download/remote.txt", "local": "local.txt"}}

// 删除文件
{"tool": "delete_file", "arguments": {"path": "/sdcard/Download/remote.txt"}}
```

---

## 相关文档

- [ADB 文件操作](adb_file.md)
- [网络文件通道](network_file.md)
- [文件传输开发文档](../../development/file_transfer/)
