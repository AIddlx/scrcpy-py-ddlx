# test_direct.py 文档

> ADB 隧道模式测试入口

---

## 概述

| 属性 | 值 |
|------|-----|
| **文件路径** | `tests_gui/test_direct.py` |
| **连接模式** | ADB 隧道 (USB) |
| **主要功能** | 音视频播放、录制、文件传输 |
| **代码行数** | ~520 行 |

---

## 目录结构

```
test_direct/
├── README.md           # 本文件
├── dependencies.md     # 依赖清单
├── features.md         # 功能详解
├── usage.md            # 使用说明
└── internal.md         # 内部实现
```

---

## 快速开始

```bash
cd C:\Project\IDEA\2\new\scrcpy-py-ddlx
python -X utf8 tests_gui/test_direct.py
```

---

## 核心特性

### 1. 自动设备发现

- USB 设备检测
- 无线 ADB 自动启用
- 局域网设备扫描

### 2. 音视频播放

- 视频解码 (H.264/H.265)
- 音频播放 (Opus)
- Qt OpenGL 渲染

### 3. 音频录制

- 原始 OPUS 包录制
- 定时录制
- 多格式支持 (opus/mp3/wav)

### 4. 文件传输

- 拖放传输
- APK 安装
- 文件推送

---

## 与其他入口的对比

| 特性 | test_direct.py | test_network_direct.py | scrcpy_http_mcp_server.py |
|------|---------------|----------------------|--------------------------|
| 连接模式 | ADB 隧道 | TCP+UDP 网络 | 两者都支持 |
| 需要 USB | ✅ 是 | 仅启动时 | 可选 |
| 延迟 | 较低 | 最低 | 取决于模式 |
| 适用场景 | 开发调试 | 无线使用 | AI 集成 |

---

## 详细文档

- [dependencies.md](dependencies.md) - 依赖清单
- [features.md](features.md) - 功能详解
- [usage.md](usage.md) - 使用说明
- [internal.md](internal.md) - 内部实现
