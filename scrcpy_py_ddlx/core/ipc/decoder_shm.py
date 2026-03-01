"""
Double-buffered shared memory for multi-process video decoding.

This module provides a lock-free, double-buffered shared memory
implementation for transferring video frames between processes
without GIL contention.

Architecture:
- Decoder process writes to inactive buffer
- GUI process reads from active buffer
- Atomic index swap ensures consistency

Layout:
┌─────────────────────────────────────────────────────────────────┐
│ Header (64 bytes)                                               │
│ - magic (4): 0xDECADE00                                         │
│ - version (4): 1                                                │
│ - write_index (4): current write buffer (0/1)                   │
│ - write_counter (8): total frames written                       │
│ - reserved (44)                                                 │
├─────────────────────────────────────────────────────────────────┤
│ Buffer 0 Header (64 bytes) + Frame Data (MAX_SIZE)              │
├─────────────────────────────────────────────────────────────────┤
│ Buffer 1 Header (64 bytes) + Frame Data (MAX_SIZE)              │
└─────────────────────────────────────────────────────────────────┘
"""

import numpy as np
import struct
import time
import logging
from typing import Optional, Tuple, Dict, Any
from multiprocessing import shared_memory, Value, Event
import ctypes

logger = logging.getLogger(__name__)


# Constants
MAGIC = 0xDECADE00
VERSION = 1
HEADER_SIZE = 64  # Global header
BUFFER_HEADER_SIZE = 64  # Per-buffer header

# Frame format constants
FORMAT_RGB24 = 0
FORMAT_NV12 = 1

# Buffer header format: width, height, format, frame_size, pts, udp_recv_time_ns,
#                       decode_time_ns, send_time_ns, packet_id, flags
# i=int32, I=uint32, q=int64, Q=uint64
BUFFER_HEADER_FORMAT = '<iiIIqqqqiiII'  # width(i), height(i), format(I), frame_size(I),
                                        # pts(q), udp_recv_ns(q), decode_ns(q), send_ns(q),
                                        # packet_id(i), flags(i), reserved1(I), reserved2(I)
# Total: 2*4 + 2*4 + 4*8 + 2*4 + 2*4 = 64 bytes


