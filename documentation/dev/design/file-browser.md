# 文件浏览与双向传输功能设计

> **状态**: 设计中
> **日期**: 2026-02-25

---

## 功能概述

在 `scrcpy_http_mcp_server.py` 中添加文件管理功能：
1. **浏览手机文件系统** - 列出目录内容、获取文件信息
2. **手机 → 电脑传输** - 从设备下载文件
3. **电脑 → 手机传输** - 上传/推送文件到设备
4. **文件操作** - 删除、重命名、创建目录

## 兼容性

| 模式 | ADB 命令 | 可用性 |
|------|----------|--------|
| ADB 隧道模式 (USB) | `adb shell ls`, `adb push`, `adb pull` | ✅ 完全支持 |
| 网络模式 (WiFi) | `adb -s <ip>:5555 shell ls` | ✅ 完全支持 |

**关键点**: 两种模式都通过 ADB 命令实现，无需修改 scrcpy 协议。

---

## MCP 工具定义

### 1. 浏览文件

```python
{
    "name": "list_dir",
    "description": "List files and directories on the Android device",
    "inputSchema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "default": "/sdcard",
                "description": "Directory path on device (e.g., /sdcard, /sdcard/Download)"
            },
            "show_hidden": {
                "type": "boolean",
                "default": False,
                "description": "Show hidden files (starting with .)"
            }
        }
    }
}
```

**返回示例**:
```json
{
    "path": "/sdcard/Download",
    "entries": [
        {"name": "README.md", "type": "file", "size": 12345, "modified": "2026-02-25 18:30:00"},
        {"name": "Documents", "type": "directory", "size": 0, "modified": "2026-02-20 10:00:00"}
    ]
}
```

### 2. 下载文件 (手机 → 电脑)

```python
{
    "name": "pull_file",
    "description": "Download a file from the Android device to PC",
    "inputSchema": {
        "type": "object",
        "properties": {
            "device_path": {
                "type": "string",
                "description": "File path on device (e.g., /sdcard/Download/file.txt)"
            },
            "local_dir": {
                "type": "string",
                "default": "~/Downloads",
                "description": "Local directory to save the file"
            }
        },
        "required": ["device_path"]
    }
}
```

### 3. 上传文件 (电脑 → 手机)

```python
{
    "name": "push_file",
    "description": "Upload a file from PC to the Android device",
    "inputSchema": {
        "type": "object",
        "properties": {
            "local_path": {
                "type": "string",
                "description": "Local file path on PC"
            },
            "device_dir": {
                "type": "string",
                "default": "/sdcard/Download",
                "description": "Target directory on device"
            }
        },
        "required": ["local_path"]
    }
}
```

### 4. 安装 APK

```python
{
    "name": "install_apk",
    "description": "Install an APK file from PC to the Android device",
    "inputSchema": {
        "type": "object",
        "properties": {
            "local_path": {
                "type": "string",
                "description": "Local APK file path on PC"
            },
            "reinstall": {
                "type": "boolean",
                "default": True,
                "description": "Reinstall if app already exists"
            }
        },
        "required": ["local_path"]
    }
}
```

### 5. 删除文件

```python
{
    "name": "delete_file",
    "description": "Delete a file on the Android device",
    "inputSchema": {
        "type": "object",
        "properties": {
            "device_path": {
                "type": "string",
                "description": "File path to delete on device"
            }
        },
        "required": ["device_path"]
    }
}
```

### 6. 创建目录

```python
{
    "name": "make_dir",
    "description": "Create a directory on the Android device",
    "inputSchema": {
        "type": "object",
        "properties": {
            "device_path": {
                "type": "string",
                "description": "Directory path to create"
            }
        },
        "required": ["device_path"]
    }
}
```

### 7. 获取文件信息

```python
{
    "name": "stat_file",
    "description": "Get detailed file information on the Android device",
    "inputSchema": {
        "type": "object",
        "properties": {
            "device_path": {
                "type": "string",
                "description": "File or directory path"
            }
        },
        "required": ["device_path"]
    }
}
```

