# Demuxer (客户端)

> **目录**: `core/demuxer/`
> **文件**: 8 个 Python 文件
> **功能**: 视频流解复用

---

## 文件清单

| 文件 | 职责 |
|------|------|
| `base.py` | 基类和异常定义 |
| `video.py` | TCP 视频解复用 |
| `audio.py` | TCP 音频解复用 |
| `udp_video.py` | UDP 视频解复用 |
| `udp_audio.py` | UDP 音频解复用 |
| `fec.py` | FEC 解码器 |
| `factory.py` | 解复用器工厂 |
| `__init__.py` | 模块导出 |

---

## 类层次结构

```
BaseDemuxer (缓冲式)
    └── VideoDemuxer (TCP)
    └── AudioDemuxer (TCP)

StreamingDemuxerBase (流式)
    └── StreamingVideoDemuxer
    └── StreamingAudioDemuxer

UdpVideoDemuxer (UDP)
UdpAudioDemuxer (UDP)
FecDecoder (FEC 解码)
```

---

## BaseDemuxer

缓冲式解复用器基类。

### 核心参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `buffer_size` | 2MB | 接收缓冲区 |
| `packet_queue` | - | 输出队列 |

### 核心方法

```python
class BaseDemuxer:
    def __init__(
        self,
        sock: socket.socket,
        packet_queue: Queue,
        buffer_size: int = 2 * 1024 * 1024
    ):
        """初始化解复用器。"""

    def start(self) -> None:
        """启动解复用线程。"""

    def stop(self) -> None:
        """停止解复用线程。"""

    def pause(self) -> None:
        """暂停解析 (继续接收数据)。"""

    def resume(self) -> None:
        """恢复解析。"""

    def get_stats(self) -> dict:
        """获取统计信息。"""
```

### 缓冲区管理

```python
# 懒压缩策略
COMPRESSION_THRESHOLD = 0.75  # 75% 满时压缩

def _compact_buffer(self, buffer: bytearray) -> None:
    """压缩缓冲区：移动剩余数据到开头。"""
    remaining = self._write_offset - self._read_offset
    if remaining > 0:
        buffer[:remaining] = buffer[self._read_offset:self._write_offset]
    self._read_offset = 0
    self._write_offset = remaining
```

---

## StreamingDemuxerBase

流式解复用器基类（无固定缓冲区）。

### 核心特点

- 无固定缓冲区分配
- 先读头部，再读精确负载
- 线程安全操作
- 优雅处理部分读取

### 核心方法

```python
class StreamingDemuxerBase:
    RECV_TIMEOUT = 5.0  # Socket 超时
    MAX_PACKET_SIZE = 16 * 1024 * 1024  # 最大包大小
    RECV_CHUNK_SIZE = 65536  # 接收块大小

    def _recv_exact(self, size: int) -> bytes:
        """
        精确读取指定字节数。

        循环直到读取完成或连接关闭。
        """

    def _recv_packet(self):
        """接收完整包 (子类实现)。"""

    def add_packet_sink(self, queue: Queue) -> None:
        """添加包接收器 (用于录制)。"""

    def get_last_packet_time(self) -> Optional[float]:
        """获取最后一个包的时间戳。"""

    def get_idle_seconds(self) -> float:
        """获取空闲秒数 (用于息屏检测)。"""
```

---

## VideoDemuxer (TCP)

TCP 视频解复用器。

```python
class VideoDemuxer(StreamingDemuxerBase):
    """
    TCP 视频流解复用器。

    解析格式:
    1. 编解码器 ID (4B)
    2. 视频尺寸 (8B: width + height)
    3. 包 (12B 头 + N 负载)
    """

    def _recv_packet(self) -> Optional[VideoPacket]:
        # 1. 解析包头 (12B)
        header_data = self._recv_exact(12)
        header = self._parse_header(header_data)

        # 2. 读取负载
        payload = self._recv_exact(header.size)

        return VideoPacket(header, payload, ...)
```

---

## UdpVideoDemuxer

UDP 视频解复用器。

