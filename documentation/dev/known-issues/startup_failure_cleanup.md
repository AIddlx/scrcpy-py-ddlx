# 启动失败时清理服务端

> 日期：2026-03-02
> 状态：已解决

---

## 问题描述

### 场景

使用 `--stay-alive` 模式启动 MCP 服务器时：

```
python scrcpy_http_mcp_server.py --net --video --audio --stay-alive
```

### 问题流程

```
1. 推送服务端到手机 ✓
2. 启动服务端 (stay_alive=true) ✓
3. 建立网络连接... ✗ (超时/网络问题)
4. 退出
   ↓
   服务端仍在手机上运行！
```

### 影响

1. **残留进程**：手机上残留 `stay_alive=true` 的服务端
2. **资源浪费**：下次启动时要先杀掉再推送
3. **状态混乱**：用户排查问题时状态不干净

---

## 解决方案

### 设计思路

`--stay-alive` 的正确语义：
- ✓ 启动成功 + 断开连接 → 服务端继续运行
- ✗ **启动失败** → 应该清理服务端

### 实现

1. **添加全局状态跟踪**

```python
# Server state tracking (for cleanup on failure)
_server_started = False      # 服务端是否已启动
_server_device_id = None     # 服务端运行的设备ID
_server_stay_alive = False   # 服务端是否以stay_alive模式启动
```

2. **在服务端启动成功后记录状态**

```python
# on_startup() 中，服务端启动成功后
global _server_started, _server_device_id, _server_stay_alive
_server_started = True
_server_device_id = device_id
_server_stay_alive = _stay_alive
```

3. **修改 `_exit_on_failure()` 添加清理逻辑**

```python
def _exit_on_failure(reason: str, exit_code: int = 1):
    global _server_started, _server_device_id, _server_stay_alive

    # 清理手机上残留的服务端（如果已启动）
    if _server_started and _server_device_id:
        print("正在清理手机上的服务端...")
        kill_cmd = ["adb", "-s", _server_device_id, "shell", "pkill -9 -f app_process"]
        subprocess.run(kill_cmd, capture_output=True, timeout=5)
        print("服务端已清理 ✓")

    os._exit(exit_code)
```

---

## 验证结果

### 测试 1

```
日志: session_20260302_114725.log

11:47:29 | Server started on device abc12345, stay_alive=True
11:47:45 | Connection failed: Failed to connect
11:47:45 | Server cleanup: returncode=0 ✓
```

### 测试 2

```
日志: session_20260302_115013.log

11:50:16 | Server started on device abc12345, stay_alive=True
11:50:32 | Connection failed: Failed to connect
11:50:32 | Server cleanup: returncode=0 ✓
```

### ADB 验证

```bash
adb shell ps -A | grep app_process
# 无输出 → 手机上没有残留服务端 ✓
```

---

## 代码位置

| 文件 | 位置 |
|------|------|
| 全局变量 | `scrcpy_http_mcp_server.py` 约 3363-3366 行 |
| 状态设置 | `scrcpy_http_mcp_server.py` `on_startup()` 函数 |
| 清理逻辑 | `scrcpy_http_mcp_server.py` `_exit_on_failure()` 函数 |

---

## 相关文档

- [网络模式入口](../../project_analysis/features/entry_points/network_mode.md)
- [setsid vs stay_alive](../../project_analysis/features/connection/network_mode.md)
