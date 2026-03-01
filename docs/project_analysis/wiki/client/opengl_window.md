# OpenGLWindow - 视频渲染器

> **路径**: `scrcpy_py_ddlx/core/player/video/opengl_window.py`
> **职责**: 基于 QOpenGLWindow 的高性能视频渲染器

---

## 类定义

### OpenGLVideoRenderer

**职责**: OpenGL视频渲染，支持NV12 GPU渲染

**继承**: QOpenGLWindow, InputHandler, CoordinateMapper

**线程**: GUI线程 (Qt主线程)

**依赖**: PySide6, PyOpenGL, numpy

---

## 主要属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `_delay_buffer` | DelayBuffer | 帧源 |
| `_y_texture_id` | int | Y平面纹理 |
| `_uv_texture_id` | int | UV平面纹理 |
| `_nv12_shader` | QOpenGLShaderProgram | NV12着色器 |
| `_control_queue` | ControlMessageQueue | 控制队列 |
| `_device_size` | tuple | 设备尺寸 |
| `_frame_size` | tuple | 帧尺寸 |

---

## 主要方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `initialize` | - | - | 初始化OpenGL资源 |
| `render` | - | - | 渲染帧 |
| `set_delay_buffer` | buffer | - | 设置帧源 |
| `set_shm_source` | ... | - | 设置共享内存源 |
| `set_control_queue` | queue | - | 设置控制队列 |
| `_on_frame_ready` | - | - | 事件驱动回调 |
| `_paint_rgb` | frame | - | RGB渲染 |
| `_paint_nv12` | frame | - | NV12 GPU渲染 |

---

## 着色器

### NV12 顶点着色器

```glsl
attribute vec4 vertex;
attribute vec2 texCoord;
varying vec2 v_texCoord;
void main() {
    gl_Position = vertex;
    v_texCoord = texCoord;
}
```

### NV12 片段着色器 (YUV→RGB)

```glsl
uniform sampler2D y_texture;
uniform sampler2D uv_texture;
varying vec2 v_texCoord;

void main() {
    float y = texture2D(y_texture, v_texCoord).r;
    float u = texture2D(uv_texture, v_texCoord).r - 0.5;
    float v = texture2D(uv_texture, v_texCoord).g - 0.5;

    float r = y + 1.402 * v;
    float g = y - 0.344 * u - 0.714 * v;
    float b = y + 1.772 * u;

    gl_FragColor = vec4(r, g, b, 1.0);
}
```

---

## 渲染流程

### NV12 GPU渲染

```
1. 从 DelayBuffer 获取帧
2. 上传 Y 平面到 y_texture
3. 上传 UV 平面到 uv_texture (GL_RG格式)
4. 绑定着色器
5. 绘制四边形
6. YUV→RGB 转换在 GPU 完成
```

### RGB CPU渲染

```
1. 从 DelayBuffer 获取帧
2. 上传到 GL_RGB 纹理
3. 绑定着色器
4. 绘制四边形
```

---

## 输入处理

继承 InputHandler 和 CoordinateMapper:

| 事件 | 处理 |
|------|------|
| `mousePressEvent` | 发送触摸DOWN |
| `mouseReleaseEvent` | 发送触摸UP |
| `mouseMoveEvent` | 发送触摸MOVE |
| `wheelEvent` | 发送滚动事件 |
| `keyPressEvent` | 发送按键DOWN |
| `keyReleaseEvent` | 发送按键UP |

---

## 事件驱动

```python
# 设置帧就绪信号
self._frame_ready_signal = Signal()
self._delay_buffer.set_frame_ready_signal(self._frame_ready_signal)

# 连接信号到更新
self._frame_ready_signal.connect(self._on_frame_ready)
```

帧到达时自动触发渲染，无需轮询。

---

## 坐标映射

```python
def map_to_device_coords(window_x, window_y):
    # 窗口坐标 → 设备坐标
    # 考虑黑边和缩放
    ...
```

---

## 依赖关系

```
OpenGLVideoRenderer
    │
    ├──→ PySide6.QtOpenGL
    │
    ├──→ OpenGL.GL
    │
    ├──→ numpy
    │
    ├──→ DelayBuffer (帧源)
    │
    └──→ InputHandler (输入处理)
```

---

*此文档基于客户端代码分析生成*
