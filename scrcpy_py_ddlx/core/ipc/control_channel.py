"""
Control channel for inter-process communication.

Provides bidirectional message passing between GUI process and decoder process.
"""

import logging
from multiprocessing import Queue, Value
import ctypes
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Optional, Any, Dict
import time

logger = logging.getLogger(__name__)


class ControlMessageType(IntEnum):
    """Control message types for decoder process communication."""

    # GUI → Decoder Process
    START_DECODING = 1
    STOP_DECODING = 2
    PAUSE_DECODING = 3
    RESUME_DECODING = 4
    REQUEST_KEYFRAME = 5  # PLI request
    SET_BITRATE = 6
    RECONNECT = 7

    # Decoder → GUI Process
    DECODER_READY = 100
    DECODER_ERROR = 101
    FRAME_SIZE_CHANGED = 102
    STATS_UPDATE = 103
    CONNECTION_LOST = 104
    DECODER_STOPPED = 105


@dataclass
class ControlMessage:
    """Control message structure."""
    type: ControlMessageType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class ControlChannel:
    """
    Bidirectional control channel between GUI and decoder processes.

    Uses multiprocessing.Queue for reliable ordered delivery.

    Example usage:

    # In GUI process:
    channel = ControlChannel()
    decoder_proc = DecoderProcess(channel.get_decoder_end())
    channel.send_to_decoder(ControlMessageType.START_DECODING, {'codec': 'h265'})
    msg = channel.recv_from_decoder()  # Non-blocking

    # In decoder process:
    decoder_channel = DecoderChannel.from_tuple(decoder_end)
    msg = decoder_channel.recv_from_gui()
    decoder_channel.send_to_gui(ControlMessageType.DECODER_READY)
    """

    def __init__(self, queue_size: int = 100):
        """
        Create control channel.

        Args:
            queue_size: Maximum number of messages in each direction
        """
        # GUI → Decoder
        self._to_decoder = Queue(maxsize=queue_size)
        # Decoder → GUI
        self._to_gui = Queue(maxsize=queue_size)

        # Shared running flag
        self._running = Value(ctypes.c_bool, True)

    def get_decoder_end(self) -> tuple:
        """
        Get tuple of objects needed by decoder process.

        Returns:
            (to_decoder_queue, to_gui_queue, running_value)
        """
        return (self._to_decoder, self._to_gui, self._running)

    # GUI Process Methods

    def send_to_decoder(self, msg_type: ControlMessageType, data: Dict[str, Any] = None) -> bool:
        """
        Send control message to decoder process (called by GUI).

        Args:
            msg_type: Message type
            data: Optional data dict

        Returns:
            True if sent successfully
        """
        try:
            msg = ControlMessage(type=msg_type, data=data or {})
            self._to_decoder.put(msg, timeout=0.1)
            return True
        except Exception as e:
            logger.warning(f"Failed to send to decoder: {e}")
            return False

    def recv_from_decoder(self, timeout: float = 0.01) -> Optional[ControlMessage]:
        """
        Receive status/update from decoder (called by GUI).

        Args:
            timeout: Max wait time in seconds

        Returns:
            ControlMessage or None
        """
        try:
            return self._to_gui.get(timeout=timeout)
        except:
            return None

    def is_running(self) -> bool:
        """Check if decoder is still running."""
        return self._running.value

    def stop(self):
        """Signal decoder to stop."""
        self._running.value = False

    # Context manager
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stop()


class DecoderChannel:
    """
    Control channel endpoint for decoder process.

    This is the decoder-side interface to the control channel.
    """

    def __init__(self, to_decoder_queue: Queue, to_gui_queue: Queue, running_value: Value):
        """
        Initialize decoder channel endpoint.

        Args:
            to_decoder_queue: Queue for receiving from GUI
            to_gui_queue: Queue for sending to GUI
            running_value: Shared running flag
        """
        self._from_gui = to_decoder_queue
        self._to_gui = to_gui_queue
        self._running = running_value

    @classmethod
    def from_tuple(cls, data: tuple) -> 'DecoderChannel':
        """Create from tuple returned by ControlChannel.get_decoder_end()."""
        return cls(data[0], data[1], data[2])

    def recv_from_gui(self, timeout: float = 0.001) -> Optional[ControlMessage]:
        """
        Receive control message from GUI (called by decoder).

        Args:
            timeout: Max wait time in seconds (short for non-blocking)

        Returns:
            ControlMessage or None
        """
        try:
            return self._from_gui.get(timeout=timeout)
        except:
            return None

    def send_to_gui(self, msg_type: ControlMessageType, data: Dict[str, Any] = None) -> bool:
        """
        Send status/update to GUI (called by decoder).

        Args:
            msg_type: Message type
            data: Optional data dict

        Returns:
            True if sent successfully
        """
        try:
            msg = ControlMessage(type=msg_type, data=data or {})
            self._to_gui.put(msg, timeout=0.1)
            return True
        except Exception as e:
            logger.warning(f"Failed to send to GUI: {e}")
            return False

    def send_error(self, error_msg: str, details: Dict[str, Any] = None):
        """Send error message to GUI."""
        data = {'error': error_msg}
        if details:
            data.update(details)
        self.send_to_gui(ControlMessageType.DECODER_ERROR, data)

    def send_stats(self, stats: Dict[str, Any]):
        """Send statistics update to GUI."""
        self.send_to_gui(ControlMessageType.STATS_UPDATE, stats)

    def send_frame_size_changed(self, width: int, height: int):
        """Notify GUI of frame size change."""
        self.send_to_gui(ControlMessageType.FRAME_SIZE_CHANGED, {
            'width': width,
            'height': height
        })

    def is_running(self) -> bool:
        """Check if decoder should continue running."""
        return self._running.value

    def stop(self):
        """Signal that decoder is stopping."""
        self._running.value = False
        self.send_to_gui(ControlMessageType.DECODER_STOPPED)


__all__ = [
    'ControlChannel',
    'DecoderChannel',
    'ControlMessage',
    'ControlMessageType',
]
