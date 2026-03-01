"""
Multi-process component factory for scrcpy client.

This module provides an alternative component factory that runs the
video decoder in a separate process to avoid GIL contention.

Use this factory for:
- UDP network mode with hardware decoding
- Low-latency requirements (<150ms E2E)
"""

import socket
import threading
import logging
from typing import Optional

from scrcpy_py_ddlx.core.protocol import CodecId
from scrcpy_py_ddlx.core.control import ControlMessageQueue
from scrcpy_py_ddlx.core.av_player import Recorder, Screen
from scrcpy_py_ddlx.core.audio import AudioPlayer
from scrcpy_py_ddlx.core.device_msg import DeviceMessageReceiver, ReceiverCallbacks
from scrcpy_py_ddlx.client.config import ClientConfig, ClientState

logger = logging.getLogger(__name__)


class MultiprocessComponentFactory:
    """
    Factory for creating components with multi-process decoder.

    This factory spawns a separate process for video decoding,
    eliminating GIL contention between UDP receive and decode operations.
    """

    def __init__(self, config: ClientConfig, state: ClientState,
                 control_socket: socket.socket = None,
                 audio_socket: socket.socket = None,
                 video_port: int = 27185,
                 connection_mode: str = "udp"):
        """
        Initialize multi-process component factory.

        Args:
            config: Client configuration
            state: Client state (will be updated with component references)
            control_socket: Control socket connection
            audio_socket: Audio socket (stays in main process for audio demuxer)
            video_port: UDP video port (for decoder process)
            connection_mode: Connection mode ('udp' recommended)
        """
        self.config = config
        self.state = state
        self._control_socket = control_socket
        self._audio_socket = audio_socket  # Audio stays in main process
        self._video_port = video_port
        self._connection_mode = connection_mode

        # Decoder process manager
        self._decoder_process = None

        # SHM info for renderer
        self._shm_info = None

        # Audio packet queue (for audio decoder connection)
        self._audio_packet_queue = None

    def create_decoder_process(self, extradata: bytes = None):
        """
        Create and start the decoder process.

        This replaces both create_video_demuxer() and create_video_decoder()
        in the single-process architecture.

        Args:
            extradata: Codec extradata (SPS/PPS) if available

        Returns:
            DecoderProcessManager instance
        """
        try:
            from scrcpy_py_ddlx.core.decoder.decoder_process import DecoderProcessManager

            # Get video dimensions from state (may be 0 if waiting for config packet)
            width, height = self.state.device_size if self.state.device_size else (0, 0)
            codec_id = self.state.codec_id if self.state.codec_id else 0

            # If dimensions unknown, use max values for SHM allocation
            shm_width = max(width, 4096) if width > 0 else 4096
            shm_height = max(height, 4096) if height > 0 else 4096

            # Create decoder process manager
            self._decoder_process = DecoderProcessManager(
                video_port=self._video_port,
                codec_id=codec_id,  # May be 0 - decoder will wait for config packet
                width=width,         # May be 0
                height=height,       # May be 0
                extradata=extradata,
                hw_accel=getattr(self.config, 'gpu_rendering', True),
                max_width=shm_width,
                max_height=shm_height
            )

            # Store SHM info for renderer
            self._shm_info = self._decoder_process.get_shm_info()

            logger.info(f"DecoderProcessManager created: port={self._video_port}, "
                       f"codec={hex(codec_id) if codec_id else 'unknown'}, size={width}x{height if width else 'unknown'}")
            logger.info(f"SHM: {self._shm_info['name']}")

            return self._decoder_process

        except Exception as e:
            logger.error(f"DecoderProcessManager creation failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def start_decoder_process(self):
        """Start the decoder subprocess."""
        if self._decoder_process:
            self._decoder_process.start()
            logger.info("Decoder process started")

    def stop_decoder_process(self):
        """Stop the decoder subprocess."""
        if self._decoder_process:
            self._decoder_process.stop()
            logger.info("Decoder process stopped")

    def get_shm_info(self):
        """Get shared memory info for renderer."""
        return self._shm_info

    def create_audio_demuxer(self):
        """
        Initialize audio demuxer (runs in main process, separate from video).

        Audio processing is lightweight compared to video, so it stays in
        the main process without causing significant GIL contention.
        """
        from queue import Queue

        try:
            # Audio uses separate socket
            if self._audio_socket is None:
                logger.warning("Audio socket not initialized, skipping AudioDemuxer")
                return None

            # Import audio demuxer factory
            from scrcpy_py_ddlx.core.demuxer.audio import create_audio_demuxer_for_mode

            # Create FEC decoder for audio if enabled
            audio_fec_decoder = None
            if self.config.is_audio_fec_enabled():
                from scrcpy_py_ddlx.core.demuxer.fec import FecDecoder
                audio_fec_decoder = FecDecoder()
                logger.info(f"FEC decoder created for audio: group_size={self.config.fec_group_size}")

            demuxer, queue = create_audio_demuxer_for_mode(
                mode='udp',
                sock=self._audio_socket,
                audio_codec=self.config.audio_codec,
                packet_queue_size=3,
                fec_decoder=audio_fec_decoder
            )

            self._audio_packet_queue = queue
            logger.info("AudioDemuxer initialized (multi-process mode)")
            return demuxer

        except Exception as e:
            logger.error(f"AudioDemuxer initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def create_audio_decoder(self):
        """
        Initialize audio decoder (runs in main process, not affected by GIL as much).

        Note: Audio decoding is much lighter than video and typically
        doesn't cause significant GIL contention.
        """
        from scrcpy_py_ddlx.core.decoder import AudioDecoder

        try:
            # Use the packet queue from audio demuxer
            if self._audio_packet_queue is None:
                logger.warning("Audio packet queue not initialized, creating standalone queue")
                from queue import Queue
                self._audio_packet_queue = Queue(maxsize=3)

            decoder = AudioDecoder(
                sample_rate=48000,
                channels=2,
                audio_codec=self.config.audio_codec,
                frame_sink=None,
                packet_queue=self._audio_packet_queue
            )
            logger.info("AudioDecoder initialized")
            return decoder
        except Exception as e:
            logger.error(f"AudioDecoder initialization failed: {e}")
            return None

    def create_recorder(self):
        """Initialize recorder (optional)."""
        if not self.config.record_filename:
            return None

        try:
            from scrcpy_py_ddlx.core.av_player import Recorder

            def on_ended(success):
                logger.info(f"Recording {'completed' if success else 'failed'}")

            recorder = Recorder(
                filename=self.config.record_filename,
                format=self.config.record_format,
                video=True,
                audio=self.config.audio,
                on_ended=on_ended
            )

            video_codec_ctx = {
                "width": self.state.device_size[0],
                "height": self.state.device_size[1],
                "codec_id": self.state.codec_id
            }
            recorder.open(video_codec_ctx)
            recorder.start()

            logger.info(f"Recorder initialized: {self.config.record_filename}")
            return recorder
        except Exception as e:
            logger.error(f"Recorder initialization failed: {e}")
            return None

    def create_controller(self, control_loop_func):
        """Initialize controller (Step 7)."""
        try:
            control_thread = threading.Thread(
                target=control_loop_func,
                name="Controller",
                daemon=True
            )
            control_thread.start()
            logger.info("Controller started")
            return control_thread
        except Exception as e:
            logger.error(f"Controller initialization failed: {e}")
            return None

    def create_screen(self, video_decoder, video_window):
        """Initialize screen (simplified for multi-process)."""
        try:
            # In multi-process mode, screen is just a pass-through
            # The actual frame handling is done by SHM

            def wrapped_frame_callback(frame):
                if video_window is not None:
                    video_window.update_frame(None)
                if self.config.frame_callback:
                    self.config.frame_callback(frame)

            screen = Screen(
                on_frame_callback=wrapped_frame_callback,
                on_init_callback=self.config.init_callback
            )

            video_codec_ctx = {
                "width": self.state.device_size[0],
                "height": self.state.device_size[1]
            }
            screen.open(video_codec_ctx)

            logger.info("Screen initialized (multi-process mode)")
            return screen
        except Exception as e:
            logger.error(f"Screen initialization failed: {e}")
            return None

    def create_video_window(self, video_decoder, control_queue):
        """
        Initialize video window with SHM frame source.

        This is the key modification for multi-process architecture:
        the video window reads frames from shared memory instead of DelayBuffer.
        """
        if not self.config.show_window:
            return None

        try:
            from scrcpy_py_ddlx.core.player.video.factory import create_video_window

            video_window = create_video_window(use_opengl=True)
            if video_window is None:
                logger.warning("Video window creation failed (PySide6 not available)")
                return None

            # Set device info
            video_window.set_device_info(
                self.state.device_name,
                self.state.device_size[0],
                self.state.device_size[1]
            )

            # Set control queue
            video_window.set_control_queue(control_queue)

            # Set SHM info for multi-process frame reading
            if self._shm_info:
                video_window.set_shm_source(
                    shm_name=self._shm_info['name'],
                    shm_size=self._shm_info['size'],
                    max_width=self._shm_info['max_width'],
                    max_height=self._shm_info['max_height']
                )
                logger.info(f"Video window configured with SHM source: {self._shm_info['name']}")

            # Show window
            video_window.show()

            logger.info("Video window initialized (multi-process mode)")
            return video_window
        except Exception as e:
            logger.error(f"Video window initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def create_audio_player(self, audio_decoder):
        """Initialize audio player (optional)."""
        if audio_decoder is None:
            return None

        try:
            from scrcpy_py_ddlx.core.audio import AudioPlayer

            if AudioPlayer is None:
                logger.warning("No audio player available")
                return None

            player = AudioPlayer()
            audio_decoder._frame_sink = player
            audio_decoder.start()

            import time
            for _ in range(20):
                time.sleep(0.1)
                if hasattr(audio_decoder.codec_impl, 'detected_sample_rate'):
                    detected_rate = audio_decoder.codec_impl.detected_sample_rate
                    if detected_rate is not None:
                        break
            else:
                detected_rate = 48000

            audio_codec_ctx = {
                "sample_rate": detected_rate,
                "channels": 2,
                "codec_type": "audio"
            }
            player.open(audio_codec_ctx)
            player.start()

            logger.info(f"AudioPlayer initialized")
            return player
        except Exception as e:
            logger.error(f"AudioPlayer initialization failed: {e}")
            return None

    def create_device_receiver(self, clipboard_event_callback):
        """Initialize device message receiver."""
        try:
            callbacks = ReceiverCallbacks(
                on_clipboard=clipboard_event_callback,
                on_uhid_output=None,
                on_app_list=None,
                on_screenshot=None
            )

            if not self.config.control or self._control_socket is None:
                logger.info("Control disabled, skipping DeviceReceiver")
                return None

            receiver = DeviceMessageReceiver(
                socket=self._control_socket,
                callbacks=callbacks
            )
            receiver.start()
            logger.info("DeviceReceiver started")
            return receiver
        except Exception as e:
            logger.error(f"DeviceReceiver initialization failed: {e}")
            return None

    def create_control_queue(self):
        """Create the control message queue."""
        return ControlMessageQueue()

    def close(self):
        """Clean up resources."""
        self.stop_decoder_process()


__all__ = ["MultiprocessComponentFactory"]
