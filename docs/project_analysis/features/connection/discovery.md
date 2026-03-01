# 设备发现与唤醒

> 自动发现局域网设备，唤醒休眠设备

---

## 功能清单

| 功能 | 文件 | 协议 | 端口 |
|------|------|------|------|
| UDP 发现 | `client/udp_discovery.py` | UDP 广播 | 27186 |
| UDP 唤醒 | `client/udp_wake.py` | UDP 魔术包 | 27186 |

---

## UDP 设备发现

### 工作原理

```
┌──────────────┐                    ┌──────────────┐
│    Python    │                    │   Android    │
│   Discovery  │                    │   Receiver   │
└──────────────┘                    └──────────────┘
       │                                   │
       │──── "SCRCPY_DISCOVER" ──────────►│ (广播)
       │◄─── Device Info JSON ────────────│
       │                                   │
```

### 发现响应格式

```json
{
  "device": "Pixel 6",
  "serial": "12345678",
  "ip": "192.168.1.100",
  "port": 27183,
  "version": "1.4"
}
```

### 使用方式

```python
from scrcpy_py_ddlx.client.udp_discovery import UdpDiscovery

discovery = UdpDiscovery()
devices = discovery.discover(timeout=5.0)

for device in devices:
    print(f"{device['device']} @ {device['ip']}")
```

---

## UDP 设备唤醒

### 工作原理

当设备屏幕休眠时，可以通过 UDP 魔术包唤醒：

```
┌──────────────┐                    ┌──────────────┐
│    Python    │                    │   Android    │
│    Wake      │                    │   Receiver   │
└──────────────┘                    └──────────────┘
       │                                   │
       │──── WAKE_MAGIC_PACKET ──────────►│
       │                                   │
       │           (设备唤醒)               │
       │                                   │
```

### 唤醒包格式

```
[WAKE_HEADER: 4 bytes] [DEVICE_SERIAL: 变长]
     "WAKE"                "12345678"
```

### 使用方式

```python
from scrcpy_py_ddlx.client.udp_wake import UdpWake

wake = UdpWake()
wake.wake_device("192.168.1.100", "12345678")
```

---

## 服务端实现

| 功能 | 文件 |
|------|------|
| 发现响应 | `udp/UdpDiscoveryReceiver.java` |
| 唤醒处理 | 集成在 Discovery 中 |

---

## 注意事项

1. **防火墙**: 确保 UDP 端口 27186 未被阻止
2. **同一网段**: 发现和唤醒需要同一局域网
3. **权限**: Android 端需要保持服务运行
