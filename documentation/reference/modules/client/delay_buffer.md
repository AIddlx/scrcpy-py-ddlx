# DelayBuffer - 单帧缓冲区

> **路径**: `scrcpy_py_ddlx/core/decoder/delay_buffer.py`
> **职责**: 单帧延迟缓冲区，实现事件驱动的帧通知机制

---

## 类定义

### FrameWithMetadata (NamedTuple)

**职责**: 带元数据的帧容器

| 字段 | 类型 | 说明 |
|------|------|------|
| `frame` | any | 帧数据 (numpy数组) |
| `packet_id` | int | 包ID (延迟追踪) |
| `pts` | int | 显示时间戳 (纳秒) |
| `capture_time` | float | 解码时间 (秒) |
| `udp_recv_time` | float | UDP接收时间 (秒) |
| `send_time_ns` | int | 设备发送时间 (纳秒) |
| `width` | int | 帧宽度 |
| `height` | int | 帧高度 |

---

### DelayBuffer

**职责**: 单帧缓冲区，事件驱动通知

**基于**: scrcpy/app/src/frame_buffer.c

**线程安全**: 使用 Lock + Condition

---

## 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `_pending_frame` | FrameWithMetadata | 当前帧 |
| `_tmp_frame` | any | 临时帧 (原子交换) |
| `_consumed` | bool | 消费标志 |
| `_lock` | Lock | 线程锁 |
| `_condition` | Condition | 条件变量 |
| `_frame_ready_signal` | Signal | Qt信号 (事件驱动) |

---

## 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `push` | frame, packet_id, pts, ... | (bool, bool) | 推送帧 |
| `consume` | - | FrameWithMetadata | 消费帧 |
| `wait_for_frame` | timeout | FrameWithMetadata | 等待帧 |
| `set_frame_ready_signal` | signal | - | 设置事件信号 |
| `has_new_frame` | - | bool | 检查新帧 |
| `clear` | - | - | 清空缓冲 |

---

## push() 方法

```python
def push(frame, packet_id, pts, capture_time, udp_recv_time,
         send_time_ns, width, height) -> Tuple[bool, bool]:
    """
    推送帧到缓冲区

    Returns:
        (success, previous_skipped)
        - success: 是否成功
        - previous_skipped: 上一帧是否被跳过
    """
```

**流程**:
1. 获取锁
2. 检查上一帧是否被消费
3. 直接赋值 (无拷贝)
4. 重置 consumed 标志
5. 通知等待者
6. 触发信号 (事件驱动)

---

## consume() 方法

```python
def consume() -> FrameWithMetadata:
    """
    消费当前帧

    Returns:
        FrameWithMetadata 或 None
    """
```

**流程**:
1. 获取锁
2. 检查 consumed 标志
3. 返回帧引用 (零拷贝)
4. 设置 consumed = True

---

## 事件驱动机制

```python
# 设置 Qt 信号
buffer.set_frame_ready_signal(self._frame_ready_signal)

# push 时自动触发
if self._frame_ready_signal:
    self._frame_ready_signal.emit()  # 通知渲染器
```

**优势**: 无需轮询，帧到达立即渲染

---

## 单帧缓冲特性

```
生产者                    消费者
   │                        │
   │ push(frame_1)          │
   │ ├─→ _pending_frame     │
   │ │   = frame_1          │
   │ │                      │ consume()
   │ │                      ├─→ return frame_1
   │ │                      │
   │ push(frame_2)          │
   │ ├─→ previous_skipped   │ consume()
   │ │   = False            ├─→ return None
   │ ├─→ _pending_frame     │ (已消费)
   │ │   = frame_2          │
```

---

## 延迟追踪

```python
# FrameWithMetadata 包含完整延迟信息
frame = buffer.consume()

# E2E 延迟计算
e2e_ms = (time.time() * 1e9 - frame.send_time_ns) / 1e6

# 解码延迟
decode_ms = frame.capture_time - frame.udp_recv_time
```

---

## 依赖关系

```
DelayBuffer
    │
    ├──→ threading.Lock
    │
    ├──→ threading.Condition
    │
    └──→ PySide6.Signal (可选)
```

**被依赖**:
- VideoDecoder (输出)
- OpenGLWindow (输入)
- Screen (中间层)

---

*此文档基于代码分析生成*
