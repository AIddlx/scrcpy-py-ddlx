# MCP 服务

> Model Context Protocol AI 工具接口

---

## 概述

MCP (Model Context Protocol) 服务允许 AI 模型 (如 Claude) 通过标准化接口控制 Android 设备。

---

## 入口文件

| 文件 | 说明 |
|------|------|
| `mcp_stdio.py` | STDIO MCP 服务器 (标准输入输出) |
| `scrcpy_py_ddlx/mcp_server.py` | MCP 核心逻辑实现 |

---

## 启动方式

### STDIO 模式

```bash
python mcp_stdio.py
```

### Claude Desktop 配置

```json
{
  "mcpServers": {
    "scrcpy": {
      "command": "python",
      "args": ["C:\\path\\to\\mcp_stdio.py"]
    }
  }
}
```

---

## 工具列表

详见 [tools.md](tools.md)

| 类别 | 工具数量 |
|------|---------|
| 连接管理 | 2 |
| 媒体操作 | 4 |
| 文件操作 | 4 |
| 控制操作 | 6 |
| **总计** | **16** |

---

## 相关文档

- [工具完整列表](tools.md)
- [MCP HTTP 服务器](../../development/mcp_http_server/)
