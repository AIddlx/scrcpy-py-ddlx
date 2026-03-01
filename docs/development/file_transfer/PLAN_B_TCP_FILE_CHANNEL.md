# 方案B: 独立 TCP 文件通道 - 详细实现计划

> **状态**: 设计完成，待实现
> **日期**: 2026-02-25
> **复杂度**: 中高 (约 12.5 人天)

---

## 完整修改清单

### Java 服务端修改

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `control/ControlMessage.java` | **修改** | 添加 `TYPE_OPEN_FILE_CHANNEL = 26` |
| `control/DeviceMessage.java` | **修改** | 添加 `TYPE_FILE_CHANNEL_INFO = 6`，添加 `port`/`sessionId` 字段 |
| `control/ControlMessageReader.java` | **修改** | 添加 `parseOpenFileChannel()` 方法 |
| `control/DeviceMessageWriter.java` | **修改** | 添加 `TYPE_FILE_CHANNEL_INFO` 序列化 |
| `control/Controller.java` | **修改** | 处理 `TYPE_OPEN_FILE_CHANNEL`，调用 FileServer |
| `control/DeviceMessageSender.java` | 无需修改 | 复用现有发送机制 |
| `file/FileServer.java` | **新增** | 独立 TCP 文件服务器 |
| `file/FileChannelHandler.java` | **新增** | 处理文件命令 |
| `file/FileCommands.java` | **新增** | 命令常量定义 |

### Python 客户端修改

| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `core/protocol.py` | **修改** | 添加 `OPEN_FILE_CHANNEL = 26`，`FILE_CHANNEL_INFO = 6` |
| `core/control.py` | **修改** | 添加 `set_open_file_channel()` 和序列化 |
| `core/device_msg.py` | **修改** | 添加 `FILE_CHANNEL_INFO` 类型和解析 |
| `client/client.py` | **修改** | 添加 `open_file_channel()` 方法 |
| `core/file/file_channel.py` | **新增** | 文件通道客户端 |
| `core/file/file_commands.py` | **新增** | 命令常量定义 |

---

## 阶段 1: 协议扩展

### 1.1 Java: ControlMessage.java

```java
// 在现有类型后添加
public static final int TYPE_OPEN_FILE_CHANNEL = 26;  // 请求打开文件通道

// 添加工厂方法
public static ControlMessage createOpenFileChannel() {
    ControlMessage msg = new ControlMessage();
    msg.type = TYPE_OPEN_FILE_CHANNEL;
    return msg;
}
```

### 1.2 Java: DeviceMessage.java

```java
// 在现有类型后添加
public static final int TYPE_FILE_CHANNEL_INFO = 6;  // 文件通道端口信息

// 添加字段
private int port;           // 文件服务器端口
private int sessionId;      // 会话ID (用于验证)

// 添加工厂方法
public static DeviceMessage createFileChannelInfo(int port, int sessionId) {
    DeviceMessage event = new DeviceMessage();
    event.type = TYPE_FILE_CHANNEL_INFO;
    event.port = port;
    event.sessionId = sessionId;
    return event;
}

// 添加 getter
public int getPort() { return port; }
public int getSessionId() { return sessionId; }
```

### 1.3 Java: ControlMessageReader.java

```java
// 在 read() 方法的 switch 中添加
case ControlMessage.TYPE_OPEN_FILE_CHANNEL:
    return parseOpenFileChannel();

// 添加解析方法
private ControlMessage parseOpenFileChannel() throws IOException {
    // 空消息，只有类型字节
    return ControlMessage.createOpenFileChannel();
}
```

### 1.4 Java: DeviceMessageWriter.java

```java
// 在 write() 方法的 switch 中添加
case DeviceMessage.TYPE_FILE_CHANNEL_INFO:
    dos.writeShort(msg.getPort());      // 2 bytes: port
    dos.writeInt(msg.getSessionId());   // 4 bytes: session ID
    break;
```

### 1.5 Python: protocol.py

```python
class ControlMessageType(IntEnum):
    # ...existing...
    PING = 25
    OPEN_FILE_CHANNEL = 26  # 新增

class DeviceMessageType(IntEnum):
    # ...existing...
    PONG = 5
    FILE_CHANNEL_INFO = 6   # 新增
```

---

## 阶段 2: Java 文件服务器实现

