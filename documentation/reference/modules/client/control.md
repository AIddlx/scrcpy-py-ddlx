# ControlMessage - 控制消息

> **路径**: `scrcpy_py_ddlx/core/control.py`
> **职责**: 控制消息的序列化和队列管理

---

## 类定义

### ControlMessage

**职责**: 表示一个待发送的控制消息

**依赖**: protocol.py 中的枚举和常量

---

## 主要方法

### 设置方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `set_keycode` | action, keycode, repeat, metastate | 设置按键事件 |
| `set_text` | text | 设置文本注入 |
| `set_touch_event` | action, pointer_id, x, y, ... | 设置触摸事件 |
| `set_scroll_event` | x, y, w, h, hscroll, vscroll | 设置滚动事件 |
| `set_back_or_screen_on` | action | 返回/亮屏 |
| `set_clipboard` | sequence, text, paste | 设置剪贴板 |
| `set_ping` | timestamp | 设置心跳 |

### 序列化

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `serialize` | bytes | 序列化为字节 |
| `is_droppable` | bool | 是否可丢弃 |

---

## 序列化格式

### 通用头部

```
[type: 1B][length: 4B][payload: NB]
```

### 按键事件

```
[type:1B][len:4B][action:1B][keycode:4B][repeat:4B][metastate:4B]
```

### 触摸事件

```
[type:1B][len:4B][action:1B][pointer_id:8B][x:4B][y:4B]
[width:4B][height:4B][pressure:4B][buttons:4B]
```

### 文本注入

```
[type:1B][len:4B][text_len:4B][text:NB]
```

### 剪贴板

```
[type:1B][len:4B][sequence:4B][paste:1B][text_len:4B][text:NB]
```

### 心跳

```
[type:1B][len:4B][timestamp:8B]
```

---

## ControlMessageQueue

**职责**: 线程安全的控制消息队列

**基于**: 官方 scrcpy 设计

---

## 队列常量

| 常量 | 值 | 说明 |
|------|-----|------|
| `MAX_DROPPABLE_SIZE` | 60 | 可丢弃消息上限 |
| `MAX_NON_DROPPABLE_SIZE` | 4 | 不可丢弃消息保留槽 |

---

## 队列属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `_queue` | deque | 消息队列 |
| `_lock` | Lock | 线程锁 |
| `_cond` | Condition | 条件变量 |
| `_droppable_count` | int | 可丢弃消息计数 |

---

## 队列方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `put` | msg | bool | 入队 (自动丢弃旧消息) |
| `get` | timeout | ControlMessage | 出队 |
| `peek` | - | ControlMessage | 查看队首 |
| `clear` | - | - | 清空 |
| `size` | - | int | 获取大小 |

---

## 队列丢弃策略

```python
def put(msg):
    # 不可丢弃消息 (如 SET_CLIPBOARD)
    if not msg.is_droppable():
        # 确保保留槽位
        while size() >= MAX_SIZE - MAX_NON_DROPPABLE_SIZE:
            # 丢弃最旧的可丢弃消息
            drop_oldest_droppable()

    # 可丢弃消息 (如 TOUCH_EVENT)
    else:
        # 超过上限则丢弃
        if _droppable_count >= MAX_DROPPABLE_SIZE:
            return False  # 拒绝入队

    _queue.append(msg)
```

---

## 依赖关系

```
ControlMessage
    │
    └──→ protocol.py (枚举、常量)

ControlMessageQueue
    │
    ├──→ threading.Lock
    │
    ├──→ threading.Condition
    │
    └──→ collections.deque
```

**被依赖**:
- client.py (创建和使用)
- opengl_window.py (发送控制)
- input_handler.py (发送控制)

---

*此文档基于代码分析生成*
