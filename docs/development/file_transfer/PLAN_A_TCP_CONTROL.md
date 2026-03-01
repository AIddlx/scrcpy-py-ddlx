# 方案A: TCP 控制通道文件传输

> **状态**: 设计完成，待实现
> **日期**: 2026-02-25
> **复杂度**: 高 (约 15 人天)

---

## 概述

扩展现有 TCP 控制通道，添加文件操作消息类型。所有文件传输复用现有的 ControlMessage/DeviceMessage 协议。

## 架构

```
┌─────────────────────┐    ControlChannel    ┌─────────────────────┐
│  PC Python Client   │◄════════════════════►│  Android scrcpy     │
│  file_ops.py        │    (双向消息)         │  FileTransferHandler│
│  (新模块)           │                       │  (新模块)           │
└─────────────────────┘                       └─────────────────────┘
```

---

## 协议设计

### 新增 ControlMessage 类型 (PC → Android)

| 类型 | 值 | 说明 |
|------|-----|------|
| TYPE_FILE_LIST | 26 | 列出目录 |
| TYPE_FILE_PULL | 27 | 请求下载文件 |
| TYPE_FILE_PUSH_START | 28 | 开始上传 |
| TYPE_FILE_PUSH_DATA | 29 | 上传数据块 |
| TYPE_FILE_PUSH_END | 30 | 结束上传 |
| TYPE_FILE_DELETE | 31 | 删除文件 |
| TYPE_FILE_MKDIR | 32 | 创建目录 |
| TYPE_FILE_STAT | 33 | 获取文件信息 |

### 新增 DeviceMessage 类型 (Android → PC)

| 类型 | 值 | 说明 |
|------|-----|------|
| TYPE_FILE_LIST | 6 | 目录列表响应 |
| TYPE_FILE_PULL_DATA | 7 | 下载文件数据 |
| TYPE_FILE_PULL_END | 8 | 下载结束 |
| TYPE_FILE_PUSH_ACK | 9 | 上传确认 |
| TYPE_FILE_ERROR | 10 | 错误响应 |
| TYPE_FILE_STAT | 11 | 文件信息响应 |

---

## 消息格式

### TYPE_FILE_LIST (请求)

```
┌─────────────┬──────────────┬─────────────────┐
│ type (1B)   │ path_len (2B)│ path (variable) │
│ = 26        │ big-endian   │ UTF-8 string    │
└─────────────┴──────────────┴─────────────────┘
```

### TYPE_FILE_LIST (响应)

```
┌─────────────┬──────────────┬───────────────────────────────────┐
│ type (1B)   │ count (2B)   │ entries...                        │
│ = 6         │ big-endian   │ (每个 entry 格式见下)              │
└─────────────┴──────────────┴───────────────────────────────────┘

Entry 格式:
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┬───────────┐
│ name_len(2B) │ name         │ type (1B)    │ size (8B)    │ mtime (8B)   │ perm(2B)  │
│              │ UTF-8        │ 0=file,1=dir │ big-endian   │ Unix时间戳   │ mode      │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┴───────────┘
```

### TYPE_FILE_PUSH_DATA (分块上传)

```
┌─────────────┬──────────────┬──────────────┬─────────────────┐
│ type (1B)   │ chunk_id (4B)│ data_len (4B)│ data            │
│ = 29        │ big-endian   │ big-endian   │ binary          │
└─────────────┴──────────────┴──────────────┴─────────────────┘

建议块大小: 64KB (MESSAGE_MAX_SIZE = 256KB, 留余量给 header)
```

### TYPE_FILE_PULL_DATA (分块下载)

```
┌─────────────┬──────────────┬──────────────┬─────────────────┐
│ type (1B)   │ chunk_id (4B)│ data_len (4B)│ data            │
│ = 7         │ big-endian   │ big-endian   │ binary          │
└─────────────┴──────────────┴──────────────┴─────────────────┘
```

---

## 流程设计

### 上传文件 (PC → Android)