### 2.1 新建: file/FileCommands.java

```java
package com.genymobile.scrcpy.file;

/**
 * 文件通道命令常量
 */
public final class FileCommands {
    // 客户端 -> 服务器
    public static final int CMD_LIST = 1;           // 列出目录
    public static final int CMD_PULL = 3;           // 下载文件
    public static final int CMD_PUSH = 5;           // 开始上传
    public static final int CMD_PUSH_DATA = 6;      // 上传数据块
    public static final int CMD_DELETE = 8;         // 删除文件
    public static final int CMD_MKDIR = 9;          // 创建目录
    public static final int CMD_STAT = 10;          // 获取文件信息

    // 服务器 -> 客户端
    public static final int CMD_LIST_RESP = 2;      // 目录列表响应
    public static final int CMD_PULL_DATA = 4;      // 文件数据块
    public static final int CMD_PUSH_ACK = 7;       // 上传确认
    public static final int CMD_STAT_RESP = 11;     // 文件信息响应
    public static final int CMD_ERROR = 255;        // 错误响应

    // 块大小
    public static final int CHUNK_SIZE = 64 * 1024; // 64KB
}
```

### 2.2 新建: file/FileServer.java

```java
package com.genymobile.scrcpy.file;

import com.genymobile.scrcpy.util.Ln;

import java.io.*;
import java.net.*;
import java.nio.channels.*;
import java.util.concurrent.*;

public class FileServer {
    private static final int BACKLOG = 1;

    private ServerSocketChannel serverChannel;
    private ExecutorService executor;
    private volatile boolean running = false;
    private int sessionId;

    public FileServer() {
        this.sessionId = (int) (System.currentTimeMillis() & 0x7FFFFFFF);
    }

    /**
     * 启动文件服务器，返回监听端口
     */
    public int start() throws IOException {
        serverChannel = ServerSocketChannel.open();
        serverChannel.socket().bind(new InetSocketAddress(0), BACKLOG);
        serverChannel.configureBlocking(true);

        int port = serverChannel.socket().getLocalPort();
        running = true;
        executor = Executors.newCachedThreadPool(r -> {
            Thread t = new Thread(r, "file-client");
            t.setDaemon(true);
            return t;
        });

        new Thread(this::acceptLoop, "file-server").start();
        Ln.i("FileServer started on port " + port + ", sessionId=" + sessionId);
        return port;
    }

    public void stop() {
        running = false;
        try {
            if (serverChannel != null) {
                serverChannel.close();
            }
        } catch (IOException e) {
            // ignore
        }
        if (executor != null) {
            executor.shutdownNow();
        }
        Ln.i("FileServer stopped");
    }

    public int getSessionId() {
        return sessionId;
    }

    private void acceptLoop() {
        while (running) {
            try {
                SocketChannel client = serverChannel.accept();
                executor.submit(() -> handleClient(client));
            } catch (IOException e) {
                if (running) {
                    Ln.e("FileServer accept error", e);
                }
            }
        }
    }

    private void handleClient(SocketChannel client) {
        try (SocketChannel ch = client) {
            ch.configureBlocking(true);

            // 读取 session_id 验证
            DataInputStream input = new DataInputStream(
                Channels.newInputStream(ch));
            int clientSessionId = input.readInt();

            if (clientSessionId != sessionId) {
                Ln.w("FileServer: invalid session_id " + clientSessionId);
                return;
            }

            Ln.d("FileServer: client connected with valid session_id");

            DataOutputStream output = new DataOutputStream(
                Channels.newOutputStream(ch));

            while (running && ch.isConnected()) {
                // 读取命令帧: [cmd:1B][length:4B][payload:N]
                int cmd = input.readUnsignedByte();
                int length = input.readInt();
                byte[] payload = new byte[length];
                if (length > 0) {
                    input.readFully(payload);
                }

                // 处理命令
                FileChannelHandler.handle(cmd, payload, output);
            }
        } catch (IOException e) {
            Ln.d("FileServer client disconnected: " + e.getMessage());
        }
    }
}
```

### 2.3 新建: file/FileChannelHandler.java

