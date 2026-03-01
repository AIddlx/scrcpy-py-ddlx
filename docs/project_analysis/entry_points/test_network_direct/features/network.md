# 网络模式详解

> TCP 控制 + UDP 媒体流

---

## 架构

### 通道分离

```
┌──────────────────────────────────────────┐
│              4 个独立通道                 │
├──────────────────────────────────────────┤
│  TCP 控制通道 (27184)                    │
│    - 触摸/按键事件                       │
│    - 剪贴板同步                          │
│    - 心跳 (PING/PONG)                    │
│    - 文件命令                            │
├──────────────────────────────────────────┤
│  UDP 视频流 (27185)                      │
│    - H.264/H.265/AV1 数据               │
│    - 可选 FEC                            │
├──────────────────────────────────────────┤
│  UDP 音频流 (27186)                      │
│    - Opus/AAC/FLAC 数据                 │
│    - 可选 FEC                            │
├──────────────────────────────────────────┤
│  TCP 文件传输 (27187)                    │
│    - LIST/PUSH/PULL/DELETE              │
│    - 大文件传输                          │
└──────────────────────────────────────────┘
```

---

## 连接流程

### 1. 服务端启动

```python
# 通过 ADB 启动服务端
adb shell nohup sh -c 'CLASSPATH=/data/local/tmp/scrcpy-server.apk
    app_process / com.genymobile.scrcpy.Server 3.3.4
    control_port=27184 video_port=27185 audio_port=27186 ...'
```

### 2. 客户端连接

```python
config = ClientConfig(
    connection_mode=ConnectionMode.NETWORK,
    host="192.168.1.100",
    control_port=27184,
    video_port=27185,
    audio_port=27186,
)
client = ScrcpyClient(config)
client.connect()
```

---

## UDP 包格式

### Header (24 字节)

```
┌─────────────────────────────────────────────────────────────┐
│  seq (4B)  │ timestamp (8B) │ flags (4B) │ send_time_ns (8B)│
├─────────────────────────────────────────────────────────────┤
│                       Payload (N bytes)                     │
└─────────────────────────────────────────────────────────────┘

seq:          包序号 (递增)
timestamp:    采集时间戳
flags:        标志位 (关键帧/FEC/配置包)
send_time_ns: 发送时间 (E2E 延迟计算)
```

### 标志位

| 位 | 名称 | 说明 |
|----|------|------|
| 0 | KEY_FRAME | 关键帧 |
| 1 | CONFIG | 配置包 (SPS/PPS) |
| 2 | FEC_DATA | FEC 数据包 |
| 3 | FEC_PARITY | FEC 校验包 |

---

## TCP 控制消息

### 心跳机制

```
客户端                    服务端
   │                        │
   │ ─── PING (25) ───────> │
   │                        │
   │ <── PONG (5) ───────── │
   │                        │
   │   (每 5 秒一次)        │
```

### 触摸事件

```
[type: 1B][action: 1B][pointer_id: 8B][position: 8B][pressure: 4B]

action: 0=DOWN, 1=UP, 2=MOVE
```

---

## Stay-Alive 模式

### 概念

```
传统模式:
  客户端断开 → 服务端退出

Stay-Alive 模式:
  客户端断开 → 服务端保持 → 等待下一个连接
```

### 使用

```bash
# 启动服务端 (stay-alive)
python test_network_direct.py --stay-alive --ip 192.168.1.100

# 之后可以快速重连
python test_network_direct.py --reuse --no-push --ip 192.168.1.100
```

### 进程持久化 (setsid)

**重要**：服务端使用 `setsid` 启动，确保 USB 断开后服务端继续运行。

```bash
# 启动命令（内部实现）
nohup setsid sh -c 'app_process ...' > /data/local/tmp/scrcpy_server.log 2>&1 &
```

`setsid` 创建新会话，让服务端脱离 ADB shell 进程组，避免 USB 断开时被一起杀死。

### UDP Wake

```
┌─────────────────────────────────────────────┐
│  UDP Wake Packet (Discovery Port 27183)     │
├─────────────────────────────────────────────┤
│  Magic: "SCRCPY_WAKE" (11 bytes)            │
│  Server starts listening for connection     │
└─────────────────────────────────────────────┘
```

---

## 相关文档

- [fec.md](fec.md) - FEC 前向纠错
- [low_latency.md](low_latency.md) - 低延迟优化
