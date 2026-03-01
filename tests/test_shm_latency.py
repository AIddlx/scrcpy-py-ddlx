"""
跨进程 SHM 延迟测试

模拟当前架构中的跨进程通信延迟：
1. 解码进程 -> SHM 写入
2. SHM 读取 -> 预览进程

运行方式：
    python tests/test_shm_latency.py
"""

import time
import multiprocessing as mp
from multiprocessing import shared_memory
import struct
import os


def shm_writer_process(shm_name: str, frame_count: int, frame_size: int, results_queue: mp.Queue):
    """模拟解码进程写入 SHM"""
    try:
        shm = shared_memory.SharedMemory(name=shm_name)
    except FileNotFoundError:
        results_queue.put({"error": "SHM not found"})
        return

    latencies = []

    for i in range(frame_count):
        # 模拟帧数据
        frame_data = bytes([i % 256] * frame_size)

        # 记录写入时间
        write_time = time.perf_counter()

        # 写入时间戳和帧数据
        header = struct.pack('d', write_time)  # 8 bytes
        shm.buf[:8] = header
        shm.buf[8:8+len(frame_data)] = frame_data

        # 标记帧就绪 (写入帧ID)
        shm.buf[8+len(frame_data):8+len(frame_data)+4] = struct.pack('I', i)

        # 等待下一帧 (60fps)
        time.sleep(1/60)

    shm.close()
    results_queue.put({"role": "writer", "frames": frame_count})


def shm_reader_process(shm_name: str, frame_count: int, frame_size: int, results_queue: mp.Queue,
                       use_timer: bool = True, timer_interval: float = 0.016):
    """模拟预览进程读取 SHM"""
    try:
        shm = shared_memory.SharedMemory(name=shm_name)
    except FileNotFoundError:
        results_queue.put({"error": "SHM not found"})
        return

    latencies = []
    last_frame_id = -1

    for _ in range(frame_count + 10):  # 多读几次确保读完
        if use_timer:
            timer_start = time.perf_counter()

        # 读取帧ID
        frame_id_bytes = bytes(shm.buf[8+frame_size:8+frame_size+4])
        frame_id = struct.unpack('I', frame_id_bytes)[0]

        if frame_id != last_frame_id and frame_id > last_frame_id:
            # 新帧到达
            last_frame_id = frame_id

            # 读取写入时间戳
            write_time = struct.unpack('d', bytes(shm.buf[:8]))[0]
            read_time = time.perf_counter()

            latency_ms = (read_time - write_time) * 1000
            latencies.append(latency_ms)

        if use_timer:
            elapsed = time.perf_counter() - timer_start
            sleep_time = timer_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
        else:
            time.sleep(0.001)  # 事件驱动模式，更频繁检查

    shm.close()

    if latencies:
        results_queue.put({
            "role": "reader",
            "frames": len(latencies),
            "avg_ms": sum(latencies) / len(latencies),
            "max_ms": max(latencies),
            "min_ms": min(latencies),
            "p95_ms": sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 20 else max(latencies),
        })
    else:
        results_queue.put({"role": "reader", "frames": 0, "avg_ms": 0})


def test_shm_latency(use_timer: bool = True, frame_count: int = 100):
    """测试 SHM 跨进程延迟"""
    mode = "16ms定时器轮询" if use_timer else "1ms轮询"
    print(f"\n{'='*60}")
    print(f"SHM 跨进程延迟测试 - {mode}")
    print(f"{'='*60}")

    frame_size = 1920 * 1080 * 3 // 2  # NV12 格式 ~3MB

    # 创建共享内存
    shm = shared_memory.SharedMemory(create=True, size=8 + frame_size + 4)
    shm_name = shm.name

    results_queue = mp.Queue()

    # 启动进程
    writer = mp.Process(target=shm_writer_process,
                        args=(shm_name, frame_count, frame_size, results_queue))
    reader = mp.Process(target=shm_reader_process,
                        args=(shm_name, frame_count, frame_size, results_queue, use_timer))

    start_time = time.perf_counter()

    writer.start()
    reader.start()

    writer.join()
    reader.join()

    total_time = time.perf_counter() - start_time

    # 收集结果
    results = []
    while not results_queue.empty():
        results.append(results_queue.get())

    # 清理
    shm.close()
    shm.unlink()

    # 打印结果
    for r in results:
        if r.get("role") == "reader":
            print(f"总时间: {total_time:.2f}s")
            print(f"接收帧数: {r['frames']}")
            print(f"平均延迟: {r['avg_ms']:.3f}ms")
            print(f"P95 延迟: {r['p95_ms']:.3f}ms")
            print(f"最大延迟: {r['max_ms']:.3f}ms")
            print(f"最小延迟: {r['min_ms']:.3f}ms")
            return r

    return {"error": "No results"}


