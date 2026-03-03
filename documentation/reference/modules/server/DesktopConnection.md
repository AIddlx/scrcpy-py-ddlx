# DesktopConnection.java - 连接管理

> **路径**: `scrcpy/server/src/main/java/com/genymobile/scrcpy/device/DesktopConnection.java`
> **职责**: 管理与客户端的连接（ADB 隧道或网络模式）

---

## 类定义

### DesktopConnection (implements Closeable)

**职责**: 连接管理器

**类型**: class implements Closeable

---

## 连接模式

### ADB 隧道模式

```
使用 LocalSocket (Unix Domain Socket)
通过 ADB forward 隧道通信
```

### 网络模式

```
TCP 控制 + UDP 媒体 + TCP 文件
直连通信，无 ADB 隧道
```

---

## 字段

### ADB 隧道模式

| 字段 | 类型 | 说明 |
|------|------|------|
| `videoSocket` | LocalSocket | 视频 socket |
| `audioSocket` | LocalSocket | 音频 socket |
| `controlSocket` | LocalSocket | 控制 socket |
| `fileSocket` | LocalSocket | 文件 socket |
| `videoFd` | FileDescriptor | 视频 FD |
| `audioFd` | FileDescriptor | 音频 FD |
| `fileFd` | FileDescriptor | 文件 FD |

### 网络模式

| 字段 | 类型 | 说明 |
|------|------|------|
| `controlTcpSocket` | Socket | TCP 控制 |
| `fileTcpSocket` | Socket | TCP 文件 |
| `videoUdpSocket` | DatagramSocket | UDP 视频 |
| `audioUdpSocket` | DatagramSocket | UDP 音频 |
| `videoUdpSender` | UdpMediaSender | UDP 视频发送器 |
| `audioUdpSender` | UdpMediaSender | UDP 音频发送器 |
| `clientAddress` | InetAddress | 客户端地址 |
| `clientVideoPort` | int | 客户端视频端口 |
| `clientAudioPort` | int | 客户端音频端口 |
| `clientFilePort` | int | 客户端文件端口 |

---

## 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `open` | maxSize, video, audio, control, file, sendDummyByte | DesktopConnection | ADB 模式连接 |
| `openNetwork` | controlPort, videoPort, audioPort, filePort, ... | DesktopConnection | 网络模式连接 |
| `sendDeviceMeta` | name | void | 发送设备名称 |
| `sendCapabilities` | videoCodecs, audioCodecs | void | 发送设备能力 |
| `receiveClientConfig` | - | ClientConfig | 接收客户端配置 |
| `connectFileSocket` | - | void | 连接文件传输通道 |
| `close` | - | void | 关闭连接 |

---

## 连接流程

### ADB 模式

```
1. 创建 LocalServerSocket 监听
2. 等待 ADB forward 连接
3. 依次建立 video/audio/control/file socket
4. 返回 DesktopConnection
```

### 网络模式

```
1. 连接客户端 TCP 控制端口
2. 创建 UDP 视频/音频 socket
3. 发送 dummy byte
4. 连接文件传输端口
5. 返回 DesktopConnection
```

---

## 依赖关系

```
DesktopConnection
    │
    ├──→ LocalSocket (ADB 模式)
    │
    ├──→ Socket/DatagramSocket (网络模式)
    │
    ├──→ UdpMediaSender (UDP 发送)
    │
    └──→ CapabilityNegotiation (能力协商)
```

---

*此文档基于服务端代码分析生成*
