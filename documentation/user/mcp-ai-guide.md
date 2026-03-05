# MCP 工具使用指南（AI 版）

本文档为 AI 助手提供 MCP 工具的精简使用指南。

---

## 核心原则

### 1. 始终先调用 get_state()

```
这是第一步。get_state() 返回：
- connected: 是否已连接设备
- mode: 服务器启动模式 ("adb" 或 "network")
- capabilities: 可用功能列表
- limitations: 不可用功能列表
```

### 2. 根据模式选择参数

| 服务器模式 | device_id | connection_mode |
|-----------|-----------|-----------------|
| `--adb` 启动 | 设备 serial | `adb_tunnel`（默认） |
| `--net` 启动 | 设备 IP 地址 | `network` |

**从 list_devices() 的 connect_hint 获取正确参数**

### 3. 检查功能可用性

调用前检查 `capabilities` 和 `limitations`：

```json
{
  "capabilities": ["control", "file", "screenshot"],
  "limitations": ["preview", "record_audio"]
}
```

- `preview` 在 limitations 中 → 不能调用 start_preview()
- `record_audio` 在 limitations 中 → 不能调用 record_audio()

---

## 工作流程

```
1. get_state()
   ├─ connected=true → 直接执行操作
   └─ connected=false → 查看 hint 和 retry_action

2. list_devices()（如需连接参数）
   ├─ 查看 server_mode 确定当前模式
   └─ 查看 connect_hint 获取正确参数

3. connect()（如需要）
   └─ 使用 connect_hint 中的参数

4. 执行操作
```

---

## 坐标系统

```
原点 (0,0): 屏幕左上角
X 轴: 向右递增 (0 到 width-1)
Y 轴: 向下递增 (0 到 height-1)

竖屏: width < height (例: 1080x2400)
横屏: width > height (例: 2400x1080)

重要: 旋转后 width/height 会交换，调用 get_state() 获取当前尺寸
```

---

## 常见错误

### 模式不匹配

```json
{
  "success": false,
  "mode_mismatch": true,
  "server_mode": "network",
  "requested_mode": "adb_tunnel",
  "example": "connect(device_id='192.168.x.x', connection_mode='network')"
}
```

**解决**: 按 example 字段的示例修正参数

### 功能不可用

```json
{
  "success": false,
  "error": "Video not enabled"
}
```

**解决**: 检查 get_state() 的 limitations，确认功能是否可用

---

## 文件路径

- 设备路径: `/sdcard/...` (Android 存储根目录)
- 下载文件夹: `/sdcard/Download/`
- 相机照片: `/sdcard/DCIM/Camera/`

---

## 完整示例

### 查看设备状态

```bash
curl -X POST http://127.0.0.1:3359/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_state","arguments":{}}}'
```

### 列出设备

```bash
curl -X POST http://127.0.0.1:3359/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_devices","arguments":{}}}'
```

### 点击屏幕

```bash
curl -X POST http://127.0.0.1:3359/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"tap","arguments":{"x":540,"y":1200}}}'
```

### 截图

```bash
curl -X POST http://127.0.0.1:3359/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"screenshot","arguments":{}}}'
```

### 列出文件

```bash
curl -X POST http://127.0.0.1:3359/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_dir","arguments":{"path":"/sdcard/Download"}}}'
```
