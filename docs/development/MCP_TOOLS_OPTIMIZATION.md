# MCP 工具描述优化

## 背景

阶跃AI 在测试 MCP 服务器时出现以下问题：

1. **不知道已连接状态**：AI 不知道服务器已经自动连接了设备
2. **传错参数**：传 serial 而不是 IP，因为不知道服务器启动模式
3. **破坏已有连接**：`connect()` 会断开现有连接再尝试新连接
4. **没有先检查状态**：直接调用 `connect()`，没有先调用 `get_state()`
5. **错误提示不清晰**：hint 没有告诉 AI 正确的参数应该是什么
6. **不知道功能状态**：AI 不知道 video/audio 是否启用

## 问题根因

MCP 服务器的 API 设计假设使用者是人类，但实际使用者是 AI：

| 传统 API 设计 | AI 作为使用者 |
|--------------|--------------|
| 假设用户读过文档 | 只看工具描述 |
| 用户知道上下文 | 上下文有限，需要明确提示 |
| 错误信息给人看 | 错误信息要能指导下一步行动 |
| 灵活性优先 | 明确的流程优先 |

## 解决方案

### 1. get_state 返回值增强

**优化前**：
```json
{
  "connected": false,
  "device_name": null,
  "device_size": null
}
```

**优化后**（未连接）：
```json
{
  "connected": false,
  "mode": "network",
  "hint": "Server started in network mode. Device should auto-connect when stay-alive server is running.",
  "retry_action": "Ensure stay-alive server is running on device, or use wake_up() to wake device."
}
```

**优化后**（已连接）：
```json
{
  "connected": true,
  "mode": "network",
  "device_name": "RMX1931",
  "width": 1080,
  "height": 2400,
  "orientation": "portrait",
  "capabilities": ["control", "file", "screenshot"],
  "limitations": ["preview", "record_audio"]
}
```

**新增字段**：
- `mode`: 启动模式（"adb" 或 "network"）
- `capabilities`: 可用功能列表
- `limitations`: 不可用功能列表
- `hint`: 状态说明
- `retry_action`: 下一步建议

### 2. list_devices 返回值增强

**优化后**：
```json
{
  "success": true,
  "count": 1,
  "devices": [{
    "serial": "c96d1705",
    "ip": "192.168.5.4",
    "connect_hint": {
      "adb_tunnel": {"device_id": "c96d1705", "connection_mode": "adb_tunnel"},
      "network": {"device_id": "192.168.5.4", "connection_mode": "network"}
    }
  }],
  "server_mode": "network",
  "mode_hint": "Server is in network mode. Use device's IP address for device_id."
}
```

**新增字段**：
- `server_mode`: 当前服务器模式
- `mode_hint`: 模式使用提示
- `devices[].connect_hint`: 每种模式应使用的连接参数

### 3. connect 错误返回增强

**优化后**（模式不匹配）：
```json
{
  "success": false,
  "error": "Failed to connect",
  "server_mode": "network",
  "requested_mode": "adb_tunnel",
  "mode_mismatch": true,
  "hint": "Server started with --net mode. Use connection_mode='network' and device_id='IP_ADDRESS'.",
  "example": "connect(device_id='192.168.x.x', connection_mode='network')"
}
```

**新增字段**：
- `server_mode`: 服务器启动模式
- `requested_mode`: 请求的连接模式
- `mode_mismatch`: 是否模式不匹配
- `example`: 正确调用示例

### 4. 工具描述改进

**connect**:
```
Connect to an Android device. IMPORTANT: Call get_state() FIRST to check
if already connected and to determine the correct connection_mode.
If server started with --adb, use connection_mode='adb_tunnel' (default).
If server started with --net, use connection_mode='network' and device_id
must be an IP address. Parameters must match the server startup mode.
```

**get_state**:
```
ALWAYS CALL THIS FIRST. Returns: connected (bool), mode (string: 'adb' or
'network'), capabilities (list of available features), limitations (list
of unavailable features). If connected: also returns device_name, width,
height, orientation. If not connected: returns hint and retry_action.
Use this to determine what operations are available before calling other tools.
```

**list_devices**:
```
List ADB connected devices. Returns devices with serial, ip, and connect_hint
showing correct parameters for each connection mode. Check server_mode and
mode_hint in the response to determine which connect_hint to use.
```

### 5. 日志显示修复

修复了 `--net` 模式下错误显示视频/音频信息的问题：

| 条件 | 显示 |
|------|------|
| `_enable_video = False` | 不显示视频端口、视频解码器 |
| `DEFAULT_AUDIO_ENABLED = False` | 不显示音频端口、音频解码器 |

## 代码改动

### ScrcpyMCPHandler 类

```python
# 新增属性
self._startup_mode = None       # "adb" 或 "network"
self._startup_video = False     # 启动时是否启用 video
self._startup_audio = False     # 启动时是否启用 audio

# 新增方法
def set_startup_config(self, mode: str, video: bool, audio: bool):
    """设置启动配置（由 main() 调用）"""
```

### main() 函数

```python
# 注入启动配置到 handler
startup_mode = "adb" if args.adb else ("network" if args.net else "unknown")
handler.set_startup_config(
    mode=startup_mode,
    video=_enable_video,
    audio=DEFAULT_AUDIO_ENABLED
)
```

## AI 使用流程（优化后）

```
1. AI 调用 get_state()
   - 如果 connected=true → 直接执行操作
   - 如果 connected=false → 查看 hint 和 retry_action

2. AI 调用 list_devices()
   - 查看 server_mode 确定当前模式
   - 查看 connect_hint 确定正确参数

3. AI 调用 connect()（如需要）
   - 使用 connect_hint 中的参数
   - 如果失败，查看 example 字段

4. AI 执行其他操作
   - 查看 capabilities 确认可用功能
   - 查看 limitations 确认不可用功能
```

## 文件

- `scrcpy_http_mcp_server.py`: 主要改动文件

## 日期

2026-03-05
