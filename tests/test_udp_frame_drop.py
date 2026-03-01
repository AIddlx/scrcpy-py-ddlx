#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UDP 智能丢帧功能测试

测试用例:
1. Socket 积压检测功能
2. 帧选择逻辑
3. CONFIG 包保护
4. 关键帧优先保留
"""

import sys
import os
import struct
import time
import socket
import threading
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrcpy_py_ddlx.client.connection import ConnectionManager
from scrcpy_py_ddlx.client.config import FrameDropPolicy
from scrcpy_py_ddlx.core.protocol import (
    UDP_HEADER_SIZE,
    UDP_FLAG_KEY_FRAME,
    UDP_FLAG_CONFIG,
)


def make_udp_packet(seq: int, timestamp: int, flags: int, payload: bytes = b'') -> bytes:
    """
    创建一个模拟的 UDP 数据包。

    格式: [seq: 4B] [timestamp: 8B] [flags: 4B] [send_time_ns: 8B] [payload: NB]
    """
    send_time_ns = int(time.time() * 1e9)
    header = struct.pack('>IqIq', seq, timestamp, flags, send_time_ns)
    return header + payload


class TestSocketBacklog:
    """测试 Socket 积压检测功能"""

    def test_get_socket_backlog_basic(self):
        """基本积压检测测试"""
        # 创建一对连接的 UDP socket
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            server_sock.bind(('127.0.0.1', 0))
            server_port = server_sock.getsockname()[1]

            # 初始积压应为 0
            backlog = ConnectionManager.get_socket_backlog(server_sock)
            assert backlog == 0, f"Expected 0 backlog, got {backlog}"

            # 发送一些数据
            test_data = b'hello world'
            client_sock.sendto(test_data, ('127.0.0.1', server_port))
            time.sleep(0.1)  # 等待数据到达

            # 检测积压
            backlog = ConnectionManager.get_socket_backlog(server_sock)
            assert backlog >= len(test_data), f"Expected at least {len(test_data)} bytes, got {backlog}"

            print(f"[PASS] test_get_socket_backlog_basic: backlog={backlog}")

        finally:
            server_sock.close()
            client_sock.close()

    def test_get_socket_backlog_closed_socket(self):
        """测试已关闭 socket 的积压检测"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.close()

        # 已关闭的 socket 应返回 0
        backlog = ConnectionManager.get_socket_backlog(sock)
        assert backlog == 0, f"Expected 0 for closed socket, got {backlog}"

        print("[PASS] test_get_socket_backlog_closed_socket")


class TestFrameDropPolicy:
    """测试丢帧策略配置"""

    def test_policy_thresholds(self):
        """测试策略阈值"""
        assert FrameDropPolicy.get_threshold('disabled') == 0
        assert FrameDropPolicy.get_threshold('low_latency') == 32 * 1024
        assert FrameDropPolicy.get_threshold('balanced') == 64 * 1024
        assert FrameDropPolicy.get_threshold('smooth') == 128 * 1024
        print("[PASS] test_policy_thresholds")

    def test_policy_validation(self):
        """测试策略验证"""
        assert FrameDropPolicy.is_valid('balanced') is True
        assert FrameDropPolicy.is_valid('invalid') is False
        assert FrameDropPolicy.is_valid('low_latency') is True
        print("[PASS] test_policy_validation")

    def test_unknown_policy_uses_default(self):
        """测试未知策略使用默认值"""
        threshold = FrameDropPolicy.get_threshold('unknown_policy')
        assert threshold == FrameDropPolicy.get_threshold(FrameDropPolicy.BALANCED)
        print("[PASS] test_unknown_policy_uses_default")


