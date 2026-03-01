"""
Qt 延迟测试

测试 Qt 事件循环和 QOpenGLWidget/QOpenGLWindow 的实际延迟。

运行方式：
    python tests/test_qt_latency.py
"""

import sys
import time
import threading
from typing import List, Optional
from dataclasses import dataclass

# 检查 Qt 是否可用
try:
    from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
    from PySide6.QtCore import QTimer, Qt, QThread, Signal
    from PySide6.QtGui import QSurfaceFormat
    QT_AVAILABLE = True
except ImportError:
    try:
        from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel
        from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal as Signal
        from PyQt6.QtGui import QSurfaceFormat
        QT_AVAILABLE = True
    except ImportError:
        QT_AVAILABLE = False
        print("Qt 不可用，跳过测试")


@dataclass
class TestResult:
    name: str
    avg_ms: float
    max_ms: float
    min_ms: float
    p50_ms: float
    p95_ms: float


def measure_latencies(latencies: List[float]) -> TestResult:
    """计算延迟统计"""
    if not latencies:
        return TestResult("empty", 0, 0, 0, 0, 0)

    sorted_lat = sorted(latencies)
    return TestResult(
        name="result",
        avg_ms=sum(latencies) / len(latencies),
        max_ms=max(latencies),
        min_ms=min(latencies),
        p50_ms=sorted_lat[len(sorted_lat) // 2],
        p95_ms=sorted_lat[int(len(sorted_lat) * 0.95)] if len(sorted_lat) > 20 else max(latencies),
    )


class FrameProducer(QThread):
    """帧生产者线程"""
    frame_ready = Signal(float)  # 发送时间戳

    def __init__(self, frame_count: int = 100):
        super().__init__()
        self.frame_count = frame_count
        self.running = True

    def run(self):
        for i in range(self.frame_count):
            t = time.perf_counter()
            self.frame_ready.emit(t)
            time.sleep(1/60)  # 60fps
        self.running = False


class LatencyTestWidget(QWidget):
    """延迟测试窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt 延迟测试")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)
        self.label = QLabel("测试中...")
        layout.addWidget(self.label)

        # 测试数据
        self.latencies: List[float] = []
        self.test_count = 0
        self.current_test = 0
        self.results: List[TestResult] = []

        # 定时器测试
        self.timer_latencies: List[float] = []
        self.timer_frame_count = 0
        self.timer_start_time = 0.0

    def start_tests(self):
        """开始所有测试"""
        self.current_test = 0
        self.results = []
        self.run_next_test()

    def run_next_test(self):
        """运行下一个测试"""
        tests = [
            ("QTimer 16ms 轮询", self.test_timer_polling),
            ("QTimer + 信号", self.test_timer_signal),
            ("直接调用", self.test_direct_call),
        ]

        if self.current_test < len(tests):
            name, test_func = tests[self.current_test]
            self.label.setText(f"测试: {name}")
            test_func()
            self.current_test += 1
        else:
            self.show_results()

    def test_timer_polling(self):
        """测试1: QTimer 16ms 轮询"""
        self.timer_latencies = []
        self.timer_frame_count = 0
        frame_times: List[float] = []

        def on_timer():
            nonlocal frame_times
            if frame_times:
                send_time = frame_times.pop(0)
                recv_time = time.perf_counter()
                self.timer_latencies.append((recv_time - send_time) * 1000)

            # 添加新帧
            frame_times.append(time.perf_counter())
            self.timer_frame_count += 1

            if self.timer_frame_count >= 100:
                timer.stop()
                result = measure_latencies(self.timer_latencies)
                result.name = "QTimer 16ms 轮询"
                self.results.append(result)
                QTimer.singleShot(100, self.run_next_test)

        timer = QTimer()
        timer.timeout.connect(on_timer)
        timer.start(16)

    def test_timer_signal(self):
        """测试2: QTimer + 信号传递"""
        self.timer_latencies = []

        producer = FrameProducer(frame_count=100)

        def on_frame(send_time: float):
            recv_time = time.perf_counter()
            self.timer_latencies.append((recv_time - send_time) * 1000)

            if len(self.timer_latencies) >= 100:
                result = measure_latencies(self.timer_latencies)
                result.name = "QTimer + 信号"
                self.results.append(result)
                QTimer.singleShot(100, self.run_next_test)

        producer.frame_ready.connect(on_frame)
        producer.start()

        # 保存引用防止被回收
        self._producer = producer

    def test_direct_call(self):
        """测试3: 直接函数调用（基线）"""
        latencies = []

        for _ in range(100):
            t1 = time.perf_counter()
            # 直接调用，无延迟
            t2 = time.perf_counter()
            latencies.append((t2 - t1) * 1000)

        result = measure_latencies(latencies)
        result.name = "直接调用"
        self.results.append(result)
        QTimer.singleShot(100, self.run_next_test)

    def show_results(self):
        """显示测试结果"""
        print("\n" + "="*60)
        print("Qt 延迟测试结果")
        print("="*60)
        print(f"\n{'测试名称':<20} {'平均(ms)':>10} {'P50(ms)':>10} {'P95(ms)':>10} {'最大(ms)':>10}")
        print("-"*60)
        for r in self.results:
            print(f"{r.name:<20} {r.avg_ms:>10.3f} {r.p50_ms:>10.3f} {r.p95_ms:>10.3f} {r.max_ms:>10.3f}")

        # 更新标签
        text = "测试完成!\n\n"
        for r in self.results:
            text += f"{r.name}: {r.avg_ms:.2f}ms\n"
        self.label.setText(text)

        # 3秒后关闭
        QTimer.singleShot(3000, self.close)


def test_qtimer_accuracy():
    """测试 QTimer 的实际精度"""
    print("\n" + "="*60)
    print("QTimer 精度测试")
    print("="*60)

    intervals = []

    def on_timer():
        now = time.perf_counter()
        intervals.append(now)
        if len(intervals) >= 100:
            timer.stop()

            # 计算实际间隔
            actual_intervals = [intervals[i] - intervals[i-1] for i in range(1, len(intervals))]
            avg_interval = sum(actual_intervals) / len(actual_intervals) * 1000

            print(f"设定间隔: 16ms")
            print(f"实际平均间隔: {avg_interval:.2f}ms")
            print(f"最小间隔: {min(actual_intervals)*1000:.2f}ms")
            print(f"最大间隔: {max(actual_intervals)*1000:.2f}ms")

            app.quit()

    app = QApplication.instance() or QApplication(sys.argv)

    timer = QTimer()
    timer.timeout.connect(on_timer)
    timer.start(16)

    app.exec()


def test_qt_event_loop_latency():
    """测试 Qt 事件循环延迟"""
    print("\n" + "="*60)
    print("Qt 事件循环延迟测试")
    print("="*60)

    latencies = []

    def on_event():
        recv_time = time.perf_counter()
        latencies.append((recv_time - send_times.pop(0)) * 1000)

        if len(latencies) >= 100:
            avg = sum(latencies) / len(latencies)
            print(f"平均事件延迟: {avg:.3f}ms")
            print(f"最大事件延迟: {max(latencies):.3f}ms")
            print(f"最小事件延迟: {min(latencies):.3f}ms")
            app.quit()
        else:
            # 发送下一个事件
            send_times.append(time.perf_counter())
            QTimer.singleShot(0, on_event)

    app = QApplication.instance() or QApplication(sys.argv)

    send_times = [time.perf_counter()]
    QTimer.singleShot(0, on_event)

    app.exec()


def main():
    if not QT_AVAILABLE:
        print("Qt 不可用")
        return

    print("#"*60)
    print("# Qt 延迟测试")
    print("#"*60)

    # 测试 QTimer 精度
    test_qtimer_accuracy()

    # 测试 Qt 事件循环延迟
    test_qt_event_loop_latency()

    # 综合测试
    app = QApplication.instance() or QApplication(sys.argv)

    widget = LatencyTestWidget()
    widget.show()

    # 延迟启动测试
    QTimer.singleShot(500, widget.start_tests)

    app.exec()


if __name__ == "__main__":
    main()