def test_in_process_latency(frame_count: int = 100):
    """测试进程内延迟（无跨进程开销）"""
    print(f"\n{'='*60}")
    print("进程内延迟测试（无跨进程）")
    print(f"{'='*60}")

    frame_size = 1920 * 1080 * 3 // 2  # NV12 格式

    # 创建共享内存（但不用多进程）
    shm = shared_memory.SharedMemory(create=True, size=8 + frame_size + 4)

    latencies = []

    for i in range(frame_count):
        # 写入
        write_time = time.perf_counter()
        frame_data = bytes([i % 256] * frame_size)
        header = struct.pack('d', write_time)
        shm.buf[:8] = header
        shm.buf[8:8+len(frame_data)] = frame_data
        shm.buf[8+len(frame_data):8+len(frame_data)+4] = struct.pack('I', i)

        # 模拟定时器延迟
        time.sleep(0.016)

        # 读取
        read_time = time.perf_counter()
        latency_ms = (read_time - write_time) * 1000
        latencies.append(latency_ms)

    shm.close()
    shm.unlink()

    print(f"帧数: {frame_count}")
    print(f"平均延迟: {sum(latencies)/len(latencies):.3f}ms")
    print(f"最大延迟: {max(latencies):.3f}ms")
    print(f"最小延迟: {min(latencies):.3f}ms")

    return {
        "frames": frame_count,
        "avg_ms": sum(latencies)/len(latencies),
        "max_ms": max(latencies),
        "min_ms": min(latencies),
    }


def test_queue_ipc_latency(frame_count: int = 100):
    """测试 multiprocessing.Queue 延迟"""
    print(f"\n{'='*60}")
    print("multiprocessing.Queue 延迟测试")
    print(f"{'='*60}")

    frame_size = 1920 * 1080 * 3 // 2  # NV12 格式
    queue = mp.Queue(maxsize=3)

    def writer_proc():
        for i in range(frame_count):
            write_time = time.perf_counter()
            # 不发送大帧，只发送时间戳
            queue.put(write_time)
            time.sleep(1/60)
        queue.put(None)  # 结束信号

    def reader_proc(results: mp.Queue):
        latencies = []
        while True:
            try:
                msg = queue.get(timeout=1)
                if msg is None:
                    break
                write_time = msg
                read_time = time.perf_counter()
                latency_ms = (read_time - write_time) * 1000
                latencies.append(latency_ms)
            except:
                break
        results.put(latencies)

    results_queue = mp.Queue()

    writer = mp.Process(target=writer_proc)
    reader = mp.Process(target=reader_proc, args=(results_queue,))

    start_time = time.perf_counter()
    writer.start()
    reader.start()
    writer.join()
    reader.join()
    total_time = time.perf_counter() - start_time

    latencies = results_queue.get()

    print(f"总时间: {total_time:.2f}s")
    print(f"帧数: {len(latencies)}")
    if latencies:
        print(f"平均延迟: {sum(latencies)/len(latencies):.3f}ms")
        print(f"最大延迟: {max(latencies):.3f}ms")
        print(f"最小延迟: {min(latencies):.3f}ms")


def main():
    print("#"*60)
    print("# 跨进程延迟测试")
    print("#"*60)

    # 测试1: 进程内延迟（基线）
    test_in_process_latency(50)

    # 测试2: SHM + 16ms 定时器
    test_shm_latency(use_timer=True, frame_count=50)

    # 测试3: SHM + 1ms 轮询（更快响应）
    test_shm_latency(use_timer=False, frame_count=50)

    # 测试4: Queue IPC 延迟
    test_queue_ipc_latency(50)

    print("\n" + "#"*60)
    print("# 结论")
    print("#"*60)
    print("""
跨进程通信本身的延迟很低（<1ms），但如果配合 16ms 定时器轮询，
延迟会增加到 8-16ms。

这不能解释 300-400ms 的延迟。需要进一步分析：
1. Qt 事件循环的实际开销
2. OpenGL 渲染的实际时间
3. 服务端到客户端的网络延迟
""")


if __name__ == "__main__":
    main()
