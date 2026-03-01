# 触摸控制

> 模拟触摸屏点击、滑动、长按等操作

---

## 功能清单

| 操作 | 方法 | 说明 |
|------|------|------|
| 点击 | `tap(x, y)` | 单次点击 |
| 滑动 | `swipe(start, end, duration)` | 滑动手势 |
| 长按 | `long_press(x, y, duration)` | 长按操作 |
| 多点触控 | `inject_touch_event(...)` | 多指触控 |

---

## 坐标系统

- 原点: 屏幕左上角
- X 轴: 向右递增
- Y 轴: 向下递增
- 单位: 像素

```
(0,0) ────────────► X
  │
  │
  │
  ▼
  Y
```

---

## 触摸消息格式

```
┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│ type (1) │ action(1)│ pointer_id│ x (4)   │ y (4)    │ ...      │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘

action:
  0 = DOWN
  1 = UP
  2 = MOVE
```

---

## 使用示例

### Python API

```python
from scrcpy_py_ddlx import Client

client = Client(device="device_serial")
client.start()

# 点击屏幕中心
client.control.tap(540, 960)

# 滑动解锁
client.control.swipe(
    start=(540, 1500),
    end=(540, 500),
    duration=0.3
)

# 长按
client.control.long_press(540, 960, duration=1.0)
```

### MCP 工具

```json
{
  "tool": "tap",
  "arguments": {
    "x": 540,
    "y": 960
  }
}
```

---

## 代码位置

| 组件 | 文件 |
|------|------|
| 客户端控制 | `core/control.py` |
| 服务端处理 | `control/Controller.java` |
| 指针状态 | `control/PointersState.java` |

---

## 注意事项

1. **坐标转换**: 自动处理设备分辨率
2. **多点触控**: 最多支持 10 个触点
3. **压力感应**: 部分设备支持
