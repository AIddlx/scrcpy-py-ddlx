"""
OpenGL video renderer using QOpenGLWindow for optimal performance.

This module provides a QOpenGLWindow-based renderer that has significantly
lower CPU usage than QOpenGLWidget on Windows.

Performance comparison (Windows, single-core):
- QOpenGLWidget: ~6.6% CPU (FBO offscreen rendering overhead)
- QOpenGLWindow: ~0.5% CPU (direct rendering)

Based on CPU_OPTIMIZATION_RESEARCH.md findings.
"""

import logging
import os
import time
from typing import Optional, Tuple, TYPE_CHECKING
from ctypes import c_void_p
from collections import defaultdict
import numpy as np

# 性能监控开关（设置环境变量 PROFILE_OPENGL=1 启用）
PROFILE_OPENGL = os.environ.get('PROFILE_OPENGL', '0') == '1'
_profile_timings = defaultdict(list) if PROFILE_OPENGL else None

def _profile_time(name):
    """性能计时的上下文管理器"""
    class Timer:
        def __enter__(self):
            self.start = time.perf_counter()
            return self
        def __exit__(self, *args):
            if _profile_timings is not None:
                elapsed = (time.perf_counter() - self.start) * 1000
                _profile_timings[name].append(elapsed)
    return Timer()

def _profile_report():
    """输出性能报告"""
    if _profile_timings is None:
        return
    logger.info("=" * 60)
    logger.info("OpenGL Performance Report")
    logger.info("=" * 60)
    for name, times in sorted(_profile_timings.items()):
        if times:
            avg = sum(times) / len(times)
            max_t = max(times)
            logger.info(f"{name}: avg={avg:.3f}ms, max={max_t:.3f}ms, calls={len(times)}")

try:
    from PySide6.QtOpenGL import QOpenGLWindow
    from PySide6.QtCore import Qt, QTimer, Signal
    from PySide6.QtGui import QSurfaceFormat, QKeyEvent, QMouseEvent, QWheelEvent
except ImportError:
    QOpenGLWindow = object
    Qt = None
    QTimer = None
    Signal = None
    QSurfaceFormat = None
    QKeyEvent = None
    QMouseEvent = None
    QWheelEvent = None

try:
    from OpenGL.GL import (
        glGenTextures, glBindTexture, glTexParameteri, glDeleteTextures,
        glTexImage2D, glTexSubImage2D, glClearColor, glClear,
        glViewport, glMatrixMode, glLoadIdentity,
        glOrtho, glEnable, glDisable,
        glColor3f, glBegin, glEnd,
        glTexCoord2f, glMultiTexCoord2f, glVertex2f,
        glActiveTexture, glPixelStorei,
        GL_UNSIGNED_BYTE, GL_RGB, GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
        GL_TEXTURE_MAG_FILTER, GL_LINEAR, GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T,
        GL_CLAMP_TO_EDGE, GL_COLOR_BUFFER_BIT, GL_QUADS,
        GL_PROJECTION, GL_MODELVIEW, GL_TEXTURE0, GL_TEXTURE1, GL_TEXTURE2,
        GL_UNPACK_ALIGNMENT, GL_LUMINANCE
    )
    try:
        from PySide6.QtOpenGL import QOpenGLShader, QOpenGLShaderProgram
        SHADER_AVAILABLE = True
    except ImportError:
        QOpenGLShader = None
        QOpenGLShaderProgram = None
        SHADER_AVAILABLE = False
    OPENGL_AVAILABLE = True
except ImportError:
    OPENGL_AVAILABLE = False
    SHADER_AVAILABLE = False

from scrcpy_py_ddlx.core.protocol import (
    POINTER_ID_MOUSE,
    AndroidMotionEventAction,
    AndroidKeyEventAction,
)
from scrcpy_py_ddlx.core.player.video.input_handler import InputHandler, CoordinateMapper
from scrcpy_py_ddlx.core.player.video.keycode_mapping import qt_key_to_android_keycode

if TYPE_CHECKING:
    from scrcpy_py_ddlx.core.control import ControlMessageQueue
    from scrcpy_py_ddlx.core.decoder import DelayBuffer

logger = logging.getLogger(__name__)

# NV12 YUV Shader sources
NV12_VERTEX_SHADER = """
varying highp vec2 v_texCoord;
void main() {
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    v_texCoord = gl_MultiTexCoord0.xy;
}
"""

