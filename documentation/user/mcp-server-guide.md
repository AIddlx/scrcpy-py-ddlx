# MCP 服务器使用指南

本文档介绍 `scrcpy_http_mcp_server.py` 的完整参数和使用方法。

服务器启动后默认监听 `http://127.0.0.1:3359/mcp`

---

## 连接模式（必选）

| 参数 | 说明 | 适用场景 |
|------|------|----------|
| `--adb` | ADB 模式：通过 ADB 隧道连接 | USB 连接、WiFi ADB |
| `--net [IP]` | 网络模式：TCP/UDP 直连 | WiFi 无线、远程控制 |

### ADB 模式 (`--adb`)

通过 ADB 转发通信，最稳定的方式：

```bash
# USB 线连接
python scrcpy_http_mcp_server.py --adb

# WiFi ADB（需先用 USB 开启）
adb tcpip 5555
adb connect 192.168.1.100:5555
python scrcpy_http_mcp_server.py --adb
```

### 网络模式 (`--net`)

TCP/UDP 直连，无需 ADB：

```bash
# 自动发现设备 IP（需先用 USB 连接一次）
python scrcpy_http_mcp_server.py --net

# 手动指定设备 IP
python scrcpy_http_mcp_server.py --net 192.168.1.100

# 驻留模式：服务端保持运行，断开后可重连
python scrcpy_http_mcp_server.py --net --stay-alive
```

---

## 功能开关（可选）

| 参数 | 说明 |
|------|------|
| `--video` | 启用视频（截图、预览） |
| `--audio` | 启用音频（录音） |

```bash
# 基础控制（点击、滑动、按键等）- 无需额外参数
python scrcpy_http_mcp_server.py --adb

# 需要截图功能
python scrcpy_http_mcp_server.py --adb --video

# 需要录音功能
python scrcpy_http_mcp_server.py --adb --audio

# 完整功能
python scrcpy_http_mcp_server.py --adb --video --audio
```

---

## 网络模式高级选项

### 驻留模式 (`--stay-alive`)

服务端在客户端断开后保持运行，便于重连：

```bash
python scrcpy_http_mcp_server.py --net --stay-alive
```

**优点：**
- 断开后可快速重连
- 下次连接无需重新推送服务端

**配合快捷开关 APK 使用体验最佳。**

### 强制推送 (`--force`)

停止旧服务端并推送新版本（需要 USB 连接）：

```bash
python scrcpy_http_mcp_server.py --net --force
```

### 停止远程服务端 (`--stop-server`)

通过 UDP 发送停止命令：

```bash
# 自动发现设备 IP
python scrcpy_http_mcp_server.py --stop-server

# 手动指定 IP
python scrcpy_http_mcp_server.py --stop-server 192.168.1.100
```

---

## 服务器配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--host` | `127.0.0.1` | 监听地址 |
| `--port` / `-p` | `3359` | 监听端口 |

```bash
# 指定端口
python scrcpy_http_mcp_server.py --adb --port 8080

# 监听所有网卡（允许局域网访问）
python scrcpy_http_mcp_server.py --adb --host 0.0.0.0
```

---

## 视频参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--bitrate` / `-b` | 8M | 视频码率 |
| `--fps` | 60 | 帧率 |
| `--codec` | auto | 编码器 (auto/h264/h265/av1) |

```bash
# 降低码率（弱网环境）
python scrcpy_http_mcp_server.py --net --video --bitrate 4M

# 30fps（省电）
python scrcpy_http_mcp_server.py --adb --video --fps 30

# 指定编码器
python scrcpy_http_mcp_server.py --adb --video --codec h265
```

---

## 日志配置

| 参数 | 说明 |
|------|------|
| `--log-level` | 日志级别 (DEBUG/INFO/WARNING/ERROR/CRITICAL) |
| `--log-keep` | 保留日志文件数量（默认 3） |

```bash
# 调试模式
python scrcpy_http_mcp_server.py --adb --log-level DEBUG

# 环境变量方式
set SCRCPY_DEBUG=1
python scrcpy_http_mcp_server.py --adb
```

---

## 常用组合

```bash
# USB 基础控制
python scrcpy_http_mcp_server.py --adb

# USB 完整功能
python scrcpy_http_mcp_server.py --adb --video --audio

# 网络模式 + 驻留
python scrcpy_http_mcp_server.py --net --stay-alive

# 网络模式 + 弱网优化
python scrcpy_http_mcp_server.py --net --video --bitrate 4M --fps 30

# 开发调试
python scrcpy_http_mcp_server.py --adb --video --audio --log-level DEBUG
```

---

## MCP 工具列表

服务器启动后提供以下工具供 AI 调用：

| 工具 | 功能 | 依赖参数 |
|------|------|----------|
| `connect` | 连接设备 | - |
| `disconnect` | 断开设备 | - |
| `screenshot` | 截图 | `--video` |
| `tap` | 点击 | - |
| `swipe` | 滑动 | - |
| `type_text` | 输入文字 | - |
| `press_key` | 按键 | - |
| `get_device_info` | 获取设备信息 | - |
| `list_apps` | 应用列表 | - |
| `start_app` | 启动应用 | - |
| `push_file` | 推送文件 | - |
| `pull_file` | 拉取文件 | - |
| `get_clipboard` | 获取剪贴板 | - |
| `set_clipboard` | 设置剪贴板 | - |
| `start_recording` | 开始录音 | `--audio` |
| `stop_recording` | 停止录音 | `--audio` |