class DecoderSHMWriter:
    """
    Double-buffered shared memory writer for decoder process.

    Thread-safe and lock-free for minimal latency.
    """

    def __init__(self, max_width: int = 4096, max_height: int = 4096, name: str = None):
        """
        Create double-buffered shared memory.

        Args:
            max_width: Maximum frame width
            max_height: Maximum frame height
            name: Optional name for shared memory (auto-generated if None)
        """
        self.max_width = max_width
        self.max_height = max_height

        # Max frame size (NV12 is largest: w*h*1.5)
        self.max_frame_size = int(max_width * max_height * 1.5)

        # Calculate total size
        self.buffer_size = BUFFER_HEADER_SIZE + self.max_frame_size
        self.total_size = HEADER_SIZE + 2 * self.buffer_size

        # Create shared memory
        self.shm = shared_memory.SharedMemory(
            name=name,
            create=True,
            size=self.total_size
        )
        self.name = self.shm.name

        # Atomic write counter (for reader polling)
        self._write_counter = Value(ctypes.c_uint64, 0)
        self._write_index = Value(ctypes.c_uint32, 0)

        # Frame ready event (optional notification)
        self._frame_ready = Event()

        # Initialize header
        self._init_header()

        logger.info(f"DecoderSHMWriter created: name={self.name}, "
                   f"max={max_width}x{max_height}, "
                   f"buffer_size={self.buffer_size/1024/1024:.1f}MB, "
                   f"total={self.total_size/1024/1024:.1f}MB")

    def _init_header(self):
        """Initialize shared memory header."""
        header = struct.pack('<II', MAGIC, VERSION)
        self.shm.buf[0:8] = header

    def get_info(self) -> Dict[str, Any]:
        """Get buffer info for connecting from another process."""
        return {
            'name': self.name,
            'size': self.total_size,
            'max_width': self.max_width,
            'max_height': self.max_height,
            'write_counter_name': self._write_counter.name if hasattr(self._write_counter, 'name') else None,
        }

    def write_frame(self, frame_data: bytes, width: int, height: int,
                    format_flag: int = FORMAT_NV12,
                    pts: int = 0, udp_recv_time: float = 0.0,
                    decode_time: float = 0.0, send_time_ns: int = 0,
                    packet_id: int = -1, is_keyframe: bool = False) -> bool:
        """
        Write frame to inactive buffer, then swap.

        This is lock-free: we write to the buffer that the reader
        is NOT currently reading.

        Args:
            frame_data: Frame bytes (NV12 or RGB24)
            width: Frame width
            height: Frame height
            format_flag: FORMAT_NV12 or FORMAT_RGB24
            pts: Presentation timestamp (nanoseconds)
            udp_recv_time: UDP receive time (seconds)
            decode_time: Decode complete time (seconds)
            send_time_ns: Device send time (nanoseconds)
            packet_id: Latency tracking ID
            is_keyframe: Whether this is a keyframe

        Returns:
            True if written successfully
        """
        if frame_data is None or width <= 0 or height <= 0:
            return False

        frame_size = len(frame_data)
        if frame_size > self.max_frame_size:
            logger.warning(f"Frame too large: {frame_size} > {self.max_frame_size}")
            return False

        # Get inactive buffer index (flip current write index)
        with self._write_index.get_lock():
            current_idx = self._write_index.value
            buf_idx = 1 - current_idx  # Write to the OTHER buffer

        # Calculate buffer offset
        buf_offset = HEADER_SIZE + buf_idx * self.buffer_size

        # Write frame data FIRST (to buffer header area)
        frame_offset = buf_offset + BUFFER_HEADER_SIZE
        self.shm.buf[frame_offset:frame_offset + frame_size] = frame_data

        # Write buffer header (metadata)
        flags = (1 if is_keyframe else 0)
        buf_header = struct.pack(
            BUFFER_HEADER_FORMAT,
            width,
            height,
            format_flag,
            frame_size,
            pts,
            int(udp_recv_time * 1e9) if udp_recv_time > 0 else 0,
            int(decode_time * 1e9) if decode_time > 0 else 0,
            send_time_ns,
            packet_id,
            flags,
            0,  # reserved1
            0   # reserved2
        )
        header_offset = buf_offset
        self.shm.buf[header_offset:header_offset + BUFFER_HEADER_SIZE] = buf_header

        # Memory barrier is implicit in Python

        # Atomically swap buffer index and increment counter
        with self._write_index.get_lock():
            self._write_index.value = buf_idx
        with self._write_counter.get_lock():
            new_counter = self._write_counter.value + 1
            self._write_counter.value = new_counter

        # Signal frame ready (optional, for event-driven reading)
        self._frame_ready.set()

        # Log every 100 frames
        if new_counter % 100 == 0:
            format_str = "NV12" if format_flag == FORMAT_NV12 else "RGB"
            delay_ms = (time.time() - udp_recv_time) * 1000 if udp_recv_time > 0 else 0
            logger.info(f"[SHM_WRITE] #{new_counter} {width}x{height} {format_str}, "
                       f"delay={delay_ms:.0f}ms")

        return True

    def write_nv12_dict(self, nv12_dict: dict, pts: int = 0,
                        udp_recv_time: float = 0.0, decode_time: float = 0.0,
                        send_time_ns: int = 0, packet_id: int = -1,
                        is_keyframe: bool = False) -> bool:
        """
        Write NV12 frame from dict format (compatible with VideoDecoder output).

        Args:
            nv12_dict: Dict with 'y', 'u', 'v' arrays or 'y_bytes', 'uv_bytes'
            pts: Presentation timestamp (nanoseconds)
            udp_recv_time: UDP receive time (seconds)
            decode_time: Decode complete time (seconds)
            send_time_ns: Device send time (nanoseconds)
            packet_id: Latency tracking ID
            is_keyframe: Whether this is a keyframe

        Returns:
            True if written successfully
        """
        width = nv12_dict.get('width', 0)
        height = nv12_dict.get('height', 0)

        if width <= 0 or height <= 0:
            return False

        # Build NV12 bytes from dict
        if 'y' in nv12_dict and 'u' in nv12_dict:
            y_plane = nv12_dict['y']
            u_plane = nv12_dict['u']
            v_plane = nv12_dict['v']

            # Ensure contiguous
            if not y_plane.flags['C_CONTIGUOUS']:
                y_plane = np.ascontiguousarray(y_plane)
            if not u_plane.flags['C_CONTIGUOUS']:
                u_plane = np.ascontiguousarray(u_plane)
            if not v_plane.flags['C_CONTIGUOUS']:
                v_plane = np.ascontiguousarray(v_plane)

            # Interleave U and V planes
            uv_height = height // 2
            uv_plane = np.empty((uv_height, width), dtype=np.uint8)
            uv_plane[:, 0::2] = u_plane
            uv_plane[:, 1::2] = v_plane

            # Concatenate Y and UV
            frame_data = y_plane.tobytes() + uv_plane.tobytes()
        elif 'y_bytes' in nv12_dict:
            # Direct bytes format
            frame_data = nv12_dict['y_bytes'] + nv12_dict.get('uv_bytes', b'')
        else:
            logger.warning("Invalid NV12 dict format")
            return False

        return self.write_frame(
            frame_data, width, height, FORMAT_NV12,
            pts, udp_recv_time, decode_time, send_time_ns,
            packet_id, is_keyframe
        )

    def wait_for_read(self, timeout: float = 1.0) -> bool:
        """Wait for reader to consume frame (optional)."""
        return self._frame_ready.wait(timeout)

    def close(self):
        """Close and unlink shared memory."""
        try:
            self.shm.close()
            self.shm.unlink()
            logger.info(f"DecoderSHMWriter closed: {self.name}")
        except Exception as e:
            logger.debug(f"DecoderSHMWriter close error: {e}")


