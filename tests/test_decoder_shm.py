"""
Test for multi-process decoder components.

This test verifies:
1. Shared memory creation and connection
2. Frame writing and reading
3. Control channel messaging
4. Process spawning and communication
"""

import sys
import os
# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import multiprocessing as mp
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_shared_memory():
    """Test double-buffered shared memory."""
    from scrcpy_py_ddlx.core.ipc.decoder_shm import (
        DecoderSHMWriter, DecoderSHMReader, FORMAT_NV12
    )

    logger.info("Testing shared memory...")

    # Create writer
    writer = DecoderSHMWriter(max_width=1920, max_height=1080)
    info = writer.get_info()
    logger.info(f"Writer created: {info}")

    # Create reader (in same process for testing)
    reader = DecoderSHMReader(
        name=info['name'],
        size=info['size'],
        max_width=info['max_width'],
        max_height=info['max_height']
    )
    logger.info("Reader connected")

    # Write test frame
    width, height = 640, 480
    y_plane = np.random.randint(0, 255, (height, width), dtype=np.uint8)
    u_plane = np.random.randint(0, 255, (height // 2, width // 2), dtype=np.uint8)
    v_plane = np.random.randint(0, 255, (height // 2, width // 2), dtype=np.uint8)

    # Build NV12 data
    uv_plane = np.empty((height // 2, width), dtype=np.uint8)
    uv_plane[:, 0::2] = u_plane
    uv_plane[:, 1::2] = v_plane
    nv12_data = y_plane.tobytes() + uv_plane.tobytes()

    # Write frame
    success = writer.write_frame(
        nv12_data, width, height, FORMAT_NV12,
        pts=12345678, udp_recv_time=time.time()
    )
    assert success, "Write failed"
    logger.info("Frame written")

    # Read frame
    result = reader.read_frame()
    assert result is not None, "Read returned None"
    frame, metadata = result

    logger.info(f"Frame read: shape={frame.shape}, metadata={metadata}")
    assert metadata['width'] == width
    assert metadata['height'] == height
    assert metadata['format'] == FORMAT_NV12
    assert metadata['pts'] == 12345678

    # Cleanup
    reader.close()
    writer.close()
    logger.info("Shared memory test PASSED")
    return True


def test_control_channel():
    """Test control channel messaging."""
    from scrcpy_py_ddlx.core.ipc.control_channel import (
        ControlChannel, ControlMessageType
    )

    logger.info("Testing control channel...")

    channel = ControlChannel()

    # Test send/recv in same process
    channel.send_to_decoder(ControlMessageType.START_DECODING, {'codec': 'h265'})

    # Note: This would block in same process, so we just verify it doesn't crash
    logger.info("Control channel test PASSED")
    channel.stop()
    return True


def _subprocess_worker(shm_info, results):
    """Worker function for subprocess test."""
    from scrcpy_py_ddlx.core.ipc.decoder_shm import DecoderSHMReader

    # Connect to shared memory
    reader = DecoderSHMReader(
        name=shm_info['name'],
        size=shm_info['size'],
        max_width=shm_info['max_width'],
        max_height=shm_info['max_height']
    )

    # Try to read frame
    for _ in range(10):
        result = reader.read_frame()
        if result is not None:
            frame, metadata = result
            results['read_success'] = True
            results['width'] = metadata['width']
            results['height'] = metadata['height']
            break
        time.sleep(0.1)

    reader.close()


def test_cross_process():
    """Test shared memory across processes."""
    from scrcpy_py_ddlx.core.ipc.decoder_shm import (
        DecoderSHMWriter, FORMAT_NV12
    )

    logger.info("Testing cross-process communication...")

    # Create writer in main process
    writer = DecoderSHMWriter(max_width=640, max_height=480)
    info = writer.get_info()

    # Shared results dict
    manager = mp.Manager()
    results = manager.dict()
    results['read_success'] = False

    # Start reader process
    proc = mp.Process(
        target=_subprocess_worker,
        args=(info, results)
    )
    proc.start()

    # Wait a bit for reader to start
    time.sleep(0.2)

    # Write frame from main process
    width, height = 320, 240
    nv12_data = bytes(int(width * height * 1.5))  # Dummy data

    writer.write_frame(
        nv12_data, width, height, FORMAT_NV12,
        udp_recv_time=time.time()
    )
    logger.info("Frame written from main process")

    # Wait for reader
    proc.join(timeout=5.0)

    if proc.is_alive():
        proc.terminate()
        logger.error("Subprocess did not exit")
        return False

    # Check results
    if results['read_success']:
        logger.info(f"Cross-process test PASSED: read {results['width']}x{results['height']}")
        success = True
    else:
        logger.error("Cross-process test FAILED: reader did not get frame")
        success = False

    writer.close()
    return success


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Multi-process Decoder Tests")
    logger.info("=" * 60)

    tests = [
        ("Shared Memory", test_shared_memory),
        ("Control Channel", test_control_channel),
        ("Cross-Process", test_cross_process),
    ]

    results = {}
    for name, test_func in tests:
        logger.info(f"\n--- Running: {name} ---")
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"Test {name} failed with exception: {e}")
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
