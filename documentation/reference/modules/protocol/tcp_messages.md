# TCP 消息格式

> **通道**: TCP 控制/文件通道
> **格式**: [type:1B][length:4B][payload:N字节]

---

## 消息头格式

```
偏移   大小   字段        说明
──────────────────────────────────
0      1      type       消息类型
1      4      length     载荷长度 (big-endian)
5      N      payload    载荷数据
──────────────────────────────────
头大小: 5 字节
```

---

## 控制消息 (客户端→服务端)

### INJECT_KEYCODE (0)

```
[type:1B][length:4B]
[action:1B][keycode:4B][repeat:4B][metastate:4B]
```

| 字段 | 大小 | 说明 |
|------|------|------|
| action | 1 | DOWN=0, UP=1 |
| keycode | 4 | Android KeyCode |
| repeat | 4 | 重复次数 |
| metastate | 4 | 修饰键状态 |

### INJECT_TEXT (1)

```
[type:1B][length:4B]
[text_length:4B][text:NB]
```

### INJECT_TOUCH_EVENT (2)

```
[type:1B][length:4B]
[action:1B][pointer_id:8B][x:4B][y:4B]
[width:4B][height:4B][pressure:4B][buttons:4B]
```

| 字段 | 大小 | 说明 |
|------|------|------|
| action | 1 | 触摸动作 |
| pointer_id | 8 | 指针 ID |
| x, y | 4+4 | 坐标 (像素) |
| width, height | 4+4 | 接触区域 |
| pressure | 4 | 压力 (0.0-1.0) |
| buttons | 4 | 按钮标志 |

### INJECT_SCROLL_EVENT (3)

```
[type:1B][length:4B]
[pointer_id:8B][x:4B][y:4B]
[width:4B][height:4B][hscroll:4B][vscroll:4B]
```

### SET_CLIPBOARD (9)

```
[type:1B][length:4B]
[sequence:4B][paste:1B][text_length:4B][text:NB]
```

| 字段 | 大小 | 说明 |
|------|------|------|
| sequence | 4 | 序列号 |
| paste | 1 | 是否模拟粘贴 |
| text | N | 剪贴板文本 |

### RESET_VIDEO (17)

```
[type:1B][length:4B]
(无载荷)
```

请求服务端发送新的关键帧 (PLI)

### SCREENSHOT (18)

```
[type:1B][length:4B]
(无载荷)
```

请求服务端截取屏幕

### PING (25) - 心跳

```
[type:1B][length:4B]
[timestamp:8B]
```

---

## 设备消息 (服务端→客户端)

### 消息头格式

```
偏移   大小   字段        说明
──────────────────────────────────
0      3      reserved   保留 (0x00 0x00 0x00)
3      1      type       消息类型
4      4      length     载荷长度 (big-endian)
8      N      payload    载荷数据
──────────────────────────────────
头大小: 8 字节
```

### CLIPBOARD (0)

```
[reserved:3B][type:1B][length:4B]
[sequence:4B][text:NB]
```

### SCREENSHOT (4)

```
[reserved:3B][type:1B][length:4B]
[jpeg_data:NB]
```

返回 JPEG 格式的截图数据

### PONG (5) - 心跳响应

```
[reserved:3B][type:1B][length:4B]
(无载荷)
```

---

## 心跳机制 (v1.3)

### 流程

```
客户端                              服务端
   │                                  │
   │ ──── PING (timestamp) ─────────> │
   │         (每 2 秒)                 │
   │                                  │
   │ <─── PONG ─────────────────────  │
   │                                  │
   │    如果 10 秒无响应               │
   │    → 判定连接断开                 │
```

### 参数

| 参数 | 值 | 说明 |
|------|-----|------|
| PING 间隔 | 2 秒 | 客户端发送频率 |
| 超时判断 | 10 秒 | 无响应判定断开 |

---

## 相关代码

| 文件 | 说明 |
|------|------|
| `core/control.py` | 控制消息编码/解码 |
| `client/client.py` | 发送控制消息 |
| `server/control/ControlMessage.java` | 服务端解析 |

---

*此文档基于协议规范生成*
