# protocol.py - 协议常量

> **路径**: `scrcpy_py_ddlx/core/protocol.py`
> **职责**: 定义所有协议级常量、枚举和辅助函数

---

## 编码器 ID

### CodecId (IntEnum)

| 常量 | 值 | ASCII | 说明 |
|------|-----|-------|------|
| H264 | 0x68323634 | "h264" | H.264/AVC |
| H265 | 0x68323635 | "h265" | H.265/HEVC |
| AV1 | 0x00617631 | "av1" | AV1 |
| OPUS | 0x6f707573 | "opus" | Opus 音频 |
| AAC | 0x00616163 | "aac" | AAC 音频 |
| FLAC | 0x666c6163 | "flac" | FLAC 音频 |
| RAW | 0x00726177 | "raw" | RAW 音频 |

### 辅助函数

| 函数 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `codec_id_to_string` | codec_id: int | str | 数字ID转字符串 |
| `codec_id_from_string` | codec_str: str | int | 字符串转数字ID |

---

## 数据包标志

### Packet Flags

| 常量 | 值 | 说明 |
|------|-----|------|
| `PACKET_FLAG_CONFIG` | 1 << 63 | 配置包 (bit 63) |
| `PACKET_FLAG_KEY_FRAME` | 1 << 62 | 关键帧 (bit 62) |
| `PACKET_PTS_MASK` | (1<<62)-1 | PTS 掩码 (低62位) |
| `PACKET_HEADER_SIZE` | 12 | 包头大小 |

### 包头格式 (12字节)

```
字节 7    字节 6-0
┌────┬─────────────────────────────────────────────────────┐
│ CK │                    PTS (62 bits)                     │
└────┴─────────────────────────────────────────────────────┘
  ││
  │└─ Key frame (bit 62)
  └── Config packet (bit 63)
```

---

## 控制消息类型 (客户端→服务端)

### ControlMessageType (IntEnum)

| 值 | 常量 | 说明 |
|-----|------|------|
| 0 | INJECT_KEYCODE | 注入按键 |
| 1 | INJECT_TEXT | 注入文本 |
| 2 | INJECT_TOUCH_EVENT | 注入触摸 |
| 3 | INJECT_SCROLL_EVENT | 注入滚动 |
| 4 | BACK_OR_SCREEN_ON | 返回/点亮屏幕 |
| 5 | EXPAND_NOTIFICATION_PANEL | 展开通知栏 |
| 6 | EXPAND_SETTINGS_PANEL | 展开设置栏 |
| 7 | COLLAPSE_PANELS | 收起面板 |
| 8 | GET_CLIPBOARD | 获取剪贴板 |
| 9 | SET_CLIPBOARD | 设置剪贴板 |
| 10 | SET_DISPLAY_POWER | 设置显示电源 |
| 11 | ROTATE_DEVICE | 旋转设备 |
| 12 | UHID_CREATE | 创建 UHID 设备 |
| 13 | UHID_INPUT | UHID 输入 |
| 14 | UHID_DESTROY | 销毁 UHID 设备 |
| 15 | OPEN_HARD_KEYBOARD_SETTINGS | 打开键盘设置 |
| 16 | START_APP | 启动应用 |
| 17 | RESET_VIDEO | 重置视频 (PLI) |
| 18 | SCREENSHOT | 截图请求 |
| 19 | GET_APP_LIST | 获取应用列表 |
| 20 | REQUEST_VIDEO_FRAME | 请求单帧 |
| 21 | START_VIDEO | 启动视频流 |
| 22 | STOP_VIDEO | 停止视频流 |
| 23 | START_AUDIO | 启动音频流 |
| 24 | STOP_AUDIO | 停止音频流 |
| 25 | PING | 心跳请求 |
| 26 | OPEN_FILE_CHANNEL | 打开文件通道 |

---

## 设备消息类型 (服务端→客户端)

