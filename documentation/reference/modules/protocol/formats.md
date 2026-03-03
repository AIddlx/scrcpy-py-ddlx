# 数据格式详解

> **来源**: 协议分析 Agent
> **状态**: ✅ 完成

---

## 1. 完整 UDP 数据包结构

### 非分片包 (小帧 < 65KB)

```
┌────────────────────┬────────────────────┬─────────────────┐
│   UDP Header (24B) │ Scrcpy Header (12B)│  Payload (NB)   │
└────────────────────┴────────────────────┴─────────────────┘
```

### 分片包 (大帧 > 65KB)

```
┌────────────────────┬──────────────┬────────────────────┬──────────────┐
│   UDP Header (24B) │ FragIdx (4B) │ Scrcpy Header (12B)│ Fragment (NB)│
└────────────────────┴──────────────┴────────────────────┴──────────────┘
  ... 后续分片无 Scrcpy Header
```

---

## 2. 视频配置包格式

### ADB 隧道模式 (原始字节)

```
codec_id: 4B (uint32, BE)
width:    4B (uint32, BE)
height:   4B (uint32, BE)
总计:     12B (无 scrcpy 头部)
```

### 网络 UDP 模式

```
[UDP Header: 24B]
  sequence:    4B
  timestamp:   8B
  flags:       4B (bit 1 = CONFIG)
  send_time_ns: 8B

[Scrcpy Header: 12B]
  pts_flags:   8B (0x8000000000000000)
  size:        4B (12)

[Config Payload: 12B]
  codec_id:    4B
  width:       4B
  height:      4B

总计: 48B
```

---

## 3. 设备能力信息格式 (TCP)

```
偏移量   字段                    大小      类型
------   ----                    ----      ----
0        screen_width            4        uint32
4        screen_height           4        uint32
8        video_encoder_count     1        uint8
9        video_encoders          N*12     bytes
         - codec_id              4        uint32
         - flags                 4        uint32
         - priority              4        uint32
9+N*12   audio_encoder_count     1        uint8
10+N*12  audio_encoders          M*12     bytes
```

---

## 4. 客户端配置格式 (TCP, 32 字节)

```
偏移量   字段              大小      类型
------   ----              ----      ----
0        video_codec_id    4        uint32
4        audio_codec_id    4        uint32
8        video_bitrate     4        uint32
12       audio_bitrate     4        uint32
16       max_fps           4        uint32
20       config_flags      4        uint32
24       reserved          4        uint32
28       i_frame_interval  4        float (IEEE 754 BE)
```

### config_flags 位定义

| Bit | 说明 |
|-----|------|
| 0 | 启用音频 |
| 1 | 启用视频 |
| 2 | CBR 模式 (0=VBR, 1=CBR) |
| 3 | 启用视频 FEC |
| 4 | 启用音频 FEC |

---

## 5. 心跳消息格式 (v1.3)

### PING (客户端 → 服务端)

```
类型:      1B = 25 (0x19)
timestamp: 8B (int64, BE, 微秒)
总大小:    9B
```

### PONG (服务端 → 客户端)

```
类型:      1B = 5 (0x05)
timestamp: 8B (int64, BE, 回显 PING 时间戳)
总大小:    9B
```

---

## 6. FEC 数据包格式

### FEC 数据包 (flags bit 2 = 1)

```
[UDP Header: 24B, flags |= 0x04]
[FEC Group Header: 4B]
  group_id:    2B (uint16, BE)
  packet_idx:  1B (uint8)
  total:       1B (uint8)
[Scrcpy Header: 12B]
[Payload: NB]
```

### FEC 校验包 (flags bit 3 = 1)

```
[UDP Header: 24B, flags |= 0x08]
[FEC Parity Header: 4B]
  group_id:    2B (uint16, BE)
  parity_idx:  1B (uint8)
  total:       1B (uint8)
[Parity Data: NB]
```

### FEC 校验包分片格式

```
[UDP Header: 24B]
[Fragment Index: 4B]
[FEC Parity Header: 5B]
  group_id:      2B (uint16, BE)
  parity_idx:    1B (uint8)
  total_data:    1B (uint8)
  total_parity:  1B (uint8)
[Parity Fragment: NB]
```

---

## 7. 触摸事件格式

### INJECT_TOUCH_EVENT

```
[type: 1B][length: 4B]
[action: 1B][pointer_id: 8B][x: 4B][y: 4B]
[width: 4B][height: 4B][pressure: 4B][buttons: 4B]
```

| 字段 | 大小 | 说明 |
|------|------|------|
| action | 1 | DOWN=0, UP=1, MOVE=2 |
| pointer_id | 8 | 指针 ID |
| x, y | 4+4 | 坐标 (像素) |
| width, height | 4+4 | 接触区域 |
| pressure | 4 | 压力 (0.0-1.0 × 65536) |
| buttons | 4 | 按钮标志 |

---

## 8. 剪贴板格式

### SET_CLIPBOARD

```
[type: 1B][length: 4B]
[sequence: 4B][paste: 1B][text_length: 4B][text: NB]
```

| 字段 | 大小 | 说明 |
|------|------|------|
| sequence | 4 | 序列号 |
| paste | 1 | 是否模拟粘贴 |
| text | N | UTF-8 文本 |

### CLIPBOARD (设备响应)

```
[reserved: 3B][type: 1B][length: 4B]
[sequence: 4B][text: NB]
```

---

## 9. 截图格式

### 请求

```
[type: 1B = 18][length: 4B = 0]
```

### 响应

```
[reserved: 3B][type: 1B = 4][length: 4B]
[jpeg_data: NB]
```

返回 JPEG 格式的截图数据

---

## 10. 字节序说明

**所有多字节字段使用 Big-Endian (网络字节序)**

```python
# Python 示例
import struct

# 编码
data = struct.pack('>I', value)  # 4字节 uint32 BE

# 解码
value = struct.unpack('>I', data)[0]
```

---

*此文档基于协议分析Agent生成*
