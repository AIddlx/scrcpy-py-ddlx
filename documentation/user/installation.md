# 安装指南

配置 scrcpy-py-ddlx 开发环境。

---

## 系统要求

### 基本要求

- **Python**: 3.8 或更高版本
- **操作系统**: Windows、macOS 或 Linux
- **Android 设备**: API 21+ (Android 5.0+)
- **ADB**: Android SDK Platform Tools

### Python 依赖

```bash
pip install -r requirements.txt
```


---

## 编译 Server

### 为什么需要编译？

本项目使用了修改过的 scrcpy server，包含以下额外功能：
- `list_apps` 控制消息
- 增强的剪贴板同步
- 其他协议扩展

### 编译步骤

1. **安装前置要求**
   - JDK 17+
   - Android SDK

2. **编译 Server**

   ```bash
   # Linux/macOS/Git Bash
   ./scrcpy/release/build_server.sh
   ```

   编译完成后，`scrcpy-server` 文件会自动生成在项目根目录。

### 验证

```bash
ls -lh scrcpy-server
# 应该显示约 90KB 的文件
```

---

## 编译 Companion APK

Companion APK 是手机端管理工具，用于网络模式下查看服务端状态和终止服务。

### 编译步骤

```bash
# Windows
scrcpy\companion\build.cmd

# 或使用 Gradle
scrcpy\companion\gradlew.bat assembleDebug

# Linux/macOS
./scrcpy/companion/build.sh
```

编译完成后，APK 位于 `scrcpy/companion/scrcpy-companion.apk`。

### 安装到设备

```bash
adb install scrcpy/companion/scrcpy-companion.apk
```

---

## 使用方式

### 直接运行脚本（推荐）

无需安装，直接运行：

```bash
# 测试脚本
python tests_gui/test_direct.py

# MCP GUI
python scrcpy_mcp_gui.py

# HTTP MCP
python scrcpy_http_mcp_server.py
```

### 作为库使用

在代码中添加项目路径：

```python
import sys
sys.path.insert(0, '/path/to/scrcpy-py-ddlx')

from scrcpy_py_ddlx import ScrcpyClient, ClientConfig

# ... 你的代码
```

或设置环境变量：

```bash
export PYTHONPATH=/path/to/scrcpy-py-ddlx:$PYTHONPATH
```

---

## 为什么不推荐 pip install？

项目目前处于活跃开发阶段，bug 较多。直接使用源码可以：
- 遇到问题直接修改代码
- 无需等待版本发布
- 更灵活的调试

---

## 验证环境

```bash
python -c "import sys; sys.path.insert(0, '.'); from scrcpy_py_ddlx import ScrcpyClient; print('环境配置成功')"
```

---

## 下一步

- [快速开始](quickstart.md) - 5 分钟上手
- [使用模式](modes/) - 选择使用方式