```
PC                                    Android
 │                                       │
 │──── TYPE_FILE_PUSH_START ────────────►│
 │     (path, total_size, chunk_size)    │
 │                                       │
 │◄─── TYPE_FILE_PUSH_ACK ───────────────│
 │     (transfer_id, accepted)           │
 │                                       │
 │──── TYPE_FILE_PUSH_DATA ─────────────►│
 │     (chunk_id=0, data)                │
 │                                       │
 │◄─── TYPE_FILE_PUSH_ACK ───────────────│
 │     (chunk_id=0, received)            │
 │                                       │
 │──── TYPE_FILE_PUSH_DATA ─────────────►│
 │     (chunk_id=1, data)                │
 │              ...                      │
 │                                       │
 │──── TYPE_FILE_PUSH_END ──────────────►│
 │     (transfer_id)                     │
 │                                       │
 │◄─── TYPE_FILE_PUSH_ACK ───────────────│
 │     (transfer_id, completed)          │
 │                                       │
```

### 下载文件 (Android → PC)

```
PC                                    Android
 │                                       │
 │──── TYPE_FILE_PULL ──────────────────►│
 │     (path)                            │
 │                                       │
 │◄─── TYPE_FILE_PULL_DATA ──────────────│
 │     (chunk_id=0, total_chunks, data)  │
 │                                       │
 │◄─── TYPE_FILE_PULL_DATA ──────────────│
 │     (chunk_id=1, data)                │
 │              ...                      │
 │                                       │
 │◄─── TYPE_FILE_PULL_END ───────────────│
 │     (total_size, checksum)            │
 │                                       │
```

---

## Java 实现设计

### 新增文件: FileTransferHandler.java

```java
package com.genymobile.scrcpy;

import java.io.*;
import java.nio.file.*;
import java.nio.file.attribute.*;

public class FileTransferHandler {
    private static final int CHUNK_SIZE = 64 * 1024; // 64KB

    public static byte[] handleListDir(String path) throws IOException {
        ByteArrayOutputStream bos = new ByteArrayOutputStream();
        DataOutput output = new DataOutputStream(bos);

        File dir = new File(path);
        File[] files = dir.listFiles();
        if (files == null) {
            throw new IOException("Cannot list directory: " + path);
        }

        // 写入条目数
        output.writeShort(files.length);

        for (File file : files) {
            // name_len + name
            byte[] nameBytes = file.getName().getBytes("UTF-8");
            output.writeShort(nameBytes.length);
            output.write(nameBytes);

            // type
            output.writeByte(file.isDirectory() ? 1 : 0);

            // size
            output.writeLong(file.length());

            // mtime
            output.writeLong(file.lastModified());

            // permissions
            output.writeShort(file.canRead() ? 0444 : 0);
        }

        return bos.toByteArray();
    }

    public static byte[] handleFilePull(String path, int chunkId)
            throws IOException {
        // 读取文件指定块
        try (RandomAccessFile raf = new RandomAccessFile(path, "r")) {
            raf.seek(chunkId * CHUNK_SIZE);
            byte[] buffer = new byte[CHUNK_SIZE];
            int read = raf.read(buffer);

            // 构建响应消息
            // ...
        }
    }

    public static void handleFilePushData(String path, int chunkId, byte[] data)
            throws IOException {
        // 写入数据块到临时文件
        // 完成后重命名为目标文件
    }
}
```

### 修改: Device.java

```java
// 添加文件操作消息处理
private void handleFileControlMessage(ControlMessage msg) {
    try {
        switch (msg.getType()) {
            case ControlMessage.TYPE_FILE_LIST:
                byte[] listResult = FileTransferHandler.handleListDir(msg.getText());
                DeviceMessage response = DeviceMessage.createFileList(listResult);
                sender.sendDeviceMessage(response);
                break;

            case ControlMessage.TYPE_FILE_PULL:
                // 分块读取并发送
                break;

            case ControlMessage.TYPE_FILE_PUSH_DATA:
                FileTransferHandler.handleFilePushData(
                    msg.getPath(), msg.getChunkId(), msg.getData());
                break;

            // ... 其他消息类型
        }
    } catch (IOException e) {
        sendError(msg.getType(), e.getMessage());
    }
}
```

