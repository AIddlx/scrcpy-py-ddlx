# 系统依赖

> 运行时需要的系统程序和库

---

## ADB (Android Debug Bridge)

### 概述

| 属性 | 值 |
|------|-----|
| **用途** | Android 设备通信 |
| **必需** | ✅ 是 |
| **最低版本** | 1.0.40 |
| **推荐版本** | 1.0.41+ |

### 功能

- 设备发现和连接
- 推送服务端到设备
- 端口转发 (USB 模式)
- Shell 命令执行

### 安装

#### Windows

```powershell
# 方式 1: SDK Platform Tools
# 下载: https://developer.android.com/studio/releases/platform-tools
# 解压后添加到 PATH

# 方式 2: Chocolatey
choco install adb

# 验证
adb version
```

#### Linux

```bash
# Debian/Ubuntu
sudo apt install android-tools-adb

# Arch Linux
sudo pacman -S android-tools

# Fedora
sudo dnf install android-tools

# 验证
adb version
```

#### macOS

```bash
# Homebrew
brew install android-platform-tools

# 验证
adb version
```

### 使用命令

```bash
# 列出设备
adb devices

# 推送服务端
adb push scrcpy-server.jar /data/local/tmp/

# 端口转发
adb forward tcp:27183 localabstract:scrcpy

# 启动服务端
adb shell CLASSPATH=/data/local/tmp/scrcpy-server.jar app_process / com.genymobile.scrcpy.Server
```

### 配置

```bash
# 启用 TCP/IP 模式 (网络连接)
adb tcpip 5555
adb connect <device-ip>:5555

# USB 调试授权
# 在设备上确认授权对话框
```

---

## FFmpeg

### 概述

| 属性 | 值 |
|------|-----|
| **用途** | 视频/音频编解码库 |
| **必需** | ✅ 是 (通过 PyAV) |
| **最低版本** | 4.0 |
| **推荐版本** | 5.0+ |

### 功能

- H.264/H.265/AV1 解码
- Opus/AAC/FLAC 解码
- 视频格式转换

### PyAV 依赖

PyAV 是 FFmpeg 的 Python 绑定，需要系统安装 FFmpeg 库。

```python
import av
# 底层调用 FFmpeg 库
```

### 安装

#### Windows

```powershell
# 方式 1: 下载预编译二进制
# https://www.gyan.dev/ffmpeg/builds/
# 下载 "ffmpeg-release-essentials.7z"
# 解压后添加 bin/ 到 PATH

# 方式 2: Chocolatey
choco install ffmpeg

# 方式 3: winget
winget install ffmpeg

# 验证
ffmpeg -version
```

#### Linux

```bash
# Debian/Ubuntu
sudo apt install ffmpeg libavcodec-dev libavformat-dev libavutil-dev libswscale-dev

# Arch Linux
sudo pacman -S ffmpeg

# Fedora
sudo dnf install ffmpeg ffmpeg-devel

# 验证
ffmpeg -version
```

#### macOS

```bash
# Homebrew
brew install ffmpeg

# 验证
ffmpeg -version
```

### 编解码器支持

```bash
# 检查 H.264 解码器
ffmpeg -decoders | grep h264

# 检查 H.265 解码器
ffmpeg -decoders | grep hevc

# 检查 Opus 解码器
ffmpeg -decoders | grep opus
```

### 硬件加速

| 平台 | 解码器 | 说明 |
|------|--------|------|
| NVIDIA | h264_cuvid, hevc_cuvid | CUDA 硬件解码 |
| Intel | h264_qsv, hevc_qsv | Quick Sync |
| Windows | h264_d3d11va | DirectX 11 |
| Linux | h264_vaapi | VAAPI |
| macOS | h264_videotoolbox | VideoToolbox |

---

## 音频库 (可选)

### PortAudio

| 属性 | 值 |
|------|-----|
| **用途** | 音频 I/O (sounddevice 依赖) |
| **必需** | ⚠️ 仅音频播放时 |

#### Linux

```bash
sudo apt install libportaudio2 libportaudio-dev
```

#### Windows / macOS

- 通常随 sounddevice pip 包自动安装

---

## OpenGL

### 概述

| 属性 | 值 |
|------|-----|
| **用途** | GPU 视频渲染 |
| **必需** | ✅ 是 (GUI 模式) |
| **最低版本** | OpenGL 3.3 |

### 驱动要求

| GPU 厂商 | 驱动 | 说明 |
|---------|------|------|
| NVIDIA | 官方驱动 | 推荐 |
| AMD | AMD 驱动 | 支持 |
| Intel | Intel 驱动 | 支持 |
| 虚拟机 | Mesa | 可能有限 |

### 验证

```python
from OpenGL.GL import glGetString, GL_VERSION, GL_RENDERER
print(glGetString(GL_VERSION))
print(glGetString(GL_RENDERER))
```

---

## 网络端口

### 默认端口

| 端口 | 协议 | 用途 |
|------|------|------|
| 27183 | UDP | 设备发现 |
| 27184 | TCP | 控制通道 |
| 27185 | UDP | 视频流 |
| 27186 | UDP | 音频流 |
| 27187 | TCP | 文件传输 |
| 8765 | TCP | MCP HTTP 服务 |

### 防火墙配置

#### Windows

```powershell
# 允许端口
netsh advfirewall firewall add rule name="scrcpy-video" dir=in action=allow protocol=udp localport=27185
netsh advfirewall firewall add rule name="scrcpy-audio" dir=in action=allow protocol=udp localport=27186
```

#### Linux (ufw)

```bash
sudo ufw allow 27183:27187/udp
sudo ufw allow 27184/tcp
sudo ufw allow 27187/tcp
```

---

## 环境变量

| 变量 | 用途 | 示例 |
|------|------|------|
| `ADB_PATH` | ADB 可执行文件路径 | `/usr/bin/adb` |
| `SCRCPY_SERVER_PATH` | 服务端 JAR 路径 | `./scrcpy-server.jar` |
| `SCRCPY_ZERO_COPY_GPU` | 启用 GPU 零拷贝 | `1` |
| `FFMPEG_BINARY` | FFmpeg 二进制路径 | `/usr/bin/ffmpeg` |

---

## 系统要求汇总

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核心 | 4+ 核心 |
| 内存 | 2 GB | 4+ GB |
| GPU | OpenGL 3.3 | OpenGL 4.5+ |
| 网络 | 10 Mbps | 100+ Mbps |
| 存储 | 100 MB | 500 MB |

---

## 相关文档

- [python.md](python.md) - Python 依赖
- [optional.md](optional.md) - 可选依赖
