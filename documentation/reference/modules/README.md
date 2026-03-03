# scrcpy-py-ddlx Wiki

> **建立时间**: 2026-02-26
> **更新时间**: 2026-03-01
> **阶段**: 第二阶段 - 完整代码分析

---

## 项目定位

本项目类似于**监控摄像头**的架构模式：

```
┌─────────────────────────────────────────────────────────────┐
│                      scrcpy-py-ddlx                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 协议规范 (核心)                       │   │
│  │              Protocol Specification                  │   │
│  │                                                      │   │
│  │  - UDP 媒体传输协议                                  │   │
│  │  - TCP 控制协议                                      │   │
│  │  - 消息格式定义                                      │   │
│  │  - HMAC-SHA256 认证                                  │   │
│  │  - FEC 前向纠错                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌───────────────────┐      ┌───────────────────┐          │
│  │   Android Agent   │      │  Reference Client  │          │
│  │    (手机端/核心)    │      │    (参考客户端)     │          │
│  │                   │      │                   │          │
│  │  - 屏幕采集       │      │  - 协议验证        │          │
│  │  - 音频采集       │      │  - 功能演示        │          │
│  │  - 控制注入       │      │  - 开发调试        │          │
│  │  - 文件操作       │      │  - MCP 服务        │          │
│  │  - FEC 编码       │      │  - FEC 解码        │          │
│  │  - 认证处理       │      │  - 认证处理        │          │
│  └───────────────────┘      └───────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Wiki 结构

```
wiki/
├── README.md              # 本文件
├── entry_points/          # 运行入口 (新增) - 4 文档
│   ├── test_direct.md
│   ├── test_network_direct.md
│   ├── mcp_http.md
│   └── mcp_stdio.md
├── protocol/              # 协议定义 - 5 文档
│   ├── README.md
│   ├── constants.md
│   ├── udp_header.md
│   ├── tcp_messages.md
│   └── formats.md
├── server/                # Android Agent - 11 文档 (新增 5)
│   ├── Server.md
│   ├── Options.md         # 新增
│   ├── DesktopConnection.md
│   ├── UdpMediaSender.md
│   ├── SimpleXorFecEncoder.md  # 新增
│   ├── UdpDiscoveryReceiver.md # 新增
│   ├── FileServer.md      # 新增
│   ├── AuthHandler.md     # 新增
│   ├── Streamer.md
│   ├── Controller.md
│   └── ScreenshotCapture.md
└── client/                # 参考客户端 - 19 文档 (新增 6)
    ├── client.md
    ├── connection.md
    ├── config.md
    ├── components.md
    ├── video_decoder.md
    ├── audio_decoder.md
    ├── udp_video_demuxer.md
    ├── udp_audio_demuxer.md
    ├── opengl_window.md
    ├── input_handler.md
    ├── control.md
    ├── delay_buffer.md
    ├── device_msg.md
    ├── auth.md             # 新增
    ├── heartbeat.md        # 新增
    ├── fec_decoder.md      # 新增
    ├── file_channel.md     # 新增
    ├── mcp_server.md       # 新增
    └── preview_process.md  # 新增
