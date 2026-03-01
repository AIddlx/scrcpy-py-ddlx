# 文件服务器 (FileServer.java)

> 网络模式文件传输服务

---

## 文件位置

```
scrcpy/server/src/main/java/com/genymobile/scrcpy/file/
├── FileServer.java          # 主服务器
├── FileChannelHandler.java  # 通道处理
└── FileCommands.java        # 命令常量
```

---

## 概述

网络模式下独立的 TCP 文件传输服务，不依赖 ADB。

---

## 通道结构

```
┌──────────┐   TCP :27185   ┌──────────┐
│  Client  │ ─────────────► │  Server  │
│ (Python) │                │ (Android)│
└──────────┘ ◄───────────── └──────────┘
```

---

## 命令类型

| 命令 | 值 | 说明 |
|------|-----|------|
| `CMD_LIST_DIR` | 0x01 | 列出目录 |
| `CMD_PUSH_FILE` | 0x02 | 上传文件 |
| `CMD_PULL_FILE` | 0x03 | 下载文件 |
| `CMD_DELETE_FILE` | 0x04 | 删除文件 |
| `CMD_RESPONSE` | 0x80 | 响应标志 |

---

## 消息格式

### 请求

```
[cmd: 1字节] [length: 4字节] [payload: N字节]
```

### 响应

```
[cmd: 1字节 | 0x80] [status: 1字节] [length: 4字节] [payload: N字节]

status:
  0 = 成功
  1 = 失败
```

---

## 核心类

### FileServer

```java
public class FileServer {
    public void start(int port);
    public void stop();
}
```

### FileChannelHandler

```java
public class FileChannelHandler {
    public void handleCommand(InputStream in, OutputStream out);
}
```

---

## 相关文档

- [网络文件传输](../file_transfer/network_file.md)