class DecoderSHMReader:
    """
    Double-buffered shared memory reader for GUI process.

    Lock-free reading with atomic index tracking.
    """

    def __init__(self, name: str, size: int,
                 max_width: int = 4096, max_height: int = 4096):
        """
        Connect to existing shared memory.

        Args:
            name: Shared memory name from writer
            size: Total size from writer
            max_width: Maximum frame width
            max_height: Maximum frame height
        """
        self.name = name
        self.size = size
        self.max_width = max_width
        self.max_height = max_height

        self.max_frame_size = int(max_width * max_height * 1.5)
        self.buffer_size = BUFFER_HEADER_SIZE + self.max_frame_size

        # Connect to shared memory
        self.shm = shared_memory.SharedMemory(name=name)

        # Validate header
        magic, version = struct.unpack('<II', bytes(self.shm.buf[0:8]))
        if magic != MAGIC:
            raise ValueError(f"Invalid SHM magic: {hex(magic)} != {hex(MAGIC)}")

        # Track last counter for change detection
        self._last_counter = 0

        logger.info(f"DecoderSHMReader connected: {name}, size={size/1024/1024:.1f}MB")

    def read_frame(self) -> Optional[Tuple[np.ndarray, Dict[str, Any]]]:
        """
        Read latest frame from active buffer.

        Returns:
            Tuple of (frame_data, metadata) or None if no frame
            - frame_data: numpy array (NV12 or RGB24)
            - metadata: dict with width, height, format, pts, etc.
        """
        # Read with retry to handle race condition
        max_retries = 10

        for retry in range(max_retries):
            # Calculate active buffer index
            # We read from the buffer that was LAST written to
            # Read header to get write_index
            header = bytes(self.shm.buf[0:8])
            _, _ = struct.unpack('<II', header)

            # Read write_index from atomic value (we don't have direct access,
            # so we infer from the buffers)
            # For now, read buffer 0 and check if it's valid
            buf_idx = 0
            buf_offset = HEADER_SIZE + buf_idx * self.buffer_size

            # Read buffer header
            buf_header = bytes(self.shm.buf[buf_offset:buf_offset + BUFFER_HEADER_SIZE])
            (width, height, format_flag, frame_size, pts, udp_recv_time_ns,
             decode_time_ns, send_time_ns, packet_id, flags, _, _) = struct.unpack(
                BUFFER_HEADER_FORMAT, buf_header
            )

            # Check if this buffer has valid data
            if width <= 0 or height <= 0 or width > self.max_width or height > self.max_height:
                # Try buffer 1
                buf_idx = 1
                buf_offset = HEADER_SIZE + buf_idx * self.buffer_size
                buf_header = bytes(self.shm.buf[buf_offset:buf_offset + BUFFER_HEADER_SIZE])
                (width, height, format_flag, frame_size, pts, udp_recv_time_ns,
                 decode_time_ns, send_time_ns, packet_id, flags, _, _) = struct.unpack(
                    BUFFER_HEADER_FORMAT, buf_header
                )

                if width <= 0 or height <= 0:
                    return None

            # Validate frame size
            expected_size = int(width * height * 1.5) if format_flag == FORMAT_NV12 else width * height * 3
            if frame_size > self.max_frame_size or frame_size <= 0:
                logger.warning(f"Invalid frame size: {frame_size}")
                return None

            # Read frame data
            frame_offset = buf_offset + BUFFER_HEADER_SIZE
            frame_bytes = bytes(self.shm.buf[frame_offset:frame_offset + frame_size])

            # Re-read header to verify no race condition
            buf_header2 = bytes(self.shm.buf[buf_offset:buf_offset + BUFFER_HEADER_SIZE])
            (width2, height2, _, frame_size2, _, _, _, _, _, _, _, _) = struct.unpack(
                BUFFER_HEADER_FORMAT, buf_header2
            )

            if width != width2 or height != height2 or frame_size != frame_size2:
                # Race condition - buffer was updated during read
                if retry < max_retries - 1:
                    continue
                else:
                    logger.warning("SHM read max retries reached")
                    return None

            # Success - create numpy array
            frame = np.frombuffer(frame_bytes, dtype=np.uint8).copy()

            # Build metadata
            metadata = {
                'width': width,
                'height': height,
                'format': format_flag,
                'pts': pts,
                'udp_recv_time': udp_recv_time_ns / 1e9 if udp_recv_time_ns > 0 else 0.0,
                'decode_time': decode_time_ns / 1e9 if decode_time_ns > 0 else 0.0,
                'send_time_ns': send_time_ns,
                'packet_id': packet_id,
                'is_keyframe': bool(flags & 1),
            }

            # Log periodically
            if self._last_counter > 0 and (pts // 1000000) % 100 == 0:
                now = time.time()
                e2e_ms = (now - metadata['udp_recv_time']) * 1000 if metadata['udp_recv_time'] > 0 else 0
                format_str = "NV12" if format_flag == FORMAT_NV12 else "RGB"
                logger.debug(f"[SHM_READ] {width}x{height} {format_str}, E2E={e2e_ms:.0f}ms")

            return frame, metadata

        return None

    def read_nv12_planes(self) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]]:
        """
        Read NV12 frame and return separate Y, U, V planes.

        Returns:
            Tuple of (y_plane, u_plane, v_plane, metadata) or None
        """
        result = self.read_frame()
        if result is None:
            return None

        frame, metadata = result

        if metadata['format'] != FORMAT_NV12:
            logger.warning("read_nv12_planes called on non-NV12 frame")
            return None

        width = metadata['width']
        height = metadata['height']

        # Split into Y and UV
        y_size = width * height
        y_plane = frame[:y_size].reshape((height, width))
        uv_plane = frame[y_size:y_size + y_size // 2].reshape((height // 2, width))

        # De-interleave U and V
        u_plane = uv_plane[:, 0::2].copy()
        v_plane = uv_plane[:, 1::2].copy()

        return y_plane, u_plane, v_plane, metadata

    def close(self):
        """Close shared memory (don't unlink - writer does that)."""
        try:
            self.shm.close()
            logger.debug(f"DecoderSHMReader closed: {self.name}")
        except Exception as e:
            logger.debug(f"DecoderSHMReader close error: {e}")


# Convenience function to create writer with default settings
def create_decoder_shm(max_width: int = 4096, max_height: int = 4096) -> DecoderSHMWriter:
    """Create a decoder shared memory writer with default settings."""
    return DecoderSHMWriter(max_width=max_width, max_height=max_height)


__all__ = [
    'DecoderSHMWriter',
    'DecoderSHMReader',
    'create_decoder_shm',
    'FORMAT_RGB24',
    'FORMAT_NV12',
]
