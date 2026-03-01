# 内部实现

> test_direct.py 的代码结构和内部逻辑

---

## 代码结构

```
test_direct.py (520 行)
│
├── 导入和配置 (1-70)
│   ├── 标准库导入
│   ├── 日志配置
│   └── 全局变量
│
├── 音频录制配置 (74-88)
│   ├── ENABLE_AUDIO_RECORDING
│   ├── AUDIO_FORMAT
│   └── RECORDING_DURATION
│
├── 设备发现函数 (90-306)
│   ├── list_devices()
│   ├── check_adb_port()
│   └── auto_discover_device()
│
├── 录制线程 (309-326)
│   └── _timed_recording_thread()
│
└── 主函数 (329-521)
    ├── 依赖检查
    ├── 设备检测
    ├── 客户端创建
    ├── 连接和运行
    └── 清理
```

---

## 核心函数

### auto_discover_device()

```python
def auto_discover_device():
    """
    自动发现并连接设备。

    策略1: USB 设备 → 自动启用无线
    策略2: 扫描局域网 → 发现 ADB 设备

    Returns:
        str: 设备地址 (如 "192.168.1.100:5555")
        None: 未找到设备
    """
```

### 流程图

```
auto_discover_device()
    │
    ├── 检查 USB 设备
    │     │
    │     ├── 发现 USB 设备
    │     │     │
    │     │     ├── adb tcpip 5555
    │     │     ├── 获取设备 IP
    │     │     │     ├── wlan0
    │     │     │     ├── wifi0
    │     │     │     └── eth0
    │     │     │
    │     │     └── adb connect {ip}:5555
    │     │
    │     └── 无 USB 设备
    │           │
    │           ├── 获取本机 IP
    │           ├── 计算网段
    │           ├── 并发扫描 1-254
    │           │     └── check_adb_port(ip)
    │           │
    │           └── 尝试连接发现的设备
    │
    └── 返回设备地址或 None
```

---

## 线程模型

```
主线程
    │
    ├── 日志配置
    ├── 依赖检查
    ├── 设备发现
    ├── 客户端创建
    │
    ├── Qt 事件循环 (client.run_with_qt())
    │     │
    │     ├── 视频解码线程 (内部)
    │     ├── 音频解码线程 (内部)
    │     └── GUI 渲染
    │
    └── 清理

定时录制线程 (可选)
    │
    ├── sleep(duration)
    └── client.stop_opus_recording()
```

---

## 配置参数

### ClientConfig 参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `device_serial` | 自动检测 | 设备序列号 |
| `host` | "localhost" | ADB 主机 |
| `port` | 27183 | ADB 端口 |
| `show_window` | True | 显示窗口 |
| `audio` | True | 启用音频 |
| `audio_dup` | False | 音频复用 |
| `clipboard_autosync` | True | 剪贴板同步 |
| `bitrate` | 2500000 | 2.5 Mbps |
| `max_fps` | 30 | 30fps |

---

## 日志配置

### 格式

```python
# 文件: 详细格式
fmt='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'

# 控制台: 精简格式
fmt='%(levelname)s - %(message)s'
```

### 文件名

```python
log_filename = f"scrcpy_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
# 例如: scrcpy_test_20260301_103000.log
```

---

## 错误处理

### 连接失败

```python
try:
    client.connect()
except KeyboardInterrupt:
    print("\n\n用户中断连接")
except Exception as e:
    print(f"\n[ERROR] 连接失败: {e}")
    traceback.print_exc()
finally:
    # 清理资源
    client.disconnect()
```

### 录制停止

```python
# 确保录制正确停止
if ENABLE_AUDIO_RECORDING and client:
    try:
        filename = client.stop_opus_recording()
        if filename:
            # 报告保存信息
    except Exception as e:
        print(f"[WARN] 停止录制时出错: {e}")
```

---

## 相关文档

- [dependencies.md](dependencies.md) - 依赖清单
- [features.md](features.md) - 功能详解
- [usage.md](usage.md) - 使用说明
