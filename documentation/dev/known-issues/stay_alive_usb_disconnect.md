# Stay-Alive 模式 USB 断开后服务端被杀死

> 状态: ✅ 已修复
> 日期: 2026-03-01
> 影响版本: v1.4 及之前

---

## 问题描述

使用 `--stay-alive` 模式启动服务端后：

| 场景 | 预期行为 | 实际行为 |
|------|----------|----------|
| USB 连接时关闭客户端 | 服务端驻留 | ✅ 正常 |
| USB 断开后关闭客户端 | 服务端驻留 | ❌ 服务端被杀死 |

用户无法在断开 USB 后重新连接到设备。

---

## 相关修复：`--no-auth` 参数行为

同一天还修复了 `--no-auth` 参数的行为问题。

### 之前的问题

`--no-auth` 只影响服务端启动，不影响客户端认证响应：
- 客户端会自动加载本地密钥并响应服务端的认证挑战
- 导致 `--no-auth` 客户端仍能连接启用认证的服务端

### 修复后

`--no-auth` 完全控制认证行为：

| 阶段 | 行为 |
|------|------|
| 服务端启动 | 不添加 `auth_key_file` 参数 |
| 客户端连接 | 不加载本地密钥，不响应认证挑战 |

### 代码变更

| 文件 | 修改 |
|------|------|
| `config.py` | 添加 `auth_enabled: bool = True` |
| `client.py` | 检查 `config.auth_enabled`，单独捕获 `AuthError` |
| `connection.py` | 检测服务端是否要求认证（peek 第一个字节是否为 0xF0） |
| `test_network_direct.py` | 检查 `connect()` 返回值 |

## 根因分析

### 原因

服务端通过 `adb shell` 启动，即使使用了 `nohup`：

```bash
adb shell "nohup sh -c 'app_process ...' > /data/local/tmp/scrcpy_server.log 2>&1 &"
```

**问题**：`nohup` 只忽略 SIGHUP 信号，但服务端进程仍然是 ADB shell 进程的子进程。

当 USB 断开时：
1. ADB 连接断开
2. ADB shell 进程被系统杀死
3. 服务端进程（作为子进程）也被杀死

这是 Android 的一个安全机制，用于清理 ADB 会话相关的进程。

### 为什么 nohup 不够？

```
ADB shell (父进程)
  └── sh -c 'app_process ...' (子进程)
        └── app_process (服务端)
```

`nohup` 只防止 SIGHUP 信号，但无法阻止父进程死亡时子进程被一起杀死。

---

## 解决方案

使用 `setsid` 创建新的会话(session)，让服务端进程完全脱离 ADB shell 的进程组：

### 修复前

```bash
nohup sh -c 'app_process ...' > log 2>&1 &
```

### 修复后

```bash
nohup setsid sh -c 'app_process ...' > log 2>&1 &
```

### setsid 的作用

```
ADB shell (父进程) - 被杀死时不再影响服务端
  └── setsid sh -c (新会话 leader)
        └── app_process (服务端) - 独立运行
```

`setsid` 创建一个新的会话，服务端成为新会话的成员，不再属于 ADB shell 的进程组。

---

## 代码变更

文件: `tests_gui/test_network_direct.py`

```python
# 修复前
cmd = f"nohup sh -c '{server_cmd}' > /data/local/tmp/scrcpy_server.log 2>&1 &"

# 修复后
cmd = f"nohup setsid sh -c '{server_cmd}' > /data/local/tmp/scrcpy_server.log 2>&1 &"
```

---

## 验证步骤

1. 启动服务端（stay-alive 模式）：
   ```bash
   python tests_gui/test_network_direct.py --stay-alive
   ```

2. 确认服务端运行：
   ```bash
   adb shell "ps -A | grep app_process"
   ```

3. 断开 USB 线

4. 关闭客户端窗口

5. 重新连接（hot-connect 模式）：
   ```bash
   python tests_gui/test_network_direct.py --hot-connect --ip <设备IP>
   ```

6. 应该能成功连接，证明服务端仍在运行

---

## 注意事项

1. **设备兼容性**：大多数 Android 设备都有 `setsid` 命令，但某些旧设备可能没有。如果 `setsid` 不存在，启动命令会失败。

2. **替代方案**（如果 setsid 不可用）：
   ```bash
   nohup sh -c 'setsid app_process ...' > log 2>&1 &
   ```
   或使用 `daemonize` 工具（需要 root）

3. **服务端日志位置**：`/data/local/tmp/scrcpy_server.log`

---

## 修复 3: Hot-Connect 自动发现

### 问题

`--hot-connect` 不指定 `--ip` 时报错，无法自动发现服务器。

### 修复后

```bash
# 自动发现并连接（无需指定 IP）
python tests_gui/test_network_direct.py --hot-connect
```

### Discovery 解析修复

服务端响应格式：`SCRCPY_HERE <device_name> <ip> <mode>`

客户端解析时需要正确处理 `mode` 字段，避免把 `stay-alive` 当成 IP 的一部分。

```python
# 修复前
parts = payload.strip().split(None, 1)  # 只分2部分，mode 被包含在 ip 中

# 修复后
parts = payload.strip().split(None, 2)  # 分3部分，正确提取 ip
device_ip = parts[1]  # IP 始终是第二部分
```

文件：`scrcpy_py_ddlx/client/udp_wake.py`

---

## 修复 4: 日志路径统一

日志从项目目录移至用户缓存目录：

```
~/.cache/scrcpy-py-ddlx/logs/test_gui_logs/
├── scrcpy_test_*.log           # USB 模式日志
├── scrcpy_network_test_*.log   # 网络模式日志
└── *_server.log                # 服务端日志
```

---

## 相关文件

- `tests_gui/test_network_direct.py` - 客户端启动脚本
- `scrcpy/server/src/main/java/com/genymobile/scrcpy/Server.java` - 服务端 stay-alive 逻辑
- `scrcpy/server/src/main/java/com/genymobile/scrcpy/CleanUp.java` - CleanUp 进程中的 `Os.setsid()`

---

## 参考

- [Linux setsid(2) man page](https://man7.org/linux/man-pages/man2/setsid.2.html)
- [Android ADB process lifecycle](https://source.android.com/docs/core/adb)
