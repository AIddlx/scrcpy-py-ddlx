# scrcpy-py-ddlx 功能清单

> 用于代码清理决策参考

---

## 一、核心功能（必须保留）

### 1.1 连接管理

| 功能 | 文件 | 说明 | 保留 |
|------|------|------|------|
| ADB Tunnel 连接 | `client/connection.py` | USB 模式核心 | ✅ |
| 网络连接 | `client/connection.py` | TCP/UDP 模式 | ✅ |
| 客户端主类 | `client/client.py` | 核心客户端 | ✅ |
| 配置管理 | `client/config.py` | 连接配置 | ✅ |
| 组件初始化 | `client/components.py` | 组件组装 | ✅ |
| 能力缓存 | `client/capability_cache.py` | 编解码器缓存 | ✅ |
| UDP 发现 | `client/udp_discovery.py` | 网络设备发现 | ✅ |
| UDP 唤醒 | `client/udp_wake.py` | 设备唤醒 | ✅ |

### 1.2 协议层

| 功能 | 文件 | 说明 | 保留 |
|------|------|------|------|
| 协议常量 | `core/protocol.py` | 版本/常量定义 | ✅ |
| 控制消息 | `core/control.py` | 触摸/键盘/剪贴板 | ✅ |
| 设备消息 | `core/device_msg.py` | 设备→客户端 | ✅ |
| 流解析 | `core/stream.py` | 二进制流解析 | ✅ |

### 1.3 视频管道

| 功能 | 文件 | 说明 | 保留 |
|------|------|------|------|
| TCP 视频解复用 | `core/demuxer/video.py` | H264/H265 | ✅ |
| UDP 视频解复用 | `core/demuxer/udp_video.py` | UDP 专用 | ✅ |
| 视频解码 | `core/decoder/video.py` | NVDEC/软解 | ✅ |
| 延迟缓冲 | `core/decoder/delay_buffer.py` | 帧同步 | ✅ |
| 解复用工厂 | `core/demuxer/factory.py` | 创建解复用器 | ✅ |

### 1.4 音频管道

| 功能 | 文件 | 说明 | 保留 |
|------|------|------|------|
| TCP 音频解复用 | `core/demuxer/audio.py` | OPUS | ✅ |
| UDP 音频解复用 | `core/demuxer/udp_audio.py` | UDP 专用 | ✅ |
| 音频解码 | `core/audio/decoder.py` | OPUS 解码 | ✅ |
| 音频播放 | `core/audio/player.py` | SoundDevice | ✅ |
| 音频同步 | `core/audio/sync.py` | A/V 同步 | ✅ |
| 音频录制 | `core/audio/recorder.py` | WAV 录制 | ✅ |
| 编解码器定义 | `core/audio/codecs/` | 编解码常量 | ✅ |

### 1.5 视频渲染

| 功能 | 文件 | 说明 | 保留 |
|------|------|------|------|
| OpenGL 窗口 | `core/player/video/opengl_window.py` | GPU NV12 渲染 | ✅ |
| 视频窗口 | `core/player/video/video_window.py` | 窗口容器 | ✅ |
| OpenGL 组件 | `core/player/video/opengl_widget.py` | 通用渲染组件 | ✅ |
| 共享内存帧 | `shared_memory_frame.py` | SHM 帧结构 | ✅ |
| 简单共享内存 | `simple_shm.py` | 跨进程 SHM | ✅ |

### 1.6 文件传输

| 功能 | 文件 | 说明 | 保留 |
|------|------|------|------|
| ADB 文件操作 | `core/file/file_ops.py` | ADB push/pull | ✅ |
| 网络文件通道 | `core/file/file_channel.py` | 第4条 TCP | ✅ |
| 文件命令 | `core/file/file_commands.py` | 命令常量 | ✅ |

### 1.7 辅助模块

| 功能 | 文件 | 说明 | 保留 |
|------|------|------|------|
| ADB 管理 | `core/adb.py` | ADB 命令封装 | ✅ |
| 日志配置 | `core/logging_config.py` | 统一日志 | ✅ |
| 文件推送器 | `core/file_pusher.py` | 文件推送 | ✅ |

---

## 二、MCP 服务（核心）

### 2.1 HTTP MCP 服务器

| 文件 | 行数 | 说明 | 保留 |
|------|------|------|------|
| `scrcpy_http_mcp_server.py` | 4000+ | 主服务 | ✅ |
| `scrcpy_py_ddlx/mcp_server.py` | 4000+ | MCP 逻辑 | ✅ |

### 2.2 MCP 工具清单

