# test_network_direct.py

> **文件**: `tests_gui/test_network_direct.py`
> **功能**: 网络模式入口脚本

---

## 概述

`test_network_direct.py` 是纯网络模式 (TCP 控制 + UDP 媒体) 的主要入口，支持 FEC 和认证。

---

## 命令行参数

### 网络设置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--ip` | 自动检测 | 设备 IP |
| `--control-port` | 27184 | TCP 控制端口 |
| `--video-port` | 27185 | UDP 视频端口 |
| `--audio-port` | 27186 | UDP 音频端口 |

### FEC 设置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--fec` | - | FEC 模式: frame/fragment |
| `--fec-k` | 4 | 每组数据帧数 |
| `--fec-m` | 1 | 每组校验帧数 |

### 视频设置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--codec` | auto | 编解码器 |
| `--bitrate` | 2500000 | 码率 |
| `--max-fps` | 60 | 最大帧率 |
| `--cbr/--vbr` | vbr | 码率模式 |

### 低延迟优化

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--low-latency` | False | 低延迟模式 |
| `--multiprocess` | False | 多进程解码 |

### 服务端生命周期

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--reuse` | False | 复用服务器 |
| `--push/--no-push` | push | 推送 APK |
| `--stay-alive` | False | Stay-Alive 模式 |

### 认证

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--auth/--no-auth` | auth | 启用/禁用认证 |

---

## 服务端启动逻辑

```python
def start_server(args, device_serial):
    """
    启动服务端流程:

    1. 检查服务器是否运行
    2. (可选) 推送 APK
    3. (可选) 推送认证密钥
    4. 启动服务器 (nohup)
    """
```

---

## 工作流程

```
1. 解析参数
2. 自动检测/验证 IP
3. 查询设备编码器
4. 选择最佳编解码器
5. 检查/启动服务端
   ├── 推送认证密钥
   ├── 推送服务器 APK
   └── 启动 (nohup)
6. 创建 ClientConfig
7. 连接设备
8. 运行 Qt 事件循环
9. 保存服务端日志
```

---

## 运行示例

```bash
# 基本使用
python tests_gui/test_network_direct.py --ip 192.168.1.100

# 启用 FEC
python tests_gui/test_network_direct.py --fec frame --fec-k 8

# 完整配置
python tests_gui/test_network_direct.py \
    --ip 192.168.1.100 \
    --codec h265 \
    --bitrate 4000000 \
    --fec frame \
    --audio
```

---

## 日志

```
test_logs/scrcpy_network_test_YYYYMMDD_HHMMSS.log
test_logs/scrcpy_network_test_YYYYMMDD_HHMMSS_server.log
```

---

## 相关文档

- [fec_decoder.md](../client/fec_decoder.md) - FEC 解码
- [auth.md](../client/auth.md) - 认证模块
