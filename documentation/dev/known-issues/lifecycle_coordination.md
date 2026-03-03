# 生命周期管理协定散乱

> 发现日期：2026-03-03
> 状态：待修复
> 优先级：中

## 问题描述

当服务端主动断开（如 Companion 终止服务端）时，客户端预览窗口无响应，不会自动退出。

## 复现步骤

1. 启动 `tests_gui/test_network_direct.py`
2. 在手机上用 Companion 终止服务端
3. 观察客户端：心跳超时日志打印，但窗口无响应

## 现象

```
[W] 11:50:57 [HEART] Heartbeat timeout: no PONG for 6.0s (threshold: 5.0s)
[W] 11:50:57 [CONN] Heartbeat timeout - disconnecting
# 窗口卡住，不会自动关闭
```

## 根本原因

### 架构层面：缺少统一的生命周期管理协定

| 组件 | 当前行为 | 问题 |
|------|----------|------|
| HeartbeatThread | 检测超时后直接调用 `window.close()` | **跨线程操作 Qt 对象** |
| Qt 主线程 | 被动等待窗口关闭 | 不知道连接已断开 |
| VideoDemuxer | 阻塞读取 socket | 没有被正确通知停止 |
| VideoWindow | 没有断开信号 | 无法感知底层状态 |

### 代码层面：线程越界

```python
# heartbeat.py - 在独立线程中运行
def _on_heartbeat_timeout(self) -> None:
    # ...
    if self._video_window is not None:
        self._video_window.close()  # ❌ 非 Qt 主线程调用，被忽略
```

Qt 要求所有 UI 操作必须在主线程执行。从其他线程调用 `close()` 会被静默忽略。

## 理想架构

```
连接断开事件
    │
    ▼
┌─────────────────────────────────────┐
│     状态管理器 (State Manager)        │
│     运行在 Qt 主线程                  │
│  - 接收所有状态变化信号               │
│  - 决定组件关闭顺序                   │
│  - 通过信号槽通知各组件               │
└─────────────────────────────────────┘
    │
    ├──▶ 关闭窗口 (主线程，合法)
    ├──▶ 设置 stop_event (通知解码器)
    ├──▶ 关闭 socket (安全关闭)
    └──▶ 退出 Qt 事件循环
```

## 当前架构问题

```
HeartbeatThread ──直接调用──▶ VideoWindow.close()  ❌ 跨线程
     │
     └── 没有信号机制通知主线程

各组件 "各管各的"，没有中央协调者
```

## 临时解决方案

使用 Qt 的跨线程调用机制：

```python
from PySide6.QtCore import QMetaObject, Qt

# 在 HeartbeatThread 中
QMetaObject.invokeMethod(
    self._video_window,
    "close",
    Qt.QueuedConnection
)
```

但这只是治标不治本。

## 长期解决方案

1. **引入状态管理器**：统一管理连接状态和生命周期
2. **定义组件接口**：明确每个组件的职责和通知机制
3. **使用信号槽**：所有跨线程通信使用 Qt 信号机制
4. **文档化协定**：在架构文档中明确定义

## 相关文件

| 文件 | 说明 |
|------|------|
| `scrcpy_py_ddlx/core/heartbeat.py` | 心跳检测线程 |
| `scrcpy_py_ddlx/client/client.py` | `_on_heartbeat_timeout()` 方法 |
| `scrcpy_py_ddlx/player/video/video_window.py` | 窗口类 |

## 影响范围

- 服务端主动断开时窗口无响应
- 网络异常断开时同样问题
- 用户体验差：需要手动关闭窗口