```

**总计**: 39 个文档 (新增 15)

---

## 目录索引

### 运行入口 (entry_points/) - 4 文档 ✅ 新增

| 文件 | 对应代码 | 说明 |
|------|----------|------|
| [test_direct.md](entry_points/test_direct.md) | `tests_gui/test_direct.py` | USB 模式入口 |
| [test_network_direct.md](entry_points/test_network_direct.md) | `tests_gui/test_network_direct.py` | 网络模式入口 |
| [mcp_http.md](entry_points/mcp_http.md) | `scrcpy_http_mcp_server.py` | HTTP MCP 服务 |
| [mcp_stdio.md](entry_points/mcp_stdio.md) | `mcp_stdio.py` | STDIO MCP 服务 |

### 协议 (protocol/) - 5 文档 ✅

| 文件 | 内容 |
|------|------|
| [README.md](protocol/README.md) | 协议概述 + 安全模型 |
| [constants.md](protocol/constants.md) | 协议常量定义 |
| [udp_header.md](protocol/udp_header.md) | UDP 数据包头部格式 |
| [tcp_messages.md](protocol/tcp_messages.md) | TCP 控制消息格式 |
| [formats.md](protocol/formats.md) | 数据格式详情 |

### Android Agent (server/) - 11 文档 ✅

| 文件 | 对应代码 | 状态 |
|------|----------|------|
| [Server.md](server/Server.md) | Server.java | ✅ |
| [Options.md](server/Options.md) | Options.java | ✅ 新增 |
| [DesktopConnection.md](server/DesktopConnection.md) | DesktopConnection.java | ✅ |
| [UdpMediaSender.md](server/UdpMediaSender.md) | UdpMediaSender.java | ✅ |
| [SimpleXorFecEncoder.md](server/SimpleXorFecEncoder.md) | SimpleXorFecEncoder.java | ✅ 新增 |
| [UdpDiscoveryReceiver.md](server/UdpDiscoveryReceiver.md) | UdpDiscoveryReceiver.java | ✅ 新增 |
| [FileServer.md](server/FileServer.md) | FileServer.java | ✅ 新增 |
| [AuthHandler.md](server/AuthHandler.md) | AuthHandler.java | ✅ 新增 |
| [Streamer.md](server/Streamer.md) | Streamer.java | ✅ |
| [Controller.md](server/Controller.md) | Controller.java | ✅ |
| [ScreenshotCapture.md](server/ScreenshotCapture.md) | ScreenshotCapture.java | ✅ |

### 参考客户端 (client/) - 19 文档 ✅

| 文件 | 对应代码 | 状态 |
|------|----------|------|
| [client.md](client/client.md) | client/client.py | ✅ |
| [connection.md](client/connection.md) | client/connection.py | ✅ |
| [config.md](client/config.md) | client/config.py | ✅ |
| [components.md](client/components.md) | client/components.py | ✅ |
| [video_decoder.md](client/video_decoder.md) | core/decoder/video.py | ✅ |
| [audio_decoder.md](client/audio_decoder.md) | core/audio/decoder.py | ✅ |
| [udp_video_demuxer.md](client/udp_video_demuxer.md) | core/demuxer/udp_video.py | ✅ |
| [udp_audio_demuxer.md](client/udp_audio_demuxer.md) | core/demuxer/udp_audio.py | ✅ |
| [opengl_window.md](client/opengl_window.md) | core/player/video/opengl_window.py | ✅ |
| [input_handler.md](client/input_handler.md) | core/player/video/input_handler.py | ✅ |
| [control.md](client/control.md) | core/control.py | ✅ |
| [delay_buffer.md](client/delay_buffer.md) | core/decoder/delay_buffer.py | ✅ |
| [device_msg.md](client/device_msg.md) | core/device_msg.py | ✅ |
| [auth.md](client/auth.md) | core/auth.py | ✅ 新增 |
| [heartbeat.md](client/heartbeat.md) | core/heartbeat.py | ✅ 新增 |
| [fec_decoder.md](client/fec_decoder.md) | core/demuxer/fec.py | ✅ 新增 |
| [file_channel.md](client/file_channel.md) | core/file/file_channel.py | ✅ 新增 |
| [mcp_server.md](client/mcp_server.md) | mcp_server.py | ✅ 新增 |
| [preview_process.md](client/preview_process.md) | preview_process.py | ✅ 新增 |

---

## 连接模式与安全性

### ADB 模式 (推荐)

```
特点：
✓ 数据完全不经过网络
✓ ADB 自身加密
✓ 适用于所有场景
```

### 网络模式

```
特点：
✓ 支持 HMAC-SHA256 认证 (v1.4)
✓ TCP 控制 + UDP 媒体
✓ FEC 前向纠错
✓ 心跳检测
⚠ 仅限可信网络使用
```

### 安全对比

| 模式 | 数据经过网络 | 加密 | 认证 | FEC |
|------|-------------|------|------|-----|
| ADB + USB | 否 | ✓ | ✓ | - |
| 网络模式 | 是 | ✗ | ✓ HMAC | ✓ |

---

## 更新日志

### 2026-03-01

**新增文档 (15)**：

运行入口 (4):
- `entry_points/test_direct.md`
- `entry_points/test_network_direct.md`
- `entry_points/mcp_http.md`
- `entry_points/mcp_stdio.md`

服务端 (5):
- `server/Options.md`
- `server/SimpleXorFecEncoder.md`
- `server/UdpDiscoveryReceiver.md`
- `server/FileServer.md`
- `server/AuthHandler.md`

客户端 (6):
- `client/auth.md`
- `client/heartbeat.md`
- `client/fec_decoder.md`
- `client/file_channel.md`
- `client/mcp_server.md`
- `client/preview_process.md`

### 2026-02-28

- 新增 `server/ScreenshotCapture.md`

### 2026-02-26

- Wiki 初始版本
- 协议文档 5 个
- 服务端文档 6 个
- 客户端文档 13 个

---

## 相关文档

- [功能清单](../features/README.md) - 功能层级文档
- [协议规范](../../PROTOCOL_SPEC.md) - 完整协议
- [开发指南](../../development/) - 开发文档

---

*此 Wiki 基于代码分析生成，反映项目真实结构*
