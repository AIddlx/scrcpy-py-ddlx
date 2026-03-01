"""
延迟模拟测试框架

模拟整个渲染管道，隔离问题根源。

测试场景：
1. 纯内存传递（基线）
2. DelayBuffer 延迟
3. QTimer 轮询延迟
4. SHM 跨进程延迟
5. Qt 事件循环延迟

运行方式：
    python tests/test_latency_simulation.py
"""

import time
import threading
import queue
from typing import Callable, Optional, Tuple, List
from dataclasses import dataclass, field
from collections import deque


@dataclass
class FramePacket:
    """模拟帧数据包"""
    id: int
    send_time: float  # 发送时间
    recv_time: float = 0.0  # 接收时间
    decode_time: float = 0.0  # 解码完成时间
    render_time: float = 0.0  # 渲染时间
    display_time: float = 0.0  # 显示时间
    data: bytes = field(default_factory=lambda: b'\x00' * 1024 * 100)  # 100KB 模拟帧


class DelayBufferSim:
    """模拟 DelayBuffer - 单帧缓冲"""

    def __init__(self):
        self._pending_frame: Optional[FramePacket] = None
        self._consumed = True
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)

    def push(self, frame: FramePacket) -> Tuple[bool, bool]:
        """推入帧"""
        with self._condition:
            previous_skipped = not self._consumed
            self._pending_frame = frame
            self._consumed = False
            self._condition.notify()
            return True, previous_skipped

    def consume(self) -> Optional[FramePacket]:
        """消费帧"""
        with self._condition:
            if self._consumed or self._pending_frame is None:
                return None
            frame = self._pending_frame
            self._consumed = True
            return frame


class QueueBufferSim:
    """模拟队列缓冲 - 多帧缓冲"""

    def __init__(self, maxsize: int = 3):
        self._queue = queue.Queue(maxsize=maxsize)

    def push(self, frame: FramePacket) -> bool:
        """推入帧，非阻塞"""
        try:
            self._queue.put_nowait(frame)
            return True
        except queue.Full:
            return False

    def consume(self, timeout: float = 0.001) -> Optional[FramePacket]:
        """消费帧"""
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None