---

## 实现代码

### ADB 命令封装

```python
class FileOperations:
    """文件操作类，封装 ADB 命令"""

    def __init__(self, device_serial: Optional[str] = None):
        self._device_serial = device_serial

    def _adb_cmd(self, *args) -> list:
        """构建 ADB 命令"""
        cmd = ["adb"]
        if self._device_serial:
            cmd.extend(["-s", self._device_serial])
        cmd.extend(args)
        return cmd

    def list_dir(self, path: str, show_hidden: bool = False) -> dict:
        """列出目录内容"""
        # 使用 ls -la 获取详细信息
        cmd = self._adb_cmd("shell", "ls", "-la", path)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            raise Exception(f"Failed to list directory: {result.stderr}")

        entries = []
        for line in result.stdout.strip().split('\n')[1:]:  # 跳过 "total xxx"
            if not line.strip():
                continue

            # 解析 ls -la 输出
            # drwxrwx--- 2 root sdcard_rw 4096 2026-02-25 18:30 Documents
            parts = line.split()
            if len(parts) >= 6:
                entry = {
                    "name": parts[-1],
                    "type": "directory" if parts[0].startswith('d') else "file",
                    "permissions": parts[0],
                    "size": int(parts[4]) if parts[4].isdigit() else 0,
                    "modified": f"{parts[5]} {parts[6]}"
                }
                # 过滤隐藏文件
                if not show_hidden and entry["name"].startswith('.'):
                    continue
                entries.append(entry)

        return {"path": path, "entries": entries}

    def pull_file(self, device_path: str, local_dir: str) -> dict:
        """从设备下载文件"""
        local_dir = Path(local_dir).expanduser()
        local_dir.mkdir(parents=True, exist_ok=True)

        cmd = self._adb_cmd("pull", device_path, str(local_dir))
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            raise Exception(f"Failed to pull file: {result.stderr}")

        filename = Path(device_path).name
        local_path = local_dir / filename

        return {
            "device_path": device_path,
            "local_path": str(local_path),
            "size": local_path.stat().st_size if local_path.exists() else 0
        }

    def push_file(self, local_path: str, device_dir: str) -> dict:
        """上传文件到设备"""
        local_path = Path(local_path).expanduser()
        if not local_path.exists():
            raise Exception(f"Local file not found: {local_path}")

        cmd = self._adb_cmd("push", str(local_path), device_dir)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            raise Exception(f"Failed to push file: {result.stderr}")

        return {
            "local_path": str(local_path),
            "device_path": f"{device_dir.rstrip('/')}/{local_path.name}",
            "size": local_path.stat().st_size
        }

    def install_apk(self, local_path: str, reinstall: bool = True) -> dict:
        """安装 APK"""
        local_path = Path(local_path).expanduser()
        if not local_path.exists():
            raise Exception(f"APK file not found: {local_path}")

        cmd = self._adb_cmd("install")
        if reinstall:
            cmd.append("-r")
        cmd.append(str(local_path))

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0 or "Failure" in result.stdout:
            raise Exception(f"Failed to install APK: {result.stdout or result.stderr}")

        return {
            "apk_path": str(local_path),
            "success": True,
            "message": "APK installed successfully"
        }

    def delete_file(self, device_path: str) -> dict:
        """删除文件"""
        cmd = self._adb_cmd("shell", "rm", "-rf", device_path)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            raise Exception(f"Failed to delete: {result.stderr}")

        return {"deleted": device_path}

    def make_dir(self, device_path: str) -> dict:
        """创建目录"""
        cmd = self._adb_cmd("shell", "mkdir", "-p", device_path)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            raise Exception(f"Failed to create directory: {result.stderr}")

        return {"created": device_path}
```

### MCP 工具处理器

