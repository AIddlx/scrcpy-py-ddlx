"""
日志配置模块

提供统一的日志配置，支持：
- 用户缓存目录存储日志
- 自动清理旧日志
- 控制台简要输出
- 文件输出（级别可配置）

日志级别控制（优先级从高到低）：
1. 环境变量 SCRCPY_DEBUG=1        → DEBUG（开发者强制全量日志）
2. 环境变量 SCRCPY_LOG_LEVEL=X    → 指定级别
3. 命令行参数 --log-level=X       → 指定级别
4. 默认值                          → WARNING（普通用户最少日志）

Usage:
    from scrcpy_py_ddlx.core.logging_config import setup_logging, get_log_dir

    # 获取日志目录
    log_dir = get_log_dir()

    # 设置日志（返回日志文件路径）
    log_file = setup_logging(prefix="session")

    # 或指定级别
    log_file = setup_logging(prefix="session", level=logging.INFO)
"""

import logging
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Union


# ============================================================================
# 日志级别常量
# ============================================================================

# 默认日志级别（普通用户）
DEFAULT_LOG_LEVEL = logging.WARNING

# 默认保留日志文件数量
DEFAULT_LOG_KEEP = 3

# 环境变量名
ENV_DEBUG = "SCRCPY_DEBUG"
ENV_LOG_LEVEL = "SCRCPY_LOG_LEVEL"
ENV_LOG_KEEP = "SCRCPY_LOG_KEEP"


def parse_log_level(value: str) -> int:
    """
    解析日志级别字符串。

    Args:
        value: 级别字符串，如 "DEBUG", "INFO", "WARNING", "ERROR" 或数字

    Returns:
        logging 级别常量
    """
    if value.isdigit():
        return int(value)

    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(value.upper(), DEFAULT_LOG_LEVEL)


def get_effective_log_level(arg_level: int = None) -> int:
    """
    获取生效的日志级别。

    优先级（从高到低）：
    1. SCRCPY_DEBUG=1 → DEBUG
    2. SCRCPY_LOG_LEVEL → 指定级别
    3. 命令行参数 arg_level
    4. 默认值 WARNING

    Args:
        arg_level: 命令行参数指定的级别

    Returns:
        生效的日志级别
    """
    # 1. SCRCPY_DEBUG 环境变量（开发者强制全量日志）
    if os.environ.get(ENV_DEBUG, "").lower() in ("1", "true", "yes"):
        return logging.DEBUG

    # 2. SCRCPY_LOG_LEVEL 环境变量
    env_level = os.environ.get(ENV_LOG_LEVEL)
    if env_level:
        return parse_log_level(env_level)

    # 3. 命令行参数
    if arg_level is not None:
        return arg_level

    # 4. 默认值（普通用户最少日志）
    return DEFAULT_LOG_LEVEL


def get_effective_log_keep(arg_keep: int = None) -> int:
    """
    获取生效的日志保留数量。

    优先级：
    1. SCRCPY_LOG_KEEP 环境变量
    2. 命令行参数 arg_keep
    3. 默认值 3

    Args:
        arg_keep: 命令行参数指定的保留数量

    Returns:
        生效的保留数量
    """
    env_keep = os.environ.get(ENV_LOG_KEEP)
    if env_keep and env_keep.isdigit():
        return int(env_keep)

    if arg_keep is not None:
        return arg_keep

    return DEFAULT_LOG_KEEP


def get_cache_dir() -> Path:
    """
    获取用户缓存目录。

    Windows: C:\\Users\\{用户名}\\.cache\\scrcpy-py-ddlx\\
    Linux/Mac: ~/.cache/scrcpy-py-ddlx/
    """
    if sys.platform == "win32":
        # Windows: 使用 USERPROFILE
        base = Path.home() / ".cache"
    else:
        # Linux/Mac
        base = Path.home() / ".cache"

    return base / "scrcpy-py-ddlx"


def get_log_dir() -> Path:
    """获取日志目录路径。"""
    log_dir = get_cache_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_config_path() -> Path:
    """获取配置文件路径。"""
    return get_cache_dir() / "config.json"


def load_config() -> dict:
    """
    加载配置文件。

    Returns:
        dict: 配置字典，至少包含 max_sessions
    """
    config_path = get_config_path()

    # 默认配置
    default_config = {
        "max_sessions": 3
    }

    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认值
                return {**default_config, **config}
        except (json.JSONDecodeError, IOError):
            pass

    return default_config


def save_config(config: dict) -> None:
    """保存配置文件。"""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)