| 工具 | 功能 | 状态 |
|------|------|------|
| `connect` | 建立连接 | ✅ |
| `disconnect` | 断开连接 | ✅ |
| `screenshot` | 截图 | ✅ |
| `list_dir` | 列目录 | ✅ |
| `push_file` | 上传文件 | ✅ |
| `pull_file` | 下载文件 | ✅ |
| `delete_file` | 删除文件 | ✅ |
| `record_audio` | 录音 | ✅ |
| `start_video_recording` | 视频录制 | ✅ |
| `stop_video_recording` | 停止录制 | ✅ |
| `get_clipboard` | 获取剪贴板 | ✅ |
| `set_clipboard` | 设置剪贴板 | ✅ |
| `tap` | 点击 | ✅ |
| `swipe` | 滑动 | ✅ |
| `input_text` | 输入文字 | ✅ |
| `press_key` | 按键 | ✅ |

---

## 三、预览进程（核心）

| 文件 | 说明 | 保留 |
|------|------|------|
| `preview_process.py` | 跨进程预览 | ✅ |

---

## 四、GUI 模块（需决策）

### 4.1 主要文件

| 文件 | 行数 | 功能 | 是否保留？ |
|------|------|------|----------|
| `gui/main_window.py` | ~800 | 主窗口 | ❓ |
| `gui/tray.py` | ~100 | 系统托盘 | ❓ |
| `gui/preview_window.py` | ~200 | 预览窗口 | ❓ |
| `gui/config_manager.py` | ~100 | 配置管理 | ❓ |

### 4.2 面板文件

| 文件 | 功能 | 是否保留？ |
|------|------|----------|
| `gui/panels/connection_panel.py` | 连接面板 | ❓ |
| `gui/panels/device_panel.py` | 设备面板 | ❓ |
| `gui/panels/media_panel.py` | 媒体面板 | ❓ |
| `gui/panels/log_panel.py` | 日志面板 | ❓ |

**问题**：GUI 主要用于独立桌面应用。如果只用 MCP 模式，可以考虑删除。

---

## 五、实验性功能（需决策）

### 5.1 多进程解码

| 文件 | 说明 | 问题 |
|------|------|------|
| `core/decoder/decoder_process.py` | 独立解码进程 | ~30 处调试 print |
| `client/multiprocess_components.py` | 多进程组件 | 依赖上面文件 |

**决策点**：
- [ ] 保留并修复（print → logger.debug）
- [ ] 删除（当前不稳定）

### 5.2 IPC 模块

| 文件 | 说明 | 状态 |
|------|------|------|
| `core/ipc/control_channel.py` | IPC 控制通道 | 🚧 未完成 |
| `core/ipc/decoder_shm.py` | IPC SHM | 🚧 未完成 |

**决策点**：
- [ ] 保留并完成
- [ ] 删除

---

## 六、待删除文件

### 6.1 废弃文件

| 文件 | 原因 |
|------|------|
| `mcp_http_server.py.deprecated` | 已被替代 |

### 6.2 临时文件（根目录）

| 文件 | 类型 | 删除？ |
|------|------|--------|
| `temp_test.py` | 测试 | ✅ 删除 |
| `temp_video_full.py` | 测试 | ✅ 删除 |
| `temp_output.txt` | 输出 | ✅ 删除 |
| `tail` | 临时 | ✅ 删除 |
| `test_download.txt` | 测试 | ✅ 删除 |
| `test_upload.txt` | 测试 | ✅ 删除 |
| `test_logs/` | 日志 | ✅ 删除 |
| `本文档.txt` | 临时 | ✅ 删除 |
| `fix_port_3359.ps1` | 脚本 | ✅ 已集成 |
| `start_mcp_server.bat` | 脚本 | ❓ 可保留 |

---

## 七、TODO 项目（需决策）

| 位置 | 内容 | 决策 |
|------|------|------|
| `gui/main_window.py:494` | UDP query | 实现/删除？ |
| `gui/main_window.py:499` | UDP terminate | 实现/删除？ |
| `udp_packet_reader.py:410` | 分片重组 | 实现/删除？ |
| `qt_opus_player.py:134` | QMediaPlayer | 实现/删除？ |
| `audio/sync.py:150,179` | 延迟调整 | 实现/删除？ |
| `mcp_server.py:1549` | 透传录制 | 实现/删除？ |

---

## 八、调试代码问题

### 8.1 decoder_process.py

约 30 处 `print()` 需要改为 `logger.debug()`：
- Line 73, 97, 103, 109, 134, 328, 363, 380, 394, 406, 412, 454, 467, 504, 524, 527, 529, 558, 561, 562, 570, 578, 614, 620, 642

---

## 九、决策记录

> 在此记录你的决策

| 模块 | 决策 | 原因 |
|------|------|------|
| GUI | | |
| 多进程解码 | | |
| IPC 模块 | | |
| TODO 项目 | | |

---

## 十、建议操作顺序

1. **立即删除**
   - `mcp_http_server.py.deprecated`
   - 根目录临时文件

2. **决策后处理**
   - GUI 模块
   - 多进程解码
   - TODO 项目

3. **代码转换**
   - `decoder_process.py` 的 print → logger.debug

---

**文档版本**: 2026-03-01
