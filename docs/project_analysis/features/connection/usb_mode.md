# USB 模式 (ADB Tunnel)

> 通过 USB 数据线使用 ADB Tunnel 连接设备

---

## 概述

USB 模式是 scrcpy 的传统连接方式，通过 ADB (Android Debug Bridge) 建立 TCP 隧道转发数据。

## 技术细节

### 通道结构

USB 模式使用 ADB 的端口转发功能，在本地建立 3 个虚拟 socket：

| 通道 | 本地端口 | 远程端口 | 用途 |
|------|---------|---------|------|
| 视频 | localhost:27183 | localabstract:scrcpy | H.264/H.265 视频流 |
| 控制 | localhost:27184 | localabstract:scrcpy | 触摸/键盘命令 |
| 音频 | localhost:27185 | localabstract:scrcpy | OPUS 音频流 |

### 数据流格式

使用 scrcpy 原生的二进制帧格式：

```
[帧头] [负载数据]
  │
  └── 非 Demux 模式: 无帧头，裸 H.264 NAL
  └── Demux 模式: [类型:1][PTS:8][包大小:4] [负载数据]
```

## 代码位置

| 组件 | 文件 |
|------|------|
| 连接建立 | `client/connection.py:connect_usb()` |
| 视频解复用 | `core/demuxer/video.py` |
| 音频解复用 | `core/demuxer/audio.py` |

## 使用方式

```python
from scrcpy_py_ddlx import Client

# USB 模式连接
client = Client(device="device_serial")
client.start()
```

## 优缺点

### 优点
- 稳定性高，ADB 成熟可靠
- 无需额外认证
- 兼容性好

### 缺点
- 需要数据线
- 延迟略高于网络模式
- ADB 转发有少量开销

## 相关文档

- [网络模式](network_mode.md)
- [ADB Tunnel 详解](../../../ADB_TUNNEL_MODE.md)
