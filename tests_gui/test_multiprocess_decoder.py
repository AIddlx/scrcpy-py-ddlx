"""
End-to-end test for multi-process decoder architecture.

This test runs the complete pipeline:
1. Decoder process receives UDP video stream
2. Decoder process decodes frames (hevc_cuvid)
3. Decoder process writes frames to SHM
4. Main process reads frames from SHM
5. Main process renders frames with OpenGL

Usage:
    python tests_gui/test_multiprocess_decoder.py --ip 192.168.x.x

Expected result: Latency should drop from ~334ms to ~150ms
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
import time
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def run_multiprocess_test(device_ip: str, video_port: int = 27185,
                          control_port: int = 27184, duration: int = 30):
    """
    Run multi-process decoder test.

    Args:
        device_ip: Device IP address
        video_port: UDP video port
        control_port: TCP control port
        duration: Test duration in seconds
    """
    from scrcpy_py_ddlx.core.protocol import CodecId
    from scrcpy_py_ddlx.core.decoder.decoder_process import DecoderProcessManager

    logger.info("=" * 60)
    logger.info("Multi-Process Decoder Test")
    logger.info("=" * 60)
    logger.info(f"Device: {device_ip}")
    logger.info(f"Video port: {video_port}")
    logger.info(f"Duration: {duration}s")

    # First, connect to get device info (using existing client)
    logger.info("Connecting to device to get video parameters...")

    try:
        import socket

        # Connect control socket
        control_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        control_sock.settimeout(5.0)
        control_sock.connect((device_ip, control_port))

        # Read dummy byte
        control_sock.recv(1)

        # Read device name (64 bytes)
        device_name = control_sock.recv(64).rstrip(b'\x00').decode('utf-8')

        # Read screen dimensions (4 + 4 bytes)
        dims = control_sock.recv(8)
        import struct
        width, height = struct.unpack('>II', dims)

        logger.info(f"Device: {device_name}, Screen: {width}x{height}")

        # Read encoder count and skip
        encoder_count = struct.unpack('>I', control_sock.recv(4))[0]
        for _ in range(encoder_count):
            control_sock.recv(12)  # Each encoder entry is 12 bytes

        # Read audio encoder count and skip
        audio_count = struct.unpack('>I', control_sock.recv(4))[0]
        for _ in range(audio_count):
            control_sock.recv(8)

        # Send client config (request H265)
        # Simplified - just send minimal config
        CLIENT_CONFIG_SIZE = 24
        config = bytearray(CLIENT_CONFIG_SIZE)
        struct.pack_into('<I', config, 0, CodecId.H265)  # video_codec
        struct.pack_into('<I', config, 4, 2500000)  # bitrate
        struct.pack_into('<I', config, 8, 60)  # max_fps
        struct.pack_into('<I', config, 12, 0)  # audio_codec (none)
        control_sock.sendall(bytes(config))

        logger.info("Client config sent")

        # Wait for first UDP packet to get codec extradata
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
        udp_sock.bind(('0.0.0.0', video_port))
        udp_sock.settimeout(10.0)

        logger.info(f"Waiting for UDP packets on port {video_port}...")

        extradata = None
        codec_id = CodecId.H265

        # Receive first few packets to get config
        for _ in range(10):
            packet, addr = udp_sock.recvfrom(65536)
            if len(packet) >= 24:
                # Parse header
                seq, ts, flags, payload_size = struct.unpack('<IQII', packet[:20])

                # Check if config packet
                if flags & 0x2:  # FLAG_CONFIG
                    payload = packet[24:]
                    # Extract VPS/SPS/PPS from config
                    extradata = payload
                    logger.info(f"Got config data: {len(extradata)} bytes")
                    break

        udp_sock.close()

        if extradata is None:
            logger.warning("No config data received, using None")
            extradata = b''

        # Now start the decoder process
        logger.info("Starting decoder process...")

        manager = DecoderProcessManager(
            video_port=video_port,
            codec_id=codec_id,
            width=width,
            height=height,
            extradata=extradata,
            hw_accel=True
        )

        shm_info = manager.get_shm_info()
        logger.info(f"SHM: {shm_info['name']}, size={shm_info['size']/1024/1024:.1f}MB")

        manager.start()

        # Wait for decoder ready
        from scrcpy_py_ddlx.core.ipc.control_channel import ControlMessageType
        control = manager.get_control_channel()

        start_time = time.time()
        ready = False
        while time.time() - start_time < 5.0:
            msg = control.recv_from_decoder(timeout=0.1)
            if msg and msg.type == ControlMessageType.DECODER_READY:
                logger.info(f"Decoder ready: {msg.data}")
                ready = True
                break

        if not ready:
            logger.error("Decoder did not become ready")
            manager.stop()
            return

        # Create SHM reader
        from scrcpy_py_ddlx.core.player.video.shm_frame_source import SHMFrameSource
        frame_source = SHMFrameSource(
            shm_name=shm_info['name'],
            shm_size=shm_info['size'],
            max_width=shm_info['max_width'],
            max_height=shm_info['max_height']
        )

        # Main loop: read frames and measure latency
        logger.info("Starting frame read loop...")

        frame_count = 0
        latency_samples = []
        test_end = time.time() + duration

        while time.time() < test_end and manager.is_running():
            result = frame_source.consume()
            if result:
                frame_data, metadata = result
                frame_count += 1

                # Calculate latency
                if metadata.get('udp_recv_time', 0) > 0:
                    latency = (time.time() - metadata['udp_recv_time']) * 1000
                    latency_samples.append(latency)

                    if frame_count % 30 == 0:
                        avg_lat = sum(latency_samples[-30:]) / min(30, len(latency_samples))
                        logger.info(f"Frame #{frame_count}, latency={latency:.0f}ms, avg={avg_lat:.0f}ms")

            time.sleep(0.001)  # 1ms polling

        # Calculate statistics
        if latency_samples:
            avg_latency = sum(latency_samples) / len(latency_samples)
            min_latency = min(latency_samples)
            max_latency = max(latency_samples)
            sorted_lat = sorted(latency_samples)
            p50 = sorted_lat[len(sorted_lat) // 2]
            p95 = sorted_lat[int(len(sorted_lat) * 0.95)]

            logger.info("=" * 60)
            logger.info("LATENCY RESULTS")
            logger.info("=" * 60)
            logger.info(f"Frames decoded: {frame_count}")
            logger.info(f"Samples: {len(latency_samples)}")
            logger.info(f"Average: {avg_latency:.1f}ms")
            logger.info(f"Min: {min_latency:.1f}ms")
            logger.info(f"Max: {max_latency:.1f}ms")
            logger.info(f"P50: {p50:.1f}ms")
            logger.info(f"P95: {p95:.1f}ms")
            logger.info("=" * 60)

            # Compare with baseline
            baseline = 334  # Single-process with hevc_cuvid
            improvement = ((baseline - avg_latency) / baseline) * 100
            logger.info(f"Baseline (single-process): {baseline}ms")
            logger.info(f"Improvement: {improvement:.1f}%")

        # Cleanup
        logger.info("Stopping...")
        manager.stop()
        frame_source.close()
        control_sock.close()

        logger.info("Test completed")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description='Multi-Process Decoder Test')
    parser.add_argument('--ip', required=True, help='Device IP address')
    parser.add_argument('--video-port', type=int, default=27185, help='UDP video port')
    parser.add_argument('--control-port', type=int, default=27184, help='TCP control port')
    parser.add_argument('--duration', type=int, default=30, help='Test duration in seconds')

    args = parser.parse_args()

    run_multiprocess_test(
        device_ip=args.ip,
        video_port=args.video_port,
        control_port=args.control_port,
        duration=args.duration
    )


if __name__ == '__main__':
    main()
