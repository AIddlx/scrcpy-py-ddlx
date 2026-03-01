# 参考客户端 (Reference Client)

> **语言**: Python 3.8+
> **目录**: `scrcpy_py_ddlx/`
> **定位**: 协议验证 + 功能演示

---

## 角色说明

本客户端是**参考实现**，用于：
- ✅ 验证协议正确性
- ✅ 演示完整功能
- ✅ 开发调试工具
- ❌ 不是生产级 SDK

**生产使用建议**：基于协议规范自行实现，或等待 AI SDK 发布。

---

## 目录结构

```
scrcpy_py_ddlx/
├── client/                    # 客户端连接层
│   ├── client.py             # 主客户端类
│   ├── connection.py         # 连接管理
│   ├── components.py         # 组件初始化
│   ├── config.py             # 配置定义
│   └── udp_packet_reader.py  # UDP包读取
│
├── core/                      # 核心功能层
│   ├── decoder/              # 解码器
│   │   ├── video.py          # 视频解码
│   │   └── audio.py          # 音频解码
│   │
│   ├── demuxer/              # 解复用器
│   │   ├── udp_video.py      # 视频解复用
│   │   └── udp_audio.py      # 音频解复用
│   │
│   ├── player/               # 播放器
│   │   └── video/
│   │       └── opengl_window.py  # OpenGL渲染
│   │
│   ├── audio/                # 音频处理
│   │   ├── recorder.py       # 录音
│   │   └── qt_push_player.py # Qt音频播放
│   │
│   ├── control.py            # 控制命令
│   ├── protocol.py           # 协议常量
│   └── stream.py             # 流解析
│
├── simple_shm.py             # 共享内存
└── mcp_server.py             # MCP服务器
```

---

## 模块清单

### client/ - 客户端连接层

| 文件 | 职责 | 状态 |
|------|------|------|
| [client.md](client.md) | 主客户端，协调所有组件 | ✅ |
| [connection.md](connection.md) | Socket连接管理 | ✅ |
| [config.md](config.md) | ClientConfig配置类 | ✅ |
| [components.md](components.md) | 组件工厂和初始化 | ✅ |

### core/decoder/ - 解码器

| 文件 | 职责 | 状态 |
|------|------|------|
| [video_decoder.md](video_decoder.md) | H.264/H.265视频解码 | ✅ |
| [audio_decoder.md](audio_decoder.md) | Opus/AAC音频解码 | ✅ |

### core/demuxer/ - 解复用器

| 文件 | 职责 | 状态 |
|------|------|------|
| [udp_video_demuxer.md](udp_video_demuxer.md) | UDP视频流解复用 | ✅ |
| [udp_audio_demuxer.md](udp_audio_demuxer.md) | UDP音频流解复用 | ✅ |

### core/player/ - 播放器

| 文件 | 职责 | 状态 |
|------|------|------|
| [opengl_window.md](opengl_window.md) | OpenGL渲染窗口 | ✅ |
| [input_handler.md](input_handler.md) | 输入事件处理 | ✅ |

### core/ - 核心模块

| 文件 | 职责 | 状态 |
|------|------|------|
| [control.md](control.md) | 触摸/按键控制命令 | ✅ |
| [delay_buffer.md](delay_buffer.md) | 单帧缓冲区 | ✅ |
| [device_msg.md](device_msg.md) | 设备消息接收器 | ✅ |

---

## 线程模型

| 线程名 | 职责 | 所在文件 |
|--------|------|----------|
| UDP接收线程 | 接收UDP数据包 | udp_packet_reader.py |
| 视频解码线程 | H.264/H.265解码 | video.py |
| 音频解码线程 | Opus/AAC解码 | audio.py |
| GUI线程 | Qt渲染 | opengl_window.py |
| 控制线程 | TCP控制命令 | control.py |

---

## 数据流概览

```
[UDP Socket]
    │
    ▼
[UdpPacketReader] ──→ 分发到对应Demuxer
    │
    ├──→ [UdpVideoDemuxer] ──→ [VideoDecoder] ──→ [OpenGLWindow]
    │
    └──→ [UdpAudioDemuxer] ──→ [AudioDecoder] ──→ [QtAudioPlayer]

[TCP Socket]
    │
    ▼
[ControlChannel] ←── 用户输入
```

---

## 类关系图

```
ScrcpyClient
    │
    ├── NetworkConnection (connection.py)
    │       ├── video_socket
    │       ├── audio_socket
    │       ├── control_socket
    │       └── file_socket
    │
    ├── UdpPacketReader (udp_packet_reader.py)
    │
    ├── UdpVideoDemuxer (udp_video.py)
    │       └── VideoDecoder (video.py)
    │
    ├── UdpAudioDemuxer (udp_audio.py)
    │       └── AudioDecoder (audio.py)
    │
    ├── OpenGLWindow (opengl_window.py)
    │
    └── ControlMessageQueue (control.py)
```

---

## 与其他组件的关系

```
┌─────────────────────────────────────────────────────────┐
│                    AI 应用层                             │
│                 (MCP / SDK / 自定义)                     │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  AI SDK (计划中)                         │
│              简化接口 + 稳定契约                          │
└───────────────────────┬─────────────────────────────────┘
                        │
            ┌───────────┴───────────┐
            │                       │
            ▼                       ▼
┌───────────────────┐    ┌───────────────────┐
│   参考客户端       │    │   Android Agent   │
│   (本目录)        │    │   (手机端)        │
│                   │    │                   │
│  Python 实现      │◄──►│  Java 实现        │
│  协议验证/演示    │    │  核心产品         │
└───────────────────┘    └───────────────────┘
```

---

## 当前状态

| 功能 | 状态 | 说明 |
|------|------|------|
| 网络模式连接 | ✅ 可用 | 明文传输，仅限内网 |
| ADB 模式连接 | ✅ 可用 | 推荐使用 |
| 视频解码 (GPU) | ✅ 可用 | NV12 模式 |
| 视频解码 (CPU) | ⚠️ 问题 | GIL 竞争 |
| 触摸控制 | ✅ 可用 | |
| 文件传输 | ✅ 可用 | |
| 音频播放 | ⚠️ 基础 | |
| 录制 | ❌ 不完整 | 已隐藏 |

---

*详细分析见各文件wiki*
