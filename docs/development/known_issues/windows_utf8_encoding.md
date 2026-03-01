# Windows UTF-8 编码修复

## 问题描述

在 Windows 的 CMD/PowerShell 中，MCP 响应中的中文文件名显示为乱码（如 `鏂囦欢澶瑰浘` 而不是 `文件夹图`）。

## 原因分析

### 1. adb shell 输出编码

Android 系统使用 UTF-8 作为默认编码，`adb shell ls` 返回的文件名是 UTF-8 编码的字节。

### 2. Python subprocess 默认行为

在 Windows 上，`subprocess.run(text=True)` 使用系统默认编码（GBK/CP936）解码输出：

```
adb 返回 UTF-8 字节 → Python 用 GBK 解码 → 乱码
```

### 3. JSON 响应编码

Starlette 默认的 JSONResponse 使用 `ensure_ascii=True`，将非 ASCII 字符转义为 `\uXXXX` 格式。虽然这是有效的 JSON，但：
- 没有明确声明 `charset=utf-8`
- 某些客户端可能错误解析

## 解决方案

### 1. 修复 adb 输出解码

**文件**: `scrcpy_py_ddlx/core/adb.py`

```python
result = subprocess.run(
    cmd,
    capture_output=capture_output,
    text=capture_output,
    encoding='utf-8' if capture_output else None,  # 强制 UTF-8
    errors='replace' if capture_output else None,
    timeout=timeout,
    check=False,
)
```

### 2. 修复 JSON 响应编码

**文件**: `scrcpy_http_mcp_server.py`

```python
class JSONResponse(StarletteJSONResponse):
    """自定义 JSONResponse，确保 UTF-8 编码支持"""

    def __init__(self, content, status_code=200, headers=None, media_type=None):
        # 明确指定 charset=utf-8
        if media_type is None:
            media_type = "application/json; charset=utf-8"
        super().__init__(content, status_code=status_code, headers=headers, media_type=media_type)

    def render(self, content):
        import json
        return json.dumps(
            content,
            ensure_ascii=False,  # 不转义中文为 \uXXXX
            indent=None,
            separators=(",", ":")
        ).encode("utf-8")
```

## 验证方法

```powershell
# 无需设置 chcp 65001，直接执行
curl.exe -s -X POST http://127.0.0.1:3359/mcp -H "Content-Type: application/json" -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "list_dir", "arguments": {"path": "/sdcard"}}}'
```

## 关键经验

1. **Android 使用 UTF-8**：adb shell 返回的数据始终是 UTF-8 编码
2. **Windows 默认 GBK**：Python subprocess 在 Windows 上默认使用系统编码
3. **明确指定编码**：不要依赖系统默认值，在 I/O 边界明确指定 UTF-8
4. **JSON charset 声明**：HTTP 响应头明确声明 `charset=utf-8` 帮助客户端正确解析

## 调试技巧

检查原始字节确定实际编码：

```python
import subprocess
result = subprocess.run(['adb', 'shell', 'ls', '/sdcard'], capture_output=True)
raw = result.stdout
for line in raw.split(b'\n'):
    if any(b > 127 for b in line):
        print('Hex:', line.hex())
        print('UTF-8:', line.decode('utf-8', errors='replace'))
        print('GBK:', line.decode('gbk', errors='replace'))
```

---

**状态**: ✅ 已修复
**影响版本**: Windows 平台
**创建日期**: 2026-02-28
