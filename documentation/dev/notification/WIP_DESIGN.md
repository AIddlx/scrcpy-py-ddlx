# 通知转发功能开发经验 (WIP)

> **状态**: 开发中，需要大量设计和实测改进
> **日期**: 2026-02-25
> **提交**: f014c04 (回退点)

---

## 功能概述

将 Android 设备的系统通知转发到 PC 客户端显示。

## 设计方案

### 架构选择

#### ~~方案 A: 通过 scrcpy-companion + UDP (已放弃)~~
- 问题：需要额外配置 PC 地址
- 问题：Gradle 构建不稳定
- 问题：需要用户手动授权通知权限

#### 方案 B: 通过 scrcpy-server TCP 控制通道 (推荐)
- 复用现有 TCP 控制通道，无需额外端口
- 无需解决地址配置问题
- 更可靠，连接已建立

**实现思路**：
1. 服务端添加 NotificationListenerService（需要单独授权）
2. 通知通过现有 DeviceMessage 通道发送（类似 CLIPBOARD）
3. 客户端在控制消息接收器中处理

**架构**：
```
┌──────────────────────┐   TCP 控制通道   ┌─────────────────────┐
│  Android             │  ═══════════════► │  PC                 │
│  scrcpy-server       │  (DeviceMessage)  │  Python 客户端      │
│  NotificationListener│                   │  DeviceMessageReceiver│
└──────────────────────┘                   └─────────────────────┘
```

---

## 已实现：文件传输功能

> **状态**: ✅ 已完成
> **日期**: 2026-02-25
> **详细文档**: [FILE_TRANSFER_GUIDE.md](../FILE_TRANSFER_GUIDE.md)

### 实现方式

scrcpy 的文件传输是通过 **ADB 命令** 实现的，不是通过 scrcpy 协议：

- **APK 文件** → `adb install -r <file>`
- **其他文件** → `adb push <file> /sdcard/Download/`

### 关键技术点

1. **QOpenGLWindow 拖放问题**
   - PySide6 的 `QWindow` 没有 `setAcceptDrops` 方法
   - 解决：在 `QMainWindow` 容器上处理，用 `eventFilter` 转发事件

2. **后台线程处理**
   - ADB 命令可能耗时较长
   - 解决：使用后台线程 + 队列，不阻塞 UI

3. **VideoDecoder 缺失方法**
   - `configure_content_detection()` 和 `set_on_decode_error_callback()` 未实现
   - 解决：添加方法到 `VideoDecoder` 类

### 修改的文件

| 文件 | 修改内容 |
|------|----------|
| `core/file_pusher.py` | 新增：文件推送后台线程 |
| `core/player/video/video_window.py` | 添加拖放事件处理、eventFilter |
| `core/decoder/video.py` | 添加缺失的方法 |
| `tests_gui/test_direct.py` | 初始化文件推送器 |

### 使用方式

1. 运行 `python -X utf8 tests_gui/test_direct.py`
2. 拖放 APK 文件到窗口 → 自动安装
3. 拖放其他文件到窗口 → 推送到 `/sdcard/Download/`
4. 支持批量拖放多个文件

---

## 更好的策略：优先复现 scrcpy 原有功能

在实现新功能（如通知转发）之前，应该优先确保 scrcpy 原有功能都已复现。

### 待复现功能清单

| 功能 | 状态 | 备注 |
|------|------|------|
| 屏幕镜像 | ✅ | |
| 触控/键鼠控制 | ✅ | |
| 音频转发 | ✅ | |
| 剪贴板同步 | ✅ | |
| 文件传输 | ✅ | 拖放安装 APK / 推送文件 |
| 摄像头镜像 | ❌ | --video-source=camera |
| 音量控制 | ❌ | SET_VOLUME |
| 通知转发 | ❌ | 非官方功能 |
| 录屏 | ⚠️ | 仅音频录制 |

---

## 已完成的代码

### Android (scrcpy-companion)