```java
package com.genymobile.scrcpy.file;

import com.genymobile.scrcpy.util.Ln;
import org.json.*;

import java.io.*;
import java.nio.charset.StandardCharsets;

public class FileChannelHandler {

    static void handle(int cmd, byte[] payload, DataOutputStream output)
            throws IOException {
        switch (cmd) {
            case FileCommands.CMD_LIST:
                handleList(payload, output);
                break;
            case FileCommands.CMD_PULL:
                handlePull(payload, output);
                break;
            case FileCommands.CMD_PUSH:
                handlePushStart(payload, output);
                break;
            case FileCommands.CMD_PUSH_DATA:
                handlePushData(payload, output);
                break;
            case FileCommands.CMD_DELETE:
                handleDelete(payload, output);
                break;
            case FileCommands.CMD_MKDIR:
                handleMkdir(payload, output);
                break;
            case FileCommands.CMD_STAT:
                handleStat(payload, output);
                break;
            default:
                sendError(output, "Unknown command: " + cmd);
        }
    }

    static void handleList(byte[] payload, DataOutputStream output)
            throws IOException {
        String path = new String(payload, StandardCharsets.UTF_8);
        File dir = new File(path);

        JSONObject result = new JSONObject();
        result.put("path", path);

        JSONArray entries = new JSONArray();
        File[] files = dir.listFiles();
        if (files != null) {
            for (File file : files) {
                JSONObject entry = new JSONObject();
                entry.put("name", file.getName());
                entry.put("type", file.isDirectory() ? "directory" : "file");
                entry.put("size", file.length());
                entry.put("mtime", file.lastModified());
                entries.put(entry);
            }
        }
        result.put("entries", entries);

        sendResponse(output, FileCommands.CMD_LIST_RESP,
                     result.toString().getBytes(StandardCharsets.UTF_8));
        Ln.d("FileServer: LIST " + path + " -> " + files.length + " entries");
    }

    static void handlePull(byte[] payload, DataOutputStream output)
            throws IOException {
        String path = new String(payload, StandardCharsets.UTF_8);
        File file = new File(path);

        if (!file.exists() || !file.isFile()) {
            sendError(output, "File not found: " + path);
            return;
        }

        long totalSize = file.length();
        byte[] buffer = new byte[FileCommands.CHUNK_SIZE];

        try (FileInputStream fis = new FileInputStream(file)) {
            int chunkId = 0;
            int bytesRead;
            while ((bytesRead = fis.read(buffer)) != -1) {
                // 帧格式: [chunk_id:4B][total_size:8B][data:N]
                ByteArrayOutputStream bos = new ByteArrayOutputStream();
                DataOutputStream frame = new DataOutputStream(bos);
                frame.writeInt(chunkId);
                frame.writeLong(totalSize);
                frame.write(buffer, 0, bytesRead);

                sendResponse(output, FileCommands.CMD_PULL_DATA,
                             bos.toByteArray());
                chunkId++;
            }
        }
        Ln.d("FileServer: PULL " + path + " -> " + totalSize + " bytes");
    }

    // PUSH 状态管理 (简化版，单文件)
    private static String currentPushPath = null;
    private static FileOutputStream currentPushStream = null;
    private static long currentPushTotal = 0;
    private static long currentPushReceived = 0;

    static void handlePushStart(byte[] payload, DataOutputStream output)
            throws IOException {
        // 格式: [total_size:8B][path_len:2B][path:N]
        DataInputStream input = new DataInputStream(
            new ByteArrayInputStream(payload));

        long totalSize = input.readLong();
        int pathLen = input.readUnsignedShort();
        byte[] pathBytes = new byte[pathLen];
        input.readFully(pathBytes);
        String path = new String(pathBytes, StandardCharsets.UTF_8);

        // 关闭之前的传输
        if (currentPushStream != null) {
            try { currentPushStream.close(); } catch (Exception e) {}
        }

        // 创建父目录
        File file = new File(path);
        file.getParentFile().mkdirs();

        currentPushPath = path;
        currentPushStream = new FileOutputStream(path);
        currentPushTotal = totalSize;
        currentPushReceived = 0;

        // 发送 ACK
        sendPushAck(output, 0);
        Ln.d("FileServer: PUSH start " + path + ", total=" + totalSize);
    }

    static void handlePushData(byte[] payload, DataOutputStream output)
            throws IOException {
        if (currentPushStream == null) {
            sendError(output, "No active push session");
            return;
        }

        // 格式: [chunk_id:4B][data:N]
        DataInputStream input = new DataInputStream(
            new ByteArrayInputStream(payload));
        int chunkId = input.readInt();
        byte[] data = new byte[payload.length - 4];
        input.readFully(data);

        currentPushStream.write(data);
        currentPushReceived += data.length;

        // 发送 ACK
        sendPushAck(output, chunkId);

        // 检查是否完成
        if (currentPushReceived >= currentPushTotal) {
            currentPushStream.close();
            currentPushStream = null;
            Ln.d("FileServer: PUSH complete " + currentPushPath +
                 ", received=" + currentPushReceived);
        }
    }

    static void handleDelete(byte[] payload, DataOutputStream output)
            throws IOException {
        String path = new String(payload, StandardCharsets.UTF_8);
        boolean success = deleteRecursively(new File(path));

        JSONObject result = new JSONObject();
        result.put("path", path);
        result.put("success", success);
        sendResponse(output, FileCommands.CMD_STAT_RESP,
                     result.toString().getBytes(StandardCharsets.UTF_8));
        Ln.d("FileServer: DELETE " + path + " -> " + success);
    }

    static void handleMkdir(byte[] payload, DataOutputStream output)
            throws IOException {
        String path = new String(payload, StandardCharsets.UTF_8);
        boolean success = new File(path).mkdirs();

        JSONObject result = new JSONObject();
        result.put("path", path);
        result.put("success", success);
        sendResponse(output, FileCommands.CMD_STAT_RESP,
                     result.toString().getBytes(StandardCharsets.UTF_8));
        Ln.d("FileServer: MKDIR " + path + " -> " + success);
    }

    static void handleStat(byte[] payload, DataOutputStream output)
            throws IOException {
        String path = new String(payload, StandardCharsets.UTF_8);
        File file = new File(path);

        JSONObject result = new JSONObject();
        result.put("path", path);
        result.put("exists", file.exists());
        if (file.exists()) {
            result.put("type", file.isDirectory() ? "directory" : "file");
            result.put("size", file.length());
            result.put("mtime", file.lastModified());
            result.put("canRead", file.canRead());
            result.put("canWrite", file.canWrite());
        }

        sendResponse(output, FileCommands.CMD_STAT_RESP,
                     result.toString().getBytes(StandardCharsets.UTF_8));
        Ln.d("FileServer: STAT " + path);
    }

    // === 工具方法 ===

    private static void sendResponse(DataOutputStream output, int cmd,
                                     byte[] data) throws IOException {
        output.writeByte(cmd);
        output.writeInt(data.length);
        output.write(data);
        output.flush();
    }

    private static void sendError(DataOutputStream output, String message)
            throws IOException {
        sendResponse(output, FileCommands.CMD_ERROR,
                     message.getBytes(StandardCharsets.UTF_8));
    }

    private static void sendPushAck(DataOutputStream output, int chunkId)
            throws IOException {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        DataOutputStream frame = new DataOutputStream(bos);
        frame.writeInt(chunkId);
        frame.writeByte(0); // status = OK

        sendResponse(output, FileCommands.CMD_PUSH_ACK, bos.toByteArray());
    }

    private static boolean deleteRecursively(File file) {
        if (file.isDirectory()) {
            File[] children = file.listFiles();
            if (children != null) {
                for (File child : children) {
                    deleteRecursively(child);
                }
            }
        }
        return file.delete();
    }
}
```

