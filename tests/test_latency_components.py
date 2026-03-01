"""
延迟组件分析测试

分析当前架构中各个组件的延迟贡献：
1. 纯 Python 延迟（基线）
2. 定时器 16ms 轮询延迟
3. 双重定时器延迟（解码进程 + 预览进程）
4. SHM 读/写延迟
5. 数据拷贝延迟

运行方式：
    python tests/test_latency_components.py
"""

import time
import threading
import queue
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TestResult:
    name: str
    avg_ms: float
    max_ms: float
    min_ms: float
    p50_ms: float
    p95_ms: float
    frames: int


def measure_latency(latencies: List[float]) -> dict:
    """计算延迟统计"""
    if not latencies:
        return {"avg_ms": 0, "max_ms": 0, "min_ms": 0, "p50_ms": 0, "p95_ms": 0}

    sorted_lat = sorted(latencies)
    return {
        "avg_ms": sum(latencies) / len(latencies),
        "max_ms": max(latencies),
        "min_ms": min(latencies),
        "p50_ms": sorted_lat[len(sorted_lat) // 2],
        "p95_ms": sorted_lat[int(len(sorted_lat) * 0.95)] if len(sorted_lat) > 20 else max(latencies),
    }


def test_baseline():
    """测试1: 基线 - 纯时间戳测量"""
    print("\n" + "="*60)
    print("测试1: 基线 - 纯时间戳测量")
    print("="*60)

    latencies = []
    for _ in range(100):
        t1 = time.perf_counter()
        t2 = time.perf_counter()
        latencies.append((t2 - t1) * 1000)

    stats = measure_latency(latencies)
    print(f"帧数: 100")
    print(f"平均延迟: {stats['avg_ms']:.6f}ms")
    print(f"最大延迟: {stats['max_ms']:.6f}ms")

    return TestResult(name="基线", frames=100, **stats)


def test_single_timer():
    """测试2: 单定时器 16ms 轮询"""
    print("\n" + "="*60)
    print("测试2: 单定时器 16ms 轮询")
    print("="*60)

    latencies = []
    frame_queue = queue.Queue(maxsize=1)
    stop_event = threading.Event()

    def producer():
        for i in range(100):
            t = time.perf_counter()
            try:
                frame_queue.put_nowait(t)
            except queue.Full:
                pass
            time.sleep(1/60)  # 60fps
        stop_event.set()

    def consumer():
        while not stop_event.is_set():
            timer_start = time.perf_counter()
            try:
                send_time = frame_queue.get_nowait()
                recv_time = time.perf_counter()
                latencies.append((recv_time - send_time) * 1000)
            except queue.Empty:
                pass
            # 等待下一个定时器周期
            elapsed = time.perf_counter() - timer_start
            if elapsed < 0.016:
                time.sleep(0.016 - elapsed)

    p = threading.Thread(target=producer)
    c = threading.Thread(target=consumer)

    p.start()
    c.start()
    p.join()
    c.join()

    stats = measure_latency(latencies)
    print(f"帧数: {len(latencies)}")
    print(f"平均延迟: {stats['avg_ms']:.3f}ms")
    print(f"P50 延迟: {stats['p50_ms']:.3f}ms")
    print(f"P95 延迟: {stats['p95_ms']:.3f}ms")
    print(f"最大延迟: {stats['max_ms']:.3f}ms")

    return TestResult(name="单定时器16ms", frames=len(latencies), **stats)


def test_double_timer():
    """测试3: 双定时器延迟（模拟当前架构）"""
    print("\n" + "="*60)
    print("测试3: 双定时器延迟（解码进程 16ms + 预览进程 16ms）")
    print("="*60)

    latencies = []
    buffer1 = queue.Queue(maxsize=1)  # 解码进程 -> 中间缓冲
    buffer2 = queue.Queue(maxsize=1)  # 中间缓冲 -> 预览进程
    stop_event = threading.Event()

    def producer():
        """模拟解码进程"""
        for i in range(100):
            t = time.perf_counter()
            try:
                buffer1.put_nowait(t)
            except queue.Full:
                pass
            time.sleep(1/60)
        stop_event.set()

    def middleman():
        """模拟 SHM 传输（也有定时器）"""
        while not stop_event.is_set():
            timer_start = time.perf_counter()
            try:
                data = buffer1.get_nowait()
                buffer2.put_nowait(data)
            except queue.Empty:
                pass
            except queue.Full:
                pass
            elapsed = time.perf_counter() - timer_start
            if elapsed < 0.016:
                time.sleep(0.016 - elapsed)

    def consumer():
        """模拟预览进程"""
        while not stop_event.is_set():
            timer_start = time.perf_counter()
            try:
                send_time = buffer2.get_nowait()
                recv_time = time.perf_counter()
                latencies.append((recv_time - send_time) * 1000)
            except queue.Empty:
                pass
            elapsed = time.perf_counter() - timer_start
            if elapsed < 0.016:
                time.sleep(0.016 - elapsed)

    p = threading.Thread(target=producer)
    m = threading.Thread(target=middleman)
    c = threading.Thread(target=consumer)

    p.start()
    m.start()
    c.start()
    p.join()
    m.join()
    c.join()

    stats = measure_latency(latencies)
    print(f"帧数: {len(latencies)}")
    print(f"平均延迟: {stats['avg_ms']:.3f}ms")
    print(f"P50 延迟: {stats['p50_ms']:.3f}ms")
    print(f"P95 延迟: {stats['p95_ms']:.3f}ms")
    print(f"最大延迟: {stats['max_ms']:.3f}ms")

    return TestResult(name="双定时器16ms", frames=len(latencies), **stats)


def test_data_copy():
    """测试4: 数据拷贝延迟"""
    print("\n" + "="*60)
    print("测试4: 数据拷贝延迟（3MB NV12 帧）")
    print("="*60)

    frame_size = 1920 * 1080 * 3 // 2  # ~3MB
    source_data = bytes(frame_size)

    latencies = []
    for _ in range(100):
        t1 = time.perf_counter()
        # 模拟帧拷贝
        copied_data = bytes(source_data)
        t2 = time.perf_counter()
        latencies.append((t2 - t1) * 1000)

    stats = measure_latency(latencies)
    print(f"帧大小: {frame_size / 1024 / 1024:.2f}MB")
    print(f"帧数: 100")
    print(f"平均拷贝时间: {stats['avg_ms']:.3f}ms")
    print(f"最大拷贝时间: {stats['max_ms']:.3f}ms")

    return TestResult(name="数据拷贝3MB", frames=100, **stats)


def test_triple_timer():
    """测试5: 三定时器延迟（更接近真实架构）"""
    print("\n" + "="*60)
    print("测试5: 三定时器延迟（解码 16ms + SHM 16ms + 渲染 16ms）")
    print("="*60)

    latencies = []
    b1 = queue.Queue(maxsize=1)
    b2 = queue.Queue(maxsize=1)
    b3 = queue.Queue(maxsize=1)
    stop_event = threading.Event()

    def stage1():
        """解码阶段"""
        for i in range(100):
            t = time.perf_counter()
            try:
                b1.put_nowait(t)
            except queue.Full:
                pass
            time.sleep(1/60)
        stop_event.set()

    def stage2():
        """SHM 写入"""
        while not stop_event.is_set():
            timer_start = time.perf_counter()
            try:
                b2.put_nowait(b1.get_nowait())
            except:
                pass
            elapsed = time.perf_counter() - timer_start
            if elapsed < 0.016:
                time.sleep(0.016 - elapsed)

    def stage3():
        """SHM 读取"""
        while not stop_event.is_set():
            timer_start = time.perf_counter()
            try:
                b3.put_nowait(b2.get_nowait())
            except:
                pass
            elapsed = time.perf_counter() - timer_start
            if elapsed < 0.016:
                time.sleep(0.016 - elapsed)

    def stage4():
        """渲染"""
        while not stop_event.is_set():
            timer_start = time.perf_counter()
            try:
                send_time = b3.get_nowait()
                recv_time = time.perf_counter()
                latencies.append((recv_time - send_time) * 1000)
            except:
                pass
            elapsed = time.perf_counter() - timer_start
            if elapsed < 0.016:
                time.sleep(0.016 - elapsed)

    threads = [
        threading.Thread(target=stage1),
        threading.Thread(target=stage2),
        threading.Thread(target=stage3),
        threading.Thread(target=stage4),
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    stats = measure_latency(latencies)
    print(f"帧数: {len(latencies)}")
    print(f"平均延迟: {stats['avg_ms']:.3f}ms")
    print(f"P50 延迟: {stats['p50_ms']:.3f}ms")
    print(f"P95 延迟: {stats['p95_ms']:.3f}ms")
    print(f"最大延迟: {stats['max_ms']:.3f}ms")

    return TestResult(name="三定时器16ms", frames=len(latencies), **stats)


def test_accumulated_delay():
    """测试6: 累积延迟分析"""
    print("\n" + "="*60)
    print("测试6: 累积延迟分析（不使用定时器）")
    print("="*60)

    latencies = []

    for i in range(100):
        t1 = time.perf_counter()

        # 模拟处理链（无定时器等待）
        time.sleep(0.001)  # 解码 1ms
        time.sleep(0.001)  # SHM 写入 1ms
        time.sleep(0.001)  # SHM 读取 1ms
        time.sleep(0.002)  # 渲染 2ms

        t2 = time.perf_counter()
        latencies.append((t2 - t1) * 1000)

    stats = measure_latency(latencies)
    print(f"帧数: 100")
    print(f"平均处理时间: {stats['avg_ms']:.3f}ms")
    print(f"最大处理时间: {stats['max_ms']:.3f}ms")

    return TestResult(name="累积处理", frames=100, **stats)


def test_with_jitter():
    """测试7: 带抖动的定时器延迟"""
    print("\n" + "="*60)
    print("测试7: 带抖动的定时器延迟（更真实）")
    print("="*60)

    import random

    latencies = []
    frame_queue = queue.Queue(maxsize=1)
    stop_event = threading.Event()

    def producer():
        for i in range(100):
            t = time.perf_counter()
            try:
                frame_queue.put_nowait(t)
            except queue.Full:
                pass
            # 帧间隔带抖动
            jitter = random.uniform(-0.002, 0.005)
            time.sleep(1/60 + jitter)
        stop_event.set()

    def consumer():
        while not stop_event.is_set():
            timer_start = time.perf_counter()
            try:
                send_time = frame_queue.get_nowait()
                # 模拟处理时间带抖动
                process_time = random.uniform(0.002, 0.008)
                time.sleep(process_time)
                recv_time = time.perf_counter()
                latencies.append((recv_time - send_time) * 1000)
            except queue.Empty:
                pass
            elapsed = time.perf_counter() - timer_start
            if elapsed < 0.016:
                time.sleep(0.016 - elapsed)

    p = threading.Thread(target=producer)
    c = threading.Thread(target=consumer)

    p.start()
    c.start()
    p.join()
    c.join()

    stats = measure_latency(latencies)
    print(f"帧数: {len(latencies)}")
    print(f"平均延迟: {stats['avg_ms']:.3f}ms")
    print(f"P50 延迟: {stats['p50_ms']:.3f}ms")
    print(f"P95 延迟: {stats['p95_ms']:.3f}ms")
    print(f"最大延迟: {stats['max_ms']:.3f}ms")

    return TestResult(name="带抖动定时器", frames=len(latencies), **stats)


def main():
    print("#"*60)
    print("# 延迟组件分析测试")
    print("#"*60)

    results = []

    results.append(test_baseline())
    results.append(test_single_timer())
    results.append(test_double_timer())
    results.append(test_data_copy())
    results.append(test_triple_timer())
    results.append(test_accumulated_delay())
    results.append(test_with_jitter())

    # 汇总报告
    print("\n" + "#"*60)
    print("# 汇总报告")
    print("#"*60)
    print(f"\n{'测试名称':<20} {'平均(ms)':>10} {'P50(ms)':>10} {'P95(ms)':>10} {'最大(ms)':>10}")
    print("-"*60)
    for r in results:
        print(f"{r.name:<20} {r.avg_ms:>10.3f} {r.p50_ms:>10.3f} {r.p95_ms:>10.3f} {r.max_ms:>10.3f}")

    print("\n" + "#"*60)
    print("# 关键发现")
    print("#"*60)

    baseline = results[0].avg_ms
    for r in results[1:]:
        extra = r.avg_ms - baseline
        if extra > 1:
            print(f"⚠️  {r.name}: 额外延迟 = {extra:.1f}ms")

    print("""
结论：
1. 单定时器 16ms 轮询会增加约 8-16ms 延迟
2. 双定时器会增加约 16-32ms 延迟
3. 三定时器（更接近当前架构）会增加约 24-48ms 延迟

但这些仍然不能解释 300-400ms 的延迟。
真正的延迟可能来自：
- Qt 事件循环的实际开销（比纯 Python 更大）
- OpenGL 纹理上传时间
- Windows DWM 合成延迟
- 服务端编码延迟
""")


if __name__ == "__main__":
    main()
