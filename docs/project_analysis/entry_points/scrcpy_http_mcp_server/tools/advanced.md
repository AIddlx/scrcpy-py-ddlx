# 高级功能工具

> 录制、剪贴板、调试等

---

## 剪贴板工具

### get_clipboard

获取设备剪贴板内容。

```json
{
  "name": "get_clipboard"
}
```

返回:
```json
{
  "success": true,
  "text": "clipboard content"
}
```

### set_clipboard

设置设备剪贴板内容。

```json
{
  "name": "set_clipboard",
  "arguments": {
    "text": "new clipboard content"
  }
}
```

### sync_clipboard

同步剪贴板 (双向)。

```json
{
  "name": "sync_clipboard",
  "arguments": {
    "direction": "to_device | from_device"
  }
}
```

---

## 录制工具

### start_recording

开始视频录制。

```json
{
  "name": "start_recording",
  "arguments": {
    "output_path": "recording.mp4",
    "format": "mp4"
  }
}
```

### stop_recording

停止视频录制。

```json
{
  "name": "stop_recording"
}
```

返回:
```json
{
  "success": true,
  "path": "recording.mp4",
  "duration": 30,
  "size": 12345678
}
```

### start_audio_recording

开始音频录制。

```json
{
  "name": "start_audio_recording",
  "arguments": {
    "output_path": "audio.opus",
    "format": "opus"
  }
}
```

### stop_audio_recording

停止音频录制。

```json
{
  "name": "stop_audio_recording"
}
```

---

## 调试工具

### start_tcpdump

开始网络抓包。

```json
{
  "name": "start_tcpdump",
  "arguments": {
    "output_path": "/sdcard/capture.pcap"
  }
}
```

### stop_tcpdump

停止抓包。

```json
{
  "name": "stop_tcpdump"
}
```

---

## 系统工具

### open_url

打开 URL。

```json
{
  "name": "open_url",
  "arguments": {
    "url": "https://example.com"
  }
}
```

### send_intent

发送 Intent。

```json
{
  "name": "send_intent",
  "arguments": {
    "action": "android.intent.action.VIEW",
    "data": "content://...",
    "package": "com.example.app"
  }
}
```

### set_brightness

设置屏幕亮度。

```json
{
  "name": "set_brightness",
  "arguments": {
    "level": 128
  }
}
```

参数: `level` 0-255

### set_volume

设置音量。

```json
{
  "name": "set_volume",
  "arguments": {
    "stream": "music | notification | alarm",
    "level": 50
  }
}
```

参数: `level` 0-100

---

## 工作流示例

### 自动化测试

```json
// 1. 开始录制
start_recording({ "output_path": "test.mp4" })

// 2. 执行操作
tap({ "x": 540, "y": 200 })  // 点击按钮
wait(1000)
type_text({ "text": "test input" })
press_key({ "keycode": "ENTER" })

// 3. 截图验证
screenshot({ "save_path": "result.png" })

// 4. 停止录制
stop_recording()
```

### 跨设备复制

```json
// 设备 A 复制
get_clipboard() -> "text to copy"

// 设备 B 粘贴
set_clipboard({ "text": "text to copy" })
```
