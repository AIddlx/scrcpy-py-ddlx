# protocol.py

> **文件**: `core/protocol.py`
> **功能**: 协议常量和枚举定义

---

## 概述

`protocol.py` 定义了客户端与服务端通信所需的所有协议常量。

---

## 编解码器 ID

```python
class CodecId(IntEnum):
    H264 = 0x68323634  # "h264"
    H265 = 0x68323635  # "h265"
    AV1 = 0x00617631   # "av1"
    OPUS = 0x6f707573  # "opus"
    AAC = 0x00616163   # "aac"
    FLAC = 0x666c6163  # "flac"
    RAW = 0x00726177   # "raw"
```

### 转换函数

```python
# ID → 字符串
codec_id_to_string(0x68323634)  # → "h264"

# 字符串 → ID
codec_id_from_string("h264")    # → 0x68323634
```

---

## TCP 数据包标志

```python
# 包头: 12 字节
# [PTS + flags: 8B][size: 4B]

PACKET_FLAG_CONFIG: Final[int] = 1 << 63    # 配置包
PACKET_FLAG_KEY_FRAME: Final[int] = 1 << 62 # 关键帧
PACKET_PTS_MASK: Final[int] = PACKET_FLAG_KEY_FRAME - 1  # PTS 掩码
```

---

## 控制消息类型 (Client → Server)

```python
class ControlMessageType(IntEnum):
    INJECT_KEYCODE = 0        # 按键
    INJECT_TEXT = 1           # 文字输入
    INJECT_TOUCH_EVENT = 2    # 触摸
    INJECT_SCROLL_EVENT = 3   # 滚动
    BACK_OR_SCREEN_ON = 4     # 返回/唤醒
    EXPAND_NOTIFICATION_PANEL = 5
    EXPAND_SETTINGS_PANEL = 6
    COLLAPSE_PANELS = 7
    GET_CLIPBOARD = 8
    SET_CLIPBOARD = 9
    SET_DISPLAY_POWER = 10
    ROTATE_DEVICE = 11
    UHID_CREATE = 12
    UHID_INPUT = 13
    UHID_DESTROY = 14
    START_APP = 16
    RESET_VIDEO = 17          # PLI 请求
    SCREENSHOT = 18
    GET_APP_LIST = 19
    REQUEST_VIDEO_FRAME = 20
    START_VIDEO = 21
    STOP_VIDEO = 22
    START_AUDIO = 23
    STOP_AUDIO = 24
    PING = 25                 # 心跳
    OPEN_FILE_CHANNEL = 26
```

---

## 设备消息类型 (Server → Client)

```python
class DeviceMessageType(IntEnum):
    CLIPBOARD = 0
    ACK_CLIPBOARD = 1
    UHID_OUTPUT = 2
    APP_LIST = 3
    SCREENSHOT = 4
    PONG = 5                  # 心跳响应
    FILE_CHANNEL_INFO = 6
```

---

## UDP 协议常量

### UDP Header (24 字节)

```
[seq: 4B][timestamp: 8B][flags: 4B][send_time_ns: 8B]
```

### UDP 标志位

```python
UDP_FLAG_KEY_FRAME: Final[int] = 1 << 0
UDP_FLAG_CONFIG: Final[int] = 1 << 1
UDP_FLAG_FEC_DATA: Final[int] = 1 << 2
UDP_FLAG_FEC_PARITY: Final[int] = 1 << 3
UDP_FLAG_FRAGMENTED: Final[int] = 1 << 31
```

---

## 认证消息类型 (v1.4)

```python
TYPE_CHALLENGE: Final[int] = 0xF0     # Server → Client
TYPE_RESPONSE: Final[int] = 0xF1      # Client → Server
TYPE_AUTH_RESULT: Final[int] = 0xF2   # Server → Client

AUTH_KEY_SIZE: Final[int] = 32        # 256 bits
AUTH_CHALLENGE_SIZE: Final[int] = 32
AUTH_RESPONSE_SIZE: Final[int] = 32
```

---

## 工具函数

```python
# 检查包类型
is_config_packet(pts_flags)   # 是否配置包
is_key_frame(pts_flags)       # 是否关键帧

# 提取 PTS
extract_pts(pts_flags)        # 获取时间戳

# 格式化输出
pts_flags_to_string(pts_flags)  # 人类可读格式
```

---

## 大小限制

```python
CONTROL_MSG_MAX_SIZE: Final[int] = 1 << 18  # 256KB
DEVICE_MSG_MAX_SIZE: Final[int] = 1 << 18   # 256KB
CONTROL_MSG_INJECT_TEXT_MAX_LENGTH: Final[int] = 300
DEVICE_NAME_FIELD_LENGTH: Final[int] = 64
```

---

## 相关文档

- [stream.md](stream.md) - 流解析器
- [constants.md](../protocol/constants.md) - 协议常量详解
- [PROTOCOL_SPEC.md](../../../PROTOCOL_SPEC.md) - 完整协议规范
