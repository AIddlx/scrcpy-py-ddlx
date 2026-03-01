# 低延迟优化

> 减少 End-to-End 延迟的技术

---

## 延迟组成

```
总延迟 = 采集 + 编码 + 传输 + 解码 + 渲染

典型值:
  采集:     16ms (60fps)
  编码:     10-30ms
  传输:     5-20ms (WiFi)
  解码:     5-15ms (GPU)
  渲染:     5-10ms

总计:       40-90ms (理想情况)
```

---

## 优化选项

### 1. MediaCodec 低延迟模式

```bash
--low-latency
```

**效果**: 减少编码器缓冲延迟

**要求**: Android 11+

**注意**: 部分设备可能不支持

### 2. 编码器优先级

```bash
--encoder-priority 2  # realtime
```

| 值 | 级别 | 说明 |
|----|------|------|
| 0 | normal | 正常优先级 |
| 1 | urgent | 紧急 (默认) |
| 2 | realtime | 实时 |

### 3. 编码器缓冲

```bash
--encoder-buffer 1  # 禁用 B 帧
```

| 值 | 说明 |
|----|------|
| 0 | 自动 (默认) |
| 1 | 禁用 B 帧 |

### 4. 跳帧模式

```bash
--skip-frames        # 启用 (默认)
--no-skip-frames     # 禁用
```

**效果**: 丢弃积压帧，只处理最新帧

### 5. 多进程解码

```bash
--multiprocess
```

**效果**: 避免 Python GIL 竞争

**性能**: 延迟从 ~330ms 降至 ~150ms

---

## 配置组合

### 最低延迟

```bash
python test_network_direct.py \
    --low-latency \
    --encoder-priority 2 \
    --encoder-buffer 1 \
    --skip-frames \
    --multiprocess \
    --bitrate-mode cbr \
    --i-frame-interval 2
```

### 平衡模式

```bash
python test_network_direct.py \
    --encoder-priority 1 \
    --skip-frames \
    --bitrate-mode vbr
```

---

## 参数详解

### I-Frame 间隔

```bash
--i-frame-interval 2  # 2秒一个关键帧
```

| 值 | 效果 |
|----|------|
| 低 (0.5-2) | 快速恢复，带宽高 |
| 中 (5-10) | 平衡 |
| 高 (10+) | 带宽低，恢复慢 |

### 码率模式

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| VBR | 可变码率，质量优先 | 一般使用 |
| CBR | 恒定码率，带宽可控 | 弱网环境 |

---

## 延迟测量

### E2E 延迟追踪

```
UDP Header 包含 send_time_ns 字段:

接收延迟 = current_time - send_time_ns
```

### 日志输出

```
[INFO] E2E latency: 45.2ms (avg: 48.5ms, max: 65.3ms)
```

---

## 性能基准

| 配置 | 延迟 | CPU | 带宽 |
|------|------|-----|------|
| 默认 | ~100ms | 低 | 2.5 Mbps |
| 低延迟 | ~50ms | 中 | 3 Mbps |
| 最低延迟 | ~30ms | 高 | 4 Mbps |
| 多进程 | -50ms | 中 | 不变 |

---

## 相关文档

- [network.md](network.md) - 网络模式
- [fec.md](fec.md) - FEC 前向纠错
