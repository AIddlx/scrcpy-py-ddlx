# scrcpy-py-ddlx Wiki

> **建立时间**: 2026-02-26
> **阶段**: 第一阶段 - 代码层级组织

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
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌───────────────────┐      ┌───────────────────┐          │
│  │   Android Agent   │      │  Reference Client  │          │
│  │    (手机端/核心)    │      │    (参考客户端)     │          │
│  │                   │      │                   │          │
│  │  - 屏幕采集       │      │  - 协议验证        │          │
│  │  - 音频采集       │      │  - 功能演示        │          │
│  │  - 控制注入       │      │  - 开发调试        │          │
│  │  - 文件操作       │      │                   │          │
│  └───────────────────┘      └───────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 组件说明

| 组件 | 角色 | 重要性 |
|------|------|--------|
| **Protocol Spec** | 通信规范 | ⭐⭐⭐ 核心 |
| **Android Agent** | 手机端数据采集+控制执行 | ⭐⭐⭐ 核心产品 |
| **Reference Client** | Python 参考实现 | ⭐⭐ 演示/验证 |
| **AI SDK/MCP** | AI 接入层 | ⭐ 衍生应用 |

---

## 连接模式与安全性

### ADB 模式 (推荐)

```
┌─────────┐      USB 线       ┌─────────┐
│  PC     │ ══════════════════│ 手机    │
│         │    物理连接        │         │
└─────────┘                    └─────────┘

特点：
✓ 数据完全不经过网络
✓ ADB 自身加密
✓ 适用于所有场景（包括公司网络）
```

### 网络模式 (受限)

```
┌─────────┐     UDP/TCP      ┌─────────┐
│  PC     │ ──────────────────│ 手机    │
│         │    明文传输        │         │
└─────────┘                    └─────────┘

特点：
✗ 数据明文，可被监听
✗ 无认证机制
⚠ 仅限可信网络使用（内网/局域网）
⚠ 不适用于公网或公司网络

计划改进：
- [ ] 添加认证机制 (v2.0)
- [ ] 支持加密传输 (v3.0)
```

### 安全对比

| 模式 | 数据经过网络 | 加密 | 认证 | 适用场景 |
|------|-------------|------|------|----------|
| ADB + USB | 否 | ✓ | ✓ | 所有场景 |
| ADB + tcpip | 是 | ⚠️ 弱 | ✓ | 可信网络 |
| 网络模式 | 是 | ✗ | ✗ | 内网/隔离网络 |

---

## 开发优先级

```
优先级 1: 协议规范稳定
├── 定义清晰
├── 版本锁定
└── 文档完善

优先级 2: Android Agent 可靠性
├── 网络异常处理
├── 断线重连
├── 长时间运行
└── 资源不泄漏

优先级 3: 客户端验证
├── 协议正确性验证
├── 功能完整性演示
└── 问题排查工具

优先级 4: AI 集成 (衍生)
├── MCP Server
├── SDK 封装
└── 文档示例
```

---

## Wiki 结构

```
wiki/
├── client/          # 参考客户端代码分析 (Python) - 13 文档
├── server/          # Android Agent 代码分析 (Java) - 6 文档
├── protocol/        # 协议定义分析 - 5 文档
└── README.md        # 本文件
```

**总计**: 24 个文档

---

## 目录索引

### 协议 (protocol/) - 5 文档 ✅

| 文件 | 内容 | 状态 |
|------|------|------|
| [README.md](protocol/README.md) | 协议概述 + 安全模型 | ✅ 完成 |
| [constants.md](protocol/constants.md) | 协议常量定义 | ✅ 完成 |
| [udp_header.md](protocol/udp_header.md) | UDP数据包头部格式 | ✅ 完成 |
| [tcp_messages.md](protocol/tcp_messages.md) | TCP控制消息格式 | ✅ 完成 |
| [formats.md](protocol/formats.md) | 数据格式详情 | ✅ 完成 |

### Android Agent (server/) - 6 文档 ✅

