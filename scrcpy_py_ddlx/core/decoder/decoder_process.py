"""
Complete decoder process with UDP receiver and hardware decoder.

This module runs in a separate process to avoid GIL contention:
- UDP packet reception (releases GIL during I/O)
- Packet parsing and fragment reassembly
- Hardware video decoding (hevc_cuvid)
- Frame output to shared memory

The main process reads frames from shared memory for GPU rendering.
"""

import logging
import socket
import time
import struct
import multiprocessing as mp
from typing import Optional, Dict, Any, Tuple
from multiprocessing import shared_memory
import numpy as np

# Protocol constants - MUST match protocol.py
UDP_HEADER_SIZE = 24
FLAG_CONFIG = 0x2         # Bit 1: Config packet
FLAG_KEY_FRAME = 0x1      # Bit 0: Key frame
FLAG_FRAGMENT = 0x80000000  # Bit 31: Fragmented packet


def setup_process_logging(log_level: int = logging.INFO, log_file: str = None):
    """Setup logging for decoder process."""
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S',
        handlers=handlers
    )


def decoder_process_main(
    # Control channel queues
    control_queue_gui_to_decoder,
    control_queue_decoder_to_gui,
    running_flag,
    # Shared memory info
    shm_name: str,
    shm_size: int,
    shm_max_width: int,
    shm_max_height: int,
    # Network config
    video_port: int,
    # Decoder config (may be 0 if unknown - will be set from config packet)
    codec_id: int,
    width: int,
    height: int,
    extradata: bytes = None,
    hw_accel: bool = True,
    # Logging
    log_level: int = logging.INFO,
):
    """
    Main function for decoder process.

    This runs in a separate process and handles the complete pipeline:
    UDP receive → Parse → Decode → Write SHM

    All in one process to avoid GIL contention between stages.
    """
    import sys
    print(f"[DECODER_PROC] Starting decoder process: port={video_port}", file=sys.stderr, flush=True)

    setup_process_logging(log_level)
    logger = logging.getLogger('decoder_proc')
    logger.info(f"Decoder process starting: video_port={video_port}")

    try:
        # Import heavy modules inside process
        from scrcpy_py_ddlx.core.ipc.decoder_shm import FORMAT_NV12
        from scrcpy_py_ddlx.core.ipc.control_channel import DecoderChannel, ControlMessageType
        from scrcpy_py_ddlx.core.protocol import CodecId, UDP_HEADER_SIZE, codec_id_to_string

        # Create control channel endpoint
        channel = DecoderChannel(
            control_queue_gui_to_decoder,
            control_queue_decoder_to_gui,
            running_flag
        )

        # Connect to shared memory
        shm = shared_memory.SharedMemory(name=shm_name)
        logger.info(f"Connected to SHM: {shm_name}, size={shm_size/1024/1024:.1f}MB")

        # Create UDP socket FIRST (before initializing decoder)
        print(f"[DECODER_PROC] Creating UDP socket on port {video_port}...", file=sys.stderr, flush=True)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Allow port reuse
        sock.bind(('0.0.0.0', video_port))
        sock.settimeout(0.5)  # 500ms timeout for initial config packets
        print(f"[DECODER_PROC] UDP socket bound to port {video_port}", file=sys.stderr, flush=True)
        logger.info(f"UDP socket bound to port {video_port}")

        # If codec_id/width/height unknown, wait for first config packet
        if codec_id == 0 or width == 0 or height == 0:
            logger.info("Waiting for config packet to determine codec/size...")
            print("[DECODER_PROC] Waiting for config packet...", file=sys.stderr, flush=True)

            config_received = False
            max_wait = 5.0  # 5 seconds max
            wait_start = time.time()

            while not config_received and time.time() - wait_start < max_wait:
                try:
                    packet, addr = sock.recvfrom(65536)
                    if len(packet) >= UDP_HEADER_SIZE:
                        seq, ts, flags, send_ns = struct.unpack('>IqIq', packet[:24])
                        if flags & FLAG_CONFIG:
                            # Parse config packet
                            payload = packet[UDP_HEADER_SIZE:]
                            if len(payload) >= 12:
                                pts_flags, payload_size = struct.unpack('>QI', payload[:12])
                                config_data = payload[12:12+payload_size]
                                if len(config_data) >= 12:
                                    codec_id = struct.unpack('>I', config_data[0:4])[0]
                                    width = struct.unpack('>I', config_data[4:8])[0]
                                    height = struct.unpack('>I', config_data[8:12])[0]
                                    if len(config_data) > 12:
                                        extradata = config_data[12:]
                                    config_received = True
                                    logger.info(f"Config packet received: codec={hex(codec_id)}, size={width}x{height}")
                                    print(f"[DECODER_PROC] Config: codec={hex(codec_id)}, size={width}x{height}", file=sys.stderr, flush=True)
                except socket.timeout:
                    continue

            if not config_received:
                logger.error("Failed to receive config packet")
                channel.send_to_gui(ControlMessageType.DECODER_ERROR, {'error': 'No config packet'})
                return

        # Now initialize decoder with known codec/size
        import av
        from av.video.codeccontext import VideoCodecContext

        # Get codec name
        codec_name_map = {
            CodecId.H264: 'h264',
            CodecId.H265: 'hevc',
            CodecId.AV1: 'av1',
        }
        base_codec = codec_name_map.get(codec_id, 'hevc')

        # Use HWAccel like single-process mode (instead of direct cuvid decoder)
        # This ensures consistent NV12 output format
        hwaccel = None
        decoder_name = base_codec

        if hw_accel:
            # Try to use HWAccel with CUDA (same as single-process mode)
            try:
                hwaccel = av.HWAccel(device_type="cuda", allow_software_fallback=True)
                logger.info(f"Using HWAccel with cuda device (same as single-process mode)")
            except Exception as e:
                logger.warning(f"Failed to create HWAccel: {e}, trying cuvid decoder")
                # Fallback: try direct cuvid decoder
                hw_decoders = ['hevc_cuvid', 'h264_cuvid']
                for hw_dec in hw_decoders:
                    try:
                        test_ctx = av.CodecContext.create(hw_dec, 'r')
                        decoder_name = hw_dec
                        logger.info(f"Using direct hardware decoder: {decoder_name}")
                        break
                    except:
                        continue

        # Create decoder context
        if hwaccel:
            codec_ctx = av.CodecContext.create(base_codec, 'r', hwaccel=hwaccel)
            logger.info(f"Created decoder with HWAccel: {base_codec}")
        else:
            codec_ctx = av.CodecContext.create(decoder_name, 'r')
            logger.info(f"Created decoder: {decoder_name}")

        codec_ctx.width = width
        codec_ctx.height = height
        codec_ctx.pix_fmt = "yuv420p"

        # Set extradata if provided (SPS/PPS)
        if extradata:
            codec_ctx.extradata = extradata
            logger.info(f"Set extradata: {len(extradata)} bytes")

        logger.info(f"Decoder initialized: {base_codec if hwaccel else decoder_name} (hwaccel={hwaccel is not None}) for {width}x{height}")

        # Notify GUI that decoder is ready with actual size
        channel.send_to_gui(ControlMessageType.DECODER_READY, {
            'width': width,
            'height': height,
            'decoder': base_codec if hwaccel else decoder_name
        })

        # State for fragment reassembly
        fragment_buffer = {}
        current_config_data = None

        # Stats
        frame_count = 0
        packet_count = 0
        last_stats_time = time.time()

        # IMPORTANT: Prepend extradata to first N frames to handle devices
        # where MediaCodec doesn't reliably set BUFFER_FLAG_KEY_FRAME
        # This ensures decoder gets valid data even if keyframe flag is missing
        FRAMES_TO_PREPEND_EXTRADATA = 10
        prepend_countdown = FRAMES_TO_PREPEND_EXTRADATA

        # Triple-buffered SHM constants (must match SimpleSHMWriter)
        CONTROL_SIZE = 16  # active_buffer(4) + write_counter(4) + padding(8)
        BUFFER_HEADER_SIZE = 48  # counter(4) + w(4) + h(4) + format(4) + pts(8) + capture_ns(8) + udp_ns(8) + buf_idx(4) + pad(4)
        BUFFER_HEADER_FORMAT = '<IiIIqqqII'
        FORMAT_NV12 = 1
        NUM_BUFFERS = 3  # Triple buffering
        # CRITICAL: Must use max(rgb_size, nv12_size) to match SimpleSHMWriter/SimpleSHMReader layout!
        max_rgb_size = shm_max_width * shm_max_height * 3  # RGB24 size
        max_nv12_size = int(shm_max_width * shm_max_height * 1.5)  # NV12 size
        max_frame_size = max(max_rgb_size, max_nv12_size)  # Must match SimpleSHMWriter!
        buffer_size = BUFFER_HEADER_SIZE + max_frame_size

        # Triple buffer state
        write_counter = 0
        last_written_buffer = 2  # Track last written buffer

        def get_buffer_offset(buf_idx: int) -> int:
            """Get byte offset for a specific buffer."""
            return CONTROL_SIZE + buf_idx * buffer_size

        def get_next_write_buffer() -> int:
            """Get next buffer to write to (prioritize avoiding reading_buffer)."""
            nonlocal last_written_buffer
            # Read control header: [active_buffer:4][write_counter:4][reading_buffer:4][padding:4]
            control_data = bytes(shm.buf[0:12])
            active_buffer, _, reading_buffer = struct.unpack('<III', control_data[:12])

            # With triple buffering, we have 3 buffers:
            # - active_buffer: the latest complete frame (reader should read from this)
            # - reading_buffer: the buffer reader is currently reading (0xFF = not reading)
            # - last_written_buffer: same as active_buffer after we update control header
            #
            # Priority for avoiding: reading_buffer > active_buffer > last_written_buffer
            # It's OK to overwrite active/last_written (old frames), but NOT reading_buffer

            # Normalize reading_buffer (0xFF or invalid means not reading any buffer)
            if reading_buffer >= NUM_BUFFERS:
                reading_buffer = -1  # No buffer being read

            # First choice: buffer that's not active, not reading, not last_written
            for i in range(NUM_BUFFERS):
                if i != active_buffer and i != last_written_buffer and i != reading_buffer:
                    return i

            # Fallback: All buffers blocked (reader is slow)
            # Overwrite the oldest frame, but NEVER the one being read
            selected = -1
            for i in range(NUM_BUFFERS):
                if i != reading_buffer:
                    selected = i
                    break

            if selected >= 0:
                # Log when we have to reuse a buffer
                frame_count_local = frame_count
                if frame_count_local % 50 == 0:
                    logger.warning(f"[DECODER_BUF] Reusing buffer {selected}: "
                                  f"active={active_buffer}, reading={reading_buffer}, last={last_written_buffer}")
                return selected

            # Extreme fallback: reading_buffer is invalid, use any buffer
            # This shouldn't happen in normal operation
            return (last_written_buffer + 1) % NUM_BUFFERS

        def write_frame_to_shm(frame_data: bytes, w: int, h: int, pts: int,
                               udp_recv_time: float, decode_time: float):
            nonlocal frame_count, write_counter, last_written_buffer
            frame_count += 1

            # Get next write buffer (avoid active and last written)
            buffer_idx = get_next_write_buffer()
            offset = get_buffer_offset(buffer_idx)

            # Calculate checksum for data integrity verification
            import zlib
            checksum = zlib.crc32(frame_data) & 0xffffffff

            # Write frame data
            frame_size = len(frame_data)
            shm.buf[offset + BUFFER_HEADER_SIZE:offset + BUFFER_HEADER_SIZE + frame_size] = frame_data

            # Write header (with checksum for verification)
            write_counter += 1
            capture_time_ns = int(decode_time * 1e9) if decode_time > 0 else 0
            udp_recv_time_ns = int(udp_recv_time * 1e9) if udp_recv_time > 0 else 0

            header = struct.pack(
                BUFFER_HEADER_FORMAT,
                write_counter,
                w,
                h,
                FORMAT_NV12,
                pts,
                capture_time_ns,
                udp_recv_time_ns,
                buffer_idx,  # buffer_index
                checksum  # Use checksum instead of padding
            )
            shm.buf[offset:offset + BUFFER_HEADER_SIZE] = header

            # Update last_written_buffer BEFORE updating control header
            last_written_buffer = buffer_idx

            # Update control header to make this buffer the active one
            # This signals to reader that a new frame is available
            shm.buf[0:8] = struct.pack('<II', buffer_idx, write_counter)

        # Main loop
        logger.info("Entering main decode loop...")
        print(f"[DECODER_PROC] Entering main decode loop...", file=sys.stderr, flush=True)

        while channel.is_running():
            try:
                # Check for control messages (non-blocking)
                msg = channel.recv_from_gui(timeout=0)
                if msg:
                    if msg.type == ControlMessageType.STOP_DECODING:
                        logger.info("Received STOP command")
                        break

                # Receive UDP packet (releases GIL)
                try:
                    packet, addr = sock.recvfrom(65536)
                    packet_count += 1
                    udp_recv_time = time.time()
                except socket.timeout:
                    continue
                except Exception as e:
                    if channel.is_running():
                        logger.error(f"UDP recv error: {e}")
                    continue

                if len(packet) < UDP_HEADER_SIZE:
                    continue

                # Parse UDP header (MUST match UdpVideoDemuxer format)
                # Header: seq(4), ts(8), flags(4), send_time_ns(8) = 24 bytes
                # IMPORTANT: Use big-endian (network byte order) like udp_video.py
                seq, ts, flags, send_ns = struct.unpack('>IqIq', packet[:24])

                payload = packet[UDP_HEADER_SIZE:]

                # Debug: log first few packets
                if packet_count <= 5:
                    print(f"[DECODER_PROC] Packet #{packet_count}: len={len(packet)}, flags=0x{flags:x}, is_config={bool(flags & FLAG_CONFIG)}", file=sys.stderr, flush=True)

                # Parse scrcpy packet header (12 bytes)
                # Format: pts_flags (8 bytes) + payload_size (4 bytes)
                if len(payload) < 12:
                    continue

                pts_flags, scrcpy_payload_size = struct.unpack('>QI', payload[:12])
                scrcpy_payload = payload[12:12+scrcpy_payload_size]

                # Use UDP header flags for keyframe/config detection (like UdpPacketReader does)
                # UDP_FLAG_KEY_FRAME = 1 << 0, UDP_FLAG_CONFIG = 1 << 1
                is_keyframe = bool(flags & FLAG_KEY_FRAME)
                is_config = bool(flags & FLAG_CONFIG)

                # Debug first few packets
                if packet_count <= 5:
                    print(f"[DECODER_PROC] Packet #{packet_count}: udp_flags=0x{flags:x}, is_config={is_config}, is_keyframe={is_keyframe}, scrcpy_pts={pts_flags & 0x3FFFFFFFFFFFFFFF}", file=sys.stderr, flush=True)

                # Check if config packet (using scrcpy flags)
                if is_config:
                    # Store config data for merging with keyframes
                    # Config packet payload is the full config data (same as single-process mode)
                    current_config_data = scrcpy_payload
                    logger.info(f"Config packet received: {len(scrcpy_payload)} bytes")

                    # Also set extradata for codec context (for hardware decoders)
                    # Use the config payload directly - PyAV will handle format conversion
                    if len(scrcpy_payload) > 0:
                        codec_ctx.extradata = scrcpy_payload
                        logger.info(f"Set extradata: {len(scrcpy_payload)} bytes")
                        print(f"[DECODER_PROC] Extradata: {scrcpy_payload[:20].hex()}", file=sys.stderr, flush=True)
                    continue

                # Check if fragment (using UDP flags for this)
                is_fragment = bool(flags & FLAG_FRAGMENT)

                # For H.265/H.264, config data (SPS/PPS) should be prepended to keyframes
                # This matches the single-process PacketMerger behavior
                prepend_config = False
                if current_config_data and len(current_config_data) > 0:
                    if is_keyframe:
                        prepend_config = True
                        print(f"[DECODER_PROC] Keyframe at packet #{packet_count}, will prepend {len(current_config_data)} bytes config", file=sys.stderr, flush=True)
                    elif prepend_countdown > 0:
                        # Prepend config to first N frames even without keyframe flag
                        # This handles devices where MediaCodec doesn't set BUFFER_FLAG_KEY_FRAME
                        prepend_config = True
                        prepend_countdown -= 1
                        print(f"[DECODER_PROC] Packet #{packet_count} (early frame #{FRAMES_TO_PREPEND_EXTRADATA - prepend_countdown}), will prepend config", file=sys.stderr, flush=True)

                if is_fragment:
                    # Fragment reassembly
                    # Fragment format: [frag_idx: 4 bytes] [data: N bytes]
                    if len(scrcpy_payload) < 4:
                        continue
                    frag_idx = struct.unpack('>I', scrcpy_payload[:4])[0]
                    frag_data = scrcpy_payload[4:]

                    key = ts  # Use timestamp as key
                    if key not in fragment_buffer:
                        fragment_buffer[key] = {'frags': {}, 'is_keyframe': is_keyframe, 'pts_flags': pts_flags}

                    fragment_buffer[key]['frags'][frag_idx] = frag_data
                    fragment_buffer[key]['is_keyframe'] = is_keyframe  # Update if later frag has keyframe flag

                    # Heuristic: if this is a small fragment after larger ones, assume end of sequence
                    # Or if we have many fragments, try to decode
                    frag_count = len(fragment_buffer[key]['frags'])

                    # Check if we might have all fragments:
                    # - If fragment is small (< 50KB), it might be the last one
                    # - If we have multiple fragments and current one is smaller than previous
                    should_reassemble = False
                    if len(frag_data) < 50000 and frag_count >= 1:
                        # Last fragment is typically smaller
                        should_reassemble = True
                    elif frag_count > 10:
                        # Too many fragments accumulated, try to decode
                        should_reassemble = True

                    if should_reassemble:
                        # Reassemble in order
                        sorted_idx = sorted(fragment_buffer[key]['frags'].keys())
                        full_payload = b''.join(fragment_buffer[key]['frags'][i] for i in sorted_idx)
                        frag_is_keyframe = fragment_buffer[key]['is_keyframe']
                        del fragment_buffer[key]

                        # Prepend config data to keyframes (like single-process PacketMerger)
                        if frag_is_keyframe and current_config_data:
                            full_payload = current_config_data + full_payload
                            print(f"[DECODER_PROC] Reassembled keyframe from {frag_count} frags, prepended {len(current_config_data)} bytes config", file=sys.stderr, flush=True)

                        decode_payload = full_payload
                    else:
                        continue  # Wait for more fragments
                else:
                    # Non-fragmented packet
                    decode_payload = scrcpy_payload

                    # Merge config with keyframe if needed (like single-process PacketMerger)
                    if prepend_config and current_config_data:
                        decode_payload = current_config_data + decode_payload
                        if packet_count <= 5:
                            print(f"[DECODER_PROC] Prepended {len(current_config_data)} bytes config to keyframe", file=sys.stderr, flush=True)

                # Create AVPacket and decode
                try:
                    av_packet = av.Packet(decode_payload)
                    av_packet.pts = pts_flags & 0x3FFFFFFFFFFFFFFF  # Extract PTS (lower 62 bits)

                    decode_start = time.perf_counter()
                    frames = codec_ctx.decode(av_packet)
                    decode_time = time.perf_counter() - decode_start

                    for frame in frames:
                        # Convert to NV12 format - use planes API to handle stride correctly
                        # This matches the single-process _frame_to_nv12_dict logic
                        try:
                            actual_width = frame.width
                            actual_height = frame.height

                            # Convert to NV12
                            nv12_frame = frame.reformat(format='nv12')
                            planes = nv12_frame.planes

                            if planes is None or len(planes) < 2:
                                # Fallback to to_ndarray
                                nv12_array = nv12_frame.to_ndarray()
                                frame_data = nv12_array.tobytes()
                            else:
                                # Handle stride padding like single-process mode
                                # NV12 format: Y plane (h x w) + UV plane interleaved (h/2 x w)
                                # UV plane is already interleaved: U0 V0 U1 V1 U2 V2 ...
                                y_plane = planes[0]
                                uv_plane = planes[1]
                                y_linesize = y_plane.line_size
                                uv_linesize = uv_plane.line_size

                                # Debug: always show stride info for first few frames
                                if frame_count <= 3:
                                    print(f"[DECODER_STRIDE] Frame #{frame_count}: "
                                          f"actual_size={actual_width}x{actual_height}, "
                                          f"y_linesize={y_linesize}, uv_linesize={uv_linesize}, "
                                          f"use_fast_path={y_linesize == actual_width and uv_linesize == actual_width}",
                                          file=sys.stderr, flush=True)

                                # Fast path: no stride padding (same as single-process mode)
                                if y_linesize == actual_width and uv_linesize == actual_width:
                                    # Direct copy without numpy processing - avoids potential issues
                                    frame_data = bytes(y_plane) + bytes(uv_plane)
                                    if frame_count <= 3:
                                        # Check raw UV data distribution
                                        uv_raw = np.frombuffer(uv_plane, np.uint8).reshape(actual_height // 2, uv_linesize)
                                        u_raw = uv_raw[:, 0::2]
                                        v_raw = uv_raw[:, 1::2]
                                        third = u_raw.shape[1] // 3
                                        u_left = u_raw[:, :third]
                                        u_right = u_raw[:, 2*third:]
                                        v_left = v_raw[:, :third]
                                        v_right = v_raw[:, 2*third:]
                                        print(f"[DECODER_FAST] Frame #{frame_count}: Using fast path (no stride), "
                                              f"y_size={len(bytes(y_plane))}, uv_size={len(bytes(uv_plane))}",
                                              file=sys.stderr, flush=True)
                                        print(f"[DECODER_FAST]   u_left=[{u_left.min()},{u_left.max()}], "
                                              f"u_right=[{u_right.min()},{u_right.max()}]", file=sys.stderr, flush=True)
                                        print(f"[DECODER_FAST]   v_left=[{v_left.min()},{v_left.max()}], "
                                              f"v_right=[{v_right.min()},{v_right.max()}]", file=sys.stderr, flush=True)
                                else:
                                    # Slow path: handle stride padding
                                    # Extract Y plane (remove stride padding)
                                    y_array = np.frombuffer(y_plane, np.uint8).reshape(actual_height, y_linesize)
                                    y_data = y_array[:, :actual_width].copy()

                                    # Extract UV plane (already interleaved, just remove stride padding)
                                    uv_array = np.frombuffer(uv_plane, np.uint8).reshape(actual_height // 2, uv_linesize)
                                    uv_data = uv_array[:, :actual_width].copy()

                                    # Debug: check UV data integrity at source (PyAV output)
                                    if frame_count <= 3:
                                        # Check RAW UV plane data from PyAV (before stride removal)
                                        uv_raw = np.frombuffer(uv_plane, np.uint8)
                                        uv_raw_2d = uv_raw.reshape(actual_height // 2, uv_linesize)

                                        # Check different regions of the RAW UV data
                                        # UV is interleaved: U0 V0 U1 V1 ... so width bytes = width/2 U + width/2 V
                                        u_raw = uv_raw_2d[:, 0::2]  # U at even columns
                                        v_raw = uv_raw_2d[:, 1::2]  # V at odd columns

                                        # Check left/middle/right thirds
                                        third = u_raw.shape[1] // 3
                                        u_left = u_raw[:, :third]
                                        u_mid = u_raw[:, third:2*third]
                                        u_right = u_raw[:, 2*third:]

                                        print(f"[DECODER_SLOW] Frame #{frame_count}: "
                                              f"uv_linesize={uv_linesize}, actual_width={actual_width}, "
                                              f"uv_raw_shape={uv_raw_2d.shape}, u_raw_shape={u_raw.shape}", file=sys.stderr, flush=True)
                                        print(f"[DECODER_SLOW]   y_range=[{y_data.min()},{y_data.max()}]", file=sys.stderr, flush=True)
                                        print(f"[DECODER_SLOW]   u_left=[{u_left.min()},{u_left.max()}], "
                                              f"u_mid=[{u_mid.min()},{u_mid.max()}], "
                                              f"u_right=[{u_right.min()},{u_right.max()}]", file=sys.stderr, flush=True)

                                        # Check if stride causes the issue
                                        if uv_linesize > actual_width:
                                            # Check the stride padding region
                                            stride_padding = uv_raw_2d[:, actual_width:uv_linesize]
                                            print(f"[DECODER_SLOW]   STRIDE_PADDING region shape={stride_padding.shape}, "
                                                  f"range=[{stride_padding.min()},{stride_padding.max()}]", file=sys.stderr, flush=True)

                                        # Also log processed data
                                        u_processed = uv_data[:, 0::2]
                                        v_processed = uv_data[:, 1::2]
                                        u_p_left = u_processed[:, :third]
                                        u_p_right = u_processed[:, 2*third:]
                                        print(f"[DECODER_SLOW]   u_proc_left=[{u_p_left.min()},{u_p_left.max()}], "
                                              f"u_proc_right=[{u_p_right.min()},{u_p_right.max()}]", file=sys.stderr, flush=True)

                                    # Combine Y and UV planes directly - no need to separate/re-interleave
                                    frame_data = np.concatenate([y_data.ravel(), uv_data.ravel()]).tobytes()

                            # Debug first frame
                            if frame_count < 3:
                                expected_size = int(actual_width * actual_height * 1.5)
                                logger.info(f"Frame #{frame_count}: size={len(frame_data)}, expected={expected_size}, "
                                           f"w={actual_width}, h={actual_height}")
                                logger.info(f"Frame #{frame_count}: first_bytes={frame_data[:20].hex()}")

                            # Write to SHM
                            write_frame_to_shm(
                                frame_data,
                                actual_width,
                                actual_height,
                                frame.pts if frame.pts else ts,
                                udp_recv_time,
                                decode_time
                            )

                            if frame_count % 100 == 0:
                                delay_ms = (time.time() - udp_recv_time) * 1000
                                logger.info(f"[DECODER] Frame #{frame_count}, "
                                           f"delay={delay_ms:.0f}ms, decode={decode_time*1000:.1f}ms")

                        except Exception as e:
                            logger.error(f"Frame conversion error: {e}")

                except Exception as e:
                    logger.debug(f"Decode error: {e}, payload_size={len(decode_payload)}")
                    # Log first decode error in detail
                    if frame_count == 0 and packet_count < 10:
                        logger.warning(f"Early decode error #{packet_count}: {e}")
                        print(f"[DECODER_PROC] Decode error: {e}", file=sys.stderr, flush=True)

                # Periodic stats
                now = time.time()
                if now - last_stats_time > 2.0:
                    logger.info(f"[DECODER_PROC] Stats: packets={packet_count}, frames={frame_count}")
                    print(f"[DECODER_PROC] Stats: packets={packet_count}, frames={frame_count}", file=sys.stderr, flush=True)
                    channel.send_stats({
                        'packets_received': packet_count,
                        'frames_decoded': frame_count,
                    })
                    last_stats_time = now

            except Exception as e:
                logger.error(f"Error in decode loop: {e}")
                time.sleep(0.01)

        # Cleanup
        logger.info("Decoder process shutting down...")
        sock.close()
        shm.close()
        channel.send_to_gui(ControlMessageType.DECODER_STOPPED)
        logger.info(f"Decoder process stopped: {frame_count} frames decoded")

    except Exception as e:
        logger.error(f"Decoder process fatal error: {e}")
        import traceback
        import sys
        print(f"[DECODER_PROC] FATAL ERROR: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()


class DecoderProcessManager:
    """
    Manages the decoder subprocess from the main process.

    Handles:
    - Process lifecycle (start/stop)
    - Shared memory setup
    - Control channel creation
    - Configuration passing
    """

    def __init__(self,
                 video_port: int,
                 codec_id: int,
                 width: int,
                 height: int,
                 extradata: bytes = None,
                 hw_accel: bool = True,
                 max_width: int = 4096,
                 max_height: int = 4096):
        """
        Initialize decoder process manager.

        Args:
            video_port: UDP port for video stream
            codec_id: Video codec ID (CodecId.H264/H265/AV1)
            width: Initial video width
            height: Initial video height
            extradata: Codec extradata (SPS/PPS)
            hw_accel: Use hardware acceleration
            max_width: Maximum frame width for SHM
            max_height: Maximum frame height for SHM
        """
        self.video_port = video_port
        self.codec_id = codec_id
        self.width = width
        self.height = height
        self.extradata = extradata
        self.hw_accel = hw_accel
        self.max_width = max_width
        self.max_height = max_height

        # Control channel
        from scrcpy_py_ddlx.core.ipc.control_channel import ControlChannel
        self.control = ControlChannel()

        # Shared memory - use existing SimpleSHM format for compatibility
        from scrcpy_py_ddlx.simple_shm import SimpleSHMWriter
        self.shm_writer = SimpleSHMWriter(
            max_width=max_width,
            max_height=max_height
        )

        # Process handle
        self._process: Optional[mp.Process] = None

        self.logger = logging.getLogger(__name__)

    def get_shm_info(self) -> Dict[str, Any]:
        """Get shared memory info for reader."""
        return self.shm_writer.get_info()

    def get_control_channel(self):
        """Get control channel for sending commands."""
        return self.control

    def start(self):
        """Start the decoder subprocess."""
        if self._process is not None and self._process.is_alive():
            self.logger.warning("Decoder process already running")
            return

        # Get control channel endpoints
        control_end = self.control.get_decoder_end()

        # Create and start process
        self._process = mp.Process(
            target=decoder_process_main,
            kwargs={
                'control_queue_gui_to_decoder': control_end[0],
                'control_queue_decoder_to_gui': control_end[1],
                'running_flag': control_end[2],
                'shm_name': self.shm_writer.name,
                'shm_size': self.shm_writer.total_size,
                'shm_max_width': self.max_width,
                'shm_max_height': self.max_height,
                'video_port': self.video_port,
                'codec_id': self.codec_id,
                'width': self.width,
                'height': self.height,
                'extradata': self.extradata,
                'hw_accel': self.hw_accel,
            },
            name="DecoderProcess",
            daemon=True
        )
        self._process.start()
        self.logger.info(f"Decoder process started: PID={self._process.pid}")

        # Check if process is still alive after a short delay
        import time
        time.sleep(0.1)
        if not self._process.is_alive():
            exit_code = self._process.exitcode
            self.logger.error(f"Decoder process exited immediately with code: {exit_code}")
        else:
            self.logger.info("Decoder process is running")

    def stop(self, timeout: float = 5.0):
        """Stop the decoder subprocess."""
        if self._process is None:
            return

        self.logger.info("Stopping decoder process...")

        # Send stop command
        from scrcpy_py_ddlx.core.ipc.control_channel import ControlMessageType
        self.control.send_to_decoder(ControlMessageType.STOP_DECODING)

        # Wait for process to exit
        self._process.join(timeout=timeout)

        if self._process.is_alive():
            self.logger.warning("Decoder process did not stop, terminating...")
            self._process.terminate()
            self._process.join(timeout=1.0)

        self._process = None
        self.logger.info("Decoder process stopped")

    def is_running(self) -> bool:
        """Check if decoder process is running."""
        return self._process is not None and self._process.is_alive()

    def update_config(self, width: int, height: int, extradata: bytes = None):
        """Update decoder configuration (requires restart)."""
        self.width = width
        self.height = height
        self.extradata = extradata

    def close(self):
        """Stop process and cleanup resources."""
        self.stop()
        if self.shm_writer:
            self.shm_writer.close()
            self.shm_writer = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


__all__ = [
    'DecoderProcessManager',
    'decoder_process_main',
]
