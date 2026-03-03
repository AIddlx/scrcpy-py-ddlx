# mcp_stdio.py

> **文件**: `mcp_stdio.py`
> **功能**: STDIO MCP 服务器入口

---

## 概述

`mcp_stdio.py` 提供 STDIO MCP 服务，用于 Claude Desktop 集成。

---

## 协议

使用标准 MCP 协议通过 STDIN/STDOUT 通信。

---

## 配置

### Claude Desktop (Windows)

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

### Claude Desktop (macOS/Linux)

```json
{
  "mcpServers": {
    "scrcpy": {
      "command": "python3",
      "args": ["/path/to/mcp_stdio.py"]
    }
  }
}
```

---

## 核心 API

```python
# 使用 mcp 库
from mcp.server import Server
from mcp.server.stdio import stdio_server

server = Server("scrcpy-py-ddlx")

@server.list_tools()
async def list_tools():
    return get_tools()

@server.call_tool()
async def call_tool(name: str, args: dict):
    return await execute_tool(name, args)

# 运行服务器
async with stdio_server() as (read_stream, write_stream):
    await server.run(read_stream, write_stream)
```

---

## 运行方式

```bash
python mcp_stdio.py
```

---

## 相关文档

- [mcp_server.md](../client/mcp_server.md) - MCP 核心实现