### DeviceMessageType (IntEnum)

| 值 | 常量 | 说明 |
|-----|------|------|
| 0 | CLIPBOARD | 剪贴板内容 |
| 1 | ACK_CLIPBOARD | 剪贴板确认 |
| 2 | UHID_OUTPUT | UHID 输出 |
| 3 | APP_LIST | 应用列表 |
| 4 | SCREENSHOT | 截图数据 (JPEG) |
| 5 | PONG | 心跳响应 |
| 6 | FILE_CHANNEL_INFO | 文件通道信息 |

---

## Android 按键事件

### AndroidKeyEventAction (IntEnum)

| 值 | 常量 | 说明 |
|-----|------|------|
| 0 | DOWN | 按下 |
| 1 | UP | 释放 |
| 2 | MULTIPLE | 多次 |

---

## Android 触摸事件

### AndroidMotionEventAction (IntEnum)

| 值 | 常量 | 说明 |
|-----|------|------|
| 0 | DOWN | 按下 |
| 1 | UP | 抬起 |
| 2 | MOVE | 移动 |
| 3 | CANCEL | 取消 |
| 4 | OUTSIDE | 外部 |
| 5 | POINTER_DOWN | 多点按下 |
| 6 | POINTER_UP | 多点抬起 |
| 7 | HOVER_MOVE | 悬停移动 |
| 8 | SCROLL | 滚动 |
| 9 | HOVER_ENTER | 悬停进入 |
| 10 | HOVER_EXIT | 悬停离开 |
| 11 | BUTTON_PRESS | 按钮按下 |
| 12 | BUTTON_RELEASE | 按钮释放 |

### AndroidMotionEventButtons (IntEnum)

| 常量 | 值 | 说明 |
|------|-----|------|
| PRIMARY | 1 << 0 | 主按钮 (左键) |
| SECONDARY | 1 << 1 | 次按钮 (右键) |
| TERTIARY | 1 << 2 | 第三按钮 (中键) |
| BACK | 1 << 3 | 后退按钮 |
| FORWARD | 1 << 4 | 前进按钮 |
| STYLUS_PRIMARY | 1 << 5 | 触笔主按钮 |
| STYLUS_SECONDARY | 1 << 6 | 触笔次按钮 |

---

## Android 元状态

### AndroidMetaState (IntEnum)

| 常量 | 值 | 说明 |
|------|-----|------|
| ALT_LEFT | 0x02 | 左 Alt |
| ALT_RIGHT | 0x04 | 右 Alt |
| SHIFT_LEFT | 0x10 | 左 Shift |
| SHIFT_RIGHT | 0x20 | 右 Shift |
| SYM | 0x40 | 符号键 |
| FUNCTION | 0x80 | 功能键 |
| CAPS_LOCK | 0x100 | 大写锁定 |
| NUM_LOCK | 0x200 | 数字锁定 |
| SCROLL_LOCK | 0x400 | 滚动锁定 |

---

## 特殊指针 ID

| 常量 | 值 | 说明 |
|------|-----|------|
| `POINTER_ID_MOUSE` | -1 | 鼠标事件 |
| `POINTER_ID_GENERIC_FINGER` | -2 | 通用触摸 |
| `POINTER_ID_VIRTUAL_FINGER` | -3 | 虚拟手指 (缩放) |

---

## 依赖关系

```
protocol.py
    │
    └──→ 被所有需要协议常量的模块引用:
         ├── client/client.py
         ├── core/control.py
         ├── core/demuxer/*.py
         └── ...
```

---

## 与服务端一致性

| 定义 | 客户端 (Python) | 服务端 (Java) |
|------|----------------|---------------|
| 控制消息类型 | ControlMessageType | ControlMessage.Type |
| 设备消息类型 | DeviceMessageType | DeviceMessage.Type |
| 编码器ID | CodecId | Codec.id |

---

*此文档基于代码分析生成*
