# MCP 工具总览

> 47+ 工具的完整清单

---

## 工具分类

### 连接管理 (5 个)

| 工具 | 说明 |
|------|------|
| `connect` | 连接设备 |
| `disconnect` | 断开连接 |
| `push_server` | 推送服务端 |
| `list_devices` | 列出设备 |
| `get_connection_info` | 获取连接信息 |

### 屏幕操作 (8 个)

| 工具 | 说明 |
|------|------|
| `screenshot` | 截图 |
| `get_state` | 获取状态 |
| `rotate` | 旋转屏幕 |
| `set_display_power` | 开关屏幕 |
| `expand_notification_panel` | 展开通知 |
| `collapse_panels` | 收起面板 |
| `expand_settings_panel` | 展开设置 |
| `get_screen_resolution` | 获取分辨率 |

### 输入控制 (10 个)

| 工具 | 说明 |
|------|------|
| `tap` | 点击 |
| `swipe` | 滑动 |
| `long_press` | 长按 |
| `double_tap` | 双击 |
| `type_text` | 输入文字 |
| `press_key` | 按键 |
| `press_back` | 返回键 |
| `press_home` | 主页键 |
| `press_recent` | 最近任务 |
| `scroll` | 滚动 |

### 文件操作 (6 个)

| 工具 | 说明 |
|------|------|
| `list_files` | 列出文件 |
| `push_file` | 推送文件 |
| `pull_file` | 拉取文件 |
| `delete_file` | 删除文件 |
| `mkdir` | 创建目录 |
| `download_file` | 下载文件 |

### 应用管理 (5 个)

| 工具 | 说明 |
|------|------|
| `list_apps` | 列出应用 |
| `start_app` | 启动应用 |
| `stop_app` | 停止应用 |
| `install_apk` | 安装 APK |
| `uninstall_app` | 卸载应用 |

### 剪贴板 (3 个)

| 工具 | 说明 |
|------|------|
| `get_clipboard` | 获取剪贴板 |
| `set_clipboard` | 设置剪贴板 |
| `sync_clipboard` | 同步剪贴板 |

### 录制 (4 个)

| 工具 | 说明 |
|------|------|
| `start_recording` | 开始录制 |
| `stop_recording` | 停止录制 |
| `start_audio_recording` | 开始音频录制 |
| `stop_audio_recording` | 停止音频录制 |

### 高级功能 (6+ 个)

| 工具 | 说明 |
|------|------|
| `start_tcpdump` | 开始抓包 |
| `stop_tcpdump` | 停止抓包 |
| `open_url` | 打开 URL |
| `send_intent` | 发送 Intent |
| `set_brightness` | 设置亮度 |
| `set_volume` | 设置音量 |

---

## 坐标系统

所有坐标工具遵循统一坐标系:

```
原点 (0, 0): 屏幕左上角

竖屏 (width < height):
  ┌─────────────┐
  │ (0,0)       │
  │             │
  │    中心     │
  │             │
  │       (w-1, │
  │        h-1) │
  └─────────────┘

横屏 (width > height):
  ┌───────────────────────┐
  │ (0,0)            (w-1,0)│
  │                       │
  │         中心          │
  │                       │
  │ (0,h-1)        (w-1,h-1)│
  └───────────────────────┘
```

**重要**: 使用坐标工具前，先调用 `get_state()` 获取当前宽高和方向。

---

## 工具调用示例

### connect

```json
{
  "name": "connect",
  "arguments": {
    "connection_mode": "adb_tunnel",
    "device_id": "auto",
    "codec": "auto",
    "bitrate": 8000000,
    "max_fps": 60
  }
}
```

### tap

```json
{
  "name": "tap",
  "arguments": {
    "x": 540,
    "y": 1200
  }
}
```

### screenshot

```json
{
  "name": "screenshot",
  "arguments": {
    "save_path": "screenshot.png"
  }
}
```

---

## 详细文档

- [connection.md](connection.md) - 连接管理工具
- [screen.md](screen.md) - 屏幕操作工具
- [input.md](input.md) - 输入控制工具
- [file.md](file.md) - 文件操作工具
- [app.md](app.md) - 应用管理工具
- [advanced.md](advanced.md) - 高级功能工具
