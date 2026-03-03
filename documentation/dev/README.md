# 开发文档

面向贡献者的开发文档。

---

## 目录

| 目录 | 说明 |
|------|------|
| [guides/](guides/) | 开发指南 - 流程、调试、规范 |
| [design/](design/) | 设计文档 - 架构、技术方案 |
| [protocols/](protocols/) | 协议规范 - 通信协议详细定义 |
| [server/](server/) | 服务端 - Android/Java 文档 |
| [mcp-http-server/](mcp-http-server/) | MCP HTTP 服务器 |
| [file-transfer/](file-transfer/) | 文件传输 |
| [preview/](preview/) | 预览窗口 |
| [known-issues/](known-issues/) | 已知问题 |
| [notification/](notification/) | 通知转发 |
| [changelog/](changelog/) | 变更日志 |

---

## 必读文档

1. [开发流程](guides/workflow.md) - 修改代码前必读
2. [协议规范](protocols/PROTOCOL_SPEC.md) - 通信协议定义
3. [协议修改检查清单](protocols/change-checklist.md) - 修改协议前必读

---

## 核心设计

- [网络管线](design/network-pipeline.md) - TCP 控制 + UDP 媒体
- [音视频管线](design/media-pipeline.md) - 解码、渲染、录制
- [下一版架构](design/next-gen-architecture.md) - 未来规划
