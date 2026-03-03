# 连接管理

> 客户端与设备之间的连接建立、维护和断开

---

## 功能清单

| 功能 | 文件 | 说明 | 状态 |
|------|------|------|------|
| [USB 模式](usb_mode.md) | `client/connection.py` | ADB Tunnel 转发 | ✅ 稳定 |
| [网络模式](network_mode.md) | `client/connection.py` | TCP + UDP 直连 | ✅ 稳定 |
| [设备发现](discovery.md) | `client/udp_discovery.py` | UDP 广播发现 | ✅ 稳定 |
| [设备唤醒](discovery.md) | `client/udp_wake.py` | UDP 魔术包唤醒 | ✅ 稳定 |
| [网络认证](auth.md) | `core/auth.py` | HMAC-SHA256 认证 | ✅ 稳定 |
| 心跳机制 | `core/heartbeat.py` | TCP PING/PONG | ✅ 稳定 |
| 能力协商 | `core/negotiation.py` | 编解码器协商 | ✅ 稳定 |
| 能力缓存 | `client/capability_cache.py` | 编解码器缓存 | ✅ 稳定 |

---

## 连接模式对比

| 特性 | USB 模式 | 网络模式 |
|------|---------|---------|
| 传输层 | ADB Tunnel (TCP) | TCP 控制 + UDP 媒体 |
| 视频通道 | 单 TCP | UDP (低延迟) |
| 需要数据线 | 是 | 否 |
| 延迟 | ~20-40ms | ~10-30ms |
| 认证 | ADB 内置 | HMAC-SHA256 |
| 文件传输 | ADB push/pull | 独立 TCP 通道 |

---

## 连接流程

### USB 模式

```
┌──────────┐     ADB Forward      ┌──────────┐
│  Python  │ ──────────────────► │  Android │
│  Client  │    localhost:27183   │  Server  │
└──────────┘ ◄────────────────── └──────────┘
               (视频/控制/音频)
```

### 网络模式

```
┌──────────┐    TCP 控制     ┌──────────┐
│  Python  │ ──────────────► │  Android │
│  Client  │    :27183       │  Server  │
└──────────┘ ◄────────────── └──────────┘
      │
      │    UDP 媒体 (视频+音频)
      └───────────────────────────►
              :27184
```

---

## 相关文档

- [协议规范](../../../PROTOCOL_SPEC.md)
- [网络管道详解](../../../development/NETWORK_PIPELINE.md)
- [认证设计](../../../development/AUTH_DESIGN.md)
