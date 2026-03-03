# 齺拷贝 GPU 模式状态

> 状态: 📋 信息
> 日期: 2026-03-01

---

## 当前状态

**零拷贝 GPU 模式未启用**，当前使用 **CPU 拷贝模式**：GPU 解码 → CPU 内存 → GPU 纹理

---

## 抣况分析

### CUDA-GL Interop

```
[CUDA-GL] Loaded CUDA runtime: C:\...\CUDA\v13.0\bin\x64\cudart64_13.dll
[CUDA-GL] CUDA-OpenGL Interop functions loaded successfully
```

✅ CUDA 运行时和 Interop 函数加载成功

### 零拷贝解码器

```
[LOW_DELAY] Hardware decoder surfaces=2 (ultra low latency mode)
```

✅ 硬件解码器工作正常

### 零拷贝路径

```
[DECODER] NV12 dict: y_shape=..., u_shape=..., v_shape=...
```

❌ **未进入零拷贝路径**（没有 `is_gpu=True` 的日志）

---

## 原因

零拷贝模式需要 **环境变量** `SCRCPY_ZERO_COPY_GPU=1`

```python
# video.py 第 394-395 行
if ZERO_COPY_GPU_ENABLED and HWACCEL_AVAILABLE:
    self._zero_copy_mode = True
```

当前环境变量未设置， 所以零拷贝模式未启用。

### 其他要求

- PyAV 17+ (支持 `is_hw_owned` 参数)
- 当前版本: PyAV 16.1.0

---

## 数据流对比

| 模式 | 路径 | 延迟 |
|------|------|------|
| CPU 拷贝 (当前) | GPU解码 → CPU内存 → GPU纹理 | 较高 |
| 零拷贝 (未启用) | GPU解码 → GPU纹理 (直接) | 最低 |

---

## 如何启用

```bash
# 设置环境变量
set SCRCPY_ZERO_COPY_GPU=1

# 运行测试
python tests_gui/test_direct.py
```

---

## 验证零拷贝是否日志中应该看到:
```
[EXPERIMENTAL] Zero-copy GPU mode enabled: h264 with cuda
[OPENGL] Using TRUE ZERO-COPY (CUDA-GL Interop)```

---

## 相关文件

- `scrcpy_py_ddlx/core/decoder/video.py` - 解码器零拷贝逻辑
- `scrcpy_py_ddlx/core/player/video/opengl_widget.py` - CUDA-GL Interop
