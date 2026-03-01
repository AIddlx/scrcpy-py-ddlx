# 依赖清单

> 本目录统计 scrcpy-py-ddlx 项目的所有依赖项

---

## 目录结构

```
dependencies/
├── README.md           # 本文件 - 依赖概览
├── python.md           # Python 依赖详解
├── android.md          # Android/Java 依赖
├── system.md           # 系统依赖 (ADB, FFmpeg 等)
└── optional.md         # 可选依赖和开发工具
```

---

## 快速安装

### 完整安装 (推荐)

```bash
# Python 依赖
pip install -r requirements.txt

# 系统依赖
# Windows: 下载 ADB, FFmpeg
# Linux: sudo apt install android-tools-adb ffmpeg
# macOS: brew install android-platform-tools ffmpeg
```

### 最小安装 (仅核心功能)

```bash
pip install av numpy
```

### GUI 功能

```bash
pip install PySide6 PyOpenGL PyOpenGL_accelerate
```

### MCP 服务器

```bash
pip install mcp starlette uvicorn[standard]
```

---

## 依赖分类

| 类别 | 数量 | 说明 |
|------|------|------|
| Python 核心 | 2 | av, numpy |
| Python GUI | 3 | PySide6, PyOpenGL, PyOpenGL_accelerate |
| Python 音频 | 1 | sounddevice |
| Python MCP | 3 | mcp, starlette, uvicorn |
| Python 开发 | 3 | pytest, black, mypy |
| Android | 1 | JUnit (测试) |
| 系统 | 2 | ADB, FFmpeg |

---

## 版本要求

| 组件 | 最低版本 | 推荐版本 |
|------|---------|---------|
| Python | 3.8 | 3.11+ |
| Android SDK | 21 (5.0) | 31+ (12) |
| ADB | 1.0.40 | 1.0.41+ |
| FFmpeg | 4.0 | 5.0+ |

---

## 详细文档

- [python.md](python.md) - Python 依赖详解
- [android.md](android.md) - Android/Java 依赖
- [system.md](system.md) - 系统依赖
- [optional.md](optional.md) - 可选依赖和开发工具
