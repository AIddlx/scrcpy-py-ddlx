# 功能详解

> test_direct.py 的全部功能说明

---

## 1. 设备发现

### 1.1 已连接设备检测

```python
def list_devices():
    """获取已连接的设备列表"""
    result = subprocess.run(["adb", "devices"], ...)
    # 返回: ["device_serial_1", "192.168.1.100:5555", ...]
```

### 1.2 自动发现流程

```
开始
  │
  ├── 检测 USB 设备
  │     │
  │     ├── 有 USB 设备
  │     │     │
  │     │     ├── 启用 TCP/IP (adb tcpip 5555)
  │     │     ├── 获取设备 IP
  │     │     └── 建立无线连接
  │     │
  │     └── 无 USB 设备
  │           │
  │           └── 扫描局域网 (并发扫描 1-254)
  │
  └── 返回设备地址
```

### 1.3 局域网扫描

```python
# 并发扫描 254 个 IP
with ThreadPoolExecutor(max_workers=50) as executor:
    for i in range(1, 255):
        ip = f"{network_prefix}.{i}"
        futures[executor.submit(check_adb_port, ip)] = ip
```

---

## 2. 音视频播放

### 2.1 视频配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `bitrate` | 2500000 | 2.5 Mbps |
| `max_fps` | 30 | 30 帧/秒 |
| `show_window` | True | 显示窗口 |

### 2.2 音频配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `audio` | True | 启用音频 |
| `audio_dup` | False | 不复用 |

### 2.3 剪贴板同步

```python
config = ClientConfig(
    clipboard_autosync=True,  # PC ↔ 设备双向同步
)
```

---

## 3. 音频录制

### 3.1 配置开关

```python
# 录制开关
ENABLE_AUDIO_RECORDING = False  # 改为 True 启用

# 录制格式: 'opus', 'mp3', 'wav'
AUDIO_FORMAT = 'opus'

# 录制时长（秒），None = 无限制
RECORDING_DURATION = 10
```

### 3.2 录制流程

```
开始录制
    │
    ├── client.start_opus_recording(filename)
    │
    ├── 有时长限制?
    │     │
    │     ├── 是 → 启动定时线程
    │     │        │
    │     │        └── 时间到 → client.stop_opus_recording()
    │     │
    │     └── 否 → 窗口关闭时停止
    │
    └── 保存文件 (OGG Opus 格式)
```

### 3.3 录制特点

- **零 CPU 开销**: 原始 OPUS 包直接写入
- **格式**: OGG Opus 容器
- **文件名**: `recording_{timestamp}.{format}`

---

## 4. 文件传输

### 4.1 初始化

```python
file_pusher = init_file_pusher(
    device_serial=device_id,
    on_complete=on_file_transfer_complete
)
```

### 4.2 支持的操作

| 操作 | 说明 |
|------|------|
| APK 拖放 | 自动安装到设备 |
| 文件拖放 | 推送到设备 Download 目录 |

### 4.3 回调函数

```python
def on_file_transfer_complete(success: bool, action: str, file_path: str):
    """文件传输完成回调"""
    if success:
        if action == "install":
            print(f"APK 安装成功: {filename}")
        else:
            print(f"文件推送成功: {filename}")
```

---

## 5. 用户交互

### 5.1 支持的操作

| 操作 | 说明 |
|------|------|
| 鼠标点击 | 触摸点击 |
| 鼠标拖拽 | 触摸滑动 |
| 滚轮 | 滚动 |
| 键盘 | 文字输入 |
| 文件拖放 | 文件传输 |

### 5.2 退出方式

- 关闭窗口
- Ctrl+C

---

## 相关文档

- [dependencies.md](dependencies.md) - 依赖清单
- [usage.md](usage.md) - 使用说明
- [internal.md](internal.md) - 内部实现
