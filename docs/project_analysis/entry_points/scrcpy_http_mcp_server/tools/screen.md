# 屏幕操作工具

> 截图、状态、旋转等

---

## screenshot

截取屏幕图像。

### 参数

```json
{
  "save_path": "string (optional)",
  "format": "png | jpg",
  "quality": 90
}
```

### 返回

```json
{
  "success": true,
  "path": "/path/to/screenshot.png",
  "width": 1080,
  "height": 2340,
  "size": 245678
}
```

### 示例

```json
{
  "name": "screenshot",
  "arguments": {
    "save_path": "screenshots/test.png"
  }
}
```

---

## get_state

获取设备状态。

### 参数

无

### 返回

```json
{
  "connected": true,
  "device_name": "Samsung SM-S908B",
  "width": 1080,
  "height": 2340,
  "orientation": "portrait",
  "fps": 60,
  "codec": "h264",
  "bitrate": 8000000
}
```

### 用途

- 确定屏幕方向
- 获取当前分辨率
- 验证连接状态

---

## rotate

旋转屏幕。

### 参数

```json
{
  "direction": "left | right | portrait | landscape"
}
```

### 返回

```json
{
  "success": true,
  "new_orientation": "landscape"
}
```

---

## set_display_power

开关屏幕。

### 参数

```json
{
  "on": true | false
}
```

### 返回

```json
{
  "success": true,
  "display_on": true
}
```

---

## expand_notification_panel

展开通知面板。

### 参数

无

### 返回

```json
{
  "success": true
}
```

---

## collapse_panels

收起所有面板。

### 参数

无

### 返回

```json
{
  "success": true
}
```

---

## expand_settings_panel

展开设置面板。

### 参数

无

### 返回

```json
{
  "success": true
}
```

---

## get_screen_resolution

获取屏幕分辨率。

### 参数

无

### 返回

```json
{
  "width": 1080,
  "height": 2340,
  "density": 420,
  "orientation": "portrait"
}
```

---

## 坐标计算

### 获取中心点

```json
// 先获取状态
get_state() -> { "width": 1080, "height": 2340 }

// 计算中心
center_x = 1080 / 2 = 540
center_y = 2340 / 2 = 1170

// 点击中心
tap(540, 1170)
```

### 适应旋转

```json
// 竖屏: 1080 x 2340
// 横屏: 2340 x 1080

// 旋转后需要重新获取分辨率
rotate("right")
get_state() -> { "width": 2340, "height": 1080 }
```