```python
def handle_list_dir(arguments: dict) -> dict:
    """处理 list_dir 工具调用"""
    handler = get_global_handler()
    if not handler or not handler._connected:
        return {"error": "Not connected to device"}

    path = arguments.get("path", "/sdcard")
    show_hidden = arguments.get("show_hidden", False)

    try:
        file_ops = FileOperations(handler._device_serial)
        result = file_ops.list_dir(path, show_hidden)
        return result
    except Exception as e:
        return {"error": str(e)}

def handle_pull_file(arguments: dict) -> dict:
    """处理 pull_file 工具调用"""
    handler = get_global_handler()
    if not handler or not handler._connected:
        return {"error": "Not connected to device"}

    device_path = arguments.get("device_path")
    local_dir = arguments.get("local_dir", "~/Downloads")

    if not device_path:
        return {"error": "device_path is required"}

    try:
        file_ops = FileOperations(handler._device_serial)
        result = file_ops.pull_file(device_path, local_dir)
        return result
    except Exception as e:
        return {"error": str(e)}

# 类似实现其他工具处理器...
```

---

## 添加到 TOOLS 列表

在 `scrcpy_http_mcp_server.py` 的 `TOOLS` 列表末尾添加：

```python
# 文件管理工具
{
    "name": "list_dir",
    "description": "List files and directories on the Android device",
    "inputSchema": {...}
},
{
    "name": "pull_file",
    "description": "Download a file from the Android device to PC",
    "inputSchema": {...}
},
{
    "name": "push_file",
    "description": "Upload a file from PC to the Android device",
    "inputSchema": {...}
},
{
    "name": "install_apk",
    "description": "Install an APK file from PC to the Android device",
    "inputSchema": {...}
},
{
    "name": "delete_file",
    "description": "Delete a file on the Android device",
    "inputSchema": {...}
},
{
    "name": "make_dir",
    "description": "Create a directory on the Android device",
    "inputSchema": {...}
},
{
    "name": "stat_file",
    "description": "Get detailed file information",
    "inputSchema": {...}
},
```

---

## 使用示例

### Claude Code 中的使用

```
用户: 列出手机 Download 目录下的文件
Claude: [调用 list_dir(path="/sdcard/Download")]

用户: 把手机上的 /sdcard/DCIM/photo.jpg 下载到电脑
Claude: [调用 pull_file(device_path="/sdcard/DCIM/photo.jpg", local_dir="~/Downloads")]

用户: 把电脑上的 test.apk 安装到手机
Claude: [调用 install_apk(local_path="C:/Downloads/test.apk")]
```

---

## 注意事项

### 1. 权限问题

Android 11+ 的存储权限限制：
- `/sdcard/` 是受限目录
- 应用私有目录需要 root 权限
- 建议操作 `/sdcard/Download/`, `/sdcard/DCIM/` 等公共目录

### 2. 大文件传输

- `pull_file` 和 `push_file` 默认超时 300 秒
- 对于超大文件，可能需要增加超时或实现进度回调

### 3. 网络模式

网络模式下，ADB 命令需要指定设备：
```bash
adb -s 192.168.1.100:5555 push file.txt /sdcard/
```

代码中已经通过 `self._device_serial` 处理。

---

## 扩展建议

### 1. 批量操作

```python
{
    "name": "pull_files",
    "description": "Download multiple files from device",
    "inputSchema": {
        "properties": {
            "device_paths": {"type": "array", "items": {"type": "string"}},
            "local_dir": {"type": "string"}
        }
    }
}
```

### 2. 文件搜索

```python
{
    "name": "find_files",
    "description": "Search for files on device",
    "inputSchema": {
        "properties": {
            "path": {"type": "string"},
            "pattern": {"type": "string", "description": "Glob pattern like *.jpg"}
        }
    }
}
```

### 3. 文件校验

```python
{
    "name": "get_file_hash",
    "description": "Calculate MD5/SHA hash of a file on device",
    "inputSchema": {
        "properties": {
            "device_path": {"type": "string"},
            "algorithm": {"type": "string", "enum": ["md5", "sha256"]}
        }
    }
}
```
