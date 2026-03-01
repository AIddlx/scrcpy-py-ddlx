# ADB 文件操作

> 通过 ADB 进行文件传输

---

## 功能清单

| 操作 | ADB 命令 | 说明 |
|------|---------|------|
| 列出目录 | `adb shell ls` | 列出目录内容 |
| 上传文件 | `adb push` | 推送文件到设备 |
| 下载文件 | `adb pull` | 从设备拉取文件 |
| 删除文件 | `adb shell rm` | 删除设备文件 |

---

## 代码位置

| 组件 | 文件 |
|------|------|
| 文件操作封装 | `core/file/file_ops.py` |
| ADB 命令封装 | `core/adb.py` |

---

## 实现细节

### 列出目录

```python
def list_dir(self, path: str) -> List[FileInfo]:
    """列出目录内容"""
    # adb shell ls -la <path>
    # 解析输出返回文件列表
```

### 上传文件

```python
def push_file(self, local: str, remote: str):
    """上传文件"""
    # adb push <local> <remote>
```

### 下载文件

```python
def pull_file(self, remote: str, local: str):
    """下载文件"""
    # adb pull <remote> <local>
```

---

## 注意事项

1. **权限**: 某些目录需要 root 权限
2. **路径**: 使用 Unix 风格路径 (`/`)
3. **编码**: 文件名使用 UTF-8
