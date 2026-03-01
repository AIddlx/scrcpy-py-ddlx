"""
Inter-process communication modules for multi-process video decoding.

This package provides:
- decoder_shm: Double-buffered shared memory for frame transfer
- control_channel: Bidirectional message passing between processes
"""

from .decoder_shm import (
    DecoderSHMWriter,
    DecoderSHMReader,
    create_decoder_shm,
    FORMAT_RGB24,
    FORMAT_NV12,
)

from .control_channel import (
    ControlChannel,
    DecoderChannel,
    ControlMessage,
    ControlMessageType,
)

__all__ = [
    # Shared memory
    'DecoderSHMWriter',
    'DecoderSHMReader',
    'create_decoder_shm',
    'FORMAT_RGB24',
    'FORMAT_NV12',
    # Control channel
    'ControlChannel',
    'DecoderChannel',
    'ControlMessage',
    'ControlMessageType',
]
