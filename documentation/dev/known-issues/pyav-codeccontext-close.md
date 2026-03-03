# PyAV AudioCodecContext.close() 不存在

## 问题描述

在音频解码器重置时，日志中出现以下警告：

```
DEBUG | Error closing codec context: 'av.audio.codeccontext.AudioCodecContext' object has no attribute 'close'
```

## 原因分析

PyAV 的 `CodecContext` 基类（包括 `AudioCodecContext` 和 `VideoCodecContext`）**没有公开的 `close()` 方法**。

PyAV 使用 Cython 的 `__dealloc__` 生命周期方法来释放资源：

```python
# PyAV 源码 (av/codec/codeccontext.pyx)
def __dealloc__(self):
    lib.avcodec_free_context(&self.ptr)
```

## 问题位置

`scrcpy_py_ddlx/core/audio/codecs/base.py:193-204`

```python
# 错误代码
def reset(self) -> None:
    if self._codec_context is not None:
        try:
            self._codec_context.close()  # 这个方法不存在
        except Exception as e:
            logger.debug(f"Error closing codec context: {e}")
```

## 解决方案

移除无意义的 `close()` 调用，直接将 `_codec_context` 设为 `None`，让 Python 垃圾回收机制处理旧对象。

```python
# 修复后
def reset(self) -> None:
    # PyAV CodecContext uses __dealloc__ for cleanup, no close() method
    # Just let Python's garbage collector handle the old context
    self._codec_context = None
    self._stream_analyzed = False
    self._actual_sample_rate = None
    self._actual_channels = None
    self._initialize_decoder()
```

## 影响

- **功能影响**: 无。由于已有 try/except 捕获，不影响实际运行
- **日志污染**: DEBUG 日志中会出现无意义的错误信息
- **修复优先级**: 低（不影响功能）

## 修复日期

2026-03-03

## 参考资料

- [PyAV GitHub - CodecContext](https://github.com/PyAV-Org/PyAV/blob/main/av/codec/codeccontext.pyx)