### 2.4 修改: control/Controller.java

```java
// 添加导入
import com.genymobile.scrcpy.file.FileServer;

// 添加字段
private FileServer fileServer;

// 在 handleEvent() 的 switch 中添加
case ControlMessage.TYPE_OPEN_FILE_CHANNEL:
    openFileChannel();
    break;

// 添加方法
private void openFileChannel() {
    try {
        if (fileServer == null) {
            fileServer = new FileServer();
        }
        int port = fileServer.start();
        int sessionId = fileServer.getSessionId();

        DeviceMessage msg = DeviceMessage.createFileChannelInfo(port, sessionId);
        sender.send(msg);
        Ln.i("File channel opened: port=" + port + ", sessionId=" + sessionId);
    } catch (Exception e) {
        Ln.e("Failed to open file channel", e);
    }
}

// 在 stop() 方法中添加
if (fileServer != null) {
    fileServer.stop();
}
```

---

## 阶段 3: Python 客户端实现

### 3.1 修改: core/control.py

```python
# 添加到 ControlMessage 类

def set_open_file_channel(self):
    """请求打开文件通道"""
    pass  # 空消息，只有类型字节

# 在 serialize() 方法中添加
elif self.type == ControlMessageType.OPEN_FILE_CHANNEL:
    buf.append(self.type)  # 只有类型字节
```

