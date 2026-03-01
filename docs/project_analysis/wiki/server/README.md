# Android Agent (手机端)

> **语言**: Java 17+
> **目录**: `scrcpy/server/src/main/java/com/genymobile/scrcpy/`
> **定位**: 核心产品 - 手机端数据采集 + 控制执行

---

## 角色说明

Android Agent 是本项目的**核心产品**，负责：
- 📱 屏幕采集 → 编码 → 发送
- 🎤 音频采集 → 编码 → 发送
- 👆 接收控制命令 → 注入系统
- 📁 文件操作

**稳定性要求**：长时间运行、异常恢复、资源不泄漏。

---

## 目录结构

```
com/genymobile/scrcpy/
├── device/                    # 设备端核心
│   ├── DesktopConnection.java    # 连接管理
│   ├── Device.java              # 设备信息
│   ├── ScreenEncoder.java       # 屏幕编码
│   ├── Streamer.java            # 流发送
│   └── Configuration.java       # 配置
│
├── udp/                       # UDP发送
│   ├── UdpMediaSender.java      # UDP媒体发送
│   └── UdpConfiguration.java    # UDP配置
│
├── file/                      # 文件传输
│   ├── FileChannelHandler.java  # 文件通道处理
│   ├── FileCommands.java        # 文件命令
│   └── FileServer.java          # 文件服务器
│
├── Server.java                # 服务入口
└── Ln.java                    # 日志工具
```

---

## 模块清单

### 合并模块文档 (推荐)

| 文档 | 包含文件数 | 职责 |
|------|-----------|------|
| [ServerCore.md](ServerCore.md) | 7 | 服务入口、配置、工具类 |
| [VideoPipeline.md](VideoPipeline.md) | 14 | 视频捕获和编码 |
| [AudioPipeline.md](AudioPipeline.md) | 10 | 音频捕获和编码 |
| [ControlProtocol.md](ControlProtocol.md) | 8 | 控制消息协议 |
| [SystemWrappers.md](SystemWrappers.md) | 12 | Android 系统 API 包装 |

### device/ - 设备端核心

| 文件 | 职责 | 状态 |
|------|------|------|
| [DesktopConnection.md](DesktopConnection.md) | 网络连接管理 | ✅ |
| [Streamer.md](Streamer.md) | 媒体流发送 | ✅ |

### control/ - 控制模块

| 文件 | 职责 | 状态 |
|------|------|------|
| [Controller.md](Controller.md) | 控制消息处理 | ✅ |

### video/ - 视频模块

| 文件 | 职责 | 状态 |
|------|------|------|
| [ScreenshotCapture.md](ScreenshotCapture.md) | video=false 模式截图组件 | ✅ |

### udp/ - UDP发送

| 文件 | 职责 | 状态 |
|------|------|------|
| [UdpMediaSender.md](UdpMediaSender.md) | UDP媒体数据发送 | ✅ |
| [UdpDiscoveryReceiver.md](UdpDiscoveryReceiver.md) | UDP 发现和唤醒 | ✅ |
| [SimpleXorFecEncoder.md](SimpleXorFecEncoder.md) | FEC 编码器 | ✅ |

### 认证模块

| 文件 | 职责 | 状态 |
|------|------|------|
| [AuthHandler.md](AuthHandler.md) | HMAC-SHA256 认证 | ✅ |

### 文件传输

| 文件 | 职责 | 状态 |
|------|------|------|
| [FileServer.md](FileServer.md) | 文件服务器 | ✅ |

### 核心入口

| 文件 | 职责 | 状态 |
|------|------|------|
| [Server.md](Server.md) | 服务入口和会话管理 | ✅ |
| [Options.md](Options.md) | 命令行参数 | ✅ |

---

## 线程模型

| 线程 | 职责 | 所在文件 |
|------|------|----------|
| 主线程 | 服务启动和初始化 | Server.java |
| 视频编码线程 | MediaCodec编码 | ScreenEncoder.java |
| UDP发送线程 | UDP数据包发送 | UdpMediaSender.java |
| 文件处理线程 | 文件操作 | FileChannelHandler.java |

---

## 数据流概览

```
[ScreenCapture]
    │
    ▼
[MediaCodec] ──→ H.264/H.265编码
    │
    ▼
[Streamer] ──→ 分发到各通道
    │
    ├──→ [UdpMediaSender] ──→ UDP视频/音频
    │
    └──→ [TCP Control] ──→ 控制响应

[FileChannelHandler]
    │
    ▼
文件操作 (LIST/PUSH/PULL/DELETE/MKDIR)
```

---

## 类关系图

```
Server
    │
    ├── DesktopConnection
    │       ├── videoSocket
    │       ├── audioSocket
    │       ├── controlSocket
    │       └── fileSocket
    │
    ├── ScreenEncoder
    │       └── MediaCodec
    │
    ├── Streamer
    │       └── UdpMediaSender
    │
    └── FileChannelHandler
```

---

## 与客户端的对应关系

| 服务端 | 客户端 | 说明 |
|--------|--------|------|
| DesktopConnection | NetworkConnection | 连接管理 |
| ScreenEncoder | VideoDecoder | 编解码 |
| UdpMediaSender | UdpPacketReader | UDP收发 |
| FileChannelHandler | FileChannel | 文件传输 |

---

## 稳定性要求

作为核心产品，Android Agent 需要：

| 要求 | 说明 | 状态 |
|------|------|------|
| 长时间运行 | 8+ 小时不崩溃 | ⚠️ 待测试 |
| 内存稳定 | 无泄漏 | ⚠️ 待排查 |
| 断线恢复 | 自动重连 | ⚠️ 需加强 |
| 异常处理 | 优雅降级 | ⚠️ 需完善 |

---

## 安全特性

### v1.4 已实现

| 功能 | 实现方式 | 状态 |
|------|---------|------|
| **HMAC-SHA256 认证** | Challenge-Response 协议 | ✅ 已实现 |
| 密钥分发 | ADB 推送，用后删除 | ✅ |
| 本地密钥存储 | ~/.config/scrcpy-py-ddlx/auth_keys/ | ✅ |

### 未来计划

| 版本 | 功能 | 状态 |
|------|------|------|
| v2.0 | 传输加密 (TLS/Noise Protocol) | 计划中 |
| v3.0 | 端到端加密 | 计划中 |

**安全建议**：
- 网络模式已支持认证，可在可信网络使用
- 高安全场景建议使用 ADB + USB 模式

---

## 近期更新

### 2026-02-28

**新增组件**：
- `ScreenshotCapture.java` - video=false 模式截图组件

**功能改进**：
- `Server.java` - 在 video=false 时也创建 ScreenshotCapture
- `Controller.java` - 添加 ScreenshotCapture 集成

**截图方案对比**：

| 方案 | 延迟 | 可靠性 |
|------|------|--------|
| SurfaceControl.screenshot() | ~50ms | ❌ 权限问题 |
| 编码器方案 | ~200-500ms | ✅ 可靠 |
| **ScreenshotCapture** | ~70-120ms | ✅ 可靠 |

---

*详细分析见各文件wiki*
