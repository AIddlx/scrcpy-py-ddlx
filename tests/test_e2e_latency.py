"""
端到端延迟测试脚本

测量从手机屏幕采集到客户端显示的完整延迟。

方法：
1. 手机端：显示当前时间（毫秒级）
2. 客户端：截取显示的帧，读取帧中的时间戳
3. 计算延迟 = 客户端当前时间 - 帧中显示的时间

使用方式：
    python tests/test_e2e_latency.py --host 192.168.5.4

手机端准备：
    方式1: 打开网页 http://<pc-ip>:8080/time.html（本脚本会启动服务器）
    方式2: 使用内置的数字时钟显示

注意：
    - 手机和电脑需要在同一网络
    - 手机屏幕需要保持常亮
"""

import sys
import time
import argparse
import threading
from datetime import datetime
from typing import Optional, Tuple
import queue

# 延迟测试配置
LATENCY_TEST_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Latency Test</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: #000;
            font-family: monospace;
        }
        #time {
            font-size: 15vw;
            color: #0f0;
            text-align: center;
        }
        #ms {
            font-size: 10vw;
            color: #0f0;
        }
        .container {
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div id="time"></div>
        <div id="ms"></div>
    </div>
    <script>
        function updateTime() {
            const now = new Date();
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');
            const ms = String(now.getMilliseconds()).padStart(3, '0');

            document.getElementById('time').textContent = `${hours}:${minutes}:${seconds}`;
            document.getElementById('ms').textContent = `.${ms}`;
        }

        updateTime();
        setInterval(updateTime, 1);  // 每 1ms 更新一次
    </script>
</body>
</html>
'''


class LatencyTester:
    """端到端延迟测试器"""

    def __init__(self, host: str, port: int = 27183, sample_count: int = 30):
        self.host = host
        self.port = port
        self.sample_count = sample_count
        self.results = []
        self._stop_event = threading.Event()

    def run_http_server(self, port: int = 8080):
        """启动简单的 HTTP 服务器提供时间页面"""
        from http.server import HTTPServer, SimpleHTTPRequestHandler
        import os
        import tempfile

        # 创建临时目录
        tmpdir = tempfile.mkdtemp()
        html_path = os.path.join(tmpdir, 'time.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(LATENCY_TEST_HTML)

        # 切换到临时目录
        original_dir = os.getcwd()
        os.chdir(tmpdir)

        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # 静默日志

        server = HTTPServer(('0.0.0.0', port), QuietHandler)

        print(f"[HTTP] 时间页面服务器启动: http://<本机IP>:{port}/time.html")
        print(f"[HTTP] 请在手机上打开此页面")

        def serve():
            while not self._stop_event.is_set():
                server.handle_request()

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()

        return tmpdir, original_dir

    def capture_and_measure(self, client) -> Optional[float]:
        """
        捕获一帧并测量延迟。

        返回: 延迟（毫秒），或 None 如果无法测量
        """
        import cv2
        import numpy as np

        # 获取当前帧
        frame = client.get_video_frame()
        if frame is None:
            return None

        # 记录客户端当前时间
        client_time = datetime.now()
        client_ms = client_time.hour * 3600000 + client_time.minute * 60000 + \
                    client_time.second * 1000 + client_time.microsecond // 1000

        # 尝试从帧中读取时间戳
        # 这需要 OCR 或简单的数字识别
        # 简化版本：假设帧是视频帧，我们需要手动比较

        return None  # 需要实现 OCR

    def measure_latency_manual(self) -> float:
        """
        手动测量延迟：通过快速截图对比。

        方法：
        1. 用户准备手机显示时间
        2. 脚本截取 scrcpy 窗口
        3. 用户输入手机显示的时间
        4. 计算延迟
        """
        print("\n" + "="*60)
        print("手动延迟测量模式")
        print("="*60)
        print("\n准备步骤：")
        print("1. 在手机上打开一个显示毫秒级时间的页面/应用")
        print("2. 启动 scrcpy 连接手机")
        print("3. 按 Enter 开始测量...")
        input()

        latencies = []

        for i in range(self.sample_count):
            print(f"\n测量 #{i+1}/{self.sample_count}")

            # 记录当前 PC 时间
            pc_time_before = datetime.now()

            print("观察 scrcpy 窗口中的时间，然后快速输入手机显示的时间（格式: HH:MM:SS.mmm）")
            phone_time_str = input("手机时间: ").strip()

            # 记录当前 PC 时间
            pc_time_after = datetime.now()

            try:
                # 解析手机时间
                parts = phone_time_str.split(':')
                if len(parts) == 3:
                    h, m, s_parts = int(parts[0]), int(parts[1]), parts[2]
                    if '.' in s_parts:
                        s, ms = int(s_parts.split('.')[0]), int(s_parts.split('.')[1])
                    else:
                        s, ms = int(s_parts), 0

                    # 假设手机时间和 PC 时间在同一天
                    phone_datetime = datetime.now().replace(
                        hour=h, minute=m, second=s, microsecond=ms * 1000
                    )

                    # 计算延迟（PC 时间 - 手机时间）
                    # 使用平均 PC 时间来减少输入延迟的影响
                    pc_avg_time = pc_time_before + (pc_time_after - pc_time_before) / 2

                    # 计算延迟
                    latency = (pc_avg_time - phone_datetime).total_seconds() * 1000

                    # 处理跨天情况
                    if latency < -12 * 3600 * 1000:  # 超过半天负数，可能是跨天
                        latency += 24 * 3600 * 1000
                    elif latency > 12 * 3600 * 1000:
                        latency -= 24 * 3600 * 1000

                    latencies.append(latency)
                    print(f"  延迟: {latency:.0f}ms")

            except Exception as e:
                print(f"  解析失败: {e}")
                continue

        if latencies:
            self.results = latencies
            self._print_stats()

        return latencies

    def measure_latency_screenshot(self, window_title: str = "scrcpy") -> list:
        """
        通过截图自动测量延迟。

        方法：
        1. 截取 scrcpy 窗口
        2. 使用 OCR 识别窗口中的时间
        3. 与当前 PC 时间比较
        """
        try:
            import pyautogui
            import pytesseract
            from PIL import Image
        except ImportError:
            print("需要安装: pip install pyautogui pytesseract pillow")
            print("还需要安装 Tesseract OCR: https://github.com/tesseract-ocr/tesseract")
            return []

        print("\n" + "="*60)
        print("自动截图延迟测量模式")
        print("="*60)

        latencies = []

        for i in range(self.sample_count):
            # 截图
            pc_time = datetime.now()

            try:
                # 查找窗口并截图
                window = pyautogui.getWindowsWithTitle(window_title)
                if not window:
                    print(f"未找到窗口: {window_title}")
                    continue

                win = window[0]
                if win.isMinimized:
                    win.restore()

                # 截取窗口区域
                left, top, width, height = win.left, win.top, win.width, win.height
                screenshot = pyautogui.screenshot(region=(left, top, width, height))

                # OCR 识别
                # 预处理图像以提高 OCR 准确性
                img = screenshot.convert('L')  # 灰度
                img = img.point(lambda x: 0 if x < 128 else 255)  # 二值化

                text = pytesseract.image_to_string(img, config='--psm 7 -c tessedit_char_whitelist=0123456789:.')

                # 解析时间
                text = text.strip().replace(' ', '')
                if ':' in text:
                    try:
                        parts = text.split(':')
                        if len(parts) >= 3:
                            h, m = int(parts[0]), int(parts[1])
                            s_parts = parts[2].split('.')
                            s = int(s_parts[0])
                            ms = int(s_parts[1]) if len(s_parts) > 1 else 0

                            phone_datetime = datetime.now().replace(
                                hour=h, minute=m, second=s, microsecond=ms * 1000
                            )

                            latency = (pc_time - phone_datetime).total_seconds() * 1000

                            # 处理跨天
                            if latency < -12 * 3600 * 1000:
                                latency += 24 * 3600 * 1000
                            elif latency > 12 * 3600 * 1000:
                                latency -= 24 * 3600 * 1000

                            latencies.append(latency)
                            print(f"#{i+1}: 手机={text}, PC={pc_time.strftime('%H:%M:%S.%f')[:-3]}, 延迟={latency:.0f}ms")
                    except Exception as e:
                        print(f"#{i+1}: 解析失败 '{text}': {e}")

            except Exception as e:
                print(f"#{i+1}: 截图失败: {e}")

            time.sleep(0.5)  # 间隔

        if latencies:
            self.results = latencies
            self._print_stats()

        return latencies

    def measure_latency_photodiode(self) -> list:
        """
        光电二极管延迟测量（需要硬件支持）。

        方法：
        1. 手机屏幕显示快速闪烁的图案
        2. 光电二极管同时监测手机屏幕和 PC 显示器
        3. 计算时间差
        """
        print("\n光电二极管测量模式需要额外硬件支持")
        print("请使用专业设备如:")
        print("  - Raspberry Pi + 光电二极管")
        print("  - 专业延迟测试仪")
        return []

    def _print_stats(self):
        """打印延迟统计"""
        if not self.results:
            return

        results = sorted(self.results)
        n = len(results)

        avg = sum(results) / n
        min_v = min(results)
        max_v = max(results)
        p50 = results[n // 2]
        p95 = results[int(n * 0.95)]

        print("\n" + "="*60)
        print("端到端延迟统计")
        print("="*60)
        print(f"样本数: {n}")
        print(f"平均:   {avg:.0f}ms")
        print(f"最小:   {min_v:.0f}ms")
        print(f"最大:   {max_v:.0f}ms")
        print(f"P50:    {p50:.0f}ms")
        print(f"P95:    {p95:.0f}ms")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description='端到端延迟测试')
    parser.add_argument('--host', type=str, default='192.168.5.4', help='设备IP地址')
    parser.add_argument('--port', type=int, default=27183, help='设备端口')
    parser.add_argument('--count', type=int, default=30, help='采样次数')
    parser.add_argument('--mode', type=str, default='manual',
                        choices=['manual', 'screenshot', 'http'],
                        help='测量模式: manual=手动输入, screenshot=截图OCR, http=启动HTTP服务器')
    parser.add_argument('--http-port', type=int, default=8080, help='HTTP服务器端口')

    args = parser.parse_args()

    tester = LatencyTester(args.host, args.port, args.count)

    if args.mode == 'http':
        # 启动 HTTP 服务器
        tmpdir, original_dir = tester.run_http_server(args.http_port)
        print("\nHTTP 服务器已启动")
        print(f"请在手机上打开: http://<你的电脑IP>:{args.http_port}/time.html")
        print("\n然后使用其他模式进行测量")
        print("按 Ctrl+C 退出")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    elif args.mode == 'manual':
        tester.measure_latency_manual()

    elif args.mode == 'screenshot':
        tester.measure_latency_screenshot()


if __name__ == '__main__':
    main()