### 3.2 修改: core/device_msg.py

```python
# 添加到 DeviceMessageType 枚举
class DeviceMessageType(Enum):
    # ...existing...
    FILE_CHANNEL_INFO = 6   # 文件通道端口信息

# 添加到 ReceiverCallbacks
@dataclass
class ReceiverCallbacks:
    # ...existing...
    on_file_channel_info: Optional[Callable[[int, int], None]] = None  # port, session_id

# 添加到 _process_buffer()
elif msg_type == DeviceMessageType.FILE_CHANNEL_INFO.value:
    return self._process_file_channel_info(buffer, size)

# 添加新方法
def _process_file_channel_info(self, buffer: bytearray, size: int) -> int:
    """
    处理 FILE_CHANNEL_INFO 消息 (type 6).

    格式:
    - 1 byte: type = 6
    - 2 bytes: port (big-endian)
    - 4 bytes: session_id (big-endian)
    """
    if size < 7:
        return 0

    port = struct.unpack(">H", buffer[1:3])[0]
    session_id = struct.unpack(">I", buffer[3:7])[0]

    logger.info(f"[DeviceReceiver] FILE_CHANNEL_INFO: port={port}, session_id={session_id}")

    if self._callbacks.on_file_channel_info:
        try:
            self._callbacks.on_file_channel_info(port, session_id)
        except Exception as e:
            logger.error(f"FILE_CHANNEL_INFO callback error: {e}")

    return 7
```

### 3.3 新建: core/file/__init__.py

```python
"""文件传输模块"""
from .file_channel import FileChannel
from .file_commands import FileCommand
```

### 3.4 新建: core/file/file_commands.py

```python
"""文件通道命令常量"""
from enum import IntEnum


class FileCommand(IntEnum):
    """文件通道命令类型"""
    # 客户端 -> 服务器
    LIST = 1           # 列出目录
    PULL = 3           # 下载文件
    PUSH = 5           # 开始上传
    PUSH_DATA = 6      # 上传数据块
    DELETE = 8         # 删除文件
    MKDIR = 9          # 创建目录
    STAT = 10          # 获取文件信息

    # 服务器 -> 客户端
    LIST_RESP = 2      # 目录列表响应
    PULL_DATA = 4      # 文件数据块
    PUSH_ACK = 7       # 上传确认
    STAT_RESP = 11     # 文件信息响应
    ERROR = 255        # 错误响应


CHUNK_SIZE = 64 * 1024  # 64KB
```

### 3.5 新建: core/file/file_channel.py

