# scrcpy-py-ddlx 测试指南

本文档提供完整的测试环境搭建和测试流程。

## 前置要求

- Python 3.10+
- Git
- Android 设备（已启用 USB 调试）
- ADB 工具已安装

## 测试流程

### 1. 创建工作目录并克隆项目

```bash
# 创建工作目录
mkdir ddlx
cd ddlx

# 克隆项目
git clone https://github.com/AIddlx/scrcpy-py-ddlx.git
cd scrcpy-py-ddlx
```

### 2. 创建虚拟环境

```bash
# 在工作目录中创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate
```

### 3. 安装依赖

```bash
# 安装项目依赖
pip install -r requirements.txt
```

**依赖说明：**
- `av` - 视频/音频编解码
- `numpy` - 数组操作
- `PySide6` - Qt6 GUI
- `PyOpenGL` - GPU 加速渲染
- `sounddevice` - 音频播放

### 4. 运行测试

```bash
# 运行测试脚本
python tests_gui\test_direct.py
```

## 设备连接

### 方式 1: 自动连接（推荐）

测试脚本会自动：
1. 检测 USB 设备
2. 启用无线调试模式
3. 扫描局域网设备
4. 自动连接

### 方式 2: 手动连接

```bash
# 用 USB 线连接手机后
adb tcpip 5555
adb connect <device-ip>:5555

# 然后运行测试
python tests_gui\test_direct.py
```

## 预期结果

### 成功运行

```
[SUCCESS] 连接成功!
  设备名称: <设备名称>
  设备分辨率: 1080x2400
========================================

视频窗口已显示，音频正在录制，你可以:
  - 使用鼠标点击/拖拽控制设备
  - 使用键盘输入文字
  - 使用滚轮滚动

关闭窗口或按 Ctrl+C 断开连接...
```

### 码率监控（GPU 渲染启用）

```
[VIDEO_BITRATE] Current: 7.12 Mbps | Average: 7.03 Mbps
```

- 无 GPU 渲染：约 3.7 Mbps
- 有 GPU 渲染：约 7.0 Mbps

## 常见问题

### 1. 设备未发现

```
[ERROR] 未在局域网内发现开启 ADB 无线调试的设备
```

**解决方法：**
- 用 USB 线连接设备
- 确保手机和电脑在同一网络
- 确保手机已启用 USB 调试

### 2. 编码错误

```
UnicodeDecodeError: 'gbk' codec can't decode byte...
```

**解决方法：**
```bash
python -X utf8 tests_gui\test_direct.py
```

### 3. PyOpenGL 未安装

```
WARNING - OpenGL not available, falling back to regular window
```

**解决方法：**
```bash
pip install PyOpenGL PyOpenGL_accelerate
```

## 测试功能

- ✅ 视频显示（GPU 加速）
- ✅ 音频录制
- ✅ 鼠标/键盘控制
- ✅ 剪贴板同步
- ✅ 实时码率监控

## MCP 服务器使用

scrcpy-py-ddlx 提供了 MCP (Model Context Protocol) 服务器，可以让 AI 助手（如 Claude Code）直接控制 Android 设备。

### 启动 MCP 服务器

```bash
# 启动 HTTP MCP 服务器（默认不启用音频）
python scrcpy_http_mcp_server.py

# 启动时启用音频（用于录音功能）
python scrcpy_http_mcp_server.py --audio
```

服务器默认运行在 `http://localhost:3359/mcp`

### 配置 Claude Code

在 Claude Code 设置中添加：

```json
{
  "mcpServers": {
    "scrcpy": {
      "url": "http://localhost:3359/mcp"
    }
  }
}
```

### MCP 工具列表

| 工具 | 说明 |
|------|------|
| `connect` | 连接到 Android 设备 |
| `disconnect` | 断开设备连接 |
| `screenshot` | 截取屏幕截图 |
| `tap` | 点击屏幕 |
| `swipe` | 滑动操作 |
| `wake_up` | 唤醒设备屏幕 |
| `record_audio` | 录音（异步，自动停止） |
| `get_recording_info` | 查询录音状态 |
| `stop_audio_recording` | 停止录音 |
| `list_apps` | 列出已安装应用 |

### 使用示例

```json
// 连接设备（启用音频）
{
  "device_id": "192.168.5.3:5555",
  "audio": true
}

// 截图
{
  "filename": "screenshot.jpg"
}

// 录音 10 秒
{
  "filename": "recording.opus",
  "duration": 10,
  "format": "opus"
}

// 查询录音状态
{
  "tool": "get_recording_info"
}
```

### 异步录音说明

录音是异步的，调用 `record_audio` 后立即返回，录音在后台进行：

```json
// 启动录音（立即返回）
{
  "filename": "test.opus",
  "duration": 10
}

// 响应
{
  "success": true,
  "message": "Recording started in background",
  "recording_info": {
    "active": true,
    "duration": 10,
    "remaining": 10
  }
}

// 查询状态
{
  "active": true,
  "elapsed": 3.5,
  "remaining": 6.5
}
```

录音会在指定时间后自动停止，或手动调用 `stop_audio_recording` 停止。
