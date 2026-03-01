# 应用管理工具

> 安装、卸载、启动应用

---

## list_apps

列出已安装应用。

### 参数

```json
{
  "include_system": false,
  "filter": ""
}
```

### 返回

```json
{
  "success": true,
  "apps": [
    {
      "package_name": "com.example.app",
      "label": "Example App",
      "version": "1.0.0",
      "is_system": false
    }
  ]
}
```

---

## start_app

启动应用。

### 参数

```json
{
  "package_name": "com.example.app",
  "activity": "com.example.app.MainActivity"
}
```

### 返回

```json
{
  "success": true
}
```

### 常用包名

| 应用 | 包名 |
|------|------|
| 设置 | `com.android.settings` |
| 相机 | `com.android.camera` |
| 浏览器 | `com.android.chrome` |
| 微信 | `com.tencent.mm` |
| 支付宝 | `com.eg.android.AlipayGphone` |

---

## stop_app

停止应用。

### 参数

```json
{
  "package_name": "com.example.app"
}
```

### 返回

```json
{
  "success": true
}
```

---

## install_apk

安装 APK 文件。

### 参数

```json
{
  "apk_path": "/sdcard/Download/app.apk"
}
```

### 返回

```json
{
  "success": true,
  "package_name": "com.example.app"
}
```

---

## uninstall_app

卸载应用。

### 参数

```json
{
  "package_name": "com.example.app"
}
```

### 返回

```json
{
  "success": true
}
```

---

## 操作示例

### 安装新应用

```json
// 1. 推送 APK
push_file({
  "local_path": "./app.apk",
  "remote_path": "/sdcard/Download/app.apk"
})

// 2. 安装
install_apk({
  "apk_path": "/sdcard/Download/app.apk"
})

// 3. 启动
start_app({
  "package_name": "com.example.app"
})
```

### 清理应用

```json
// 1. 停止应用
stop_app({ "package_name": "com.example.app" })

// 2. 卸载
uninstall_app({ "package_name": "com.example.app" })
```

### 查找并启动应用

```json
// 1. 列出应用
list_apps({ "filter": "chrome" })

// 2. 启动
start_app({ "package_name": "com.android.chrome" })
```
