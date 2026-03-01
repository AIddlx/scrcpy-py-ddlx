#!/usr/bin/env python3
"""
Debug script for multi-process decoder UV data issue.
Run this script to capture decoder process stderr output.
"""
import subprocess
import sys
import os

# Set environment to capture all output
env = os.environ.copy()
env['PYTHONUNBUFFERED'] = '1'

# Run the main client with multiprocess mode
cmd = [
    sys.executable,
    '-m', 'scrcpy_py_ddlx',
    '--multiprocess',
    '--network', 'direct',
    '--log-level', 'DEBUG',
]

print(f"Running: {' '.join(cmd)}")
print("=" * 60)
print("Watch for [DECODER_RAW] and [DECODER_PROC] lines in stderr")
print("These will show the UV data distribution at the decoder source")
print("=" * 60)

# Run with merged stdout/stderr to capture everything
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,  # Merge stderr to stdout
    text=True,
    bufsize=1,  # Line buffered
    env=env
)

# Print output in real-time
try:
    for line in process.stdout:
        print(line, end='')
        # Highlight decoder diagnostic lines
        if '[DECODER_RAW]' in line or '[DECODER_PROC]' in line:
            sys.stdout.write('\033[93m' + line + '\033[0m')  # Yellow highlight
except KeyboardInterrupt:
    print("\nInterrupted by user")
    process.terminate()
    process.wait()
