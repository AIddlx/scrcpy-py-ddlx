# File Transfer API

## MCP 端点

```
POST http://127.0.0.1:3359/mcp
Content-Type: application/json
```

## 请求格式

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "<tool_name>",
    "arguments": { ... }
  }
}
```

---

## list_dir

列出目录内容

**参数:**
| 名称 | 类型 | 必需 | 说明 |
|------|------|------|------|
| path | string | 否 | 目录路径，默认 /sdcard |

**请求示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "list_dir",
    "arguments": {"path": "/sdcard"}
  }
}
```

**响应示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [{
      "type": "text",
      "text": "{\"success\":true,\"path\":\"/sdcard\",\"entries\":[{\"name\":\"Download\",\"type\":\"directory\",\"size\":4096,\"mtime\":1234567890}],\"count\":1,\"mode\":\"network\"}"
    }]
  }
}
```

**curl:**
```bash
curl -s -X POST http://127.0.0.1:3359/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_dir","arguments":{"path":"/sdcard"}}}'
```

---

## file_stat

获取文件/目录信息

**参数:**
| 名称 | 类型 | 必需 | 说明 |
|------|------|------|------|
| device_path | string | 是 | 文件路径 |

**请求示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "file_stat",
    "arguments": {"device_path": "/sdcard/test.png"}
  }
}
```

**响应示例:**
```json
{
  "success": true,
  "exists": true,
  "path": "/sdcard/test.png",
  "type": "file",
  "size": 12345,
  "mtime": 1234567890,
  "mode": "network"
}
```

---

## push_file

上传文件到设备

**参数:**
| 名称 | 类型 | 必需 | 说明 |
|------|------|------|------|
| local_path | string | 是 | 本地文件路径 |
| device_path | string | 是 | 设备目标路径 |

**请求示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "push_file",
    "arguments": {
      "local_path": "./test.txt",
      "device_path": "/sdcard/test.txt"
    }
  }
}
```

**curl:**
```bash
echo "test content" > test.txt
curl -s -X POST http://127.0.0.1:3359/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"push_file","arguments":{"local_path":"test.txt","device_path":"/sdcard/test.txt"}}}'
```

---

## pull_file

从设备下载文件

**参数:**
| 名称 | 类型 | 必需 | 说明 |
|------|------|------|------|
| device_path | string | 是 | 设备文件路径 |
| local_path | string | 是 | 本地保存路径 |

**请求示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "pull_file",
    "arguments": {
      "device_path": "/sdcard/test.txt",
      "local_path": "./downloaded.txt"
    }
  }
}
```

---

## make_dir

创建目录

**参数:**
| 名称 | 类型 | 必需 | 说明 |
|------|------|------|------|
| device_path | string | 是 | 目录路径 |

**请求示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "make_dir",
    "arguments": {"device_path": "/sdcard/new_dir"}
  }
}
```

---

## delete_file

删除文件或目录

**参数:**
| 名称 | 类型 | 必需 | 说明 |
|------|------|------|------|
| device_path | string | 是 | 文件/目录路径 |

**请求示例:**
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "tools/call",
  "params": {
    "name": "delete_file",
    "arguments": {"device_path": "/sdcard/test.txt"}
  }
}
```

---

## 响应字段说明

| 字段 | 说明 |
|------|------|
| success | 操作是否成功 |
| mode | 传输模式: "adb" 或 "network" |
| entries | 目录条目列表 (list_dir) |
| size | 文件大小 (bytes) |
| mtime | 修改时间 (Unix timestamp) |
| type | 类型: "file" 或 "directory" |
| error | 错误信息 (失败时) |

---

## 错误处理

```json
{
  "success": false,
  "error": "Failed to open file channel"
}
```

常见错误:
- `Not connected` - 未连接设备
- `Failed to open file channel` - 网络模式文件通道未建立
- `Local file not found` - 本地文件不存在
- `device_path is required` - 缺少必需参数
