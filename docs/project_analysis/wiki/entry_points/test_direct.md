# test_direct.py

> **文件**: `tests_gui/test_direct.py`
> **功能**: USB 模式入口脚本

---

## 概述

`test_direct.py` 是 USB 模式 (ADB Tunnel) 的主要入口，提供自动设备发现和连接功能。

---

## 主要功能

### 1. 自动设备发现

```python
def auto_discover_device():
    """
    自动发现设备策略:

    策略1: USB 设备 → 自动启用无线模式
    - 检测 USB 设备
    - 执行 adb tcpip 5555
    - 获取设备 IP
    - 建立无线连接

    策略2: 无 USB → 局域网扫描
    - 扫描 255 个 IP 的 5555 端口
    - 找到 ADB 设备后连接
    """
```

### 2. 音频录制

```python
# 配置项
ENABLE_AUDIO_RECORDING = False  # 启用录制
AUDIO_FORMAT = 'opus'           # 格式
RECORDING_DURATION = 10         # 时长 (秒)
```

### 3. 文件拖放传输

- 拖放 APK → 自动安装
- 拖放其他文件 → 推送到设备

---

## 工作流程

```
1. 检查依赖 (numpy, PySide6, PyAV)
2. 列出/发现设备
   ├── 有设备 → 使用
   └── 无设备 → 自动发现
3. 创建 ClientConfig
4. 连接设备
5. 初始化文件推送器
6. (可选) 启动音频录制
7. 运行 Qt 事件循环
8. 清理资源
```

---

## 配置

```python
config = ClientConfig(
    device_serial=device_id,
    host="localhost",
    port=27183,
    show_window=True,
    audio=True,
    audio_dup=False,
    clipboard_autosync=True,
    bitrate=2500000,
    max_fps=30,
)
```

---

## 日志

```
scrcpy_test_YYYYMMDD_HHMMSS.log
```

DEBUG 级别写入文件，INFO 级别输出控制台。

---

## 运行方式

```bash
cd C:\Project\IDEA\2\new\scrcpy-py-ddlx
python -X utf8 tests_gui/test_direct.py
```

---

## 相关文档

- [client.md](../client/client.md) - 客户端核心
- [connection.md](../client/connection.md) - 连接管理
