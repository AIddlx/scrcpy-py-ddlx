# 功能概览

> test_network_direct.py 的功能模块总览

---

## 功能模块

| 模块 | 文档 | 说明 |
|------|------|------|
| 网络模式 | [network.md](network.md) | TCP 控制 + UDP 媒体 |
| FEC | [fec.md](fec.md) | 前向纠错 |
| 低延迟 | [low_latency.md](low_latency.md) | 延迟优化 |
| 认证 | [auth.md](auth.md) | HMAC-SHA256 |

---

## 功能矩阵

| 功能 | 状态 | 说明 |
|------|------|------|
| TCP 控制通道 | ✅ | 端口 27184 |
| UDP 视频流 | ✅ | 端口 27185 |
| UDP 音频流 | ✅ | 端口 27186 |
| TCP 文件传输 | ✅ | 端口 27187 |
| FEC 前向纠错 | ✅ | frame/fragment 模式 |
| 低延迟模式 | ✅ | MediaCodec 优化 |
| 多进程解码 | ✅ | 避免 GIL |
| HMAC 认证 | ✅ | v1.4 |
| Stay-Alive 模式 | ✅ | 持久服务端 |
| UDP Wake | ✅ | 唤醒休眠服务端 |
| 内容检测 | ⚠️ 实验性 | 画面异常检测 |

---

## 架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Android 设备                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              scrcpy-server (nohup)              │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐       │    │
│  │  │  TCP     │ │  UDP     │ │  UDP     │       │    │
│  │  │ Control  │ │  Video   │ │  Audio   │       │    │
│  │  │ :27184   │ │  :27185  │ │  :27186  │       │    │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘       │    │
│  └───────┼────────────┼────────────┼──────────────┘    │
└──────────┼────────────┼────────────┼───────────────────┘
           │            │            │
           │ TCP        │ UDP        │ UDP
           │            │            │
┌──────────┼────────────┼────────────┼───────────────────┐
│          │            │            │                   │
│  ┌───────┴─────┐ ┌────┴─────┐ ┌────┴─────┐            │
│  │   Control   │ │  Video   │ │  Audio   │            │
│  │   Channel   │ │ Demuxer  │ │ Demuxer  │            │
│  └───────┬─────┘ └────┬─────┘ └────┬─────┘            │
│          │            │            │                   │
│  ┌───────┴─────┐ ┌────┴─────┐ ┌────┴─────┐            │
│  │   Control   │ │  Video   │ │  Audio   │            │
│  │   Handler   │ │ Decoder  │ │ Decoder  │            │
│  └───────┬─────┘ └────┬─────┘ └────┬─────┘            │
│          │            │            │                   │
│  ┌───────┴────────────┴────────────┴─────┐            │
│  │           Qt GUI (OpenGL)              │            │
│  └────────────────────────────────────────┘            │
│                    Python 客户端                        │
└─────────────────────────────────────────────────────────┘
```

---

## 命令行参数分组

```bash
python tests_gui/test_network_direct.py --help

Network Settings:
  --ip                  设备 IP 地址
  --control-port        TCP 控制端口 (默认 27184)
  --video-port          UDP 视频端口 (默认 27185)
  --audio-port          UDP 音频端口 (默认 27186)

FEC Settings:
  --fec                 FEC 模式 (frame/fragment)
  --video-fec           仅视频 FEC
  --audio-fec           仅音频 FEC
  --fec-k               数据包数 (默认 4)
  --fec-m               校验包数 (默认 1)

Video Settings:
  --codec               视频编解码器 (auto/h264/h265/av1)
  --bitrate             码率 (默认 2.5 Mbps)
  --max-fps             最大帧率 (默认 60)

Low Latency Optimization:
  --low-latency         MediaCodec 低延迟模式
  --encoder-priority    编码器优先级
  --skip-frames         跳帧模式
  --multiprocess        多进程解码

Server Lifecycle:
  --reuse               重用现有服务端
  --no-push             跳过 APK 推送
  --stay-alive          Stay-Alive 模式

Authentication Settings:
  --auth                启用认证 (默认启用)
  --no-auth             禁用认证
```

---

## 相关文档

- [network.md](network.md) - 网络模式详解
- [fec.md](fec.md) - FEC 前向纠错
- [low_latency.md](low_latency.md) - 低延迟优化
- [auth.md](auth.md) - 认证机制
