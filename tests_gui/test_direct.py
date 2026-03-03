"""
直接引用源码的测试脚本 - 无需安装包
纯 USB 模式，不支持无线连接

运行方式:
    cd C:\Project\IDEA\2\new\scrcpy-py-ddlx
    python -X utf8 tests_gui/test_direct.py

要求:
    - USB 线连接手机
    - 手机开启 USB 调试
    - 已授权此电脑调试
"""

import sys
import logging
import time
import threading
import subprocess
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志 - 使用统一的日志配置模块
from scrcpy_py_ddlx.core.logging_config import setup_logging, get_effective_log_level, get_effective_log_keep

# 解析命令行参数中的日志选项
import argparse
log_parser = argparse.ArgumentParser(add_help=False)
log_parser.add_argument("--log-level", type=str, default=None,
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Log level")
log_parser.add_argument("--log-keep", type=int, default=None,
                        help="Number of log files to keep")
log_args, _ = log_parser.parse_known_args()

# 设置日志（使用 test_gui_logs 子目录）
log_file = setup_logging(
    prefix="test_gui_logs/scrcpy_test",
    level=logging.DEBUG if log_args.log_level == "DEBUG" else (
        {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING,
         "ERROR": logging.ERROR, "CRITICAL": logging.CRITICAL}.get(log_args.log_level, None)
    ) if log_args.log_level else None,
    log_keep=log_args.log_keep
)

logger = logging.getLogger(__name__)

# 提示日志文件位置
effective_level = get_effective_log_level()
effective_keep = get_effective_log_keep(log_args.log_keep)
if log_file:
    print(f"[INFO] 日志文件: {log_file}")
print(f"[INFO] 日志级别: {logging.getLevelName(effective_level)}, 保留数量: {effective_keep}")
print()

# 全局变量保持窗口和客户端存活
_global_client = None
_global_window = None
_recording_stop_event = None

# ===== 音频录制配置 =====
# 录制开关
ENABLE_AUDIO_RECORDING = False  # 改为 False 禁用自动录制

# 录制格式: 'opus', 'mp3', 'wav'
AUDIO_FORMAT = 'opus'

# 录制时长（秒），None 表示无限制（直到手动停止）
RECORDING_DURATION = 10  # 例如 10 秒

# 录制文件名（自动添加时间戳）
def get_recording_filename():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"recording_{timestamp}.{AUDIO_FORMAT}"


def list_usb_devices():
    """
    获取已连接的 USB 设备列表

    只返回 USB 设备（序列号不含冒号），
    不包含网络设备（如 192.168.x.x:5555）
    """
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=5
        )
        lines = result.stdout.strip().split('\n')
        usb_devices = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('List of devices'):
                parts = line.split()
                if len(parts) >= 2 and parts[1] == 'device':
                    # USB 设备序列号不含冒号，网络设备含冒号（如 ip:5555）
                    if ':' not in parts[0]:
                        usb_devices.append(parts[0])
        return usb_devices
    except Exception as e:
        logger.error(f"获取设备列表失败: {e}")
        return []


# ============================================================================
# 以下为 5555 无线模式相关代码，已注释禁用
# ============================================================================

# import re
# import socket
# from concurrent.futures import ThreadPoolExecutor, as_completed

# def check_adb_port(ip):
#     """检查指定 IP 的 5555 端口是否开放"""
#     try:
#         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         sock.settimeout(0.5)
#         result = sock.connect_ex((ip, 5555))
#         sock.close()
#         return ip if result == 0 else None
#     except Exception:
#         return None

# def auto_discover_device():
#     """自动发现并连接设备（已禁用）"""
#     # 此函数包含 5555 端口扫描和无线连接逻辑
#     # 纯 USB 模式下不需要
#     pass

# def enable_tcpip_5555(device_serial):
#     """启用 TCP/IP 5555 模式（已禁用）"""
#     # subprocess.run(["adb", "-s", device_serial, "tcpip", "5555"], ...)
#     pass

