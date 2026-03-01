# 文件操作工具

> 文件传输和管理

---

## list_files

列出目录内容。

### 参数

```json
{
  "path": "/sdcard/Download"
}
```

### 返回

```json
{
  "success": true,
  "files": [
    {
      "name": "document.pdf",
      "size": 123456,
      "is_directory": false,
      "modified": "2026-03-01T10:30:00"
    },
    {
      "name": "Photos",
      "is_directory": true
    }
  ]
}
```

---

## push_file

推送文件到设备。

### 参数

```json
{
  "local_path": "/path/to/file.pdf",
  "remote_path": "/sdcard/Download/file.pdf"
}
```

### 返回

```json
{
  "success": true,
  "bytes_transferred": 123456
}
```

---

## pull_file

从设备拉取文件。

### 参数

```json
{
  "remote_path": "/sdcard/DCIM/photo.jpg",
  "local_path": "/local/path/photo.jpg"
}
```

### 返回

```json
{
  "success": true,
  "bytes_transferred": 2456789
}
```

---

## delete_file

删除文件或目录。

### 参数

```json
{
  "path": "/sdcard/Download/old_file.txt"
}
```

### 返回

```json
{
  "success": true
}
```

---

## mkdir

创建目录。

### 参数

```json
{
  "path": "/sdcard/Download/new_folder"
}
```

### 返回

```json
{
  "success": true
}
```

---

## download_file

从 URL 下载文件到设备。

### 参数

```json
{
  "url": "https://example.com/file.pdf",
  "remote_path": "/sdcard/Download/file.pdf"
}
```

### 返回

```json
{
  "success": true,
  "bytes_transferred": 1234567
}
```

---

## 常用路径

| 路径 | 说明 |
|------|------|
| `/sdcard` | 存储根目录 |
| `/sdcard/Download` | 下载目录 |
| `/sdcard/DCIM` | 相册 |
| `/sdcard/Pictures` | 图片 |
| `/sdcard/Movies` | 视频 |
| `/sdcard/Music` | 音乐 |
| `/sdcard/Documents` | 文档 |

---

## 操作示例

### 下载并推送 APK

```json
// 1. 下载 APK
download_file({
  "url": "https://example.com/app.apk",
  "remote_path": "/sdcard/Download/app.apk"
})

// 2. 安装 (使用 install_apk 工具)
install_apk({
  "apk_path": "/sdcard/Download/app.apk"
})
```

### 备份照片

```json
// 1. 列出照片
list_files({ "path": "/sdcard/DCIM/Camera" })

// 2. 拉取照片
pull_file({
  "remote_path": "/sdcard/DCIM/Camera/IMG_001.jpg",
  "local_path": "./backup/IMG_001.jpg"
})
```
