# Server.java - 服务入口

> **路径**: `scrcpy/server/src/main/java/com/genymobile/scrcpy/Server.java`
> **职责**: 服务端主入口，管理会话生命周期

---

## 类定义

### Server (final class)

**职责**: 主服务类，不可实例化

**类型**: final class，所有方法为 static

### Completion (inner class)

**职责**: 异步处理器完成状态跟踪

---

## 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `main` | args... | void | 程序入口 |
| `internalMain` | args... | void | 内部主逻辑 |
| `scrcpy` | Options | void | 运行单次会话 |
| `runStayAliveMode` | Options | void | 热连接模式 |
| `scrcpySession` | Options, Connection, CleanUp | void | 执行单次会话 |
| `createConnection` | Options | DesktopConnection | 创建连接 |
| `prepareMainLooper` | - | void | 准备 Looper |
| `resetMainLooper` | - | void | 重置 Looper |

---

## 会话流程

### 传统模式 (scrcpy)

```
main()
  └── internalMain()
        └── scrcpy(options)
              ├── createConnection()
              ├── scrcpySession()
              │     ├── 发送设备名称
              │     ├── 发送能力信息
              │     ├── 接收客户端配置
              │     ├── 启动 Controller
              │     ├── 启动 SurfaceEncoder
              │     ├── 启动 AudioEncoder
              │     └── 等待结束
              └── close()
```

### 热连接模式 (stay-alive)

```
main()
  └── internalMain()
        └── runStayAliveMode(options)
              ├── 启动 UdpDiscoveryReceiver
              ├── 循环等待唤醒
              └── 每次唤醒执行 scrcpySession()
```

---

## 依赖关系

```
Server
    │
    ├──→ Options (配置解析)
    │
    ├──→ DesktopConnection (连接管理)
    │       ├── ControlChannel
    │       ├── UdpMediaSender
    │       └── CapabilityNegotiation
    │
    ├──→ Controller (控制处理)
    │
    ├──→ SurfaceEncoder (视频编码)
    │
    ├──→ AudioEncoder (音频编码)
    │
    └──→ UdpDiscoveryReceiver (唤醒接收)
```

---

## 常量

| 常量 | 值 | 说明 |
|------|-----|------|
| `SERVER_PATH` | - | 服务端 JAR 路径 |

---

*此文档基于服务端代码分析生成*