NV12_FRAGMENT_SHADER = """
varying highp vec2 v_texCoord;
uniform sampler2D y_texture;
uniform sampler2D u_texture;
uniform sampler2D v_texture;
void main() {
    mediump float y = texture2D(y_texture, v_texCoord).r;
    mediump float u = texture2D(u_texture, v_texCoord).r - 0.5;
    mediump float v = texture2D(v_texture, v_texCoord).r - 0.5;
    highp float r = y + 1.402 * v;
    highp float g = y - 0.344136 * u - 0.714136 * v;
    highp float b = y + 1.772 * u;
    gl_FragColor = vec4(r, g, b, 1.0);
}
"""


def create_opengl_video_renderer_class():
    """
    Create the OpenGLVideoRenderer class based on QOpenGLWindow.

    Returns:
        OpenGLVideoRenderer class or None if OpenGL is not available
    """
    if not OPENGL_AVAILABLE or QOpenGLWindow is None:
        return None

    class OpenGLVideoRenderer(QOpenGLWindow, InputHandler, CoordinateMapper):
        """
        OpenGL-based video renderer using QOpenGLWindow for optimal performance.

        This class provides the same interface as OpenGLVideoWidget but uses
        QOpenGLWindow instead of QOpenGLWidget, resulting in significantly
        lower CPU usage on Windows.

        Note: QOpenGLWindow is a QWindow, not a QWidget. Use
        QWidget.createWindowContainer() to embed it in a widget hierarchy.

        Event-driven rendering: Uses a Signal to receive frame-ready notifications
        from the decoder thread, eliminating the need for 16ms polling.
        """

        # Signal for event-driven rendering (thread-safe)
        _frame_ready_signal = Signal()

        def __init__(self, parent=None):
            """Initialize OpenGL video renderer."""
            super().__init__(parent)

            # Initialize base classes
            InputHandler.__init__(self)
            CoordinateMapper.__init__(self)

            # Configure surface format
            fmt = QSurfaceFormat()
            fmt.setSwapInterval(0)  # Disable V-Sync for lower CPU usage (~1.5%)
            fmt.setSwapBehavior(QSurfaceFormat.DoubleBuffer)
            fmt.setDepthBufferSize(24)
            fmt.setStencilBufferSize(8)
            # No MSAA for video - saves GPU/CPU
            self.setFormat(fmt)

            # Direct access to DelayBuffer (set by client)
            self._delay_buffer: Optional['DelayBuffer'] = None

            # Frame data
            self._frame_array: Optional[np.ndarray] = None
            self._frame_width: int = 0
            self._frame_height: int = 0

            # OpenGL texture IDs
            self._texture_id: Optional[int] = None
            self._texture_width: int = 0
            self._texture_height: int = 0

            # NV12 GPU rendering support
            self._y_texture_id: Optional[int] = None
            self._u_texture_id: Optional[int] = None
            self._v_texture_id: Optional[int] = None
            self._nv12_shader: Optional['QOpenGLShaderProgram'] = None
            self._nv12_initialized: bool = False
            self._frame_format: int = 0  # 0=RGB, 1=NV12

            # NV12 texture size tracking
            self._nv12_y_tex_width: int = 0
            self._nv12_y_tex_height: int = 0
            self._nv12_uv_tex_width: int = 0
            self._nv12_uv_tex_height: int = 0

            # Control queue (set by client)
            self._control_queue: Optional["ControlMessageQueue"] = None

            # Consume callback
            self._consume_callback: Optional[callable] = None

            # Frame size change callback
            self._frame_size_changed_callback: Optional[callable] = None

            # Mouse state
            self._mouse_buttons_state: int = 0
            self._last_position: Tuple[int, int] = (0, 0)
            self._mouse_hover: bool = False

            # Update timer (~60fps)
            if QTimer is not None:
                self._update_timer = QTimer()
                self._update_timer.timeout.connect(self._on_update_timer)
                self._update_timer.start(16)
                logger.info("[OPENGL_WINDOW] Timer started (16ms interval)")
            else:
                self._update_timer = None

        def initialize(self) -> None:
            """Initialize OpenGL resources. Called automatically by Qt."""
            logger.info("Initializing OpenGL (QOpenGLWindow)...")

            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

            # RGB texture
            self._texture_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self._texture_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

            # NV12 textures (Y, U, V)
            for tex_id_attr in ['_y_texture_id', '_u_texture_id', '_v_texture_id']:
                tex_id = glGenTextures(1)
                setattr(self, tex_id_attr, tex_id)
                glBindTexture(GL_TEXTURE_2D, tex_id)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

            # NV12 shader
            if SHADER_AVAILABLE and QOpenGLShader is not None:
                self._nv12_shader = QOpenGLShaderProgram(self)
                if self._nv12_shader.addShaderFromSourceCode(QOpenGLShader.Vertex, NV12_VERTEX_SHADER):
                    if self._nv12_shader.addShaderFromSourceCode(QOpenGLShader.Fragment, NV12_FRAGMENT_SHADER):
                        if self._nv12_shader.link():
                            self._nv12_initialized = True
                            logger.info("NV12 GPU shader initialized successfully")

            logger.info("OpenGL (QOpenGLWindow) initialized successfully")

        def resize(self, w: int, h: int) -> None:
            """Handle window resize."""
            glViewport(0, 0, w, h)

        def event(self, event):
            """Handle QEvent, particularly expose events to trigger rendering."""
            from PySide6.QtCore import QEvent
            if event.type() == QEvent.Type.UpdateRequest:
                # Trigger a render on update request
                pass
            return super().event(event)

        def exposeEvent(self, event):
            """Handle window expose event - triggered when window becomes visible."""
            super().exposeEvent(event)
            if self.isExposed():
                # Window is exposed, request an update to trigger render
                self.requestUpdate()
                logger.debug("[OPENGL_WINDOW] Window exposed, requesting update")

        def render(self) -> None:
            """Render the video frame using OpenGL."""
            render_start = time.time()  # Track total render time
            self._paint_count = getattr(self, '_paint_count', 0) + 1
            if self._paint_count <= 5:
                logger.info(f"[OPENGL_WINDOW] render() called #{self._paint_count}")

            # Ensure OpenGL is initialized (may not be called automatically with createWindowContainer)
            if self._texture_id is None:
                logger.info("[OPENGL_WINDOW] Texture not initialized, calling initialize()")
                self.initialize()

            with _profile_time('glClear'):
                glClearColor(0.0, 0.0, 0.0, 1.0)
                glClear(GL_COLOR_BUFFER_BIT)

            # Check if we have a frame source (DelayBuffer or SHM)
            if self._texture_id is None:
                return
            if self._delay_buffer is None and getattr(self, '_shm_reader', None) is None:
                return

            with _profile_time('consume'):
                try:
                    new_frame = None
                    frame_udp_time = 0  # Track UDP time for E2E latency

                    # Try SHM reader first (multi-process mode)
                    if hasattr(self, '_shm_reader') and self._shm_reader is not None:
                        shm_read_start = time.time()
                        result = self._shm_reader.read_frame_ex()
                        shm_read_end = time.time()
                        if result is not None:
                            frame_bytes, pts, capture_time, udp_recv_time, fmt, w, h = result
                            frame_udp_time = udp_recv_time
                            self._frame_consume_count = getattr(self, '_frame_consume_count', 0) + 1

                            # Calculate SHM read latency
                            shm_read_ms = (shm_read_end - shm_read_start) * 1000

                            # Debug first few frames
                            if self._frame_consume_count <= 3:
                                logger.info(f"[RENDER] SHM frame #{self._frame_consume_count}: len={len(frame_bytes)}, fmt={fmt}, w={w}, h={h}")

                            # Convert NV12 bytes to Y/U/V dict format
                            # NV12 layout: [Y plane (w*h)] [UV plane interleaved (w*h/2)]
                            # frame_bytes is a 1D numpy array from read_frame_ex()
                            if fmt == 1:  # NV12
                                y_size = w * h
                                # First convert to 2D array for easier slicing
                                nv12_2d = frame_bytes.reshape((int(h * 1.5), w))
                                y_plane = nv12_2d[:h, :].copy()
                                uv_plane = nv12_2d[h:, :]
                                u_plane = uv_plane[:, 0::2].copy()
                                v_plane = uv_plane[:, 1::2].copy()

                                # Debug: log data details
                                if self._frame_consume_count <= 3:
                                    # Check UV data distribution
                                    u_left = u_plane[:, :u_plane.shape[1]//3]
                                    u_right = u_plane[:, 2*u_plane.shape[1]//3:]
                                    v_left = v_plane[:, :v_plane.shape[1]//3]
                                    v_right = v_plane[:, 2*v_plane.shape[1]//3:]

                                    # Check how many pixels are 0 in right region
                                    u_right_zeros = np.sum(u_right == 0)
                                    v_right_zeros = np.sum(v_right == 0)
                                    u_right_total = u_right.size

                                    logger.info(f"[SHM_DATA] frame#{self._frame_consume_count}: "
                                               f"frame_bytes_len={len(frame_bytes)}, expected={int(w*h*1.5)}, "
                                               f"nv12_2d_shape={nv12_2d.shape}, y_shape={y_plane.shape}, "
                                               f"uv_shape={uv_plane.shape}, u_shape={u_plane.shape}, "
                                               f"y_range=[{y_plane.min()},{y_plane.max()}], "
                                               f"u_left_range=[{u_left.min()},{u_left.max()}], "
                                               f"u_right_range=[{u_right.min()},{u_right.max()}], "
                                               f"v_left_range=[{v_left.min()},{v_left.max()}], "
                                               f"v_right_range=[{v_right.min()},{v_right.max()}], "
                                               f"u_right_zeros={u_right_zeros}/{u_right_total} ({100*u_right_zeros/u_right_total:.1f}%), "
                                               f"v_right_zeros={v_right_zeros}/{u_right_total} ({100*v_right_zeros/u_right_total:.1f}%)")

                                new_frame = {
                                    'y': y_plane,
                                    'u': u_plane,
                                    'v': v_plane,
                                    'width': w,
                                    'height': h,
                                }
                            else:  # RGB
                                new_frame = frame_bytes.reshape((h, w, 3)).copy()

                            # Log latency for multi-process mode
                            e2e_ms = (time.time() - frame_udp_time) * 1000 if frame_udp_time > 0 else 0
                            if self._frame_consume_count <= 5 or self._frame_consume_count % 30 == 0:  # Log first 5 and every 30 frames
                                logger.info(f"[RENDER_LAG] frame#{self._frame_consume_count}: "
                                           f"e2e={e2e_ms:.0f}ms, shm_read={shm_read_ms:.1f}ms")

                    # Fallback to DelayBuffer (single-process mode)
                    elif self._delay_buffer is not None:
                        result = self._delay_buffer.consume()
                        if result is not None:
                            self._frame_consume_count = getattr(self, '_frame_consume_count', 0) + 1
                            new_frame = result.frame if hasattr(result, 'frame') else result

                    # Process the frame if we got one (COMMON CODE FOR BOTH SHM AND DelayBuffer)
                    if new_frame is not None:
                        old_width, old_height = self._frame_width, self._frame_height
                        self._frame_array = new_frame

                        # Detect frame format
                        if isinstance(new_frame, dict) and ('y' in new_frame or 'y_gpu' in new_frame):
                            self._frame_format = 1  # NV12
                            if 'y_gpu' in new_frame:
                                self._frame_width = new_frame['width']
                                self._frame_height = new_frame['height']
                            else:
                                self._frame_width = new_frame['y'].shape[1]
                                self._frame_height = new_frame['y'].shape[0]
                            CoordinateMapper.set_frame_size(self, self._frame_width, self._frame_height)
                        elif hasattr(new_frame, 'shape') and len(new_frame.shape) >= 2:
                            if len(new_frame.shape) == 3 and new_frame.shape[2] == 3:
                                self._frame_format = 0  # RGB
                                self._frame_width = new_frame.shape[1]
                                self._frame_height = new_frame.shape[0]
                            elif len(new_frame.shape) == 2:
                                self._frame_format = 1  # NV12
                                self._frame_width = new_frame.shape[1]
                                self._frame_height = int(new_frame.shape[0] * 2 / 3)
                            else:
                                self._frame_format = 0
                                self._frame_width = new_frame.shape[1] if len(new_frame.shape) > 1 else 0
                                self._frame_height = new_frame.shape[0] if len(new_frame.shape) > 0 else 0
                            CoordinateMapper.set_frame_size(self, self._frame_width, self._frame_height)

                        # Check frame size change
                        if (old_width, old_height) != (self._frame_width, self._frame_height):
                            if old_width > 0 and old_height > 0:
                                logger.info(f"[OPENGL_WINDOW] Frame size changed: {old_width}x{old_height} -> {self._frame_width}x{self._frame_height}")
                                if self._frame_size_changed_callback:
                                    self._frame_size_changed_callback(self._frame_width, self._frame_height)
                except Exception as e:
                    logger.error(f"[OPENGL_WINDOW] Error consuming frame: {e}")

            frame_array = self._frame_array
            width = self._frame_width
            height = self._frame_height
            frame_format = self._frame_format

            if frame_array is None or width == 0 or height == 0:
                return

            with _profile_time('projection'):
                size = self.size()
                glMatrixMode(GL_PROJECTION)
                glLoadIdentity()
                glOrtho(0, size.width(), size.height(), 0, -1, 1)
                glMatrixMode(GL_MODELVIEW)
                glLoadIdentity()

            # Calculate render rectangle (aspect ratio)
            if width > 0 and height > 0:
                scale_x = size.width() / width
                scale_y = size.height() / height
                scale = min(scale_x, scale_y)
                render_w = int(width * scale)
                render_h = int(height * scale)
                x = (size.width() - render_w) // 2
                y = (size.height() - render_h) // 2
            else:
                x = y = render_w = render_h = 0

            if frame_format == 1:
                if not self._nv12_initialized:
                    return
                with _profile_time('paint_nv12'):
                    self._paint_nv12(frame_array, width, height, x, y, render_w, render_h)
            else:
                with _profile_time('paint_rgb'):
                    self._paint_rgb(frame_array, width, height, x, y, render_w, render_h)

            if PROFILE_OPENGL and self._paint_count % 300 == 0:
                _profile_report()

        def _paint_rgb(self, frame_array: np.ndarray, width: int, height: int,
                       x: int, y: int, render_w: int, render_h: int) -> None:
            """Render RGB frame using single texture."""
            if not frame_array.flags['C_CONTIGUOUS']:
                frame_array = np.ascontiguousarray(frame_array)

            data_ptr = frame_array.ctypes.data_as(c_void_p)

            if self._texture_width != width or self._texture_height != height:
                glBindTexture(GL_TEXTURE_2D, self._texture_id)
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0,
                             GL_RGB, GL_UNSIGNED_BYTE, data_ptr)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                self._texture_width = width
                self._texture_height = height
            else:
                glBindTexture(GL_TEXTURE_2D, self._texture_id)
                glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height,
                              GL_RGB, GL_UNSIGNED_BYTE, data_ptr)

            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self._texture_id)
            glColor3f(1.0, 1.0, 1.0)

            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 0.0); glVertex2f(x, y)
            glTexCoord2f(1.0, 0.0); glVertex2f(x + render_w, y)
            glTexCoord2f(1.0, 1.0); glVertex2f(x + render_w, y + render_h)
            glTexCoord2f(0.0, 1.0); glVertex2f(x, y + render_h)
            glEnd()

            glDisable(GL_TEXTURE_2D)

        def _paint_nv12(self, frame_array, width: int, height: int,
                        x: int, y: int, render_w: int, render_h: int) -> None:
            """Render NV12 frame using Y/U/V textures and GPU shader."""
            if not self._nv12_initialized or self._nv12_shader is None:
                logger.warning(f"[PAINT_NV12] Not initialized: nv12_init={self._nv12_initialized}, shader={self._nv12_shader is not None}")
                return

            # Handle NV12 data format
            if isinstance(frame_array, dict):
                if frame_array.get('is_gpu', False):
                    logger.warning("[OPENGL_WINDOW] GPU zero-copy not yet supported in QOpenGLWindow")
                    return
                else:
                    y_plane = frame_array['y']
                    u_plane = frame_array['u']
                    v_plane = frame_array['v']
                    y_tex_width = y_plane.shape[1] if len(y_plane.shape) > 1 else width
                    y_tex_height = y_plane.shape[0] if len(y_plane.shape) > 1 else height
                    uv_tex_width = u_plane.shape[1] if len(u_plane.shape) > 1 else width // 2
                    uv_tex_height = u_plane.shape[0] if len(u_plane.shape) > 1 else height // 2

                    # Debug first frame - detailed logging
                    if not hasattr(self, '_nv12_first_frame_logged'):
                        self._nv12_first_frame_logged = True
                        logger.info(f"[PAINT_NV12] Dict format: y_shape={y_plane.shape}, u_shape={u_plane.shape}, v_shape={v_plane.shape}")
                        logger.info(f"[PAINT_NV12] y_contiguous={y_plane.flags['C_CONTIGUOUS']}, u_contiguous={u_plane.flags['C_CONTIGUOUS']}")
                        logger.info(f"[PAINT_NV12] y_tex={y_tex_width}x{y_tex_height}, uv_tex={uv_tex_width}x{uv_tex_height}")
                        logger.info(f"[PAINT_NV12] Y range: [{y_plane.min()}, {y_plane.max()}], U range: [{u_plane.min()}, {u_plane.max()}]")
            else:
                # Semi-planar NV12 (2D array format: [Y plane; UV plane interleaved])
                y_plane = frame_array[:height, :].copy()
                uv_plane = frame_array[height:, :]
                # UV plane is interleaved: U0 V0 U1 V1 ... per row
                u_plane = uv_plane[:, 0::2].copy()  # Even columns = U
                v_plane = uv_plane[:, 1::2].copy()  # Odd columns = V
                y_tex_width = frame_array.shape[1]
                uv_tex_width = y_tex_width // 2

            # Ensure contiguous
            with _profile_time('array_contiguous'):
                if not y_plane.flags['C_CONTIGUOUS']:
                    y_plane = np.ascontiguousarray(y_plane)
                if not u_plane.flags['C_CONTIGUOUS']:
                    u_plane = np.ascontiguousarray(u_plane)
                if not v_plane.flags['C_CONTIGUOUS']:
                    v_plane = np.ascontiguousarray(v_plane)

            uv_width = width // 2
            uv_height = height // 2

            y_size_changed = (self._nv12_y_tex_width != y_tex_width or
                              self._nv12_y_tex_height != height)
            uv_size_changed = (self._nv12_uv_tex_width != uv_width or
                               self._nv12_uv_tex_height != uv_height)

            # Debug: log texture dimensions on first frame or size change
            if not hasattr(self, '_tex_debug_logged') or uv_size_changed:
                self._tex_debug_logged = True
                logger.info(f"[TEX_DEBUG] y_tex: {y_tex_width}x{height}, uv_tex: {uv_tex_width}x{uv_tex_height}, "
                           f"uv_check: {uv_width}x{uv_height}, uv_changed={uv_size_changed}, "
                           f"u_plane: {u_plane.shape}, v_plane: {v_plane.shape}")

            with _profile_time('tex_upload'):
                # Y texture
                glActiveTexture(GL_TEXTURE0)
                glBindTexture(GL_TEXTURE_2D, self._y_texture_id)
                if y_size_changed:
                    glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, y_tex_width, height, 0,
                                GL_LUMINANCE, GL_UNSIGNED_BYTE,
                                y_plane.ctypes.data_as(c_void_p))
                    # Set texture parameters (CRITICAL - must be set after glTexImage2D)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
                    self._nv12_y_tex_width = y_tex_width
                    self._nv12_y_tex_height = height
                else:
                    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, y_tex_width, height,
                                   GL_LUMINANCE, GL_UNSIGNED_BYTE,
                                   y_plane.ctypes.data_as(c_void_p))

                # U texture
                glActiveTexture(GL_TEXTURE1)
                glBindTexture(GL_TEXTURE_2D, self._u_texture_id)
                if uv_size_changed:
                    glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, uv_tex_width, uv_height, 0,
                                GL_LUMINANCE, GL_UNSIGNED_BYTE,
                                u_plane.ctypes.data_as(c_void_p))
                    # Set texture parameters
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
                else:
                    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, uv_tex_width, uv_height,
                                   GL_LUMINANCE, GL_UNSIGNED_BYTE,
                                   u_plane.ctypes.data_as(c_void_p))

                # V texture
                glActiveTexture(GL_TEXTURE2)
                glBindTexture(GL_TEXTURE_2D, self._v_texture_id)
                if uv_size_changed:
                    glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, uv_tex_width, uv_height, 0,
                                GL_LUMINANCE, GL_UNSIGNED_BYTE,
                                v_plane.ctypes.data_as(c_void_p))
                    # Set texture parameters
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
                    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
                    self._nv12_uv_tex_width = uv_tex_width
                    self._nv12_uv_tex_height = uv_height
                else:
                    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, uv_tex_width, uv_height,
                                   GL_LUMINANCE, GL_UNSIGNED_BYTE,
                                   v_plane.ctypes.data_as(c_void_p))

            # Bind shader
            self._nv12_shader.bind()

            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self._y_texture_id)
            self._nv12_shader.setUniformValue1i("y_texture", 0)

            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_2D, self._u_texture_id)
            self._nv12_shader.setUniformValue1i("u_texture", 1)

            glActiveTexture(GL_TEXTURE2)
            glBindTexture(GL_TEXTURE_2D, self._v_texture_id)
            self._nv12_shader.setUniformValue1i("v_texture", 2)

            glActiveTexture(GL_TEXTURE0)

            # Draw quad
            glEnable(GL_TEXTURE_2D)
            glColor3f(1.0, 1.0, 1.0)

            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 0.0); glVertex2f(x, y)
            glTexCoord2f(1.0, 0.0); glVertex2f(x + render_w, y)
            glTexCoord2f(1.0, 1.0); glVertex2f(x + render_w, y + render_h)
            glTexCoord2f(0.0, 1.0); glVertex2f(x, y + render_h)
            glEnd()

            glDisable(GL_TEXTURE_2D)
            self._nv12_shader.release()
            glActiveTexture(GL_TEXTURE0)

        def _on_update_timer(self) -> None:
            """Called by QTimer to trigger repaint."""
            self._timer_count = getattr(self, '_timer_count', 0) + 1

            # Check if window is exposed before rendering
            if not self.isExposed():
                if self._timer_count <= 5:
                    logger.debug(f"[OPENGL_WINDOW] Timer tick #{self._timer_count}, exposed=False, skipping")
                return

            if self._timer_count <= 5:
                logger.debug(f"[OPENGL_WINDOW] Timer tick #{self._timer_count}, exposed=True, calling render()")

            # For QOpenGLWindow embedded in createWindowContainer, we need to:
            # 1. Make the OpenGL context current
            # 2. Call render()
            # 3. Swap buffers (if not automatic)
            try:
                # Make context current - CRITICAL for OpenGL operations
                self.makeCurrent()
                self.render()
                # For QOpenGLWindow, we may need to swap buffers manually
                self.context().swapBuffers(self.context().surface()) if self.context() else None
            except Exception as e:
                if self._timer_count <= 10:
                    logger.error(f"[OPENGL_WINDOW] render() error: {e}")
            finally:
                # Release context
                self.doneCurrent()

        # ========================================================================
        # Public Interface (must match OpenGLVideoWidget interface)
        # ========================================================================

        def set_delay_buffer(self, delay_buffer: 'DelayBuffer') -> None:
            """
            Set the DelayBuffer reference for direct frame consumption.

            Also sets up event-driven rendering: when a new frame is pushed to
            DelayBuffer, this renderer will be notified immediately via Signal,
            eliminating the need for 16ms polling.
            """
            self._delay_buffer = delay_buffer
            self._shm_reader = None  # Disable SHM mode
            logger.debug("OpenGLVideoRenderer DelayBuffer reference set")

            # EVENT-DRIVEN RENDERING: Connect signal to render slot
            if delay_buffer is not None:
                # Connect our signal to the render method
                self._frame_ready_signal.connect(self._on_frame_ready)
                # Give the signal to DelayBuffer so it can emit from decoder thread
                delay_buffer.set_frame_ready_signal(self._frame_ready_signal)
                logger.info("[OPENGL_WINDOW] Event-driven rendering enabled (Signal connected)")
                # Stop the polling timer - no longer needed
                if self._update_timer is not None:
                    self._update_timer.stop()
                    logger.info("[OPENGL_WINDOW] Polling timer stopped (using event-driven mode)")

        def _on_frame_ready(self) -> None:
            """
            Event-driven frame ready callback.

            Called by DelayBuffer (via Qt's thread-safe mechanism) when a new
            frame is available. This eliminates polling latency.

            This method is called from the GUI thread via QTimer.singleShot.
            """
            self._frame_ready_count = getattr(self, '_frame_ready_count', 0) + 1
            if self._frame_ready_count <= 5:
                logger.info(f"[OPENGL_WINDOW] _on_frame_ready() called #{self._frame_ready_count}")

            # Check if window is exposed before rendering
            if not self.isExposed():
                if self._frame_ready_count <= 5:
                    logger.debug(f"[OPENGL_WINDOW] Window not exposed, skipping render")
                return

            # Trigger immediate render
            try:
                self.makeCurrent()
                self.render()
                if self.context():
                    self.context().swapBuffers(self.context().surface())
            except Exception as e:
                logger.error(f"[OPENGL_WINDOW] Event-driven render error: {e}")
            finally:
                self.doneCurrent()

        def set_shm_source(self, shm_name: str, shm_size: int,
                          max_width: int = 4096, max_height: int = 4096) -> None:
            """
            Set shared memory source for multi-process frame reading.

            When set, the renderer will read frames from SHM instead of DelayBuffer.
            This enables multi-process architecture where the decoder runs in a
            separate process.

            Args:
                shm_name: Name of shared memory
                shm_size: Size of shared memory
                max_width: Maximum frame width
                max_height: Maximum frame height
            """
            from scrcpy_py_ddlx.simple_shm import SimpleSHMReader

            self._shm_reader = SimpleSHMReader(
                name=shm_name,
                size=shm_size,
                max_width=max_width,
                max_height=max_height
            )
            self._delay_buffer = None  # Disable DelayBuffer mode
            logger.info(f"[OPENGL_WINDOW] SHM source set: {shm_name}")

        def set_control_queue(self, queue: 'ControlMessageQueue') -> None:
            """Set the control message queue."""
            self._control_queue = queue

        def set_consume_callback(self, callback: Optional[callable]) -> None:
            """Set the consume callback."""
            self._consume_callback = callback

        def set_frame_size_changed_callback(self, callback: Optional[callable]) -> None:
            """Set the callback for frame size changes."""
            self._frame_size_changed_callback = callback

        def set_nv12_mode(self, enabled: bool) -> bool:
            """Enable or disable NV12 GPU rendering mode."""
            if enabled and not self._nv12_initialized:
                logger.error("[OPENGL_WINDOW] NV12 mode requested but shader not initialized!")
            self._frame_format = 1 if enabled else 0
            logger.info(f"[OPENGL_WINDOW] NV12 mode {'enabled' if enabled else 'disabled'}")
            return enabled and self._nv12_initialized

        def is_nv12_supported(self) -> bool:
            """Check if NV12 GPU rendering is supported."""
            return self._nv12_initialized and SHADER_AVAILABLE

        def update_frame(self, frame: np.ndarray) -> None:
            """Update the displayed frame. DEPRECATED - frames come from DelayBuffer."""
            pass

        # ========================================================================
        # Mouse Event Handlers (delegated to InputHandler)
        # ========================================================================

        def mousePressEvent(self, event: QMouseEvent) -> None:
            if event is None:
                return
            device_x, device_y = self.map_to_device_coords(
                int(event.position().x()),
                int(event.position().y()),
                self.width(),
                self.height()
            )
            if device_x < 0 or device_y < 0:
                return
            button = event.button()
            self._update_mouse_button_state(button, True)
            action_button = self._qt_button_to_android(button)
            self._send_touch_event(
                action=AndroidMotionEventAction.DOWN,
                pointer_id=POINTER_ID_MOUSE,
                position_x=device_x,
                position_y=device_y,
                pressure=1.0,
                action_button=action_button,
            )

        def mouseReleaseEvent(self, event: QMouseEvent) -> None:
            if event is None:
                return
            device_x, device_y = self.map_to_device_coords(
                int(event.position().x()),
                int(event.position().y()),
                self.width(),
                self.height()
            )
            if device_x < 0 or device_y < 0:
                return
            button = event.button()
            self._update_mouse_button_state(button, False)
            action_button = self._qt_button_to_android(button)
            self._send_touch_event(
                action=AndroidMotionEventAction.UP,
                pointer_id=POINTER_ID_MOUSE,
                position_x=device_x,
                position_y=device_y,
                pressure=0.0,
                action_button=action_button,
            )

        def mouseMoveEvent(self, event: QMouseEvent) -> None:
            if event is None:
                return
            device_x, device_y = self.map_to_device_coords(
                int(event.position().x()),
                int(event.position().y()),
                self.width(),
                self.height()
            )
            if device_x < 0 or device_y < 0:
                return
            self._last_position = (device_x, device_y)
            if self._mouse_buttons_state == 0 and not self._mouse_hover:
                return
            action = AndroidMotionEventAction.MOVE if self._mouse_buttons_state else AndroidMotionEventAction.HOVER_MOVE
            pressure = 1.0 if self._mouse_buttons_state else 0.0
            from scrcpy_py_ddlx.core.control import ControlMessage, ControlMessageType
            msg = ControlMessage(ControlMessageType.INJECT_TOUCH_EVENT)
            msg.set_touch_event(
                action=action,
                pointer_id=POINTER_ID_MOUSE,
                position_x=device_x,
                position_y=device_y,
                screen_width=self._device_size[0],
                screen_height=self._device_size[1],
                pressure=pressure,
                action_button=0,
                buttons=self._mouse_buttons_state,
            )
            if self._control_queue:
                self._control_queue.put(msg)

        def wheelEvent(self, event: QWheelEvent) -> None:
            if event is None:
                return
            device_x, device_y = self.map_to_device_coords(
                int(event.position().x()),
                int(event.position().y()),
                self.width(),
                self.height()
            )
            if device_x < 0 or device_y < 0:
                return
            delta = event.angleDelta()
            hscroll = max(-1.0, min(1.0, delta.x() / 120.0))
            vscroll = max(-1.0, min(1.0, delta.y() / 120.0))
            self._send_scroll_event(device_x, device_y, hscroll, vscroll)

        # ========================================================================
        # Keyboard Event Handlers
        # ========================================================================

        def keyPressEvent(self, event: QKeyEvent) -> None:
            if event is None:
                return
            android_keycode = qt_key_to_android_keycode(event.key())
            if android_keycode == 0:
                text = event.text()
                if text and self._control_queue:
                    from scrcpy_py_ddlx.core.control import ControlMessage, ControlMessageType
                    msg = ControlMessage(ControlMessageType.INJECT_TEXT)
                    msg.set_text(text)
                    self._control_queue.put(msg)
                return
            self._send_keycode_event(
                keycode=android_keycode,
                action=AndroidKeyEventAction.DOWN,
                repeat=0,
            )

        def keyReleaseEvent(self, event: QKeyEvent) -> None:
            if event is None:
                return
            android_keycode = qt_key_to_android_keycode(event.key())
            if android_keycode == 0:
                return
            self._send_keycode_event(
                keycode=android_keycode,
                action=AndroidKeyEventAction.UP,
                repeat=0,
            )

    return OpenGLVideoRenderer


# Create the class at import time
_OpenGLVideoRendererClass = create_opengl_video_renderer_class()

# Export
if _OpenGLVideoRendererClass is not None:
    OpenGLVideoRenderer = _OpenGLVideoRendererClass
else:
    class OpenGLVideoRenderer:
        """Stub class when OpenGL is not available."""
        def __init__(self, *args, **kwargs):
            raise RuntimeError("OpenGL is not available.")

__all__ = ["OpenGLVideoRenderer", "create_opengl_video_renderer_class"]