def cleanup_old_logs(prefix: str = None, max_sessions: int = None, log_dir: Path = None) -> List[Path]:
    """
    清理旧的日志文件。

    Args:
        prefix: 日志文件前缀（如 "session", "preview"），None 表示所有
        max_sessions: 最大保留数量，None 则从配置读取
        log_dir: 日志目录，None 则使用默认目录

    Returns:
        删除的文件列表
    """
    if max_sessions is None:
        config = load_config()
        max_sessions = config.get("max_sessions", 3)

    if log_dir is None:
        log_dir = get_log_dir()

    # 获取所有日志文件
    if prefix:
        pattern = f"{prefix}_*.log"
    else:
        pattern = "*.log"

    log_files = sorted(
        log_dir.glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    deleted = []
    # 保留最新的 max_sessions 个文件
    for old_file in log_files[max_sessions:]:
        try:
            old_file.unlink()
            deleted.append(old_file)
        except OSError:
            pass

    return deleted


class ConsoleFilter(logging.Filter):
    """
    控制台日志过滤器 - 简要输出。

    过滤规则：
    - ERROR 及以上：总是显示
    - 高频刷屏日志：完全过滤（即使 WARNING 也不显示）
    - 其他模块：INFO+ 正常显示

    高频刷屏日志特征：
    - 每帧都会输出的日志（延迟追踪、帧跳过）
    - 每个包都会输出的日志（队列状态）
    - 正常运行中的重复警告（音频下溢）
    """

    # 高频消息模式（完全过滤，即使是 WARNING 也不显示）
    # 这些是"正常运行中的高频状态"，不是真正的错误
    SUPPRESS_PATTERNS = [
        # 帧相关 - 每帧都会输出
        r'[f0',             # [F00001] 帧追踪
        r'frame_skip',      # 帧跳过
        r'frame #',         # 帧编号
        r'total_pipeline',  # 管道延迟

        # 队列相关 - 每个包都可能输出
        r'[queue]',         # 队列状态
        r'backlog',         # 队列积压

        # 音频相关 - 每个音频帧
        r'[player]',        # 音频播放器状态
        r'pushed frame',    # 音频帧推送
        r'underflow',       # 音频下溢（正常运行中常见）

        # 配置相关 - 每个关键帧
        r'[config]',        # 配置包
        r'[key_frame]',     # 关键帧信息
        r'config_merge',    # 配置合并

        # SHM 相关
        r'shm_write',       # 共享内存写入

        # 控制消息相关 - 每次触摸/按键都会输出
        r'inject_touch',    # 触摸事件
        r'inject_key',      # 按键事件
        r'putting control message',  # 控制消息入队
        r'pointer_id',      # 指针ID
        r'action=move',     # 移动事件
        r'action=down',     # 按下事件
        r'action=up',       # 抬起事件

        # 预览窗口绘制 - 每帧都会输出
        r'[paint_gl]',      # OpenGL 绘制统计
        r'[paint]',         # 绘制事件
        r'tex_upload',      # 纹理上传
        r'paint_interval',  # 绘制间隔
    ]

    # 高频模块（这些模块的 INFO 不显示，只显示 WARNING+）
    NOISY_MODULES = [
        'audio',           # 音频模块
        'decoder',         # 解码器
        'demuxer',         # 解复用器
        'fec',             # FEC 处理
        'latency',         # 延迟追踪
        'shm',             # 共享内存
        'opengl',          # OpenGL 渲染
        'heartbeat',       # 心跳
        'sounddevice',     # 音频播放
    ]

    # 重要操作关键词（这些 INFO 必须显示）
    IMPORTANT_PATTERNS = [
        'connected',
        'disconnected',
        'error',
        'failed',
        'started',
        'stopped',
        'initialized',
        'cleanup',
        'screenshot',
        'file_transfer',
    ]

    def filter(self, record):
        # ERROR 及以上总是显示
        if record.levelno >= logging.CRITICAL:
            return True

        record_name_lower = record.name.lower()
        message_lower = record.getMessage().lower() if record.message else ""

        # 检查是否是高频消息（完全过滤）
        is_suppressed = any(
            p in message_lower for p in self.SUPPRESS_PATTERNS
        )
        if is_suppressed:
            return False  # 完全过滤，即使是 WARNING

        # ERROR 级别显示（CRITICAL 已在上面处理）
        if record.levelno >= logging.ERROR:
            return True

        # 检查是否是重要操作
        is_important = any(
            p in message_lower for p in self.IMPORTANT_PATTERNS
        )
        if is_important and record.levelno >= logging.INFO:
            return True

        # 检查是否是高频模块
        is_noisy_module = any(
            p in record_name_lower for p in self.NOISY_MODULES
        )
        if is_noisy_module:
            # 高频模块只显示 WARNING+（但上面已经过滤了高频消息）
            return record.levelno >= logging.WARNING

        # 其他模块显示 INFO+
        return record.levelno >= logging.INFO


# 模块名到阶段的映射（用于控制台日志显示）
PHASE_MAP = {
    # 主程序
    '__main__': 'MAIN',
    '__mp_main__': 'MAIN',

    # 连接阶段
    'core.adb': 'USB',
    'client.client': 'CONN',
    'client.connection': 'NET',
    'client.capability_cache': 'CONF',

    # 组件初始化
    'client.components': 'INIT',

    # 媒体处理
    'core.decoder': 'DEC',
    'core.demuxer': 'DEMUX',
    'core.audio': 'AUDIO',
    'core.av_player': 'SCREEN',

    # 控制通道
    'core.control': 'CTRL',
    'core.device_msg': 'DEV',
    'core.heartbeat': 'HEART',

    # 预览窗口
    'preview_process': 'PREVIEW',
    'simple_shm': 'SHM',
    'latency_tracker': 'LAT',
}


def get_phase(module_name: str) -> str:
    """根据模块名获取阶段标识。"""
    # 直接匹配
    if module_name in PHASE_MAP:
        return PHASE_MAP[module_name]

    # 部分匹配（处理子模块）
    module_lower = module_name.lower()
    for key, phase in PHASE_MAP.items():
        if key in module_name or module_name.startswith(key):
            return phase

    # 根据关键词推断
    if 'audio' in module_lower:
        return 'AUDIO'
    if 'video' in module_lower or 'decoder' in module_lower:
        return 'DEC'
    if 'demux' in module_lower:
        return 'DEMUX'
    if 'preview' in module_lower:
        return 'PREVIEW'
    if 'client' in module_lower or 'connection' in module_lower:
        return 'CONN'
    if 'shm' in module_lower:
        return 'SHM'

    # 默认使用简化的模块名
    name = module_name.split('.')[-1] if '.' in module_name else module_name
    return name[:6].upper()


class BriefFormatter(logging.Formatter):
    """
    简洁的日志格式化器（用于控制台）。

    格式：[级别] 时间 [阶段] 消息
    """

    def format(self, record):
        # 获取阶段标识
        phase = get_phase(record.name)

        # 简化时间（只显示时分秒）
        time_str = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')

        # 简化级别名
        level_map = {
            'DEBUG': 'D',
            'INFO': 'I',
            'WARNING': 'W',
            'ERROR': 'E',
            'CRITICAL': 'C'
        }
        level = level_map.get(record.levelname, record.levelname[0])

        return f"[{level}] {time_str} [{phase}] {record.getMessage()}"


def setup_logging(
    prefix: str = "session",
    level: int = None,
    log_format: str = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    cleanup: bool = True,
    quiet_console: bool = False,
    log_keep: int = None
) -> Optional[Path]:
    """
    设置日志配置。

    日志级别控制（优先级从高到低）：
    1. 环境变量 SCRCPY_DEBUG=1        → DEBUG（开发者全量日志）
    2. 环境变量 SCRCPY_LOG_LEVEL=X    → 指定级别
    3. 命令行参数 level=X              → 指定级别
    4. 默认值 WARNING                  → 普通用户最少日志

    Args:
        prefix: 日志文件前缀
        level: 日志级别（None 则使用环境变量或默认值）
        log_format: 日志格式
        cleanup: 是否清理旧日志
        quiet_console: 控制台静默模式（只显示 ERROR+），用于 MCP 服务器
        log_keep: 保留日志文件数量（None 则使用环境变量或默认值）

    Returns:
        日志文件路径，如果级别为 CRITICAL（禁用日志）则返回 None
    """
    # 获取生效的日志级别
    effective_level = get_effective_log_level(level)
    effective_keep = get_effective_log_keep(log_keep)

    # 如果级别为 CRITICAL，禁用日志文件
    if effective_level >= logging.CRITICAL:
        # 只配置控制台错误输出
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        root_logger.setLevel(logging.CRITICAL)
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.CRITICAL)
        console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
        root_logger.addHandler(console_handler)
        return None

    # 确保日志目录存在
    log_dir = get_log_dir()

    # 支持 prefix 中包含子目录（如 "test_gui_logs/scrcpy_test"）
    prefix_path = Path(prefix.replace("\\", "/"))
    if "/" in prefix:
        # prefix 包含子目录
        subdir = prefix_path.parent
        file_prefix = prefix_path.name
        log_dir = log_dir / subdir
        log_dir.mkdir(parents=True, exist_ok=True)
    else:
        file_prefix = prefix

    # 创建日志文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"{file_prefix}_{timestamp}.log"

    # 清理旧日志
    if cleanup:
        cleanup_old_logs(prefix=file_prefix, max_sessions=effective_keep, log_dir=log_dir)

    # 重置现有处理器
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 文件处理器：使用生效的日志级别
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(effective_level)
    file_handler.setFormatter(logging.Formatter(log_format))

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    if quiet_console:
        # 静默模式：只显示 ERROR+ 级别
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    else:
        # 正常模式：简要输出
        console_handler.setLevel(effective_level)
        console_handler.setFormatter(BriefFormatter())
        console_handler.addFilter(ConsoleFilter())

    # 配置根日志器
    root_logger.setLevel(effective_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return log_file


def get_log_file_path(prefix: str = "session") -> Path:
    """
    获取新的日志文件路径（不设置 logging）。

    用于子进程只需要日志文件路径的情况。
    """
    log_dir = get_log_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return log_dir / f"{prefix}_{timestamp}.log"
