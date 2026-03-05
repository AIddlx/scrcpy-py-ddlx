# MCP 工具重设计讨论

本文档记录 MCP 工具集的重设计讨论，供未来改进参考。

---

## 当前问题

### 1. 工具数量过多
- **63 个工具**，上下文开销大
- 小上下文模型难以处理

### 2. 调用顺序不明确
- 阶跃AI 不知道需要先 `get_state()` 检查连接状态
- 盲目调用 `connect()` 导致断开现有连接

### 3. 语义分散
- 连接管理：connect, disconnect, get_state, list_devices, discover_devices, push_server...
- 截图：screenshot, screenshot_device, screenshot_standalone
- 服务端：push_server, push_server_onetime, push_server_persistent, stop_server

### 4. 错误恢复困难
- `connect()` 会断开现有连接再尝试新连接
- 参数错误时，原有连接已丢失

---

## 当前工具分类（63 个）

| 类别 | 数量 | 工具 |
|------|------|------|
| 连接管理 | 11 | connect, disconnect, get_state, list_devices, discover_devices, get_device_ip, enable_wireless, connect_wireless, disconnect_wireless, restart_adb, push_server |
| 服务端推送 | 3 | push_server_onetime, push_server_persistent, stop_server |
| 截图 | 3 | screenshot, screenshot_device, screenshot_standalone |
| 预览 | 3 | start_preview, stop_preview, get_preview_status |
| 剪贴板 | 2 | get_clipboard, set_clipboard |
| 应用 | 2 | list_apps, open_app |
| 触控 | 3 | tap, long_press, swipe |
| 键盘 | 2 | press_key, input_text |
| 导航快捷键 | 8 | back, home, recent_apps, menu, enter, tab, escape, wake_up |
| D-Pad | 5 | dpad_up, dpad_down, dpad_left, dpad_right, dpad_center |
| 面板 | 3 | expand_notification_panel, expand_settings_panel, collapse_panels |
| 显示 | 4 | turn_screen_on, turn_screen_off, rotate_device, reset_video |
| 音量 | 2 | volume_up, volume_down |
| 录音 | 4 | record_audio, stop_audio_recording, is_recording_audio, get_recording_duration |
| 文件 | 6 | list_dir, pull_file, push_file, delete_file, make_dir, file_stat |

---

## 方案讨论

### 方案 1-2：扁平化/嵌套参数

**扁平化：** `input(action="tap", x=100, y=200)`
**嵌套：** `input(action="tap", params={"x": 100, "y": 200})`

**缺点**：参数混乱或 MCP 协议支持有限

---

### 方案 3：命名前缀分组（推荐，待实施）

保持独立工具但用命名前缀分组，减少 AI 理解成本。

#### 设备管理 `device_*`
- `device_status()` - 检查连接状态
- `device_connect(mode, device_id)` - 统一连接入口
- `device_disconnect()` - 断开连接
- `device_discover()` - 发现设备
- `device_push(mode)` - 推送服务端
- `device_stop()` - 停止服务端

#### 输入操作 `input_*`
- `input_tap(x, y)`
- `input_swipe(x1, y1, x2, y2, duration_ms)`
- `input_long_press(x, y, duration_ms)`
- `input_key(key_code)`
- `input_text(text)`

#### 导航 `nav_*`
- `nav_back()`, `nav_home()`, `nav_recent()`, `nav_menu()`
- `nav_enter()`, `nav_tab()`, `nav_escape()`, `nav_wake()`

#### D-Pad `dpad_*`
- `dpad_up()`, `dpad_down()`, `dpad_left()`, `dpad_right()`, `dpad_center()`

#### 媒体 `media_*`
- `media_screenshot(format, quality)`
- `media_preview_start/stop/status()`
- `media_record/record_stop/record_status()`

#### 文件 `file_*`
- `file_list/pull/push/delete/mkdir/stat()`

#### 应用 `app_*`
- `app_list/start/stop()`

#### 剪贴板 `clipboard_*`
- `clipboard_get/set()`

#### 显示 `display_*`
- `display_on/off/rotate/reset()`

#### 面板 `panel_*`
- `panel_notification/settings/collapse()`

#### 音量 `volume_*`
- `volume_up/down()`

**优点：**
- 工具数量从 63 减到约 30
- 参数清晰，每个工具有独立 inputSchema
- AI 通过前缀知道工具类别

---

