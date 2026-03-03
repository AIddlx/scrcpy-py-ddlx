# preview_process.py

> **文件**: `scrcpy_py_ddlx/preview_process.py`
> **功能**: 跨进程预览窗口

---

## 概述

`preview_process.py` 实现独立进程运行的预览窗口，避免与 MCP 服务器的异步事件循环冲突。

---

## 解决的问题

- MCP HTTP 服务器使用 asyncio 事件循环
- Qt GUI 也需要事件循环
- 两者在同一进程会冲突

解决方案：预览窗口在独立进程运行。

---

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                      主进程                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ MCP Server  │  │   Client    │  │    Frame Queue      │  │
│  │ (asyncio)   │  │  (解码)     │  │    (multiprocessing)│  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                              │               │
│                                              │ SHM/Queue    │
│                                              ▼               │
│                                    ┌─────────────────────┐   │
│                                    │   子进程预览窗口     │   │
│                                    │   (Qt 事件循环)      │   │
│                                    └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## FrameNotifierBase 类

跨进程帧通知器基类。

```python
class FrameNotifierBase:
    def notify(self) -> None           # 发送帧就绪通知
    def get_child_handle(self)         # 获取子进程句柄
    def close(self) -> None            # 清理资源
```

### 实现类

| 类 | 平台 | 说明 |
|---|------|------|
| `LocalSocketNotifier` | 跨平台 | QLocalServer/QLocalSocket |
| `WindowsEventNotifier` | Windows | Win32 Event |

---

## PreviewManager 类

```python
class PreviewManager:
    def __init__(self)

    # 启动预览进程
    def start(
        self,
        frame_queue: mp.Queue,
        device_name: str,
        width: int,
        height: int
    ) -> None

    # 停止预览进程
    def stop(self) -> None

    # 检查是否运行
    @property
    def is_running(self) -> bool
```

---

## 使用示例

```python
from scrcpy_py_ddlx.preview_process import PreviewManager
import multiprocessing as mp

# 创建帧队列
frame_queue = mp.Queue()

# 启动预览
manager = PreviewManager()
manager.start(
    frame_queue=frame_queue,
    device_name="Pixel 6",
    width=1080,
    height=2400
)

# 发送帧
while running:
    frame = decode_frame()
    frame_queue.put(frame)

# 停止预览
manager.stop()
```

---

## 共享内存帧

```python
# shared_memory_frame.py
class SharedMemoryFrame:
    """共享内存帧结构"""

    def __init__(self, width: int, height: int, format: str = "NV12"):
        self.width = width
        self.height = height
        self.format = format
        self.shm = shared_memory.SharedMemory(create=True, size=self.frame_size)

    def write(self, frame: bytes) -> None
    def read(self) -> bytes
    def close(self) -> None
```

---

## 跨进程通信方式

| 方式 | 用途 | 延迟 |
|------|------|------|
| `mp.Queue` | 帧数据传递 | ~1-5ms |
| `SharedMemory` | 大帧零拷贝 | ~0.1ms |
| `LocalSocket` | 帧就绪通知 | ~0.5ms |

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `preview_process.py` | 预览进程管理 |
| `shared_memory_frame.py` | 共享内存帧 |
| `simple_shm.py` | 简单共享内存 |

---

## 相关文档

- [opengl_window.md](opengl_window.md) - OpenGL 渲染
