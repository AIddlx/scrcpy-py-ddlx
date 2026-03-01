"""
File Transfer Protocol Test

测试文件传输协议的各个层面：
1. MCP HTTP 接口
2. TCP 文件通道
3. 帧格式解析
4. 大文件传输
5. 错误处理
"""

import requests
import json
import time
import os
import tempfile
from pathlib import Path

# MCP 端点
MCP_URL = "http://127.0.0.1:3359/mcp"

def call_tool(name: str, arguments: dict) -> dict:
    """调用 MCP 工具"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": name,
            "arguments": arguments
        }
    }
    resp = requests.post(MCP_URL, json=payload, timeout=60)
    result = resp.json()
    if "result" in result and "content" in result["result"]:
        text = result["result"]["content"][0]["text"]
        return json.loads(text)
    return result


class TestBasicOperations:
    """基本操作测试"""

    def test_list_dir(self):
        """测试列出目录"""
        result = call_tool("list_dir", {"path": "/sdcard"})
        assert result.get("success"), f"list_dir failed: {result}"
        assert "entries" in result
        assert "count" in result
        print(f"[PASS] list_dir: {result['count']} entries, mode={result.get('mode')}")

    def test_file_stat_exists(self):
        """测试获取存在的文件信息"""
        result = call_tool("file_stat", {"device_path": "/sdcard/test_adb.png"})
        assert result.get("success"), f"file_stat failed: {result}"
        assert result.get("exists"), "File should exist"
        print(f"[PASS] file_stat: exists={result['exists']}, size={result.get('size')}")

    def test_file_stat_not_exists(self):
        """测试获取不存在的文件信息"""
        result = call_tool("file_stat", {"device_path": "/sdcard/nonexistent_file_xyz.abc"})
        assert result.get("success"), f"file_stat failed: {result}"
        assert not result.get("exists"), "File should not exist"
        print(f"[PASS] file_stat (not exists): exists={result['exists']}")


class TestDirectoryOperations:
    """目录操作测试"""

    def test_create_and_delete_directory(self):
        """测试创建和删除目录"""
        test_dir = "/sdcard/test_protocol_dir"

        # 创建目录
        result = call_tool("make_dir", {"device_path": test_dir})
        assert result.get("success"), f"make_dir failed: {result}"
        print(f"[PASS] make_dir: {test_dir}")

        # 验证目录存在
        result = call_tool("file_stat", {"device_path": test_dir})
        assert result.get("exists"), "Directory should exist"
        assert result.get("type") == "directory"
        print(f"[PASS] directory exists")

        # 删除目录
        result = call_tool("delete_file", {"device_path": test_dir})
        assert result.get("success"), f"delete_file failed: {result}"
        print(f"[PASS] delete_dir: {test_dir}")


class TestFileTransfer:
    """文件传输测试"""

    def test_small_file_push_pull(self):
        """测试小文件上传下载"""
        test_content = b"Hello, this is a test file for protocol testing.\n" * 10
        local_file = "test_upload_protocol.txt"
        device_file = "/sdcard/test_upload_protocol.txt"
        download_file = "test_download_protocol.txt"

        try:
            # 创建本地文件
            with open(local_file, "wb") as f:
                f.write(test_content)

            # 上传
            result = call_tool("push_file", {
                "local_path": local_file,
                "device_path": device_file
            })
            assert result.get("success"), f"push_file failed: {result}"
            assert result.get("size") == len(test_content)
            print(f"[PASS] push_file: {result['size']} bytes, mode={result.get('mode')}")

            # 下载
            result = call_tool("pull_file", {
                "device_path": device_file,
                "local_path": download_file
            })
            assert result.get("success"), f"pull_file failed: {result}"
            print(f"[PASS] pull_file: {result['size']} bytes")

            # 验证内容
            with open(download_file, "rb") as f:
                downloaded = f.read()
            assert downloaded == test_content, "Content mismatch!"
            print(f"[PASS] content verified")

        finally:
            # 清理
            for f in [local_file, download_file]:
                if os.path.exists(f):
                    os.remove(f)
            call_tool("delete_file", {"device_path": device_file})


class TestLargeFile:
    """大文件传输测试"""

    def test_1mb_file(self):
        """测试 1MB 文件"""
        self._test_file_size(1 * 1024 * 1024)

    def test_10mb_file(self):
        """测试 10MB 文件"""
        self._test_file_size(10 * 1024 * 1024)

    def _test_file_size(self, size: int):
        """测试指定大小的文件"""
        local_file = f"test_{size//1024//1024}mb.bin"
        device_file = f"/sdcard/{local_file}"
        download_file = f"download_{local_file}"

        try:
            # 创建随机数据文件
            print(f"Creating {size//1024//1024}MB test file...")
            with open(local_file, "wb") as f:
                remaining = size
                chunk_size = 64 * 1024
                while remaining > 0:
                    write_size = min(chunk_size, remaining)
                    f.write(os.urandom(write_size))
                    remaining -= write_size

            # 上传并计时
            start = time.time()
            result = call_tool("push_file", {
                "local_path": local_file,
                "device_path": device_file
            })
            push_time = time.time() - start
            assert result.get("success"), f"push_file failed: {result}"
            speed = size / push_time / 1024 / 1024
            print(f"[PASS] push {size//1024//1024}MB: {push_time:.2f}s, {speed:.2f} MB/s")

            # 下载并计时
            start = time.time()
            result = call_tool("pull_file", {
                "device_path": device_file,
                "local_path": download_file
            })
            pull_time = time.time() - start
            assert result.get("success"), f"pull_file failed: {result}"
            speed = size / pull_time / 1024 / 1024
            print(f"[PASS] pull {size//1024//1024}MB: {pull_time:.2f}s, {speed:.2f} MB/s")

        finally:
            for f in [local_file, download_file]:
                if os.path.exists(f):
                    os.remove(f)
            call_tool("delete_file", {"device_path": device_file})


class TestModeDetection:
    """模式检测测试"""

    def test_mode_field(self):
        """测试返回的 mode 字段"""
        result = call_tool("list_dir", {"path": "/sdcard"})
        mode = result.get("mode")
        assert mode in ["adb", "network"], f"Invalid mode: {mode}"
        print(f"[PASS] mode detection: {mode}")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("File Transfer Protocol Test")
    print("=" * 60)

    test_classes = [
        TestBasicOperations,
        TestDirectoryOperations,
        TestFileTransfer,
        TestModeDetection,
        TestLargeFile,
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        print(f"\n--- {test_class.__name__} ---")
        instance = test_class()
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                try:
                    method = getattr(instance, method_name)
                    method()
                    passed += 1
                except AssertionError as e:
                    print(f"[FAIL] {method_name}: {e}")
                    failed += 1
                except Exception as e:
                    print(f"[ERROR] {method_name}: {e}")
                    failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
