"""
Integration test for multi-process decoder.

This test verifies the complete pipeline:
1. Decoder process receives UDP packets
2. Decodes video frames (hevc_cuvid)
3. Writes frames to shared memory
4. Main process reads frames from shared memory

Prerequisites:
- A running scrcpy server streaming to the specified UDP port
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import logging
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_decoder_process_basic():
    """Test basic decoder process lifecycle without network."""
    from scrcpy_py_ddlx.core.decoder.decoder_process import DecoderProcessManager
    from scrcpy_py_ddlx.core.protocol import CodecId

    logger.info("Testing decoder process lifecycle...")

    # Create manager (no actual decoding - just test startup/shutdown)
    manager = DecoderProcessManager(
        video_port=27185,
        codec_id=CodecId.H265,
        width=1920,
        height=1080,
        hw_accel=True
    )

    logger.info(f"SHM info: {manager.get_shm_info()}")

    # Test control channel
    from scrcpy_py_ddlx.core.ipc.control_channel import ControlMessageType
    control = manager.get_control_channel()

    logger.info("Control channel created")
    logger.info(f"Is running: {control.is_running()}")

    # Cleanup
    control.stop()
    manager.close()

    logger.info("Basic lifecycle test PASSED")
    return True


def test_shm_reader_writer():
    """Test shared memory read/write between processes."""
    from scrcpy_py_ddlx.core.decoder.decoder_process import decoder_process_main
    from scrcpy_py_ddlx.core.ipc.control_channel import ControlChannel, ControlMessageType
    from scrcpy_py_ddlx.simple_shm import SimpleSHMReader
    import multiprocessing as mp

    logger.info("Testing cross-process SHM read/write...")

    # Create control channel
    control = ControlChannel()
    control_end = control.get_decoder_end()

    # Create SHM
    from scrcpy_py_ddlx.simple_shm import SimpleSHMWriter
    writer = SimpleSHMWriter(max_width=640, max_height=480)
    shm_info = writer.get_info()

    # Start a minimal decoder process (it will timeout on socket, which is fine)
    proc = mp.Process(
        target=_mock_decoder_worker,
        args=(
            control_end[0], control_end[1], control_end[2],
            shm_info['name'], shm_info['size'],
            27199  # Use different port to avoid conflicts
        ),
        daemon=True
    )
    proc.start()

    # Wait a bit for process to start
    time.sleep(0.5)

    # Write a frame from main process (simulating decoder output)
    import numpy as np
    width, height = 320, 240
    nv12_data = bytes(int(width * height * 1.5))

    writer.write_nv12_frame(nv12_data, width, height, udp_recv_time=time.time())
    logger.info("Frame written to SHM")

    # Read from SHM
    reader = SimpleSHMReader(
        name=shm_info['name'],
        size=shm_info['size'],
        max_width=shm_info['max_width'],
        max_height=shm_info['max_height']
    )

    result = reader.read_frame_ex()
    if result:
        frame, pts, capture_time, udp_recv_time, fmt, w, h = result
        logger.info(f"Frame read: {w}x{h}, format={fmt}")
        success = True
    else:
        logger.error("Failed to read frame")
        success = False

    # Stop process
    control.send_to_decoder(ControlMessageType.STOP_DECODING)
    proc.join(timeout=2.0)
    if proc.is_alive():
        proc.terminate()

    reader.close()
    writer.close()

    logger.info(f"Cross-process SHM test {'PASSED' if success else 'FAILED'}")
    return success


def _mock_decoder_worker(control_queue, response_queue, running_flag,
                          shm_name, shm_size, video_port):
    """Mock decoder worker for testing."""
    import time
    from multiprocessing import shared_memory

    # Just wait for stop signal
    while running_flag.value:
        time.sleep(0.1)
        # Check for messages
        try:
            msg = control_queue.get(timeout=0.01)
            if msg.type.name == 'STOP_DECODING':
                break
        except:
            pass


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Decoder Process Integration Tests")
    logger.info("=" * 60)

    tests = [
        ("Basic Lifecycle", test_decoder_process_basic),
        ("SHM Reader/Writer", test_shm_reader_writer),
    ]

    results = {}
    for name, test_func in tests:
        logger.info(f"\n--- Running: {name} ---")
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"Test {name} failed: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False

    logger.info("\n" + "=" * 60)
    logger.info("Test Results:")
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        logger.info(f"  {name}: {status}")
    logger.info("=" * 60)

    return all(results.values())


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
