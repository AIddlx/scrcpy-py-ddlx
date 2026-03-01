# 实验性功能

> 开发中或待决策的功能

---

## 功能清单

| 功能 | 文件 | 状态 | 说明 |
|------|------|------|------|
| 多进程解码 | `decoder/decoder_process.py` | 🚧 实验中 | 独立解码进程 |
| 多进程组件 | `client/multiprocess_components.py` | 🚧 实验中 | 依赖上述文件 |
| IPC 控制通道 | `ipc/control_channel.py` | 🚧 未完成 | 进程间控制 |
| IPC 解码器 SHM | `ipc/decoder_shm.py` | 🚧 未完成 | 共享内存帧 |

---

## 多进程解码

### 目的

- 避免 GIL 限制
- 提高多核利用率
- 降低主线程延迟

### 当前问题

- 约 30 处 `print()` 需改为 `logger.debug()`
- 稳定性待验证

### 代码位置

```
core/decoder/decoder_process.py      # 独立解码进程
client/multiprocess_components.py    # 多进程组件
```

---

## IPC 模块

### 目的

- 跨进程通信
- 共享内存帧传输
- 进程间控制

### 代码位置

```
core/ipc/control_channel.py    # IPC 控制通道
core/ipc/decoder_shm.py        # 解码器共享内存
```

---

## 待删除文件

### 废弃文件

| 文件 | 原因 |
|------|------|
| `mcp_http_server.py.deprecated` | 已被替代 |

### 临时文件 (根目录)

| 文件 | 类型 | 建议 |
|------|------|------|
| `temp_test.py` | 测试 | 删除 |
| `temp_video_full.py` | 测试 | 删除 |
| `temp_output.txt` | 输出 | 删除 |
| `tail` | 临时 | 删除 |
| `test_download.txt` | 测试 | 删除 |
| `test_upload.txt` | 测试 | 删除 |
| `test_logs/` | 日志 | 删除 |
| `本文档.txt` | 临时 | 删除 |
| `fix_port_3359.ps1` | 脚本 | 已集成，可删除 |

---

## 调试代码

### decoder_process.py

以下位置的 `print()` 需要改为 `logger.debug()`:

```
Line: 73, 97, 103, 109, 134, 328, 363, 380, 394,
      406, 412, 454, 467, 504, 524, 527, 529,
      558, 561, 562, 570, 578, 614, 620, 642
```

约 30 处需要修改。

---

## 决策点

| 功能 | 选项 | 建议 |
|------|------|------|
| 多进程解码 | 保留修复 / 删除 | 评估使用率后决定 |
| IPC 模块 | 保留完成 / 删除 | 评估需求后决定 |
| GUI 模块 | 保留 / 删除 | 如只用 MCP 可删除 |

---

## TODO 项目

| 位置 | 内容 | 状态 |
|------|------|------|
| `gui/main_window.py:494` | UDP query | 未实现 |
| `gui/main_window.py:499` | UDP terminate | 未实现 |
| `udp_packet_reader.py:410` | 分片重组 | 未实现 |
| `qt_opus_player.py:134` | QMediaPlayer | 未实现 |
| `audio/sync.py:150,179` | 延迟调整 | 未实现 |
| `mcp_server.py:1549` | 透传录制 | 未实现 |