| 文件 | 对应代码 | 状态 |
|------|----------|------|
| [Server.md](server/Server.md) | Server.java | ✅ 完成 |
| [DesktopConnection.md](server/DesktopConnection.md) | device/DesktopConnection.java | ✅ 完成 |
| [UdpMediaSender.md](server/UdpMediaSender.md) | udp/UdpMediaSender.java | ✅ 完成 |
| [Streamer.md](server/Streamer.md) | device/Streamer.java | ✅ 完成 |
| [Controller.md](server/Controller.md) | control/Controller.java | ✅ 完成 |
| [ScreenshotCapture.md](server/ScreenshotCapture.md) | video/ScreenshotCapture.java | ✅ 完成 |

### 参考客户端 (client/) - 13 文档 ✅

| 文件 | 对应代码 | 状态 |
|------|----------|------|
| [client.md](client/client.md) | client/client.py | ✅ 完成 |
| [connection.md](client/connection.md) | client/connection.py | ✅ 完成 |
| [config.md](client/config.md) | client/config.py | ✅ 完成 |
| [components.md](client/components.md) | client/components.py | ✅ 完成 |
| [video_decoder.md](client/video_decoder.md) | core/decoder/video.py | ✅ 完成 |
| [audio_decoder.md](client/audio_decoder.md) | core/audio/decoder.py | ✅ 完成 |
| [udp_video_demuxer.md](client/udp_video_demuxer.md) | core/demuxer/udp_video.py | ✅ 完成 |
| [udp_audio_demuxer.md](client/udp_audio_demuxer.md) | core/demuxer/udp_audio.py | ✅ 完成 |
| [opengl_window.md](client/opengl_window.md) | core/player/video/opengl_window.py | ✅ 完成 |
| [input_handler.md](client/input_handler.md) | core/player/video/input_handler.py | ✅ 完成 |
| [control.md](client/control.md) | core/control.py | ✅ 完成 |
| [delay_buffer.md](client/delay_buffer.md) | core/decoder/delay_buffer.py | ✅ 完成 |
| [device_msg.md](client/device_msg.md) | core/device_msg.py | ✅ 完成 |

---

## 架构概览

### 整体架构

```
                        ┌─────────────┐
                        │   AI 应用    │
                        │  (可选接入)  │
                        └──────┬──────┘
                               │
                        ┌──────▼──────┐
                        │  AI SDK/MCP │
                        │  (衍生层)    │
                        └──────┬──────┘
                               │
┌──────────────────────────────┼──────────────────────────────┐
│                              │                               │
│   ┌──────────────────────────┼──────────────────────────┐   │
│   │                     协议层                           │   │
│   │        Protocol Specification                        │   │
│   └──────────────────────────┬──────────────────────────┘   │
│                              │                               │
│   ┌──────────────────────────┴──────────────────────────┐   │
│   │                                                    │   │
│   │  ┌─────────────────┐      ┌─────────────────┐      │   │
│   │  │  Android Agent  │◄────►│ Reference Client│      │   │
│   │  │    (Java)       │      │    (Python)     │      │   │
│   │  │                 │      │                 │      │   │
│   │  │  屏幕采集       │      │  视频解码       │      │   │
│   │  │  音频采集       │      │  音频播放       │      │   │
│   │  │  控制注入       │      │  控制发送       │      │   │
│   │  │  文件操作       │      │  文件传输       │      │   │
│   │  │                 │      │                 │      │   │
│   │  └─────────────────┘      └─────────────────┘      │   │
│   │                                                    │   │
│   └────────────────────────────────────────────────────┘   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 更新日志

### 2026-02-28

**新增组件**：
- [ScreenshotCapture.md](server/ScreenshotCapture.md) - video=false 模式截图组件

**功能更新**：
- `--push` 模式（video=false + 网络模式）截图功能修复
- 使用 SurfaceControl API 创建 VirtualDisplay
- 延迟优化：~70-120ms（相比编码器方案的 ~200-500ms）

**技术要点**：
- SurfaceControl 操作必须在 Transaction 中调用
- ImageReader 直接获取帧，不经过编码器

---

## 后续阶段

### 第二阶段：协议稳定化
- 锁定协议版本 v1.0
- 完善安全模型文档
- 添加认证机制设计 (v2.0)

### 第三阶段：服务端加固
- 网络异常处理完善
- 长时间运行测试
- 资源泄漏排查

### 第四阶段：AI 集成
- MCP Server 实现
- SDK 简化接口
- 使用文档

---

*此Wiki基于代码分析生成，反映项目真实定位*
