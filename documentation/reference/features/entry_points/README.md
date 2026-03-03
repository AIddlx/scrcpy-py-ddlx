# 运行入口

> 项目提供多种运行方式，适应不同使用场景

---

## 入口总览

| 入口 | 文件 | 连接方式 | 主要用途 |
|------|------|---------|---------|
| [USB 模式](usb_mode.md) | `tests_gui/test_direct.py` | ADB Tunnel | 日常使用、调试 |
| [网络模式](network_mode.md) | `tests_gui/test_network_direct.py` | TCP + UDP | 无线投屏、远程 |
| [MCP HTTP](mcp_http.md) | `scrcpy_http_mcp_server.py` | HTTP JSON-RPC | AI 工具接口 |
| [MCP STDIO](mcp_stdio.md) | `mcp_stdio.py` | STDIO | Claude Desktop |
| [GUI 应用](gui_app.md) | `scrcpy_mcp_gui.py` | 混合 | 桌面应用 |

---

## 快速开始

### USB 模式 (推荐新手)

```bash
cd C:\Project\IDEA\2\new\scrcpy-py-ddlx
python -X utf8 tests_gui/test_direct.py
```

特性：
- 自动检测 USB 设备
- 自动启用无线模式
- 支持文件拖放传输
- 可选音频录制

### 网络模式 (纯网络)

```bash
cd C:\Project\IDEA\2\new\scrcpy-py-ddlx
python -X utf8 tests_gui/test_network_direct.py --ip 192.168.1.100
```

特性：
- TCP 控制 + UDP 媒体
- 支持 FEC 纠错
- 支持 HMAC-SHA256 认证
- 可拔掉 USB 线

### MCP HTTP 服务器

```bash
python scrcpy_http_mcp_server.py
# 访问 http://localhost:3359/mcp
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

## 功能对比

| 功能 | USB 模式 | 网络模式 | MCP |
|------|---------|---------|-----|
| 视频预览 | ✅ | ✅ | ✅ |
| 音频播放 | ✅ | ✅ | ✅ |
| 触摸控制 | ✅ | ✅ | ✅ |
| 键盘输入 | ✅ | ✅ | ✅ |
| 文件传输 | ADB | TCP | ✅ |
| 截图 | ✅ | ✅ | ✅ |
| 录制 | ✅ | ✅ | ✅ |
| FEC 纠错 | ❌ | ✅ | ✅ |
| 网络认证 | ❌ | ✅ | ✅ |
| 跨平台 | ✅ | ✅ | ✅ |

---

## 相关文档

- [USB 模式详解](usb_mode.md)
- [网络模式详解](network_mode.md)
- [MCP 工具列表](../mcp/tools.md)