1. **NotificationForwarder.java** - 通知监听服务
   - 继承 NotificationListenerService
   - 过滤系统通知、前台服务通知
   - 序列化通知数据通过 UDP 发送

2. **AndroidManifest.xml** - 服务声明
   ```xml
   <service
       android:name=".NotificationForwarder"
       android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE"
       android:exported="true">
       <intent-filter>
           <action android:name="android.service.notification.NotificationListenerService" />
       </intent-filter>
   </service>
   ```

### Python 客户端

1. **notification_receiver.py** - UDP 通知接收器
2. **notification_handler.py** - 系统通知显示（Windows toast）
3. **device_msg.py** - 添加 NOTIFICATION 消息类型
4. **protocol.py** - 添加 DeviceMessageType.NOTIFICATION = 6

---

## 遇到的问题

### 1. Companion APK 无法在桌面显示

**原因**: AndroidManifest.xml 缺少 MainActivity 的 LAUNCHER 声明

**解决**: 添加
```xml
<activity android:name=".MainActivity" android:exported="true">
    <intent-filter>
        <action android:name="android.intent.action.MAIN" />
        <category android:name="android.intent.category.LAUNCHER" />
    </intent-filter>
</activity>
```

### 2. 通知访问权限中看不到应用

**原因**:
- 构建缓存问题导致 merged manifest 未更新
- `android:testOnly="true"` 标记

**路径**: 设置 → 应用 → 特殊应用权限 → 通知访问权限

### 3. Gradle 构建问题

**现象**: `gradlew assembleDebug` 显示成功，但 APK 不存在

**原因**: Gradle 缓存，显示 "UP-TO-DATE" 但实际未生成

**解决**: 删除 build 目录重新构建
```powershell
Remove-Item -Recurse -Force app\build, build, .gradle
.\gradlew.bat assembleDebug
```

### 4. 图标资源缺失

**错误**: `resource mipmap/ic_launcher not found`

**解决**: 创建 drawable 图标或自适应图标

---

## 待完成工作

### 高优先级

1. **稳定 Companion 构建**
   - 解决 Gradle 缓存问题
   - 确保 merged manifest 正确
   - 添加 CI/CD 构建

2. **PC 端地址配置**
   - companion 需要知道 PC 的 IP 地址
   - 当前硬编码为 127.0.0.1
   - 需要动态发现或用户配置

3. **网络模式适配**
   - USB 模式：PC = 127.0.0.1
   - 网络模式：需要通过设备 IP 反向连接 PC

### 中优先级

4. **协议完善**
   - 通知 ID 用于去重和移除
   - 通知时间戳
   - 大图标/通知图标

5. **权限引导**
   - 应用内检测通知权限
   - 提供一键跳转到设置页面

6. **错误处理**
   - UDP 发送失败处理
   - 网络断开重连

### 低优先级

7. **功能增强**
   - 通知分组
   - 通知历史
   - 通知过滤规则

---

## 文件清单 (已删除，保留记录)

```
# Android
scrcpy/companion/app/src/main/java/com/genymobile/scrcpy/companion/NotificationForwarder.java
scrcpy/companion/app/src/main/res/drawable/ic_launcher.xml
scrcpy/companion/app/src/main/res/drawable/ic_launcher_foreground.xml
scrcpy/companion/app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml
scrcpy/companion/app/src/main/res/values/colors.xml

# Python
scrcpy_py_ddlx/core/notification_receiver.py
scrcpy_py_ddlx/core/notification_handler.py
```

---

## 下次开发建议

1. 先确保 companion 基础构建流程稳定
2. 考虑使用 TCP 而非 UDP，更可靠
3. 或复用现有的 scrcpy 控制通道传输通知
4. 参考 KDE Connect 的通知同步实现

---

## 参考

- [Android NotificationListenerService](https://developer.android.com/reference/android/service/notification/NotificationListenerService)
- [通知访问权限设置路径](https://developer.android.com/reference/android/provider/Settings#ACTION_NOTIFICATION_LISTENER_SETTINGS)
