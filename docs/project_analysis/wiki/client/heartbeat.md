# heartbeat.py

> **文件**: `core/heartbeat.py`
> **功能**: TCP 控制通道心跳机制

---

## 概述

`HeartbeatManager` 实现客户端心跳，检测连接是否存活。

---

## 解决的问题

1. **服务端无法检测客户端终止** - 客户端被杀死后服务端无限等待
2. **网络中断检测** - 非物理断开的网络问题
3. **短暂网络波动** - 1-2 秒的网络波动不应断开

---

## 常量

```python
DEFAULT_PING_INTERVAL = 2.0  # 每 2 秒发送 PING
DEFAULT_TIMEOUT = 5.0        # 5 秒无 PONG = 超时
```

---

## HeartbeatManager 类

```python
class HeartbeatManager:
    def __init__(
        self,
        ping_sender: Callable[[int], None],  # 发送 PING 的函数
        on_timeout: Callable[[], None],       # 超时回调
        ping_interval: float = 2.0,           # PING 间隔
        timeout: float = 5.0                  # 超时阈值
    )

    # 启动心跳线程
    def start(self) -> None

    # 停止心跳
    def stop(self) -> None

    # 收到 PONG 时调用
    def on_pong_received(self, timestamp: int) -> None

    # 状态属性
    @property
    def is_running(self) -> bool

    @property
    def stats(self) -> dict
```

---

## 工作流程

```
┌──────────────┐                    ┌──────────────┐
│    Client    │                    │    Server    │
│ HeartbeatMgr │                    │              │
└──────────────┘                    └──────────────┘
       │                                    │
       │──── PING (timestamp) ─────────────►│
       │     每 2 秒                          │
       │◄─── PONG (timestamp) ──────────────│
       │     立即响应                          │
       │                                    │
       │                                    │
       │  如果 5 秒无 PONG:                   │
       │  → 触发 on_timeout()               │
       │  → 断开连接                          │
       │                                    │
```

---

## 使用示例

```python
from scrcpy_py_ddlx.core.heartbeat import HeartbeatManager

def send_ping(timestamp):
    # 发送 PING 控制消息
    control.send_ping(timestamp)

def on_timeout():
    # 处理超时 - 断开连接
    logger.warning("Heartbeat timeout, disconnecting...")
    client.disconnect()

heartbeat = HeartbeatManager(
    ping_sender=send_ping,
    on_timeout=on_timeout
)
heartbeat.start()

# 当收到 PONG 时
heartbeat.on_pong_received(timestamp)

# 停止时
heartbeat.stop()
```

---

## 消息格式

### PING (25 bytes)

```
[TYPE_PING: 1B][timestamp: 8B][padding: 16B]

TYPE_PING: 0xAF
timestamp: 微秒时间戳
```

### PONG (5 bytes)

```
[TYPE_PONG: 1B][timestamp: 4B]

TYPE_PONG: 0xAE
timestamp: 时间戳低 32 位
```

---

## 统计信息

```python
stats = heartbeat.stats
# {
#     "pings_sent": 100,
#     "pongs_received": 100,
#     "last_pong_time": 1709123456.789,
#     "running": True
# }
```

---

## 相关文档

- [connection.md](connection.md) - 连接管理
