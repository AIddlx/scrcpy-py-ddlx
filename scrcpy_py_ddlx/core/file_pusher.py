"""
File pusher for transferring files to Android device via ADB.

Supports:
- APK installation (drag & drop .apk files)
- File push to /sdcard/Download/ (drag & drop other files)
"""

import logging
import os
import subprocess
import threading
from pathlib import Path
from typing import Optional, Callable
from queue import Queue
from enum import Enum

logger = logging.getLogger(__name__)

# Default push target directory on device
DEFAULT_PUSH_TARGET = "/sdcard/Download/"


class FilePusherAction(Enum):
    """File pusher action types."""
    INSTALL_APK = 0
    PUSH_FILE = 1


class FilePusher:
    """
    Handles file transfer to Android device via ADB.

    Similar to scrcpy's file_pusher.c, uses a background thread
    to process file push/install requests.
    """

    def __init__(
        self,
        device_serial: Optional[str] = None,
        push_target: str = DEFAULT_PUSH_TARGET,
        on_complete: Optional[Callable[[bool, str, str], None]] = None
    ):
        """
        Initialize file pusher.

        Args:
            device_serial: Device serial number (None for auto-select)
            push_target: Target directory for pushing files
            on_complete: Callback(completed: bool, action: str, file: str)
        """
        self._device_serial = device_serial
        self._push_target = push_target
        self._on_complete = on_complete

        self._queue: Queue = Queue()
        self._thread: Optional[threading.Thread] = None
        self._stopped = threading.Event()

    def start(self):
        """Start the file pusher thread."""
        if self._thread is not None:
            return

        self._stopped.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="FilePusher",
            daemon=True
        )
        self._thread.start()
        logger.info("File pusher thread started")

    def stop(self):
        """Stop the file pusher thread."""
        if self._thread is None:
            return

        self._stopped.set()
        self._queue.put(None)  # Wake up the thread
        self._thread.join(timeout=2.0)
        self._thread = None
        logger.info("File pusher thread stopped")

    def request(self, file_path: str) -> bool:
        """
        Request to push/install a file.

        Args:
            file_path: Path to the file on PC

        Returns:
            True if request was queued successfully
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False

        # Determine action based on file extension
        if file_path.lower().endswith('.apk'):
            action = FilePusherAction.INSTALL_APK
            action_name = "install"
        else:
            action = FilePusherAction.PUSH_FILE
            action_name = "push"

        logger.info(f"Request to {action_name} {file_path}")

        # Start thread if not running
        if self._thread is None:
            self.start()

        self._queue.put((action, file_path))
        return True

    def _run_loop(self):
        """Background thread loop for processing requests."""
        while not self._stopped.is_set():
            item = self._queue.get()

            if item is None:
                break

            action, file_path = item

            if action == FilePusherAction.INSTALL_APK:
                self._install_apk(file_path)
            else:
                self._push_file(file_path)

    def _install_apk(self, file_path: str):
        """Install an APK file via ADB."""
        logger.info(f"Installing {file_path}...")

        try:
            cmd = ["adb"]
            if self._device_serial:
                cmd.extend(["-s", self._device_serial])
            cmd.extend(["install", "-r", file_path])  # -r for replace existing

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # APK install can take a while
            )

            if result.returncode == 0:
                logger.info(f"Successfully installed: {file_path}")
                if self._on_complete:
                    self._on_complete(True, "install", file_path)
            else:
                logger.error(f"Failed to install {file_path}: {result.stderr}")
                if self._on_complete:
                    self._on_complete(False, "install", file_path)

        except subprocess.TimeoutExpired:
            logger.error(f"Install timeout: {file_path}")
            if self._on_complete:
                self._on_complete(False, "install", file_path)
        except Exception as e:
            logger.error(f"Install error: {e}")
            if self._on_complete:
                self._on_complete(False, "install", file_path)

    def _push_file(self, file_path: str):
        """Push a file to device via ADB."""
        logger.info(f"Pushing {file_path} to {self._push_target}...")

        try:
            cmd = ["adb"]
            if self._device_serial:
                cmd.extend(["-s", self._device_serial])
            cmd.extend(["push", file_path, self._push_target])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                logger.info(f"Successfully pushed {file_path} to {self._push_target}")
                if self._on_complete:
                    self._on_complete(True, "push", file_path)
            else:
                logger.error(f"Failed to push {file_path}: {result.stderr}")
                if self._on_complete:
                    self._on_complete(False, "push", file_path)

        except subprocess.TimeoutExpired:
            logger.error(f"Push timeout: {file_path}")
            if self._on_complete:
                self._on_complete(False, "push", file_path)
        except Exception as e:
            logger.error(f"Push error: {e}")
            if self._on_complete:
                self._on_complete(False, "push", file_path)

    def set_device_serial(self, serial: str):
        """Set device serial number."""
        self._device_serial = serial

    def set_push_target(self, target: str):
        """Set push target directory."""
        self._push_target = target


# Global instance
_file_pusher: Optional[FilePusher] = None


def get_file_pusher() -> FilePusher:
    """Get the global file pusher instance."""
    global _file_pusher
    if _file_pusher is None:
        _file_pusher = FilePusher()
    return _file_pusher


def init_file_pusher(
    device_serial: Optional[str] = None,
    push_target: str = DEFAULT_PUSH_TARGET,
    on_complete: Optional[Callable[[bool, str, str], None]] = None
) -> FilePusher:
    """Initialize the global file pusher."""
    global _file_pusher
    _file_pusher = FilePusher(
        device_serial=device_serial,
        push_target=push_target,
        on_complete=on_complete
    )
    return _file_pusher
