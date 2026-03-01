# 控制功能

> 触摸、键盘、剪贴板等控制命令

---

## 功能清单

| 功能 | 文件 | 说明 | 状态 |
|------|------|------|------|
| [触摸控制](touch.md) | `core/control.py` | 点击/滑动/长按 | ✅ |
| [键盘输入](keyboard.md) | `core/control.py` | 按键/组合键 | ✅ |
| [剪贴板同步](clipboard.md) | `core/control.py` | 获取/设置剪贴板 | ✅ |
| 文字输入 | `core/control.py` | 中文输入支持 | ✅ |
| 导航键 | `core/control.py` | 返回/主页/最近 | ✅ |
| 设备消息 | `core/device_msg.py` | 设备→客户端消息 | ✅ |

---

## 控制消息类型

| 类型 | 值 | 说明 |
|------|-----|------|
| TYPE_INJECT_KEYCODE | 0 | 按键事件 |
| TYPE_INJECT_TEXT | 1 | 文字输入 |
| TYPE_INJECT_TOUCH_EVENT | 2 | 触摸事件 |
| TYPE_INJECT_SCROLL_EVENT | 3 | 滚动事件 |
| TYPE_BACK_OR_SCREEN_ON | 4 | 返回/唤醒屏幕 |
| TYPE_EXPAND_NOTIFICATION_PANEL | 5 | 展开通知 |
| TYPE_COLLAPSE_PANELS | 6 | 收起面板 |
| TYPE_GET_CLIPBOARD | 7 | 获取剪贴板 |
| TYPE_SET_CLIPBOARD | 8 | 设置剪贴板 |
| TYPE_SET_SCREEN_POWER_MODE | 9 | 屏幕 电源控制 |

---

## 数据流

```
┌──────────┐    TCP 控制    ┌──────────┐
│  Python  │ ─────────────► │  Android │
│  Client  │    :27183      │  Server  │
└──────────┘ ◄───────────── └──────────┘
                  │
                  ▼
         ┌──────────────┐
         │ Controller   │
         │ (InputManager)│
         └──────────────┘
```

---

## 相关文档

- [触摸控制](touch.md)
- [键盘输入](keyboard.md)
- [剪贴板同步](clipboard.md)
