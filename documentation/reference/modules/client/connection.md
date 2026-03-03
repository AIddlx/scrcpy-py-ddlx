# connection.py - 连接管理

> **路径**: `scrcpy_py_ddlx/client/connection.py`
> **职责**: 管理 ADB 隧道和网络模式连接

---

## 常量

### Socket 缓冲区配置

| 常量 | 值 | 说明 |
|------|-----|------|
| `VIDEO_SOCKET_BUFFER` | 4 MB | 视频缓冲区 (~500ms @ 8Mbps) |
| `AUDIO_SOCKET_BUFFER` | 256 KB | 音频缓冲区 (~16s @ 128Kbps) |

---

## 类清单

### NetworkConnection

**职责**: 网络模式连接状态容器

**类型**: @dataclass

#### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `control_socket` | socket | TCP 控制 socket |
| `video_socket` | socket | UDP 视频 socket |
| `audio_socket` | socket | UDP 音频 socket |
| `file_socket` | socket | TCP 文件 socket |
| `client_address` | str | 客户端地址 |

---

### ConnectionManager

**职责**: 连接管理器，提供静态方法创建连接

#### 方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `create_udp_receiver` | port, timeout, buffer_size | socket | 创建 UDP 接收 socket |
| `connect_tcp_control` | host, port, timeout | socket | 连接 TCP 控制 |
| `setup_network_mode` | host, ports, ... | NetworkConnection | 设置网络模式 |
| `accept_file_connection` | conn, timeout | socket | 接受文件连接 |

---

## 方法详解

### create_udp_receiver()

```python
@staticmethod
def create_udp_receiver(port: int, timeout: float = 5.0,
                        buffer_size: int = None) -> socket.socket
```

**流程**:
1. 创建 UDP socket
2. 设置 `SO_REUSEADDR`
3. 设置接收缓冲区 `SO_RCVBUF`
4. 检查实际缓冲区大小（可能被 OS 限制）
5. 设置超时
6. 绑定到 `0.0.0.0:port`

**注意事项**:
- Linux 上可能受 `net.core.rmem_max` 限制
- 实际缓冲区可能小于请求值

---

### setup_network_mode()

```python
@staticmethod
def setup_network_mode(host: str, control_port: int, video_port: int,
                       audio_port: int, file_port: int = 0,
                       send_dummy_byte: bool = True) -> NetworkConnection
```

**连接顺序**:
1. 创建 UDP 视频接收器（先于控制连接）
2. 创建 UDP 音频接收器
3. 连接 TCP 控制
4. 等待 dummy byte
5. 创建 TCP 文件监听 socket

**端口说明**:
- 控制: TCP，主动连接服务端
- 视频/音频: UDP，被动监听
- 文件: TCP，被动监听（服务端连接）

---

### accept_file_connection()

```python
@staticmethod
def accept_file_connection(conn: NetworkConnection,
                           timeout: float = 30.0) -> Optional[socket.socket]
```

**流程**:
1. 从 file_socket 接受连接
2. 关闭监听 socket
3. 返回已连接的 socket

**超时**: 30秒（可配置）

---

## 网络架构

```
┌─────────────┐                        ┌─────────────┐
│      PC     │                        │   Android   │
│   (客户端)   │                        │   (服务端)   │
└─────────────┘                        └─────────────┘
      │                                      │
      │ ◄── UDP 27185 ──────────────────► │ 视频流
      │     (PC监听)                         │
      │                                      │
      │ ◄── UDP 27186 ──────────────────► │ 音频流
      │     (PC监听)                         │
      │                                      │
      │ ◄── TCP 27184 ──────────────────► │ 控制通道
      │     (PC主动连接)                     │
      │                                      │
      │ ◄── TCP 27187 ──────────────────► │ 文件通道
      │     (PC监听，服务端连接)              │
```

---

## 缓冲区计算

### 视频缓冲区 (4MB)

```
8 Mbps = 1 MB/s
60 fps = 16.7 KB/帧
500ms 突发 = 500 KB
4 MB 缓冲区 ≈ 2 秒突发
```

### 音频缓冲区 (256KB)

```
128 Kbps = 16 KB/s
50 fps = 320 字节/帧
256 KB 缓冲区 ≈ 16 秒音频
```

---

## 依赖关系

```
ConnectionManager
    │
    ├──→ socket (标准库)
    │
    └──→ NetworkConnection (数据类)

ScrcpyClient
    │
    └──→ ConnectionManager
            │
            └──→ NetworkConnection (存入 ClientState)
```

---

## 错误处理

| 场景 | 处理 |
|------|------|
| UDP 缓冲区受限 | 警告日志，继续运行 |
| Dummy byte 未收到 | 抛出 ConnectionError |
| TCP 连接超时 | 抛出 socket.timeout |
| 文件连接超时 | 返回 None |

---

*此文档基于代码分析生成*
