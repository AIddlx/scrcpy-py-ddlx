# 剪贴板同步

> 在 PC 和设备之间同步剪贴板内容

---

## 功能清单

| 操作 | 方法 | 说明 |
|------|------|------|
| 获取剪贴板 | `get_clipboard()` | 从设备获取剪贴板 |
| 设置剪贴板 | `set_clipboard(text)` | 设置设备剪贴板 |

---

## 消息格式

### 获取剪贴板

```
客户端 → 服务端:
┌──────────┐
│ type (1) │
│ = 7      │
└──────────┘

服务端 → 客户端:
┌──────────┬──────────┬──────────┐
│ type (1) │ length(4)│ text     │
│ = 7      │          │ (UTF-8)  │
└──────────┴──────────┴──────────┘
```

### 设置剪贴板

```
客户端 → 服务端:
┌──────────┬──────────┬──────────┬──────────┐
│ type (1) │ sequence │ length(4)│ text     │
│ = 8      │ (4)      │          │ (UTF-8)  │
└──────────┴──────────┴──────────┴──────────┘
```

---

## 使用示例

### Python API

```python
from scrcpy_py_ddlx import Client

client = Client(device="device_serial")
client.start()

# 获取设备剪贴板
text = client.control.get_clipboard()
print(f"设备剪贴板: {text}")

# 设置设备剪贴板
client.control.set_clipboard("从 PC 复制的文字")
```

### MCP 工具

```json
// 获取剪贴板
{
  "tool": "get_clipboard",
  "arguments": {}
}

// 设置剪贴板
{
  "tool": "set_clipboard",
  "arguments": {
    "text": "要同步的文字"
  }
}
```

---

## 代码位置

| 组件 | 文件 |
|------|------|
| 客户端控制 | `core/control.py` |
| 设备消息 | `core/device_msg.py` |
| 服务端处理 | `wrappers/ClipboardManager.java` |

---

## 注意事项

1. **编码**: 使用 UTF-8 编码
2. **长度限制**: 建议不超过 1MB
3. **同步策略**: 手动触发，非自动同步
