# scrcpy_http_mcp_server.py 文档

> HTTP MCP 服务器 - AI 模型集成入口

---

## 概述

| 属性 | 值 |
|------|-----|
| **文件路径** | `scrcpy_http_mcp_server.py` |
| **协议** | MCP (Model Context Protocol) over HTTP |
| **端口** | 3359 (默认) |
| **代码行数** | ~1500 行 |
| **工具数量** | 47+ |

---

## 目录结构

```
scrcpy_http_mcp_server/
├── README.md               # 本文件
├── dependencies.md         # 依赖清单
├── tools/                  # 工具分类文档
│   ├── overview.md         # 工具总览
│   ├── connection.md       # 连接管理
│   ├── screen.md           # 屏幕操作
│   ├── input.md            # 输入控制
│   ├── file.md             # 文件操作
│   ├── app.md              # 应用管理
│   └── advanced.md         # 高级功能
├── usage.md                # 使用说明
└── configuration.md        # 配置说明
```

---

## 快速开始

### 启动服务器

```bash
# 默认端口 3359
python scrcpy_http_mcp_server.py

# 指定端口
python scrcpy_http_mcp_server.py --port 8080

# 启用音频
python scrcpy_http_mcp_server.py --audio
```

### 配置 Claude Code

```json
{
  "mcpServers": {
    "scrcpy-http": {
      "url": "http://localhost:3359/mcp"
    }
  }
}
```

---

## 核心特性

### 1. MCP 协议支持

- JSON-RPC 2.0 over HTTP POST
- 无状态设计
- 标准 MCP 工具接口

### 2. 47+ 工具

| 类别 | 数量 | 说明 |
|------|------|------|
| 连接管理 | 5 | connect, disconnect, push_server... |
| 屏幕操作 | 8 | screenshot, get_state, rotate... |
| 输入控制 | 10 | tap, swipe, type, key... |
| 文件操作 | 6 | list_files, push_file, pull_file... |
| 应用管理 | 5 | list_apps, start_app, install_apk... |
| 高级功能 | 13+ | clip, record, tcpdump... |

### 3. 双模式支持

- **ADB 隧道模式**: USB 连接，安全稳定
- **网络模式**: TCP+UDP，无线自由

---

## 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    AI 应用层                             │
│              (Claude Code / 其他 MCP 客户端)             │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP POST (JSON-RPC)
                        ▼
┌─────────────────────────────────────────────────────────┐
│               scrcpy_http_mcp_server.py                  │
│  ┌─────────────────────────────────────────────────┐    │
│  │              Starlette ASGI App                 │    │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐     │    │
│  │  │ /mcp      │ │ /health   │ │ /state    │     │    │
│  │  │ JSON-RPC  │ │ Health    │ │ Debug     │     │    │
│  │  └─────┬─────┘ └───────────┘ └───────────┘     │    │
│  └────────┼────────────────────────────────────────┘    │
│           │                                              │
│  ┌────────┴────────────────────────────────────────┐    │
│  │              MCP Tool Handler                    │    │
│  │  47+ tools: connect, tap, swipe, type...        │    │
│  └────────┬────────────────────────────────────────┘    │
└───────────┼─────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│              ScrcpyClient (连接池)                       │
│  ┌───────────────────┐  ┌───────────────────┐           │
│  │   ADB Tunnel      │  │   Network Mode    │           │
│  │   (USB)           │  │   (TCP+UDP)       │           │
│  └───────────────────┘  └───────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

---

## 与其他入口的对比

| 特性 | test_direct.py | test_network_direct.py | scrcpy_http_mcp_server.py |
|------|---------------|----------------------|--------------------------|
| 主要用途 | 开发调试 | 无线使用 | AI 集成 |
| 界面 | Qt GUI | Qt GUI | HTTP API |
| 工具数量 | N/A | N/A | 47+ |
| 无状态 | ❌ | ❌ | ✅ |
| 并发支持 | 单连接 | 单连接 | 多连接池 |

---

## 详细文档

- [dependencies.md](dependencies.md) - 依赖清单
- [tools/overview.md](tools/overview.md) - 工具总览
- [usage.md](usage.md) - 使用说明
- [configuration.md](configuration.md) - 配置说明