```python
"""独立文件通道客户端"""
import json
import logging
import socket
import struct
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, List
from queue import Queue

from .file_commands import FileCommand, CHUNK_SIZE

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """文件信息"""
    name: str
    type: str  # "file" or "directory"
    size: int
    mtime: int


class FileChannel:
    """独立文件传输通道"""

    def __init__(self):
        self._socket: Optional[socket.socket] = None
        self._connected = False
        self._lock = threading.Lock()
        self._response_queue = Queue()
        self._reader_thread: Optional[threading.Thread] = None

    def connect(self, host: str, port: int, session_id: int) -> bool:
        """连接到文件服务器"""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(30.0)
            self._socket.connect((host, port))
            self._connected = True

            # 发送 session_id 验证
            self._socket.sendall(struct.pack(">I", session_id))

            # 启动读取线程
            self._reader_thread = threading.Thread(
                target=self._read_loop, daemon=True, name="FileChannelReader")
            self._reader_thread.start()

            logger.info(f"FileChannel connected to {host}:{port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect file channel: {e}")
            return False

    def close(self):
        """关闭连接"""
        self._connected = False
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
            self._socket = None
        logger.info("FileChannel closed")

    def list_dir(self, path: str, timeout: float = 10.0) -> List[FileInfo]:
        """列出目录 (同步)"""
        with self._lock:
            self._send_command(FileCommand.LIST, path.encode('utf-8'))

        response = self._response_queue.get(timeout=timeout)
        if response['cmd'] == FileCommand.ERROR:
            raise Exception(response['data'].decode('utf-8'))

        data = json.loads(response['data'].decode('utf-8'))
        return [
            FileInfo(
                name=e['name'],
                type=e['type'],
                size=e['size'],
                mtime=e['mtime']
            )
            for e in data['entries']
        ]

    def pull_file(self, device_path: str, local_path: str,
                  on_progress: Optional[Callable[[int, int], None]] = None):
        """下载文件 (同步)"""
        with self._lock:
            self._send_command(FileCommand.PULL, device_path.encode('utf-8'))

        total_size = 0
        received = 0

        with open(local_path, 'wb') as f:
            while True:
                response = self._response_queue.get(timeout=60.0)
                if response['cmd'] == FileCommand.ERROR:
                    raise Exception(response['data'].decode('utf-8'))

                if response['cmd'] == FileCommand.PULL_DATA:
                    chunk_id, total, data = self._parse_pull_data(response['data'])
                    total_size = total
                    f.write(data)
                    received += len(data)

                    if on_progress:
                        on_progress(received, total_size)

                    # 检查是否完成
                    if len(data) == 0 or received >= total_size:
                        break

        logger.info(f"Pull complete: {device_path} -> {local_path} ({received} bytes)")

    def push_file(self, local_path: str, device_path: str,
                  on_progress: Optional[Callable[[int, int], None]] = None):
        """上传文件 (同步)"""
        path = Path(local_path)
        total_size = path.stat().st_size

        # 发送开始帧
        with self._lock:
            path_bytes = device_path.encode('utf-8')
            header = struct.pack(">QH", total_size, len(path_bytes)) + path_bytes
            self._send_command(FileCommand.PUSH, header)

        # 等待 ACK
        ack = self._response_queue.get(timeout=30.0)
        if ack['cmd'] == FileCommand.ERROR:
            raise Exception(ack['data'].decode('utf-8'))

        # 分块发送
        sent = 0
        chunk_id = 0
        with open(local_path, 'rb') as f:
            while sent < total_size:
                data = f.read(CHUNK_SIZE)
                if not data:
                    break

                frame = struct.pack(">I", chunk_id) + data
                with self._lock:
                    self._send_command(FileCommand.PUSH_DATA, frame)

                # 等待 ACK
                ack = self._response_queue.get(timeout=30.0)
                if ack['cmd'] == FileCommand.ERROR:
                    raise Exception(ack['data'].decode('utf-8'))

                sent += len(data)
                chunk_id += 1

                if on_progress:
                    on_progress(sent, total_size)

        logger.info(f"Push complete: {local_path} -> {device_path} ({sent} bytes)")

    def delete(self, device_path: str) -> bool:
        """删除文件或目录"""
        with self._lock:
            self._send_command(FileCommand.DELETE, device_path.encode('utf-8'))

        response = self._response_queue.get(timeout=30.0)
        if response['cmd'] == FileCommand.ERROR:
            raise Exception(response['data'].decode('utf-8'))

        data = json.loads(response['data'].decode('utf-8'))
        return data.get('success', False)

    def mkdir(self, device_path: str) -> bool:
        """创建目录"""
        with self._lock:
            self._send_command(FileCommand.MKDIR, device_path.encode('utf-8'))

        response = self._response_queue.get(timeout=30.0)
        if response['cmd'] == FileCommand.ERROR:
            raise Exception(response['data'].decode('utf-8'))

        data = json.loads(response['data'].decode('utf-8'))
        return data.get('success', False)

    def stat(self, device_path: str) -> Optional[dict]:
        """获取文件信息"""
        with self._lock:
            self._send_command(FileCommand.STAT, device_path.encode('utf-8'))

        response = self._response_queue.get(timeout=30.0)
        if response['cmd'] == FileCommand.ERROR:
            raise Exception(response['data'].decode('utf-8'))

        data = json.loads(response['data'].decode('utf-8'))
        return data if data.get('exists') else None

    # === 内部方法 ===

    def _send_command(self, cmd: int, data: bytes):
        """发送命令帧"""
        frame = struct.pack(">BI", cmd, len(data)) + data
        self._socket.sendall(frame)

    def _read_loop(self):
        """读取响应的线程"""
        try:
            while self._connected:
                # 读取帧头: [cmd:1B][length:4B]
                header = self._recv_exactly(5)
                cmd, length = struct.unpack(">BI", header)

                # 读取负载
                data = self._recv_exactly(length) if length > 0 else b''

                self._response_queue.put({
                    'cmd': cmd,
                    'data': data
                })
        except Exception as e:
            if self._connected:
                logger.error(f"File channel read error: {e}")
            self._response_queue.put({
                'cmd': FileCommand.ERROR,
                'data': str(e).encode('utf-8')
            })

    def _recv_exactly(self, n: int) -> bytes:
        """精确读取 n 字节"""
        data = b''
        while len(data) < n:
            chunk = self._socket.recv(n - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk
        return data

    def _parse_pull_data(self, data: bytes) -> tuple:
        """解析 PULL_DATA 帧"""
        chunk_id, total = struct.unpack(">IQ", data[:12])
        return chunk_id, total, data[12:]
```

