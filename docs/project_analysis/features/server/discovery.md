# UDP 发现/终止 (UdpDiscoveryReceiver.java)

> 设备发现和远程终止支持

---

## 文件位置

```
scrcpy/server/src/main/java/com/genymobile/scrcpy/udp/UdpDiscoveryReceiver.java
```

---

## 功能

| 功能 | 说明 |
|------|------|
| 设备发现 | 响应客户端查询请求 |
| 远程终止 | 接收终止命令并停止服务器 |
| 状态查询 | 返回服务器运行状态 |

---

## 协议

### 发现请求

```
客户端 → 服务端: "SCRCPY_DISCOVER"
服务端 → 客户端: JSON 响应
```

### 发现响应

```json
{
  "device": "Pixel 6",
  "serial": "12345678",
  "ip": "192.168.1.100",
  "port": 27184,
  "version": "1.4",
  "status": "running"
}
```

### 终止请求

```
客户端 → 服务端: "SCRCPY_TERMINATE"
服务端: 设置终止标志，关闭连接
```

---

## 核心方法

```java
// 监听发现/终止请求
public void listenForTerminate()

// 检查是否收到终止请求
public boolean isTerminateRequested()

// 停止监听
public void stop()
```

---

## 默认端口

| 端口 | 用途 |
|------|------|
| 27186 | UDP 发现/终止 |

---

## 相关文档

- [连接管理](../connection/README.md)
- [设备发现](../connection/discovery.md)
