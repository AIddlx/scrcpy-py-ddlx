# config.py - 配置定义

> **路径**: `scrcpy_py_ddlx/client/config.py`
> **职责**: 客户端配置和状态管理

---

## 类清单

### ConnectionMode

**职责**: 连接模式常量

| 常量 | 值 | 说明 |
|------|-----|------|
| `ADB_TUNNEL` | "adb_tunnel" | ADB 隧道模式 |
| `NETWORK` | "network" | 网络直连模式 |

---

### ClientConfig

**职责**: 客户端完整配置，对应服务端参数

**类型**: @dataclass

---

## ClientConfig 属性

### 连接设置

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `host` | str | "localhost" | 服务器地址 |
| `port` | int | 27183 | 服务器端口 |
| `server_jar` | str | "scrcpy-server" | 服务端 JAR 路径 |
| `device_serial` | str | None | 设备序列号 |
| `connection_mode` | str | "adb_tunnel" | 连接模式 |

### 网络模式端口

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `control_port` | int | 27184 | TCP 控制端口 |
| `video_port` | int | 27185 | UDP 视频端口 |
| `audio_port` | int | 27186 | UDP 音频端口 |
| `file_port` | int | 27187 | TCP 文件端口 |
| `discovery_port` | int | 27183 | UDP 发现端口 |

### 视频设置

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `video` | bool | True | 启用视频 |
| `bitrate` | int | 2500000 | 码率 (2.5Mbps) |
| `max_fps` | int | 60 | 最大帧率 |
| `codec` | str | "auto" | 编码器 (h264/h265/av1) |
| `codec_options` | str | "" | 编码器选项 |
| `crop` | str | "" | 裁剪区域 |
| `lock_video_orientation` | int | -1 | 锁定方向 (-1=不锁定) |
| `display_id` | int | 0 | 显示器 ID |
| `bitrate_mode` | str | "vbr" | 码率模式 (cbr/vbr) |
| `i_frame_interval` | float | 10.0 | I帧间隔 (秒) |
| `gpu_rendering` | bool | True | GPU 渲染 (NV12) |

### 音频设置

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `audio` | bool | False | 启用音频 |
| `audio_codec` | int | OPUS | 音频编码 (RAW/OPUS/AAC/FLAC) |
| `audio_dup` | bool | False | 双路音频 (Android 11+) |

### FEC 设置

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `fec_enabled` | bool | False | 启用 FEC (旧版) |
| `video_fec_enabled` | bool | False | 视频流 FEC |
| `audio_fec_enabled` | bool | False | 音频流 FEC |
| `fec_group_size` | int | 4 | K: 数据包数 |
| `fec_parity_count` | int | 1 | M: 校验包数 |
| `fec_mode` | str | "frame" | FEC 模式 (frame/fragment) |

### 低延迟优化

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `low_latency` | bool | False | MediaCodec 低延迟 |
| `encoder_priority` | int | 1 | 编码器优先级 (0-2) |
| `encoder_buffer` | int | 0 | 编码器缓冲 |
| `skip_frames` | bool | True | 跳过缓冲帧 |

### 其他设置

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `control` | bool | True | 启用控制 |
| `show_window` | bool | False | 显示窗口 |
| `lazy_decode` | bool | True | 懒解码模式 |
| `multiprocess` | bool | False | 多进程模式 |
| `clipboard_autosync` | bool | False | 剪贴板同步 |
| `connection_timeout` | float | 10.0 | 连接超时 |
| `socket_timeout` | float | 5.0 | Socket 超时 |

### 回调设置

| 属性 | 类型 | 说明 |
|------|------|------|
| `frame_callback` | Callable[[np.ndarray], None] | 帧回调 |
| `init_callback` | Callable[[int, int], None] | 初始化回调 |

---

### ClientState

**职责**: 客户端运行时状态

**类型**: @dataclass

---

## ClientState 属性

### 连接状态

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `connected` | bool | False | 已连接 |
| `running` | bool | False | 运行中 |

### Socket 引用

| 属性 | 类型 | 说明 |
|------|------|------|
| `video_socket` | socket | 视频 socket |
| `audio_socket` | socket | 音频 socket |
| `control_socket` | socket | 控制 socket |
| `video_udp_socket` | socket | UDP 视频 socket |
| `audio_udp_socket` | socket | UDP 音频 socket |

### 设备信息

| 属性 | 类型 | 说明 |
|------|------|------|
| `device_name` | str | 设备名称 |
| `video_width` | int | 视频宽度 |
| `video_height` | int | 视频高度 |

---

## 辅助函数

### _auto_detect_codec()

**职责**: 自动检测最优编码器

**返回**: "h264" | "h265" | "av1"

### _auto_detect_codec_for_device(device_serial)

**职责**: 为指定设备检测最优编码器

**参数**:
- `device_serial`: 设备序列号

**返回**: 编码器名称

---

## 依赖关系

```
ClientConfig
    │
    ├──→ AudioDemuxer (codec 常量)
    │
    └──→ capability_cache (自动检测)

ClientState
    │
    └──→ socket (网络连接)
```

---

## 使用示例

```python
# 基本配置
config = ClientConfig(
    host="192.168.1.100",
    connection_mode="network",
    video=True,
    audio=True,
    gpu_rendering=True
)

# 低延迟配置
config = ClientConfig(
    low_latency=True,
    skip_frames=True,
    bitrate_mode="cbr",
    i_frame_interval=2.0
)

# 多进程模式
config = ClientConfig(
    multiprocess=True,
    connection_mode="network"
)
```

---

*此文档基于代码分析生成*
