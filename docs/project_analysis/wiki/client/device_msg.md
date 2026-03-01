# DeviceMessageReceiver - 设备消息接收器

> **路径**: `scrcpy_py_ddlx/core/device_msg.py`
> **职责**: 接收和处理来自 Android 设备的消息

---

## 枚举定义

### DeviceMessageType

| 值 | 名称 | 说明 |
|----|------|------|
| 0 | CLIPBOARD | 剪贴板内容同步 |
| 1 | ACK_CLIPBOARD | 剪贴板确认 |
| 2 | UHID_OUTPUT | UHID 输出数据 |
| 3 | APP_LIST | 应用列表 |
| 4 | SCREENSHOT | 截图数据 (JPEG) |
| 5 | PONG | 心跳响应 |
| 6 | FILE_CHANNEL_INFO | 文件通道信息 |

---

## 数据类

### ClipboardEvent

| 字段 | 类型 | 说明 |
|------|------|------|
| `text` | str | 剪贴板文本 |
| `sequence` | int | 序列号 (用于 ACK) |

### UHIDOutputEvent

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | UHID 设备 ID |
| `data` | bytes | 输出数据 |
| `size` | int | 数据大小 |

### ReceiverCallbacks

| 字段 | 类型 | 说明 |
|------|------|------|
| `on_clipboard` | Callable[[str, int], None] | 剪贴板回调 |
| `on_uhid_output` | Callable[[int, bytes, int], None] | UHID 回调 |
| `on_app_list` | Callable[[List[Dict]], None] | 应用列表回调 |
| `on_screenshot` | Callable[[bytes], None] | 截图回调 |
| `on_pong` | Callable[[int], None] | 心跳响应回调 |
| `on_file_channel_info` | Callable[[int, int], None] | 文件通道回调 |

---

## DeviceMessageReceiver 类

**职责**: 接收线程，从控制 socket 读取设备消息

**线程**: 独立接收线程 "DeviceReceiver"

**参考**: 官方 scrcpy `app/src/receiver.c`

---

## 常量

| 常量 | 值 | 说明 |
|------|-----|------|
| `DEVICE_MSG_MAX_SIZE` | 256KB | 最大消息大小 |

---

## 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `_socket` | Socket | 控制 socket |
| `_callbacks` | ReceiverCallbacks | 回调函数集 |
| `_buffer_size` | int | 缓冲区大小 |
| `_thread` | Thread | 接收线程 |
| `_stopped` | Event | 停止标志 |

---

## 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `start` | - | - | 启动接收线程 |
| `stop` | - | - | 停止接收线程 |

---

## 消息格式

### CLIPBOARD (type=0)

```
[type: 1B] [length: 4B] [text: NB]
```

### ACK_CLIPBOARD (type=1)

```
[type: 1B] [sequence: 8B]
```

### UHID_OUTPUT (type=2)

```
[type: 1B] [id: 2B] [size: 2B] [data: NB]
```

### APP_LIST (type=3)

```
[type: 1B] [count: 2B]
  For each app:
    [system: 1B] [name_len: 2B] [name: NB] [pkg_len: 2B] [package: MB]
```

### SCREENSHOT (type=4)

```
[type: 1B] [length: 4B] [jpeg_data: NB]
```

### PONG (type=5)

```
[type: 1B] [timestamp: 8B]
```

### FILE_CHANNEL_INFO (type=6)

```
[type: 1B] [port: 2B] [session_id: 4B]
```

---

## 接收循环

```python
def _run_receiver_loop():
    buffer = bytearray(BUFFER_SIZE)
    offset = 0

    while not stopped:
        chunk = socket.recv(4096)
        buffer[offset:offset+len(chunk)] = chunk
        offset += len(chunk)

        # 处理缓冲区中的完整消息
        while offset > 0:
            consumed = _process_buffer(buffer, offset)
            if consumed > 0:
                memmove(buffer, buffer + consumed, offset - consumed)
                offset -= consumed
            else:
                break  # 等待更多数据
```

---

## 消息处理流程

```
[Control Socket]
    │
    ▼
recv() ──→ [buffer]
    │
    ▼
_process_buffer()
    │
    ├─→ type=0: _process_clipboard()
    │
    ├─→ type=1: _process_ack_clipboard()
    │
    ├─→ type=2: _process_uhid_output()
    │
    ├─→ type=3: _process_app_list()
    │
    ├─→ type=4: _process_screenshot()
    │
    ├─→ type=5: _process_pong()
    │
    └─→ type=6: _process_file_channel_info()
              │
              ▼
         [callback]
```

---

## 应用列表解析

```python
def _process_app_list(buffer, size):
    count = struct.unpack(">H", buffer[1:3])[0]
    offset = 3
    apps = []

    for i in range(count):
        system = buffer[offset]
        name_len = struct.unpack(">H", buffer[offset+1:offset+3])[0]
        offset += 3

        name = buffer[offset:offset+name_len].decode('utf-8')
        offset += name_len

        pkg_len = struct.unpack(">H", buffer[offset:offset+2])[0]
        offset += 2

        package = buffer[offset:offset+pkg_len].decode('utf-8')
        offset += pkg_len

        apps.append({
            "name": name,
            "package": package,
            "system": bool(system)
        })

    callbacks.on_app_list(apps)
```

---

## 心跳机制

```python
# 客户端发送 PING
msg = ControlMessage(TYPE_PING)
msg.set_ping(timestamp)
control_queue.put(msg)

# 服务端响应 PONG
# DeviceMessageReceiver 接收
def _process_pong(buffer, size):
    timestamp = struct.unpack(">Q", buffer[1:9])[0]
    callbacks.on_pong(timestamp)  # 计算往返延迟
```

---

## 使用示例

```python
def on_clipboard(text, sequence):
    print(f"Clipboard: {text}")

def on_app_list(apps):
    for app in apps:
        print(f"App: {app['name']} ({app['package']})")

callbacks = ReceiverCallbacks(
    on_clipboard=on_clipboard,
    on_app_list=on_app_list,
)

receiver = DeviceMessageReceiver(
    socket=control_socket,
    callbacks=callbacks,
)
receiver.start()
```

---

## DeviceMessageParser 类

**职责**: 解析设备信息消息

### parse_device_info()

```
Device info format (from video socket):
[device_name: 64B] (null-terminated)
```

---

## 依赖关系

```
DeviceMessageReceiver
    │
    ├──→ socket
    │
    ├──→ struct (解析)
    │
    └──→ protocol.py (常量)

DeviceMessageParser
    │
    └──→ protocol.py (常量)
```

**被依赖**:
- client.py (创建和使用)

---

*此文档基于代码分析生成*
