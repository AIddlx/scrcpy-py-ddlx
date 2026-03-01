# Python 依赖

> Python 包依赖详解

---

## 核心依赖

### av (PyAV)

| 属性 | 值 |
|------|-----|
| **版本** | >=13.0.0 |
| **当前** | 16.1.0 |
| **用途** | FFmpeg Python 绑定 |
| **功能** | 视频/音频编解码 |

```python
import av

# 解码 H.264
container = av.open(video_stream)
for frame in container.decode(video=0):
    img = frame.to_ndarray(format='bgr24')
```

**依赖**:
- FFmpeg 库 (系统安装)

**安装**:
```bash
pip install av
# 或指定版本
pip install av>=13.0.0
```

---

### numpy

| 属性 | 值 |
|------|-----|
| **版本** | >=1.24.0, <2.0.0 |
| **当前** | 2.2.4 |
| **用途** | 数值计算 |
| **功能** | 视频帧数据处理 |

```python
import numpy as np

# BGR 帧数据
frame: np.ndarray  # shape: (height, width, 3)
```

**说明**:
- 版本限制 <2.0.0 是为了兼容性
- 实际测试支持 numpy 2.x

---

## GUI 依赖

### PySide6

| 属性 | 值 |
|------|-----|
| **版本** | >=6.6.0 |
| **当前** | 6.10.1 |
| **用途** | Qt6 Python 绑定 |
| **功能** | GUI 窗口、事件处理 |

```python
from PySide6.QtWidgets import QMainWindow
from PySide6.QtOpenGLWidgets import QOpenGLWidget
```

**子依赖**:
- PySide6_Addons
- PySide6_Essentials
- shiboken6

**安装**:
```bash
pip install PySide6
```

---

### PyOpenGL

| 属性 | 值 |
|------|-----|
| **版本** | 3.1.10 |
| **用途** | OpenGL Python 绑定 |
| **功能** | GPU 视频渲染 |

```python
from OpenGL.GL import *
from OpenGL.GLU import *

# 纹理渲染
glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, ...)
```

---

### PyOpenGL_accelerate

| 属性 | 值 |
|------|-----|
| **版本** | 同 PyOpenGL |
| **用途** | OpenGL 加速 |
| **功能** | C 扩展加速 |

**说明**:
- 可选但推荐
- 显著提升 OpenGL 性能

---

## 音频依赖

### sounddevice

| 属性 | 值 |
|------|-----|
| **版本** | 0.5.3 |
| **用途** | 音频播放/录制 |
| **功能** | 跨平台音频 I/O |

```python
import sounddevice as sd

# 播放音频
sd.play(audio_data, samplerate=48000)
```

**子依赖**:
- CFFI

**安装**:
```bash
pip install sounddevice
# Linux 可能需要
sudo apt install libportaudio2
```

---

## MCP 依赖

### mcp

| 属性 | 值 |
|------|-----|
| **版本** | 1.26.0 |
| **用途** | Model Context Protocol |
| **功能** | AI 模型集成 |

```python
from mcp.server import Server
from mcp.types import Tool, TextContent
```

**子依赖**:
- anyio
- httpx
- httpx-sse
- jsonschema
- pydantic
- pydantic-settings
- pyjwt
- python-multipart
- pywin32 (Windows)
- sse-starlette
- starlette
- typing-extensions
- typing-inspection
- uvicorn

---

### starlette

| 属性 | 值 |
|------|-----|
| **版本** | 0.50.0 |
| **用途** | ASGI Web 框架 |
| **功能** | HTTP MCP 服务器 |

```python
from starlette.applications import Starlette
from starlette.routing import Route
```

---

### uvicorn

| 属性 | 值 |
|------|-----|
| **版本** | 0.40.0 |
| **用途** | ASGI 服务器 |
| **功能** | HTTP 服务运行 |

```bash
uvicorn scrcpy_py_ddlx.mcp_server:app --host 0.0.0.0 --port 8765
```

**子依赖**:
- click
- h11

**标准扩展**:
```bash
pip install uvicorn[standard]
# 包含: uvloop, httptools, watchfiles
```

---

## 开发依赖

### pytest

| 属性 | 值 |
|------|-----|
| **版本** | >=8.0.0 |
| **用途** | 测试框架 |

```bash
pytest tests/
```

---

### black

| 属性 | 值 |
|------|-----|
| **版本** | >=24.0.0 |
| **用途** | 代码格式化 |

```bash
black scrcpy_py_ddlx/
```

---

### mypy

| 属性 | 值 |
|------|-----|
| **版本** | >=1.8.0 |
| **用途** | 类型检查 |

```bash
mypy scrcpy_py_ddlx/
```

---

## requirements.txt 完整内容

```txt
# scrcpy-py-ddlx dependencies

# Core
av
numpy

# GUI
PySide6
PyOpenGL
PyOpenGL_accelerate

# Audio
sounddevice

# HTTP MCP server
starlette
uvicorn[standard]

# MCP
mcp
```

---

## 安装命令汇总

```bash
# 完整安装
pip install -r requirements.txt

# 仅核心 (无 GUI)
pip install av numpy

# 开发环境
pip install -r requirements.txt pytest black mypy

# 可选: PyAudio (音频录制)
pip install pyaudio>=0.2.14
```
