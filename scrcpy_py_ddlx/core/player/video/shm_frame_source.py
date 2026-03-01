"""
SHM-based frame source for OpenGL renderer.

This module provides a frame source that reads from shared memory
instead of DelayBuffer, enabling multi-process architecture where
the decoder runs in a separate process.
"""

import logging
import time
import numpy as np
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)


class SHMFrameSource:
    """
    Frame source that reads from shared memory.

    Drop-in replacement for DelayBuffer in the rendering pipeline.
    Reads frames written by the decoder process.
    """

    def __init__(self, shm_name: str, shm_size: int,
                 max_width: int = 4096, max_height: int = 4096):
        """
        Initialize SHM frame source.

        Args:
            shm_name: Name of shared memory
            shm_size: Size of shared memory
            max_width: Maximum frame width
            max_height: Maximum frame height
        """
        from scrcpy_py_ddlx.simple_shm import SimpleSHMReader

        self.reader = SimpleSHMReader(
            name=shm_name,
            size=shm_size,
            max_width=max_width,
            max_height=max_height
        )

        self._last_frame = None
        self._last_metadata = None
        self._frame_count = 0

        logger.info(f"SHMFrameSource created: {shm_name}")

    def consume(self) -> Optional[Tuple[Any, Dict[str, Any]]]:
        """
        Consume the latest frame from shared memory.

        Returns:
            Tuple of (frame_data, metadata) or None if no frame
            frame_data: dict with 'y', 'u', 'v' arrays (NV12 format)
            metadata: dict with width, height, pts, etc.
        """
        result = self.reader.read_frame_ex()
        if result is None:
            return None

        frame_bytes, pts, capture_time, udp_recv_time, fmt, width, height = result

        if fmt != 1:  # Not NV12
            logger.warning(f"Unexpected frame format: {fmt}")
            return None

        # Convert NV12 bytes to Y/U/V planes for OpenGL
        y_size = width * height
        y_plane = frame_bytes[:y_size].reshape((height, width))
        uv_plane = frame_bytes[y_size:y_size + y_size // 2].reshape((height // 2, width))

        # De-interleave U and V
        u_plane = uv_plane[:, 0::2].copy()
        v_plane = uv_plane[:, 1::2].copy()

        # Build frame dict (compatible with existing NV12 dict format)
        frame_data = {
            'y': y_plane,
            'u': u_plane,
            'v': v_plane,
            'width': width,
            'height': height,
        }

        metadata = {
            'pts': pts,
            'capture_time': capture_time,
            'udp_recv_time': udp_recv_time,
            'format': fmt,
        }

        self._last_frame = frame_data
        self._last_metadata = metadata
        self._frame_count += 1

        # Log periodically
        if self._frame_count % 100 == 0:
            delay_ms = (time.time() - udp_recv_time) * 1000 if udp_recv_time > 0 else 0
            logger.debug(f"[SHM_SOURCE] Frame #{self._frame_count}, delay={delay_ms:.0f}ms")

        return frame_data, metadata

    def has_new_frame(self) -> bool:
        """Check if there's a new frame available."""
        # Always return True since we poll SHM directly
        return True

    def get_latest_frame(self) -> Optional[Tuple[Any, Dict[str, Any]]]:
        """Get the last consumed frame without consuming a new one."""
        return self._last_frame, self._last_metadata

    def get_frame_count(self) -> int:
        """Get total frames consumed."""
        return self._frame_count

    def close(self):
        """Close the shared memory reader."""
        if self.reader:
            self.reader.close()
            self.reader = None


class DelayBufferAdapter:
    """
    Adapter that mimics DelayBuffer interface but reads from SHM.

    This allows using SHM with existing code that expects DelayBuffer.
    """

    def __init__(self, shm_source: SHMFrameSource):
        """
        Create adapter around SHM frame source.

        Args:
            shm_source: SHMFrameSource instance
        """
        self._source = shm_source
        self._consumed = False

    def consume(self):
        """Consume frame (mimics DelayBuffer.consume())."""
        result = self._source.consume()
        if result:
            self._consumed = True
            # Return in format expected by renderer
            frame_data, metadata = result
            # Wrap in a simple object with frame attribute
            class FrameWrapper:
                def __init__(self, frame):
                    self.frame = frame
            return FrameWrapper(frame_data)
        return None

    def has_new_frame(self) -> bool:
        """Check for new frame."""
        return self._source.has_new_frame()

    def push(self, *args, **kwargs):
        """No-op (decoder process handles pushing)."""
        pass

    def get_nowait(self):
        """Get current frame."""
        return self._source._last_frame


def create_shm_video_source(shm_info: Dict[str, Any]) -> SHMFrameSource:
    """
    Create SHM frame source from info dict.

    Args:
        shm_info: Dict with 'name', 'size', 'max_width', 'max_height'

    Returns:
        SHMFrameSource instance
    """
    return SHMFrameSource(
        shm_name=shm_info['name'],
        shm_size=shm_info['size'],
        max_width=shm_info.get('max_width', 4096),
        max_height=shm_info.get('max_height', 4096)
    )


__all__ = [
    'SHMFrameSource',
    'DelayBufferAdapter',
    'create_shm_video_source',
]
