# 键盘输入

> 模拟按键事件和文字输入

---

## 功能清单

| 操作 | 方法 | 说明 |
|------|------|------|
| 按键 | `press_key(keycode)` | 单次按键 |
| 组合键 | `press_key(keycode, modifiers)` | Ctrl+C 等 |
| 文字输入 | `input_text(text)` | 直接输入文字 |

---

## 键码映射

### Android 键码 (常用)

| 键码 | 值 | 说明 |
|------|-----|------|
| KEYCODE_HOME | 3 | 主页键 |
| KEYCODE_BACK | 4 | 返回键 |
| KEYCODE_MENU | 82 | 菜单键 |
| KEYCODE_VOLUME_UP | 24 | 音量+ |
| KEYCODE_VOLUME_DOWN | 25 | 音量- |
| KEYCODE_POWER | 26 | 电源键 |
| KEYCODE_ENTER | 66 | 回车键 |
| KEYCODE_DEL | 67 | 退格键 |

### 键码映射文件

| 文件 | `core/keycode.py` |
|------|-------------------|
| 文件 | `core/player/video/keycode_mapping.py` |

---

## 按键消息格式

```
┌──────────┬──────────┬──────────┬──────────┐
│ type (1) │ action(1)│ keycode  │ metastate│
└──────────┴──────────┴──────────┴──────────┘

action:
  0 = DOWN
  1 = UP

metastate: (组合键标志)
  1 = SHIFT
  2 = CTRL
  4 = ALT
```

---

## 使用示例

### Python API

```python
from scrcpy_py_ddlx import Client
from scrcpy_py_ddlx.core.keycode import *

client = Client(device="device_serial")
client.start()

# 单次按键
client.control.press_key(KEYCODE_BACK)

# 组合键 (Ctrl+C)
client.control.press_key(KEYCODE_C, modifiers=[KEYMOD_CTRL])

# 文字输入 (支持中文)
client.control.input_text("你好世界")
```

### MCP 工具

```json
{
  "tool": "press_key",
  "arguments": {
    "keycode": "KEYCODE_BACK"
  }
}
```

---

## 代码位置

| 组件 | 文件 |
|------|------|
| 键码定义 | `core/keycode.py` |
| 键码映射 | `core/player/video/keycode_mapping.py` |
| 控制消息 | `core/control.py` |

---

## 文字输入

### 两种方式

1. **inject_text**: 直接注入文字，支持中文
2. **inject_keycode**: 逐字符按键，仅支持 ASCII

### 中文输入

```python
# 推荐: 直接注入
client.control.input_text("中文测试")

# 不推荐: 按键方式 (不支持中文)
```
