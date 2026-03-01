# UdpDiscoveryReceiver

> **文件**: `udp/UdpDiscoveryReceiver.java`
> **功能**: UDP 设备发现和远程终止

---

## 概述

`UdpDiscoveryReceiver` 提供：
1. 设备发现 - 响应客户端查询
2. 唤醒请求 - 启动服务器
3. 远程终止 - 停止服务器

---

## 协议消息

| 消息 | 内容 | 说明 |
|------|------|------|
| DISCOVER_REQUEST | `SCRCPY_DISCOVER` | 发现请求 |
| DISCOVER_RESPONSE | `SCRCPY_HERE <name> <ip> <mode>` | 发现响应 |
| WAKE_REQUEST | `WAKE_UP` | 唤醒请求 |
| WAKE_RESPONSE | `WAKE_ACK` | 唤醒确认 |
| TERMINATE_REQUEST | `SCRCPY_TERMINATE` | 终止请求 |
| TERMINATE_RESPONSE | `SCRCPY_TERMINATE_ACK` | 终止确认 |

---

## 核心方法

```java
public class UdpDiscoveryReceiver {
    // 构造函数
    public UdpDiscoveryReceiver(int port, boolean stayAliveMode);

    // 开始监听 (阻塞)
    public void startListening() throws IOException;

    // 仅监听终止请求
    public void listenForTerminate();

    // 停止监听
    public void stop();

    // 状态检查
    public boolean isWakeRequested();
    public boolean isTerminateRequested();
    public InetAddress getClientAddress();
}
```

---

## 使用场景

### 场景 1: 设备发现

```
客户端                                服务端
   │                                    │
   │──── "SCRCPY_DISCOVER" ────────────►│
   │◄─── "SCRCPY_HERE Pixel6 192.168.1.100 single" ──│
   │                                    │
```

### 场景 2: 唤醒服务器

```
客户端                                服务端
   │                                    │
   │──── "WAKE_UP" ────────────────────►│
   │◄─── "WAKE_ACK" ────────────────────│
   │                                    │
   │        (服务器启动)                  │
   │                                    │
```

### 场景 3: 远程终止

```
客户端                                服务端
   │                                    │
   │──── "SCRCPY_TERMINATE" ───────────►│
   │◄─── "SCRCPY_TERMINATE_ACK" ────────│
   │                                    │
   │        (服务器关闭连接)              │
   │                                    │
```

---

## 默认端口

| 端口 | 用途 |
|------|------|
| 27183 | 默认发现端口 |
| 27186 | 网络模式发现端口 |

---

## 与 Server.java 集成

```java
// Server.java 中的使用
UdpDiscoveryReceiver discovery = new UdpDiscoveryReceiver(port, false);
Thread terminateThread = new Thread(() -> discovery.listenForTerminate());
terminateThread.start();

// 监控终止请求
while (!discovery.isTerminateRequested()) {
    Thread.sleep(500);
}
// 终止时关闭连接
connection.close();
```

---

## 相关文档

- [Server.md](Server.md) - 服务端主类
- [udp_discovery.md](../../../features/connection/discovery.md) - 客户端发现模块
