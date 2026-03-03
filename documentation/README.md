# scrcpy-py-ddlx 文档

> Android 屏幕投影与控制 - Python 实现

---

## 快速导航

| 我想... | 去哪里 |
|---------|--------|
| 快速上手使用 | [用户指南](user/quickstart.md) |
| 了解 API 接口 | [API 参考](api/control.md) |
| 参与项目开发 | [开发指南](dev/guides/workflow.md) |
| 深入了解模块 | [参考文档](reference/modules/README.md) |
| 排查问题 | [故障排除](user/troubleshooting.md) |

---

## 文档目录

### [用户指南](user/)
面向使用者的文档，包括安装、配置、使用方法。

- [安装指南](user/installation.md)
- [快速开始](user/quickstart.md)
- [故障排除](user/troubleshooting.md)
- [使用模式](user/modes/)
  - [Python API 模式](user/modes/python-api.md)
  - [MCP HTTP 模式](user/modes/mcp-http.md)
  - [MCP GUI 模式](user/modes/mcp-gui.md)
  - [ADB Tunnel 模式](user/modes/adb-tunnel.md)
- [外部集成](user/integrations/)

### [API 参考](api/)
面向开发者的 API 文档。

- [控制方法](api/control.md) - 所有控制命令
- [协议参数](api/protocol.md) - 协议格式
- [功能状态](api/status.md) - 支持情况

### [开发文档](dev/)
面向贡献者的开发文档。

- [开发指南](dev/guides/) - 工作流程、调试方法
- [设计文档](dev/design/) - 架构设计、技术方案
- [协议规范](dev/protocols/) - 通信协议详细规范
- [已知问题](dev/known-issues/) - 问题追踪与修复记录
- [变更日志](dev/changelog/) - 版本变更记录

### [参考文档](reference/)
深度技术参考。

- [模块文档](reference/modules/) - 每个 Python/Java 类的详细文档
- [功能清单](reference/features/) - 完整功能列表
- [入口点](reference/entry-points/) - 各运行入口说明
- [依赖说明](reference/dependencies/) - 项目依赖
- [分析报告](reference/reports/) - 项目分析、优化路线图

---

## 根据角色选择

### 普通用户
1. [安装](user/installation.md) → [快速开始](user/quickstart.md) → [选择使用模式](user/modes/)

### AI 应用开发者
1. [API 参考](api/control.md) → [MCP HTTP 模式](user/modes/mcp-http.md)

### 项目贡献者
1. [开发流程](dev/guides/workflow.md) → [协议规范](dev/protocols/PROTOCOL_SPEC.md)

### 深度定制者
1. [参考文档](reference/modules/README.md) → [设计文档](dev/design/)

---

*文档结构重组于 2026-03-03*
