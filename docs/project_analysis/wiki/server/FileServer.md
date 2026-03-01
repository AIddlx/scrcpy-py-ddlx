# FileServer

> **文件**: `file/FileServer.java`
> **功能**: 独立 TCP 文件服务器

---

## 概述

`FileServer` 提供网络模式下的文件传输服务，独立于主数据通道运行。

---

## 架构

```
┌──────────────┐                    ┌──────────────┐
│   Python     │   TCP 文件通道      │   Android    │
│   Client     │ ──────────────────► │   FileServer │
│FileChannel   │    :随机端口        │              │
└──────────────┘ ◄───────────────── └──────────────┘
```

---

## 命令格式

### 请求

```
[session_id: 4B]           // 首次连接发送
[cmd: 1B][length: 4B][payload: NB]  // 每个命令
```

### 响应

```
[cmd | 0x80: 1B][status: 1B][length: 4B][payload: NB]

status: 0x00 = 成功, 0x01 = 失败
```

---

## 支持的命令

| 命令 | 值 | 说明 |
|------|-----|------|
| CMD_LIST_DIR | 0x01 | 列出目录 |
| CMD_PUSH_FILE | 0x02 | 上传文件 |
| CMD_PULL_FILE | 0x03 | 下载文件 |
| CMD_DELETE_FILE | 0x04 | 删除文件 |

---

## 核心方法

```java
public class FileServer {
    // 构造函数
    public FileServer();

    // 启动服务器
    public int start() throws IOException;  // 返回端口

    // 停止服务器
    public void stop();

    // 获取会话 ID
    public int getSessionId();
}
```

---

## 会话认证

```java
// 客户端连接时发送 session_id
int clientSessionId = input.readInt();

if (clientSessionId != sessionId) {
    // 拒绝连接
    return;
}
```

---

## 使用流程

```
1. Server.start() → 返回端口和 session_id
2. 客户端连接，发送 session_id
3. 客户端发送命令
4. FileChannelHandler 处理命令
5. 返回响应
```

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `FileServer.java` | 主服务器 |
| `FileChannelHandler.java` | 命令处理 |
| `FileCommands.java` | 命令常量 |

---

## 相关文档

- [file_channel.md](../../client/file_channel.md) - 客户端文件通道
- [network_file.md](../../../features/file_transfer/network_file.md) - 网络文件传输