### 3.6 修改: client/client.py

在 Client 类中添加:

```python
from ..core.file import FileChannel

class Client:
    def __init__(self, ...):
        # ...existing...
        self._file_channel: Optional[FileChannel] = None
        self._file_channel_ready = threading.Event()

    def _setup_callbacks(self):
        # ...existing...
        self._receiver_callbacks.on_file_channel_info = self._on_file_channel_info

    def _on_file_channel_info(self, port: int, session_id: int):
        """处理文件通道信息响应"""
        try:
            # 获取服务器地址 (从控制连接获取)
            host = self._get_server_host()

            self._file_channel = FileChannel()
            if self._file_channel.connect(host, port, session_id):
                self._file_channel_ready.set()
                logger.info(f"File channel ready: {host}:{port}")
            else:
                logger.error("Failed to connect file channel")
        except Exception as e:
            logger.error(f"Error setting up file channel: {e}")

    def _get_server_host(self) -> str:
        """获取服务器主机地址"""
        # 从现有连接获取
        if hasattr(self, '_control_socket') and self._control_socket:
            return self._control_socket.getpeername()[0]
        return "127.0.0.1"

    def open_file_channel(self, timeout: float = 10.0) -> bool:
        """请求打开文件通道"""
        msg = ControlMessage(ControlMessageType.OPEN_FILE_CHANNEL)
        self._control_sender.send(msg)

        # 等待响应
        return self._file_channel_ready.wait(timeout)

    @property
    def file_channel(self) -> Optional[FileChannel]:
        """获取文件通道 (需先调用 open_file_channel)"""
        return self._file_channel
```

---

## 实现顺序

```
阶段 1: 协议扩展 (1天)
├── 1.1 Java: ControlMessage.java
├── 1.2 Java: DeviceMessage.java
├── 1.3 Java: ControlMessageReader.java
├── 1.4 Java: DeviceMessageWriter.java
├── 1.5 Python: protocol.py
└── 测试: 编译通过，协议一致

阶段 2: Java 文件服务器 (4天)
├── 2.1 新建 file/FileCommands.java
├── 2.2 新建 file/FileServer.java
├── 2.3 新建 file/FileChannelHandler.java
├── 2.4 修改 control/Controller.java
└── 测试: Java 端独立测试

阶段 3: Python 客户端 (5天)
├── 3.1 修改 core/control.py
├── 3.2 修改 core/device_msg.py
├── 3.3 新建 core/file/__init__.py
├── 3.4 新建 core/file/file_commands.py
├── 3.5 新建 core/file/file_channel.py
├── 3.6 修改 client/client.py
└── 测试: 端到端测试

阶段 4: 集成测试 (2.5天)
├── ADB 模式测试
├── 网络模式测试
├── 错误处理测试
└── 性能测试
```

---

## 风险和注意事项

1. **线程安全**: FileServer 使用多线程，需要确保 FileChannelHandler 的状态管理是线程安全的

2. **资源清理**: Controller.stop() 必须关闭 FileServer

3. **超时处理**: 所有 socket 操作都需要设置超时

4. **大文件**: 需要测试大文件传输 (>100MB)

5. **网络模式**: 需要确保文件端口可达 (可能需要 ADB 端口转发)
