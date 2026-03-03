# 网络模式 cleanup 参数与 stay_alive 未联动

## 问题描述

网络模式下，即使没有使用 `--stay-alive` 参数，客户端连接失败后服务端仍然残留在设备上运行。

日志示例：
```
2026-03-03 22:07:35,415 | ERROR | scrcpy_py_ddlx.client.client | Network connection failed: timed out
```

服务端未被终止，继续在设备后台运行。

## 原因分析

`tests_gui/test_network_direct.py:689` 行硬编码了 `cleanup=false`：

```python
server_cmd += (
    f"video=true {audio_params} control=true send_device_meta=true send_dummy_byte=true cleanup=false"
)
```

### 参数含义

| 参数 | 含义 |
|------|------|
| `cleanup=true` | 客户端断开连接后，服务端自动退出 |
| `cleanup=false` | 客户端断开连接后，服务端继续运行 |
| `stay_alive=true` | 服务端允许多次连接，不自动退出 |
| `stay_alive=false` | 服务端只接受一次连接 |

### 当前问题

- 无论 `--stay-alive` 是 True 还是 False，`cleanup` 都是 `false`
- 服务端使用 `nohup setsid` 启动成为独立进程
- 客户端连接失败后没有机会发送终止命令
- 结果：服务端残留在设备上

## 正确逻辑

| stay_alive | cleanup | 预期行为 |
|------------|---------|----------|
| `false`（默认） | `true` | 客户端断开 → 服务端自动退出 |
| `true` | `false` | 服务端持续运行，等待重连 |

## 修复方案

### 1. cleanup 参数联动

修改 `tests_gui/test_network_direct.py`，让 `cleanup` 参数与 `stay_alive` 联动：

```python
# cleanup: true = server exits when client disconnects (default)
#          false = server keeps running for reconnection (--stay-alive mode)
cleanup_flag = "false" if args.stay_alive else "true"
server_cmd += (
    f"video=true {audio_params} control=true send_device_meta=true send_dummy_byte=true cleanup={cleanup_flag}"
)
```

### 2. 连接失败后清理服务端

`cleanup=true` 只在客户端成功连接后断开时生效。如果连接失败（超时），服务端不知道客户端已放弃，会继续等待。

在 `finally` 块中添加清理逻辑：

```python
# Kill server if not in stay_alive mode and ADB is available
if not args.stay_alive:
    try:
        check_result = subprocess.run(
            ['adb', 'devices'],
            capture_output=True, text=True, timeout=5
        )
        has_device = 'device' in check_result.stdout and '\tdevice' in check_result.stdout
        if has_device:
            print("[INFO] Stopping server on device...")
            subprocess.run(["adb", "shell", "pkill -f app_process"],
                          capture_output=True, timeout=5)
    except Exception:
        pass  # Ignore errors during cleanup
```

## 修复日期

2026-03-03

## 状态

✅ 已修复