```python
class UdpVideoDemuxer:
    """
    UDP 视频流解复用器。

    特点:
    - 无连接
    - 支持乱序重组
    - 支持 FEC 解码
    """

    def __init__(
        self,
        sock: socket.socket,
        packet_queue: Queue,
        fec_decoder: Optional[FecDecoder] = None
    ):
        self._fec_decoder = fec_decoder

    def _parse_udp_packet(self, data: bytes) -> Optional[UdpVideoPacket]:
        """
        解析 UDP 包格式:
        [seq: 4B][timestamp: 8B][flags: 4B][send_time_ns: 8B][payload]
        """
```

---

## FecDecoder

FEC 解码器。

```python
class FecDecoder:
    """
    前向纠错解码器。

    使用 XOR 异或校验恢复丢失的包。
    """

    def __init__(self, k: int = 4, m: int = 1):
        """
        Args:
            k: 数据包数量
            m: 校验包数量
        """

    def feed(self, packet: UdpPacket) -> Optional[List[bytes]]:
        """
        输入包，尝试恢复。

        Returns:
            恢复的数据包列表 (如果有)
        """

    def is_group_complete(self, seq: int) -> bool:
        """检查组是否完整。"""

    def get_stats(self) -> dict:
        """获取 FEC 统计。"""
```

### FEC 原理

```
组 (K=4, M=1):
  D0  D1  D2  D3  P0
  ─────────────── ───
  数据包 (4)      校验包 (1)

恢复能力: 丢失 1 个包可恢复

P0 = D0 ^ D1 ^ D2 ^ D3
D1 = P0 ^ D0 ^ D2 ^ D3  (如果 D1 丢失)
```

---

## DemuxerFactory

解复用器工厂。

```python
class DemuxerFactory:
    """创建合适的解复用器实例。"""

    @staticmethod
    def create_video_demuxer(
        sock: socket.socket,
        queue: Queue,
        mode: str = "tcp",
        fec_enabled: bool = False,
        **kwargs
    ) -> BaseDemuxer:
        """
        创建视频解复用器。

        Args:
            mode: "tcp" 或 "udp"
            fec_enabled: 是否启用 FEC
        """

    @staticmethod
    def create_audio_demuxer(
        sock: socket.socket,
        queue: Queue,
        mode: str = "tcp",
        fec_enabled: bool = False,
        **kwargs
    ) -> BaseDemuxer:
        """创建音频解复用器。"""
```

---

## 异常类型

```python
class DemuxerError(Exception):
    """解复用错误基类"""

class DemuxerStoppedError(DemuxerError):
    """解复用器已停止"""

class StreamingDemuxerError(DemuxerError):
    """流式解复用错误"""

class IncompleteReadError(StreamingDemuxerError):
    """读取不完整"""
    def __init__(self, expected: int, actual: int):
        ...
```

---

## 暂停/恢复机制

解复用器支持暂停时继续接收数据，防止 TCP 缓冲区堆积。

```python
def pause(self) -> None:
    """
    暂停解析但继续接收。

    - TCP 连接保持活跃
    - 服务端编码器不会阻塞
    - 可快速恢复
    """
    self._paused = True

def resume(self) -> None:
    """恢复解析。"""
    self._paused = False
    self._pause_event.set()
```

---

## 性能优化

### 内存视图

```python
# 使用 memoryview 避免临时字节对象
view = memoryview(buffer)
consumed = self._parse_buffer_with_offset(
    view[self._read_offset:self._write_offset],
    remaining_size
)
```

### 懒压缩

```python
# 只在缓冲区 75% 满时压缩
if available_space < self._buffer_size * (1 - 0.75):
    self._compact_buffer(buffer)
```

### 精确读取

```python
# 流式解复用器使用精确读取
def _recv_exact(self, size: int) -> bytes:
    """精确读取，避免缓冲区管理开销。"""
```

---

## 相关文档

- [stream.md](stream.md) - 流解析器
- [protocol.md](protocol.md) - 协议常量
- [Decoder.md](Decoder.md) - 解码器
- [udp_video_demuxer.md](udp_video_demuxer.md) - UDP 解复用详解
