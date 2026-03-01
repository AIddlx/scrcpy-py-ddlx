"""
Test script for file transfer functionality.

Usage:
    python tests/test_file_channel.py
"""
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scrcpy_py_ddlx.mcp_server import ScrcpyMCPServer


def test_file_transfer():
    """Test file transfer functionality."""
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Create MCP server
    server = ScrcpyMCPServer(
        log_level=logging.DEBUG,
        enable_console_log=True
    )

    print("=" * 60)
    print("File Transfer Test")
    print("=" * 60)

    # Step 1: Connect
    print("\n1. Connecting to device...")
    result = server.connect()
    print(f"   Result: {result}")

    if not result.get("success"):
        print("   ERROR: Connection failed")
        return False

    device_name = result.get("device_name", "Unknown")
    print(f"   Connected to: {device_name}")

    # Step 2: Open file channel
    print("\n2. Opening file channel...")
    result = server.open_file_channel()
    print(f"   Result: {result}")

    if not result.get("success"):
        print("   ERROR: Failed to open file channel")
        server.disconnect()
        return False

    # Step 3: List directory
    print("\n3. Listing /sdcard directory...")
    result = server.list_dir("/sdcard")
    print(f"   Result: success={result.get('success')}")

    if result.get("success"):
        entries = result.get("entries", [])
        print(f"   Found {len(entries)} entries:")
        for entry in entries[:10]:  # Show first 10
            print(f"     - {entry['type']}: {entry['name']} ({entry['size']} bytes)")
        if len(entries) > 10:
            print(f"     ... and {len(entries) - 10} more")
    else:
        print(f"   ERROR: {result.get('error')}")

    # Step 4: Get file info
    print("\n4. Getting file info for /sdcard...")
    result = server.file_stat("/sdcard")
    print(f"   Result: {result}")

    # Step 5: Create a test directory
    print("\n5. Creating test directory /sdcard/test_file_channel...")
    result = server.make_dir("/sdcard/test_file_channel")
    print(f"   Result: {result}")

    # Step 6: Upload a test file
    test_file = project_root / "README.md"
    if test_file.exists():
        print(f"\n6. Uploading {test_file.name} to device...")
        result = server.push_file(
            str(test_file),
            "/sdcard/test_file_channel/README.md"
        )
        print(f"   Result: {result}")
    else:
        print("\n6. Skipping upload test (README.md not found)")

    # Step 7: List the test directory
    print("\n7. Listing /sdcard/test_file_channel...")
    result = server.list_dir("/sdcard/test_file_channel")
    print(f"   Result: {result}")

    # Step 8: Download the file back
    print("\n8. Downloading file back...")
    download_path = str(project_root / "test_download.txt")
    result = server.pull_file(
        "/sdcard/test_file_channel/README.md",
        download_path
    )
    print(f"   Result: {result}")

    if result.get("success"):
        # Check file size
        downloaded = Path(download_path)
        if downloaded.exists():
            print(f"   Downloaded file size: {downloaded.stat().st_size} bytes")
            # Clean up
            downloaded.unlink()

    # Step 9: Clean up - delete test directory
    print("\n9. Cleaning up - deleting /sdcard/test_file_channel...")
    result = server.delete_file("/sdcard/test_file_channel")
    print(f"   Result: {result}")

    # Step 10: Disconnect
    print("\n10. Disconnecting...")
    result = server.disconnect()
    print(f"   Result: {result}")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        success = test_file_transfer()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