### 方案 3.1：进一步合并（终极目标）

在方案 3 基础上，进一步合并无参数动作和相同参数的工具。

#### 无参数动作合并

很多工具不需要参数，可以用 `action` 参数区分：

| 原工具（多个） | 合并为 | action 取值 |
|----------------|--------|-------------|
| back, home, recent, menu, enter, tab, escape, wake | `nav(action)` | back, home, recent, menu, enter, tab, escape, wake |
| dpad_up, down, left, right, center | `dpad(action)` | up, down, left, right, center |
| turn_screen_on, turn_screen_off, rotate, reset | `display(action)` | on, off, rotate, reset |
| volume_up, volume_down | `volume(action)` | up, down |
| expand_notification, expand_settings, collapse | `panel(action)` | notification, settings, collapse |

#### 相同参数工具合并

| 原工具 | 参数 | 合并为 |
|--------|------|--------|
| tap, long_press | (x, y), (x, y, duration) | `tap(x, y, duration=0)` |
| press_key, back, home, menu... | key_code | `key(code)` |
| screenshot, screenshot_device, screenshot_standalone | - | `screenshot(method="auto")` |
| record, stop_recording, is_recording... | - | `record(action, ...)` |
| preview_start, preview_stop, preview_status | - | `preview(action)` |

#### 最终工具集（约 15 个）

```
# 设备管理（6 个 action）
device(action, ...)
  - action: status, connect, disconnect, discover, push, stop

# 输入（4 个工具）
tap(x, y, duration=0)       # 点击/长按（duration=0 点击，>0 长按）
swipe(x1, y1, x2, y2, ms)   # 滑动
key(code)                   # 任意按键（HOME/BACK/volume_up...）
text(content)               # 输入文字

# 媒体（3 个工具，各有 action）
screenshot(method, format, quality)
  - method: auto, video, tcp, adb
record(action, filename, duration, format)
  - action: start, stop, status
preview(action)
  - action: start, stop, status

# 文件（1 个工具，6 个 action）
file(action, ...)
  - action: list, pull, push, delete, mkdir, stat

# 应用（1 个工具，3 个 action）
app(action, ...)
  - action: list, start, stop

# 剪贴板（1 个工具，2 个 action）
clipboard(action, text)
  - action: get, set

# 快捷动作（5 个工具，无参数用 action 区分）
nav(action)      # back, home, recent, menu, enter, tab, escape, wake
dpad(action)     # up, down, left, right, center
display(action)  # on, off, rotate, reset
volume(action)   # up, down
panel(action)    # notification, settings, collapse
```

#### 数量对比

| 方案 | 工具数量 |
|------|----------|
| 当前 | 63 |
| 方案 3（命名前缀） | ~30 |
| 方案 3.1（进一步合并） | ~15 |

#### 优点

1. **极简**：15 个工具，AI 容易理解
2. **参数统一**：同类动作共用参数结构
3. **语义清晰**：`nav("back")` 比 `back()` 更明确是导航类

#### 缺点

1. **需要 AI 理解 action**：不再是独立工具，AI 需要知道 action 取值
2. **inputSchema 复杂**：需要列出所有 action 的 enum 值
3. **改动较大**：需要重构大量代码

---

### 方案 4：保持现状，改进描述（当前采用）

不改变工具结构，只改进每个工具的 `description` 字段。

#### 4.1 需要改进的工具

**connect：**
```
PRECONDITION: 先调用 get_state() 检查连接状态
如果 get_state().connected=true，说明已连接，请勿调用 connect()
调用此工具会断开现有连接！
```

**get_state：**
```
返回值增加 hint 字段：
"hint": "设备已连接，可直接使用其他工具"
"hint": "未连接，请先调用 discover_devices() 发现设备"
```

#### 4.2 待讨论问题

1. **描述语言**：英文还是中文？中文对阶跃AI 更友好，但 Claude Code 是英文
2. **描述长度**：太长会占用更多 token
3. **错误提示**：返回值里的 hint 如何改进
4. **连接状态检查**：是否每个工具都加前置检查

---

## 实施计划

### 短期（方案 4）
- [ ] 改进 connect 工具描述
- [ ] 改进 get_state 返回值 hint
- [ ] 其他高频工具描述优化

### 长期（方案 3）
- [ ] 设计新的工具命名规范
- [ ] 重构 TOOLS 列表
- [ ] 更新文档
