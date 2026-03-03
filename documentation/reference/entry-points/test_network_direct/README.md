# test_network_direct.py 文档

> 网络模式测试入口 (TCP 控制 + UDP 媒体)

---

## 概述

| 属性 | 值 |
|------|-----|
| **文件路径** | `tests_gui/test_network_direct.py` |
| **连接模式** | TCP 控制 + UDP 视频/音频 |
| **主要功能** | 纯网络模式、FEC、低延迟优化 |
| **代码行数** | ~980 行 |
| **特点** | USB 仅用于启动服务端，之后可拔掉 |

---

## 目录结构

```
test_network_direct/
├── README.md           # 本文件
├── dependencies.md     # 依赖清单
├── features/           # 功能详解 (多层级)
│   ├── overview.md     # 功能概览
│   ├── network.md      # 网络模式
│   ├── fec.md          # FEC 前向纠错
│   ├── low_latency.md  # 低延迟优化
│   └── auth.md         # 认证机制
├── usage.md            # 使用说明
└── cli_reference.md    # 命令行参数
```

---

## 快速开始

```bash
# 自动检测设备 IP (推荐)
python -X utf8 tests_gui/test_network_direct.py

# 指定设备 IP
python -X utf8 tests_gui/test_network_direct.py --ip 192.168.1.100

# 启用 FEC
python -X utf8 tests_gui/test_network_direct.py --fec frame

# 低延迟模式
python -X utf8 tests_gui/test_network_direct.py --low-latency --multiprocess
```

---

## 核心特性

### 1. 纯网络模式

- TCP 控制通道 (27184)
- UDP 视频流 (27185)
- UDP 音频流 (27186)
- TCP 文件传输 (27187)

### 2. FEC 前向纠错

- 帧级 FEC (frame)
- 片级 FEC (fragment)
- 独立视频/音频 FEC 控制

### 3. 低延迟优化

- MediaCodec 低延迟模式
- 编码器优先级控制
- 帧跳过
- 多进程解码 (GIL 避免)

### 4. 认证机制

- HMAC-SHA256 Challenge-Response
- 密钥自动生成和分发

---

## 与其他入口的对比

| 特性 | test_direct.py | test_network_direct.py |
|------|---------------|----------------------|
| 控制通道 | ADB 隧道 | TCP 直接 |
| 视频通道 | ADB 隧道 | UDP |
| USB 依赖 | 全程 | 仅启动时 |
| 延迟 | ~100ms | ~50ms |
| FEC | ❌ | ✅ |
| 认证 | ❌ | ✅ |

---

## 详细文档

- [dependencies.md](dependencies.md) - 依赖清单
- [features/overview.md](features/overview.md) - 功能概览
- [usage.md](usage.md) - 使用说明
- [cli_reference.md](cli_reference.md) - 命令行参数参考
