# File Transfer Skill

文件传输功能 - 支持 ADB 模式和网络模式

## 快速开始

```bash
# 启动 MCP 服务器
python scrcpy_http_mcp_server.py --network-push 192.168.5.4 --audio --audio-dup

# 运行测试
test_file_transfer_network_only.bat
```

## 架构

```
ADB 模式:  PC ←→ ADB Tunnel ←→ Android
网络模式:  PC ←→ TCP/UDP ←→ Android
           - TCP 27184: 控制通道
           - UDP 27185: 视频流
           - UDP 27186: 音频流
           - TCP 27187: 文件通道
```

## API

| 工具 | 参数 | 说明 |
|------|------|------|
| list_dir | path | 列出目录 |
| file_stat | device_path | 获取文件信息 |
| push_file | local_path, device_path | 上传文件 |
| pull_file | device_path, local_path | 下载文件 |
| make_dir | device_path | 创建目录 |
| delete_file | device_path | 删除文件/目录 |

## 文件

- `API.md` - 完整 API 文档
- `test_protocol.py` - 协议测试
- `test_stress.py` - 压力测试