---

## Python 实现设计

### 新增文件: file_ops.py

```python
"""文件操作模块 - 通过控制通道传输文件"""

import logging
from dataclasses import dataclass
from enum import IntEnum
from typing import Callable, Optional, List
import struct

logger = logging.getLogger(__name__)


class FileType(IntEnum):
    FILE = 0
    DIRECTORY = 1


@dataclass
class FileInfo:
    name: str
    type: FileType
    size: int
    modified: int  # Unix timestamp
    permissions: int


class FileOperations:
    """通过控制通道进行文件操作"""

    CHUNK_SIZE = 64 * 1024  # 64KB

    def __init__(self, control_sender):
        """
        Args:
            control_sender: 发送 ControlMessage 的回调
        """
        self._sender = control_sender
        self._pending_transfers = {}  # transfer_id -> TransferState

    def list_dir(self, path: str, callback: Callable[[List[FileInfo]], None]):
        """列出目录内容 (异步)"""
        msg = self._build_list_msg(path)
        self._sender(msg)

    def pull_file(self, device_path: str, local_path: str,
                  on_complete: Callable[[bool, str], None],
                  on_progress: Optional[Callable[[int, int], None]] = None):
        """下载文件 (异步)"""
        transfer = PullTransfer(
            device_path=device_path,
            local_path=local_path,
            on_complete=on_complete,
            on_progress=on_progress
        )
        transfer_id = self._next_transfer_id()
        self._pending_transfers[transfer_id] = transfer

        msg = self._build_pull_msg(device_path)
        self._sender(msg)

    def push_file(self, local_path: str, device_path: str,
                  on_complete: Callable[[bool, str], None],
                  on_progress: Optional[Callable[[int, int], None]] = None):
        """上传文件 (异步)"""
        # 1. 发送 PUSH_START
        # 2. 等待 ACK
        # 3. 分块发送数据
        # 4. 发送 PUSH_END
        pass

    def handle_device_message(self, msg):
        """处理来自设备的文件消息"""
        msg_type = msg.get('type')

        if msg_type == DeviceMessageType.FILE_LIST:
            entries = self._parse_file_list(msg.get('data'))
            # 触发回调
        elif msg_type == DeviceMessageType.FILE_PULL_DATA:
            # 写入数据块
            pass
        elif msg_type == DeviceMessageType.FILE_PULL_END:
            # 完成下载
            pass
        elif msg_type == DeviceMessageType.FILE_PUSH_ACK:
            # 确认上传，继续发送下一块
            pass
        elif msg_type == DeviceMessageType.FILE_ERROR:
            # 错误处理
            pass
```

---

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 大文件传输阻塞控制通道 | 高 | 使用独立线程处理，优先保证控制消息 |
| 内存占用 | 中 | 严格限制块大小，使用流式处理 |
| 协议兼容性 | 中 | 使用版本号，向后兼容 |
| 权限问题 | 中 | 明确错误码，引导用户 |

---

## 实现计划

| 阶段 | 任务 | 工时 |
|------|------|------|
| 1 | 协议定义和消息格式 | 1 天 |
| 2 | Java 端 FileTransferHandler | 3 天 |
| 3 | Java 端 Device.java 集成 | 2 天 |
| 4 | Python 端 file_ops.py | 3 天 |
| 5 | Python 端 ControlChannel 集成 | 2 天 |
| 6 | 单元测试 | 2 天 |
| 7 | 集成测试和调试 | 2 天 |
| **总计** | | **15 天** |

---

## 优缺点

### 优点
- 复用现有连接，无需额外端口
- 协议设计一致性好
- 网络模式和ADB模式统一实现

### 缺点
- 大文件传输可能影响控制响应
- 实现复杂度高
- 需要仔细处理流控和并发
