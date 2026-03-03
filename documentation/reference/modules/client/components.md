# ComponentFactory - 组件工厂

> **路径**: `scrcpy_py_ddlx/client/components.py`
> **职责**: 按官方 scrcpy 初始化顺序创建组件

---

## 类定义

### ComponentFactory

**职责**: 组件工厂，管理所有组件的创建

**设计模式**: 工厂模式

---

## 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `config` | ClientConfig | 客户端配置 |
| `state` | ClientState | 客户端状态 |
| `_video_socket` | socket | 视频 socket |
| `_control_socket` | socket | 控制 socket |
| `_audio_socket` | socket | 音频 socket |
| `_connection_mode` | str | 连接模式 |
| `_video_packet_queue` | Queue | 视频包队列 |
| `_audio_packet_queue` | Queue | 音频包队列 |

---

## 创建方法

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `create_video_demuxer` | Demuxer | 创建视频解复用器 |
| `create_audio_demuxer` | Demuxer | 创建音频解复用器 |
| `create_video_decoder` | VideoDecoder | 创建视频解码器 |
| `create_audio_decoder` | AudioDecoder | 创建音频解码器 |
| `create_recorder` | Recorder | 创建录制器 |
| `create_controller` | Thread | 创建控制器线程 |
| `create_screen` | Screen | 创建屏幕 |
| `create_video_window` | OpenGLWindow | 创建视频窗口 |
| `create_audio_player` | AudioPlayer | 创建音频播放器 |
| `create_device_receiver` | DeviceReceiver | 创建设备消息接收器 |
| `create_control_queue` | ControlQueue | 创建控制队列 |

---

## 初始化顺序

遵循官方 scrcpy 初始化顺序:

```
1. VideoDemuxer     ← create_video_demuxer()
2. AudioDemuxer     ← create_audio_demuxer()
3. VideoDecoder     ← create_video_decoder()
4. AudioDecoder     ← create_audio_decoder()
5. Recorder         ← create_recorder()
6. Controller       ← create_controller()
7. VideoWindow      ← create_video_window()
8. Screen           ← create_screen()
9. AudioPlayer      ← create_audio_player()
10. DeviceReceiver  ← create_device_receiver()
11. 启动 Demuxers    ← 手动调用 start()
```

---

## 模式适配

### ADB 隧道模式

```python
# 使用 socket 流式读取
demuxer = VideoDemuxer(socket)
```

### UDP 网络模式

```python
# 使用 UdpVideoDemuxer
demuxer = UdpVideoDemuxer(socket, fec_decoder)
```

---

## 组件依赖图

```
ComponentFactory
    │
    ├──→ Demuxer (视频/音频)
    │       └──→ Queue (包队列)
    │
    ├──→ Decoder (视频/音频)
    │       ├──→ Queue (输入)
    │       └──→ DelayBuffer (输出)
    │
    ├──→ VideoWindow
    │       ├──→ DelayBuffer (帧源)
    │       └──→ ControlQueue (输入)
    │
    ├──→ Screen
    │       └──→ DelayBuffer
    │
    ├──→ AudioPlayer
    │       └──→ Decoder
    │
    └──→ DeviceReceiver
            └──→ Callbacks
```

---

## 常量

| 常量 | 值 | 说明 |
|------|-----|------|
| `USE_STREAMING_DEMUXER` | True | 使用流式解复用器 |

---

## 依赖关系

```
ComponentFactory
    │
    ├──→ config.py (配置)
    │
    ├──→ core/decoder/ (解码器)
    │
    ├──→ core/demuxer/ (解复用器)
    │
    ├──→ core/player/ (播放器)
    │
    ├──→ core/control.py (控制)
    │
    └──→ core/device_msg.py (设备消息)
```

**被依赖**:
- client.py (创建所有组件)

---

*此文档基于代码分析生成*
