"""
File Transfer Stress Test

压力测试：
1. 并发请求
2. 连续传输
3. 边界条件
4. 稳定性测试
"""

import requests
import json
import time
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

MCP_URL = "http://127.0.0.1:3359/mcp"

def call_tool(name: str, arguments: dict, timeout: int = 60) -> dict:
    """调用 MCP 工具"""
    payload = {
        "jsonrpc": "2.0",
        "id": int(time.time() * 1000),
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments}
    }
    resp = requests.post(MCP_URL, json=payload, timeout=timeout)
    result = resp.json()
    if "result" in result and "content" in result["result"]:
        return json.loads(result["result"]["content"][0]["text"])
    return result


class StressTest:
    """压力测试"""

    def test_concurrent_list_dir(self, count: int = 10):
        """并发列出目录"""
        print(f"\n--- Concurrent list_dir x{count} ---")

        def list_dir_task(i):
            start = time.time()
            result = call_tool("list_dir", {"path": "/sdcard"})
            elapsed = time.time() - start
            return i, result.get("success", False), elapsed

        with ThreadPoolExecutor(max_workers=count) as executor:
            futures = [executor.submit(list_dir_task, i) for i in range(count)]
            results = [f.result() for f in as_completed(futures)]

        success = sum(1 for _, s, _ in results if s)
        avg_time = sum(t for _, _, t in results) / len(results)
        print(f"  Success: {success}/{count}")
        print(f"  Avg time: {avg_time:.3f}s")
        return success == count

    def test_sequential_transfers(self, count: int = 5):
        """连续传输多个文件"""
        print(f"\n--- Sequential transfers x{count} ---")

        success = 0
        for i in range(count):
            local_file = f"test_seq_{i}.txt"
            device_file = f"/sdcard/test_seq_{i}.txt"

            try:
                # 创建文件
                with open(local_file, "w") as f:
                    f.write(f"Test file {i}\n" * 100)

                # 上传
                result = call_tool("push_file", {
                    "local_path": local_file,
                    "device_path": device_file
                })
                if not result.get("success"):
                    print(f"  [{i}] push failed")
                    continue

                # 下载
                result = call_tool("pull_file", {
                    "device_path": device_file,
                    "local_path": f"download_{local_file}"
                })
                if not result.get("success"):
                    print(f"  [{i}] pull failed")
                    continue

                # 删除
                call_tool("delete_file", {"device_path": device_file})
                success += 1

            finally:
                for f in [local_file, f"download_{local_file}"]:
                    if os.path.exists(f):
                        os.remove(f)

        print(f"  Success: {success}/{count}")
        return success == count

    def test_large_file_stability(self, size_mb: int = 50, iterations: int = 3):
        """大文件稳定性测试"""
        print(f"\n--- Large file stability ({size_mb}MB x {iterations}) ---")

        size = size_mb * 1024 * 1024
        success = 0

        for i in range(iterations):
            local_file = f"test_stress_{size_mb}mb.bin"
            device_file = f"/sdcard/{local_file}"

            try:
                # 创建文件
                with open(local_file, "wb") as f:
                    f.write(os.urandom(size))

                # 上传
                start = time.time()
                result = call_tool("push_file", {
                    "local_path": local_file,
                    "device_path": device_file
                }, timeout=300)
                push_time = time.time() - start

                if result.get("success"):
                    speed = size / push_time / 1024 / 1024
                    print(f"  [{i+1}] push: {push_time:.1f}s, {speed:.2f} MB/s")
                    success += 1
                else:
                    print(f"  [{i+1}] push failed: {result.get('error')}")

                # 清理
                call_tool("delete_file", {"device_path": device_file})

            finally:
                if os.path.exists(local_file):
                    os.remove(local_file)

        print(f"  Success: {success}/{iterations}")
        return success == iterations

    def test_boundary_file_sizes(self):
        """边界文件大小测试"""
        print(f"\n--- Boundary file sizes ---")

        # 测试不同大小
        sizes = [
            (1, "1 byte"),
            (1023, "1KB - 1"),
            (1024, "1KB"),
            (1025, "1KB + 1"),
            (64 * 1024 - 1, "64KB - 1"),
            (64 * 1024, "64KB (chunk size)"),
            (64 * 1024 + 1, "64KB + 1"),
            (128 * 1024, "128KB"),
            (1024 * 1024, "1MB"),
        ]

        success = 0
        for size, desc in sizes:
            local_file = f"test_boundary.bin"
            device_file = f"/sdcard/test_boundary.bin"

            try:
                with open(local_file, "wb") as f:
                    f.write(b"X" * size)

                result = call_tool("push_file", {
                    "local_path": local_file,
                    "device_path": device_file
                })

                if result.get("success"):
                    print(f"  [{desc}] OK")
                    success += 1
                else:
                    print(f"  [{desc}] FAILED")

                call_tool("delete_file", {"device_path": device_file})

            finally:
                if os.path.exists(local_file):
                    os.remove(local_file)

        print(f"  Success: {success}/{len(sizes)}")
        return success == len(sizes)

    def test_special_filenames(self):
        """特殊文件名测试"""
        print(f"\n--- Special filenames ---")

        # 注意：Android 文件系统限制
        test_names = [
            "test_with_underscore.txt",
            "test-with-dash.txt",
            "test.with.dots.txt",
            "test中文.txt",  # 中文
            "test space.txt",  # 空格
        ]

        success = 0
        for name in test_names:
            local_file = name
            device_file = f"/sdcard/{name}"

            try:
                with open(local_file, "w") as f:
                    f.write("test content")

                result = call_tool("push_file", {
                    "local_path": local_file,
                    "device_path": device_file
                })

                if result.get("success"):
                    print(f"  [{name}] OK")
                    success += 1
                else:
                    print(f"  [{name}] FAILED: {result.get('error')}")

                call_tool("delete_file", {"device_path": device_file})

            except Exception as e:
                print(f"  [{name}] ERROR: {e}")
            finally:
                if os.path.exists(local_file):
                    os.remove(local_file)

        print(f"  Success: {success}/{len(test_names)}")
        return success == len(test_names)


def run_stress_tests():
    """运行压力测试"""
    print("=" * 60)
    print("File Transfer Stress Test")
    print("=" * 60)

    tester = StressTest()
    results = []

    tests = [
        ("concurrent_list_dir", lambda: tester.test_concurrent_list_dir(10)),
        ("sequential_transfers", lambda: tester.test_sequential_transfers(5)),
        ("boundary_file_sizes", lambda: tester.test_boundary_file_sizes()),
        ("special_filenames", lambda: tester.test_special_filenames()),
        # 大文件测试可选
        # ("large_file_stability", lambda: tester.test_large_file_stability(50, 3)),
    ]

    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("Summary:")
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name}: {status}")
    print("=" * 60)

    passed = sum(1 for _, p in results if p)
    print(f"Total: {passed}/{len(results)} passed")


if __name__ == "__main__":
    run_stress_tests()