class LatencyTester:
    """延迟测试器"""

    def __init__(self, name: str):
        self.name = name
        self.latencies: List[float] = []
        self.skip_count = 0
        self.total_frames = 0

    def record(self, latency_ms: float):
        self.latencies.append(latency_ms)
        self.total_frames += 1

    def record_skip(self):
        self.skip_count += 1

    def get_stats(self) -> dict:
        if not self.latencies:
            return {"name": self.name, "frames": 0, "avg_ms": 0, "max_ms": 0, "min_ms": 0, "skip_rate": 0}

        return {
            "name": self.name,
            "frames": self.total_frames,
            "avg_ms": sum(self.latencies) / len(self.latencies),
            "max_ms": max(self.latencies),
            "min_ms": min(self.latencies),
            "skip_rate": self.skip_count / max(1, self.total_frames) * 100,
            "p50_ms": sorted(self.latencies)[len(self.latencies) // 2],
            "p95_ms": sorted(self.latencies)[int(len(self.latencies) * 0.95)] if len(self.latencies) > 20 else max(self.latencies),
        }


def test_pure_memory_pass():
    """测试1: 纯内存传递（基线）"""
    print("\n" + "="*60)
    print("测试1: 纯内存传递（基线）")
    print("="*60)

    tester = LatencyTester("纯内存传递")

    def producer():
        for i in range(100):
            frame = FramePacket(id=i, send_time=time.perf_counter())
            # 直接传递，无缓冲
            frame.recv_time = time.perf_counter()
            latency_ms = (frame.recv_time - frame.send_time) * 1000
            tester.record(latency_ms)

    producer()

    stats = tester.get_stats()
    print(f"帧数: {stats['frames']}")
    print(f"平均延迟: {stats['avg_ms']:.3f} ms")
    print(f"最大延迟: {stats['max_ms']:.3f} ms")
    print(f"最小延迟: {stats['min_ms']:.3f} ms")

    return stats


def test_delay_buffer():
    """测试2: DelayBuffer 单帧缓冲"""
    print("\n" + "="*60)
    print("测试2: DelayBuffer 单帧缓冲")
    print("="*60)

    buffer = DelayBufferSim()
    tester = LatencyTester("DelayBuffer")
    stop_event = threading.Event()

    def producer():
        frame_interval = 1/60  # 60fps
        for i in range(100):
            frame = FramePacket(id=i, send_time=time.perf_counter())
            success, skipped = buffer.push(frame)
            if skipped:
                tester.record_skip()
            time.sleep(frame_interval)
        stop_event.set()

    def consumer():
        while not stop_event.is_set() or buffer._pending_frame is not None:
            frame = buffer.consume()
            if frame:
                frame.render_time = time.perf_counter()
                latency_ms = (frame.render_time - frame.send_time) * 1000
                tester.record(latency_ms)
            time.sleep(0.001)  # 模拟渲染时间

    # 启动生产者和消费者
    p_thread = threading.Thread(target=producer)
    c_thread = threading.Thread(target=consumer)

    start_time = time.perf_counter()
    p_thread.start()
    c_thread.start()

    p_thread.join()
    c_thread.join()
    total_time = time.perf_counter() - start_time

    stats = tester.get_stats()
    print(f"总时间: {total_time:.2f}s")
    print(f"帧数: {stats['frames']}")
    print(f"跳帧率: {stats['skip_rate']:.1f}%")
    print(f"平均延迟: {stats['avg_ms']:.3f} ms")
    print(f"P50 延迟: {stats['p50_ms']:.3f} ms")
    print(f"P95 延迟: {stats['p95_ms']:.3f} ms")
    print(f"最大延迟: {stats['max_ms']:.3f} ms")

    return stats


def test_timer_polling():
    """测试3: QTimer 轮询模拟"""
    print("\n" + "="*60)
    print("测试3: QTimer 16ms 轮询模拟")
    print("="*60)

    buffer = DelayBufferSim()
    tester = LatencyTester("QTimer轮询")
    stop_event = threading.Event()

    frame_ready = threading.Event()  # 模拟帧到达事件

    def producer():
        frame_interval = 1/60  # 60fps
        for i in range(100):
            frame = FramePacket(id=i, send_time=time.perf_counter())
            success, skipped = buffer.push(frame)
            if skipped:
                tester.record_skip()
            frame_ready.set()  # 通知帧已到达
            time.sleep(frame_interval)
        stop_event.set()

    def consumer_timer_polling():
        """模拟 QTimer 16ms 轮询"""
        timer_interval = 0.016  # 16ms
        while not stop_event.is_set():
            timer_start = time.perf_counter()

            # 模拟定时器触发后的处理
            frame = buffer.consume()
            if frame:
                frame.render_time = time.perf_counter()
                latency_ms = (frame.render_time - frame.send_time) * 1000
                tester.record(latency_ms)

            # 等待下一个定时器周期
            elapsed = time.perf_counter() - timer_start
            sleep_time = timer_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    p_thread = threading.Thread(target=producer)
    c_thread = threading.Thread(target=consumer_timer_polling)

    start_time = time.perf_counter()
    p_thread.start()
    c_thread.start()

    p_thread.join()
    c_thread.join()
    total_time = time.perf_counter() - start_time

    stats = tester.get_stats()
    print(f"总时间: {total_time:.2f}s")
    print(f"帧数: {stats['frames']}")
    print(f"跳帧率: {stats['skip_rate']:.1f}%")
    print(f"平均延迟: {stats['avg_ms']:.3f} ms")
    print(f"P50 延迟: {stats['p50_ms']:.3f} ms")
    print(f"P95 延迟: {stats['p95_ms']:.3f} ms")
    print(f"最大延迟: {stats['max_ms']:.3f} ms")

    return stats


def test_event_driven():
    """测试4: 事件驱动模拟"""
    print("\n" + "="*60)
    print("测试4: 事件驱动模拟")
    print("="*60)

    buffer = DelayBufferSim()
    tester = LatencyTester("事件驱动")
    stop_event = threading.Event()
    frame_ready = threading.Event()

    def producer():
        frame_interval = 1/60  # 60fps
        for i in range(100):
            frame = FramePacket(id=i, send_time=time.perf_counter())
            success, skipped = buffer.push(frame)
            if skipped:
                tester.record_skip()
            frame_ready.set()  # 立即通知
            time.sleep(frame_interval)
        stop_event.set()
        frame_ready.set()  # 唤醒消费者退出

    def consumer_event_driven():
        """事件驱动：帧到达立即处理"""
        while not stop_event.is_set():
            # 等待帧到达通知
            frame_ready.wait(timeout=0.1)
            frame_ready.clear()

            # 处理所有可用帧
            while True:
                frame = buffer.consume()
                if frame is None:
                    break
                frame.render_time = time.perf_counter()
                latency_ms = (frame.render_time - frame.send_time) * 1000
                tester.record(latency_ms)

    p_thread = threading.Thread(target=producer)
    c_thread = threading.Thread(target=consumer_event_driven)

    start_time = time.perf_counter()
    p_thread.start()
    c_thread.start()

    p_thread.join()
    c_thread.join()
    total_time = time.perf_counter() - start_time

    stats = tester.get_stats()
    print(f"总时间: {total_time:.2f}s")
    print(f"帧数: {stats['frames']}")
    print(f"跳帧率: {stats['skip_rate']:.1f}%")
    print(f"平均延迟: {stats['avg_ms']:.3f} ms")
    print(f"P50 延迟: {stats['p50_ms']:.3f} ms")
    print(f"P95 延迟: {stats['p95_ms']:.3f} ms")
    print(f"最大延迟: {stats['max_ms']:.3f} ms")

    return stats


def test_queue_buffer():
    """测试5: 队列缓冲模拟"""
    print("\n" + "="*60)
    print("测试5: 队列缓冲 (3帧深度)")
    print("="*60)

    buffer = QueueBufferSim(maxsize=3)
    tester = LatencyTester("队列缓冲")
    stop_event = threading.Event()

    def producer():
        frame_interval = 1/60  # 60fps
        for i in range(100):
            frame = FramePacket(id=i, send_time=time.perf_counter())
            success = buffer.push(frame)
            if not success:
                tester.record_skip()
            time.sleep(frame_interval)
        stop_event.set()

    def consumer():
        while not stop_event.is_set():
            frame = buffer.consume(timeout=0.01)
            if frame:
                frame.render_time = time.perf_counter()
                latency_ms = (frame.render_time - frame.send_time) * 1000
                tester.record(latency_ms)

    p_thread = threading.Thread(target=producer)
    c_thread = threading.Thread(target=consumer)

    start_time = time.perf_counter()
    p_thread.start()
    c_thread.start()

    p_thread.join()
    c_thread.join()
    total_time = time.perf_counter() - start_time

    stats = tester.get_stats()
    print(f"总时间: {total_time:.2f}s")
    print(f"帧数: {stats['frames']}")
    print(f"跳帧率: {stats['skip_rate']:.1f}%")
    print(f"平均延迟: {stats['avg_ms']:.3f} ms")
    print(f"P50 延迟: {stats['p50_ms']:.3f} ms")
    print(f"P95 延迟: {stats['p95_ms']:.3f} ms")
    print(f"最大延迟: {stats['max_ms']:.3f} ms")

    return stats


def test_timer_with_random_delay():
    """测试6: QTimer + 随机处理延迟（更接近真实场景）"""
    print("\n" + "="*60)
    print("测试6: QTimer + 随机处理延迟")
    print("="*60)

    import random

    buffer = DelayBufferSim()
    tester = LatencyTester("QTimer+延迟")
    stop_event = threading.Event()

    def producer():
        frame_interval = 1/60  # 60fps
        for i in range(100):
            frame = FramePacket(id=i, send_time=time.perf_counter())
            # 模拟网络抖动
            jitter = random.uniform(-0.002, 0.005)  # -2ms 到 +5ms
            time.sleep(frame_interval + jitter)
            success, skipped = buffer.push(frame)
            if skipped:
                tester.record_skip()
        stop_event.set()

    def consumer_timer_polling():
        """模拟 QTimer 16ms 轮询 + 随机处理时间"""
        timer_interval = 0.016  # 16ms
        while not stop_event.is_set():
            timer_start = time.perf_counter()

            frame = buffer.consume()
            if frame:
                # 模拟渲染处理时间 (2-8ms)
                process_time = random.uniform(0.002, 0.008)
                time.sleep(process_time)

                frame.render_time = time.perf_counter()
                latency_ms = (frame.render_time - frame.send_time) * 1000
                tester.record(latency_ms)

            elapsed = time.perf_counter() - timer_start
            sleep_time = timer_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    p_thread = threading.Thread(target=producer)
    c_thread = threading.Thread(target=consumer_timer_polling)

    start_time = time.perf_counter()
    p_thread.start()
    c_thread.start()

    p_thread.join()
    c_thread.join()
    total_time = time.perf_counter() - start_time

    stats = tester.get_stats()
    print(f"总时间: {total_time:.2f}s")
    print(f"帧数: {stats['frames']}")
    print(f"跳帧率: {stats['skip_rate']:.1f}%")
    print(f"平均延迟: {stats['avg_ms']:.3f} ms")
    print(f"P50 延迟: {stats['p50_ms']:.3f} ms")
    print(f"P95 延迟: {stats['p95_ms']:.3f} ms")
    print(f"最大延迟: {stats['max_ms']:.3f} ms")

    return stats


def test_cross_thread_with_gil():
    """测试7: 跨线程 + GIL 竞争模拟"""
    print("\n" + "="*60)
    print("测试7: 跨线程 + GIL 竞争模拟")
    print("="*60)

    import random

    buffer = DelayBufferSim()
    tester = LatencyTester("GIL竞争")
    stop_event = threading.Event()

    # 模拟 GIL 竞争的额外线程
    gil_hog_running = True

    def gil_hog():
        """模拟持有 GIL 的操作"""
        while gil_hog_running:
            # 模拟 numpy 操作持有 GIL
            data = [i * 2 for i in range(10000)]
            _ = sum(data)
            time.sleep(0.001)

    def producer():
        frame_interval = 1/60
        for i in range(100):
            frame = FramePacket(id=i, send_time=time.perf_counter())
            success, skipped = buffer.push(frame)
            if skipped:
                tester.record_skip()
            time.sleep(frame_interval)
        stop_event.set()

    def consumer():
        while not stop_event.is_set():
            frame = buffer.consume()
            if frame:
                # 模拟渲染时的 GIL 竞争
                process_time = random.uniform(0.002, 0.008)
                time.sleep(process_time)

                frame.render_time = time.perf_counter()
                latency_ms = (frame.render_time - frame.send_time) * 1000
                tester.record(latency_ms)
            time.sleep(0.016)

    # 启动 GIL 竞争线程
    gil_thread = threading.Thread(target=gil_hog)
    p_thread = threading.Thread(target=producer)
    c_thread = threading.Thread(target=consumer)

    start_time = time.perf_counter()
    gil_thread.start()
    p_thread.start()
    c_thread.start()

    p_thread.join()
    c_thread.join()

    gil_hog_running = False
    gil_thread.join()

    total_time = time.perf_counter() - start_time

    stats = tester.get_stats()
    print(f"总时间: {total_time:.2f}s")
    print(f"帧数: {stats['frames']}")
    print(f"跳帧率: {stats['skip_rate']:.1f}%")
    print(f"平均延迟: {stats['avg_ms']:.3f} ms")
    print(f"P50 延迟: {stats['p50_ms']:.3f} ms")
    print(f"P95 延迟: {stats['p95_ms']:.3f} ms")
    print(f"最大延迟: {stats['max_ms']:.3f} ms")

    return stats


def run_all_tests():
    """运行所有测试"""
    print("\n" + "#"*60)
    print("# 延迟模拟测试框架")
    print("#"*60)

    results = []

    # 测试1: 基线
    results.append(test_pure_memory_pass())

    # 测试2: DelayBuffer
    results.append(test_delay_buffer())

    # 测试3: QTimer 轮询
    results.append(test_timer_polling())

    # 测试4: 事件驱动
    results.append(test_event_driven())

    # 测试5: 队列缓冲
    results.append(test_queue_buffer())

    # 测试6: QTimer + 延迟
    results.append(test_timer_with_random_delay())

    # 测试7: GIL 竞争
    results.append(test_cross_thread_with_gil())

    # 汇总报告
    print("\n" + "#"*60)
    print("# 汇总报告")
    print("#"*60)
    print(f"\n{'测试名称':<20} {'平均延迟':>12} {'P95延迟':>12} {'最大延迟':>12} {'跳帧率':>10}")
    print("-"*70)
    for r in results:
        print(f"{r['name']:<20} {r['avg_ms']:>10.3f}ms {r['p95_ms']:>10.3f}ms {r['max_ms']:>10.3f}ms {r['skip_rate']:>8.1f}%")

    print("\n" + "#"*60)
    print("# 分析结论")
    print("#"*60)

    # 找出主要延迟来源
    baseline = results[0]['avg_ms']
    for r in results[1:]:
        extra_delay = r['avg_ms'] - baseline
        print(f"{r['name']}: 额外延迟 = {extra_delay:.3f}ms")

    return results


if __name__ == "__main__":
    run_all_tests()