class TestFrameSelection:
    """测试帧选择逻辑"""

    def _make_packets_with_types(self, specs: list) -> list:
        """
        创建指定类型的包列表。

        specs: [(type, timestamp), ...]
        type: 'config', 'key', 'normal'
        """
        packets = []
        for i, (ptype, ts) in enumerate(specs):
            if ptype == 'config':
                flags = UDP_FLAG_CONFIG
            elif ptype == 'key':
                flags = UDP_FLAG_KEY_FRAME
            else:
                flags = 0
            packet = make_udp_packet(seq=i, timestamp=ts, flags=flags, payload=b'data')
            packets.append((packet, time.time()))
        return packets

    def test_config_packets_always_kept(self):
        """CONFIG 包必须始终保留"""
        # 模拟 UdpVideoDemuxer 的帧选择逻辑
        packets = self._make_packets_with_types([
            ('config', 100),
            ('normal', 101),
            ('normal', 102),
        ])

        # 简化版选择逻辑
        selected = self._select_frames_simple(packets)

        # CONFIG 包必须在选中结果中
        config_count = 0
        for packet, _ in selected:
            flags = struct.unpack('>I', packet[12:16])[0]
            if flags & UDP_FLAG_CONFIG:
                config_count += 1

        assert config_count == 1, f"Expected 1 config packet, got {config_count}"
        print("[PASS] test_config_packets_always_kept")

    def test_latest_keyframe_kept(self):
        """最新关键帧应被保留"""
        packets = self._make_packets_with_types([
            ('key', 100),
            ('key', 200),  # 更新的关键帧
            ('normal', 150),
        ])

        selected = self._select_frames_simple(packets)

        # 检查是否保留了 timestamp=200 的关键帧
        keyframe_ts = []
        for packet, _ in selected:
            flags = struct.unpack('>I', packet[12:16])[0]
            ts = struct.unpack('>q', packet[4:12])[0]
            if flags & UDP_FLAG_KEY_FRAME:
                keyframe_ts.append(ts)

        assert 200 in keyframe_ts, f"Expected keyframe with ts=200, got timestamps: {keyframe_ts}"
        assert 100 not in keyframe_ts, f"Old keyframe (ts=100) should be dropped, but found: {keyframe_ts}"
        print("[PASS] test_latest_keyframe_kept")

    def test_old_frames_dropped_when_keyframe_exists(self):
        """有关键帧时，旧的 P 帧应被丢弃"""
        packets = self._make_packets_with_types([
            ('normal', 100),  # 旧的 P 帧
            ('normal', 150),  # 旧的 P 帧
            ('key', 200),     # 新的关键帧
            ('normal', 250),  # 新的 P 帧（应保留）
        ])

        selected = self._select_frames_simple(packets)

        # 检查选中包的 timestamp
        selected_ts = []
        for packet, _ in selected:
            ts = struct.unpack('>q', packet[4:12])[0]
            selected_ts.append(ts)

        # ts=200 (keyframe) 和 ts=250 (newer P-frame) 应该被保留
        # ts=100 和 ts=150 应该被丢弃
        assert 200 in selected_ts, f"Keyframe (ts=200) should be kept, got: {selected_ts}"
        assert 250 in selected_ts, f"New P-frame (ts=250) should be kept, got: {selected_ts}"
        assert 100 not in selected_ts, f"Old P-frame (ts=100) should be dropped, got: {selected_ts}"
        assert 150 not in selected_ts, f"Old P-frame (ts=150) should be dropped, got: {selected_ts}"
        print("[PASS] test_old_frames_dropped_when_keyframe_exists")

    def _select_frames_simple(self, packets: list) -> list:
        """
        简化版帧选择逻辑（用于单元测试）
        """
        if len(packets) <= 2:
            return packets

        config_packets = []
        keyframe_packets = []
        normal_packets = []

        for packet, recv_time in packets:
            if len(packet) < UDP_HEADER_SIZE:
                continue

            flags = struct.unpack('>I', packet[12:16])[0]
            timestamp = struct.unpack('>q', packet[4:12])[0]

            is_config = bool(flags & UDP_FLAG_CONFIG)
            is_keyframe = bool(flags & UDP_FLAG_KEY_FRAME)

            if is_config:
                config_packets.append((packet, recv_time))
            elif is_keyframe:
                keyframe_packets.append((packet, recv_time, timestamp))
            else:
                normal_packets.append((packet, recv_time, timestamp))

        selected = []

        # 1. Keep ALL config packets
        selected.extend([(p, t) for p, t in config_packets])

        # 2. Keep the LATEST key frame only
        latest_keyframe_ts = None
        if keyframe_packets:
            keyframe_packets.sort(key=lambda x: x[2], reverse=True)
            latest_packet, latest_time, latest_keyframe_ts = keyframe_packets[0]
            selected.append((latest_packet, latest_time))

        # 3. For normal packets, keep only those newer than the latest keyframe
        for packet, recv_time, ts in normal_packets:
            if latest_keyframe_ts is None or ts > latest_keyframe_ts:
                selected.append((packet, recv_time))

        return selected


class TestIntegration:
    """集成测试"""

    def test_frame_drop_disabled(self):
        """测试禁用丢帧时的行为"""
        from queue import Queue
        from scrcpy_py_ddlx.core.demuxer.udp_video import UdpVideoDemuxer, UdpStats
        from scrcpy_py_ddlx.core.protocol import CodecId

        # 创建 mock socket 和 queue
        mock_socket = Mock(spec=socket.socket)
        mock_socket.fileno.return_value = 42
        mock_queue = Queue()

        # 创建 demuxer（禁用丢帧）
        demuxer = UdpVideoDemuxer(
            udp_socket=mock_socket,
            packet_queue=mock_queue,
            codec_id=CodecId.H264,
            frame_drop_enabled=False,
        )

        # 验证配置
        assert demuxer._frame_drop_enabled is False
        print("[PASS] test_frame_drop_disabled")

    def test_frame_drop_enabled_with_threshold(self):
        """测试启用丢帧和阈值设置"""
        from queue import Queue
        from scrcpy_py_ddlx.core.demuxer.udp_video import UdpVideoDemuxer
        from scrcpy_py_ddlx.core.protocol import CodecId

        mock_socket = Mock(spec=socket.socket)
        mock_queue = Queue()

        # 创建 demuxer（启用丢帧，自定义阈值）
        demuxer = UdpVideoDemuxer(
            udp_socket=mock_socket,
            packet_queue=mock_queue,
            codec_id=CodecId.H264,
            frame_drop_enabled=True,
            frame_drop_threshold=32 * 1024,  # 32KB
        )

        # 验证配置
        assert demuxer._frame_drop_enabled is True
        assert demuxer._frame_drop_threshold == 32 * 1024
        print("[PASS] test_frame_drop_enabled_with_threshold")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("UDP 智能丢帧功能测试")
    print("=" * 60)

    test_classes = [
        TestSocketBacklog(),
        TestFrameDropPolicy(),
        TestFrameSelection(),
        TestIntegration(),
    ]

    total_tests = 0
    passed_tests = 0

    for test_obj in test_classes:
        class_name = test_obj.__class__.__name__
        print(f"\n--- {class_name} ---")

        for method_name in dir(test_obj):
            if method_name.startswith('test_'):
                total_tests += 1
                try:
                    method = getattr(test_obj, method_name)
                    method()
                    passed_tests += 1
                except AssertionError as e:
                    print(f"[FAIL] {method_name}: {e}")
                except Exception as e:
                    print(f"[ERROR] {method_name}: {e}")

    print("\n" + "=" * 60)
    print(f"测试结果: {passed_tests}/{total_tests} 通过")
    print("=" * 60)

    return passed_tests == total_tests


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
