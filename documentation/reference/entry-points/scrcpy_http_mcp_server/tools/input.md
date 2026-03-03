# 输入控制工具

> 触摸、按键、文字输入

---

## tap

点击屏幕指定位置。

### 参数

```json
{
  "x": 540,
  "y": 1200
}
```

### 返回

```json
{
  "success": true
}
```

---

## swipe

滑动操作。

### 参数

```json
{
  "start_x": 540,
  "start_y": 1500,
  "end_x": 540,
  "end_y": 500,
  "duration_ms": 300
}
```

### 返回

```json
{
  "success": true
}
```

### 常用滑动

```json
// 向上滑动 (向下翻页)
{
  "start_y": 2000,
  "end_y": 500
}

// 向下滑动 (向上翻页)
{
  "start_y": 500,
  "end_y": 2000
}

// 返回手势 (从左边缘滑动)
{
  "start_x": 0,
  "end_x": 500,
  "start_y": 1200,
  "end_y": 1200
}
```

---

## long_press

长按操作。

### 参数

```json
{
  "x": 540,
  "y": 1200,
  "duration_ms": 1000
}
```

### 返回

```json
{
  "success": true
}
```

---

## double_tap

双击操作。

### 参数

```json
{
  "x": 540,
  "y": 1200,
  "interval_ms": 100
}
```

### 返回

```json
{
  "success": true
}
```

---

## type_text

输入文字。

### 参数

```json
{
  "text": "Hello World"
}
```

### 返回

```json
{
  "success": true
}
```

### 注意

- 确保输入框已获得焦点
- 支持中英文
- 特殊字符会被转义

---

## press_key

发送按键事件。

### 参数

```json
{
  "keycode": "HOME",
  "action": "down_up"
}
```

### 常用键码

| 键码 | 说明 |
|------|------|
| HOME | 主页 |
| BACK | 返回 |
| MENU | 菜单 |
| ENTER | 回车 |
| DEL | 删除 |
| VOLUME_UP | 音量+ |
| VOLUME_DOWN | 音量- |
| POWER | 电源 |

---

## press_back

发送返回键。

### 参数

无

### 返回

```json
{
  "success": true
}
```

---

## press_home

发送主页键。

### 参数

无

### 返回

```json
{
  "success": true
}
```

---

## press_recent

发送最近任务键。

### 参数

无

### 返回

```json
{
  "success": true
}
```

---

## scroll

滚动操作。

### 参数

```json
{
  "x": 540,
  "y": 1200,
  "direction": "up | down | left | right",
  "distance": 500
}
```

### 返回

```json
{
  "success": true
}
```

---

## 常用操作示例

### 打开应用

```json
// 1. 回到主页
press_home()

// 2. 上滑打开应用抽屉
swipe(540, 2000, 540, 500)

// 3. 点击应用图标
tap(270, 800)
```

### 滚动列表

```json
// 向下翻页
scroll(540, 1200, "up", 1000)

// 向上翻页
scroll(540, 1200, "down", 1000)
```

### 搜索

```json
// 1. 点击搜索框
tap(540, 100)

// 2. 输入文字
type_text("search query")

// 3. 按回车搜索
press_key("ENTER")
```