# def scan_network_for_adb():
#     """扫描局域网寻找 ADB 设备（已禁用）"""
#     # 此函数扫描 5555 端口
#     pass

# def connect_wireless(device_ip):
#     """无线连接设备（已禁用）"""
#     # subprocess.run(["adb", "connect", f"{device_ip}:5555"], ...)
#     pass

# ============================================================================


def _timed_recording_thread(duration: float, client):
    """后台线程：定时停止录制"""
    try:
        logger.info(f"[定时器] 录制将在 {duration} 秒后自动停止...")
        time.sleep(duration)
        logger.info(f"[定时器] 录制时间到，正在停止...")
        filename = client.stop_opus_recording()
        if filename:
            file_size = Path(filename).stat().st_size / 1024
            print(f"\n========================================")
            print(f"[SUCCESS] 定时录制已完成!")
            print(f"  文件名: {filename}")
            print(f"  大小: {file_size:.1f} KB")
            print(f"  格式: OGG Opus (原始 OPUS 包)")
            print(f"========================================\n")
            print("[INFO] 窗口仍可继续使用，按 Ctrl+C 或关闭窗口退出")
    except Exception as e:
        logger.error(f"[定时器] 错误: {e}")


def main():
    """主测试入口 - 纯 USB 模式"""
    global _global_client, _global_window, _recording_stop_event

    print("=" * 60)
    print("scrcpy-py-ddlsx 纯 USB 模式测试")
    print("=" * 60)
    print("[INFO] 本脚本仅支持 USB 连接，不支持无线模式")
    print()

    # 检查依赖
    try:
        import numpy as np
        print(f"[PASS] numpy: {np.__version__}")
    except ImportError:
        print("[FAIL] numpy 未安装")
        return

    try:
        from PySide6.QtWidgets import QApplication
        print(f"[PASS] PySide6 已安装")
    except ImportError:
        print("[FAIL] PySide6 未安装")
        return

    try:
        import av
        print(f"[PASS] PyAV: {av.__version__}")
    except ImportError:
        print("[FAIL] PyAV 未安装")
        return

    # 直接导入源码模块
    try:
        from scrcpy_py_ddlx.client import ScrcpyClient, ClientConfig
        from scrcpy_py_ddlx.core.player.video import create_video_window
        print("[PASS] 源码模块导入成功")
    except ImportError as e:
        print(f"[FAIL] 源码模块导入失败: {e}")
        return

    print("\n正在创建客户端...")

    # 音频录制提示
    if ENABLE_AUDIO_RECORDING:
        print(f"[INFO] 音频录制: 启用")
        print(f"[INFO] 录制格式: {AUDIO_FORMAT.upper()}")
        if RECORDING_DURATION:
            print(f"[INFO] 录制时长: {RECORDING_DURATION} 秒 (自动停止)")
        else:
            print(f"[INFO] 录制时长: 无限制（随窗口关闭停止）")
    else:
        print("[INFO] 音频录制: 禁用")

    # USB 设备检测
    print("\n正在检测 USB 设备...")
    usb_devices = list_usb_devices()

    if not usb_devices:
        print("[ERROR] 未检测到 USB 设备")
        print("[ERROR]")
        print("[ERROR] 请确保：")
        print("[ERROR]   1. USB 线已正确连接")
        print("[ERROR]   2. 手机已解锁")
        print("[ERROR]   3. USB 调试已开启")
        print("[ERROR]   4. 已授权此电脑进行调试")
        print("[ERROR]")
        print("[ERROR] 提示：本脚本仅支持 USB 连接")
        print("[ERROR]       如需无线连接，请使用 test_network_direct.py")
        print("[ERROR]")
        return

    print(f"[INFO] 检测到 {len(usb_devices)} 个 USB 设备:")
    for device in usb_devices:
        print(f"  - {device}")

    device_id = usb_devices[0]
    print(f"\n[INFO] 使用设备: {device_id}")

    # 创建客户端配置，指定设备序列号
    config = ClientConfig(
        device_serial=device_id,  # USB 设备序列号
        host="localhost",
        port=27183,
        show_window=True,  # 显示视频窗口
        audio=True,  # 启用音频
        audio_dup=False,  # 设为 True 可同时播放到手机和电脑
        clipboard_autosync=True,  # 启用剪贴板自动同步（PC ↔ 设备）
        bitrate=3000000,  # 3 Mbps
        max_fps=30,  # 30fps
    )

    # 创建客户端
    client = ScrcpyClient(config)
    _global_client = client

    print("正在连接到设备...")

    try:
        # 连接到设备
        client.connect()

        print(f"\n========================================")
        print(f"[SUCCESS] 连接成功!")
        print(f"  设备名称: {client.state.device_name}")
        print(f"  设备分辨率: {client.state.device_size[0]}x{client.state.device_size[1]}")
        print(f"========================================\n")

        # 初始化文件推送器（支持拖放文件传输）
        from scrcpy_py_ddlx.core.file_pusher import init_file_pusher

        def on_file_transfer_complete(success: bool, action: str, file_path: str):
            """文件传输完成回调"""
            filename = Path(file_path).name
            if success:
                if action == "install":
                    print(f"[SUCCESS] APK 安装成功: {filename}")
                else:
                    print(f"[SUCCESS] 文件推送成功: {filename}")
            else:
                print(f"[ERROR] {'安装' if action == 'install' else '推送'}失败: {filename}")

        file_pusher = init_file_pusher(
            device_serial=device_id,
            on_complete=on_file_transfer_complete
        )
        print("[INFO] 文件传输已启用 (拖放 APK 或文件到窗口)")

        # 启动音频录制 (使用原始 OPUS 包录制，零 CPU 开销)
        if ENABLE_AUDIO_RECORDING:
            recording_filename = get_recording_filename()
            print(f"[INFO] 开始音频录制 (原始 OPUS): {recording_filename}")

            if not client.start_opus_recording(recording_filename):
                print("[WARN] OPUS 录制启动失败")
            else:
                if RECORDING_DURATION:
                    # 有时长限制的录制 - 启动后台定时线程
                    print(f"[INFO] 录制中... ({RECORDING_DURATION} 秒后自动停止)")
                    _recording_stop_event = threading.Thread(
                        target=_timed_recording_thread,
                        args=(RECORDING_DURATION, client),
                        daemon=True
                    )
                    _recording_stop_event.start()
                else:
                    # 无限制录制（随窗口关闭停止）
                    print(f"[INFO] 录制中... (关闭窗口将停止录制)")

        print("\n视频窗口已显示，你可以:")
        print("  - 使用鼠标点击/拖拽控制设备")
        print("  - 使用键盘输入文字")
        print("  - 使用滚轮滚动")
        print("  - 拖放 APK 文件到窗口安装")
        print("  - 拖放其他文件到窗口推送到设备")
        print("\n关闭窗口或按 Ctrl+C 断开连接...")

        # 使用Qt事件循环运行客户端
        # 这将启动Qt事件循环来处理视频渲染和用户输入
        client.run_with_qt()

    except KeyboardInterrupt:
        print("\n\n用户中断连接")
    except Exception as e:
        print(f"\n[ERROR] 连接失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理
        print("\n正在清理...")

        # 停止音频录制（如果还在录制中）
        if ENABLE_AUDIO_RECORDING and client:
            try:
                filename = client.stop_opus_recording()
                if filename:
                    file_size = Path(filename).stat().st_size / 1024
                    print(f"\n========================================")
                    print(f"[SUCCESS] OPUS 录制已保存!")
                    print(f"  文件名: {filename}")
                    print(f"  大小: {file_size:.1f} KB")
                    print(f"  格式: OGG Opus (原始 OPUS 包)")
                    print(f"========================================")
            except Exception as e:
                print(f"[WARN] 停止录制时出错: {e}")

        if _global_client is not None:
            try:
                _global_client.disconnect()
            except:
                pass
        print("测试完成")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FATAL] {e}")
        import traceback
        traceback.print_exc()
