# 使用说明

> test_direct.py 的详细使用方法

---

## 基本用法

### 启动脚本

```bash
cd C:\Project\IDEA\2\new\scrcpy-py-ddlx
python -X utf8 tests_gui/test_direct.py
```

### 预期输出

```
============================================================
scrcpy-py-ddlsx 音视频录制测试
============================================================
[PASS] numpy: 2.2.4
[PASS] PySide6 已安装
[PASS] PyAV: 16.1.0
[PASS] 源码模块导入成功

正在创建客户端...
[INFO] 音频录制: 禁用

正在检测设备...
[INFO] 检测到 1 个已连接设备:
  - 192.168.1.100:5555

[INFO] 使用设备: 192.168.1.100:5555
正在连接到设备...

========================================
[SUCCESS] 连接成功!
  设备名称: Samsung SM-S908B
  设备分辨率: 1080x2340
========================================

[INFO] 文件传输已启用 (拖放 APK 或文件到窗口)

视频窗口已显示，你可以:
  - 使用鼠标点击/拖拽控制设备
  - 使用键盘输入文字
  - 使用滚轮滚动
  - 拖放 APK 文件到窗口安装
  - 拖放其他文件到窗口推送到设备

关闭窗口或按 Ctrl+C 断开连接...
```

---

## 配置修改

### 启用音频录制

编辑 `test_direct.py`:

```python
# ===== 音频录制配置 =====
ENABLE_AUDIO_RECORDING = True  # 启用录制
AUDIO_FORMAT = 'opus'          # 格式: opus/mp3/wav
RECORDING_DURATION = 30        # 录制 30 秒
```

### 调整视频参数

```python
config = ClientConfig(
    bitrate=8000000,    # 8 Mbps (更高画质)
    max_fps=60,         # 60fps (更流畅)
)
```

---

## 自动发现场景

### 场景 1: USB 连接

```
1. USB 线连接手机
2. 运行脚本
3. 自动检测到 USB 设备
4. 自动启用无线模式
5. 获取设备 IP
6. 建立无线连接
7. 可以拔掉 USB 线
```

### 场景 2: 纯无线

```
1. 手机已开启无线调试 (之前用 USB 启用过)
2. 运行脚本
3. 扫描局域网 (10-30 秒)
4. 发现设备并连接
```

---

## 日志文件

### 位置

```
scrcpy_test_{timestamp}.log
```

### 内容

```
2026-03-01 10:30:00.123 - root - DEBUG - [test_direct.py:42] - Starting...
2026-03-01 10:30:00.456 - scrcpy_py_ddlx.client - INFO - Connecting...
```

---

## 常见问题

### Q: 检测不到设备

**解决方案**:
1. 确认 USB 调试已开启
2. 确认已授权电脑调试
3. 尝试 `adb devices` 命令

### Q: 无线连接失败

**解决方案**:
1. 确认手机和电脑在同一 WiFi
2. 确认之前用 USB 成功启用过无线调试
3. 检查防火墙设置

### Q: 窗口黑屏

**解决方案**:
1. 检查 PyAV 安装
2. 检查 FFmpeg 安装
3. 查看日志文件

---

## 相关文档

- [dependencies.md](dependencies.md) - 依赖清单
- [features.md](features.md) - 功能详解
- [internal.md](internal.md) - 内部实现
