# 可选依赖和开发工具

> 非必需但有用的工具和库

---

## 开发工具

### 代码质量

#### black (代码格式化)

| 属性 | 值 |
|------|-----|
| **版本** | >=24.0.0 |
| **用途** | Python 代码格式化 |

```bash
pip install black>=24.0.0

# 格式化代码
black scrcpy_py_ddlx/

# 检查模式
black --check scrcpy_py_ddlx/
```

#### mypy (类型检查)

| 属性 | 值 |
|------|-----|
| **版本** | >=1.8.0 |
| **用途** | 静态类型检查 |

```bash
pip install mypy>=1.8.0

# 类型检查
mypy scrcpy_py_ddlx/

# 生成报告
mypy --html-report ./mypy-report scrcpy_py_ddlx/
```

#### pylint (代码分析)

```bash
pip install pylint

# 分析代码
pylint scrcpy_py_ddlx/
```

#### isort (导入排序)

```bash
pip install isort

# 排序导入
isort scrcpy_py_ddlx/
```

---

### 测试工具

#### pytest

| 属性 | 值 |
|------|-----|
| **版本** | >=8.0.0 |
| **用途** | 单元测试框架 |

```bash
pip install pytest>=8.0.0

# 运行测试
pytest tests/

# 详细输出
pytest -v tests/

# 覆盖率
pip install pytest-cov
pytest --cov=scrcpy_py_ddlx tests/
```

#### pytest-asyncio (异步测试)

```bash
pip install pytest-asyncio

# 测试异步代码
pytest tests/test_async.py
```

---

### 调试工具

#### ipython

```bash
pip install ipython

# 交互式调试
ipython
```

#### debugpy (VS Code 调试)

```bash
pip install debugpy

# 在代码中启用调试
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

---

## 可选功能依赖

### 音频录制

#### pyaudio

| 属性 | 值 |
|------|-----|
| **版本** | >=0.2.14 |
| **用途** | 音频录制 |

```bash
pip install pyaudio>=0.2.14

# Linux 依赖
sudo apt install portaudio19-dev
```

### 性能分析

#### py-spy

```bash
pip install py-spy

# 实时分析
py-spy top --pid <pid>

# 生成火焰图
py-spy record -o flamegraph.svg --pid <pid>
```

#### memory_profiler

```bash
pip install memory_profiler

# 内存分析
python -m memory_profiler script.py
```

---

## 打包工具

### PyInstaller

```bash
pip install pyinstaller

# 打包为可执行文件
pyinstaller --onefile --windowed scrcpy_py_ddlx/gui/__main__.py
```

### cx_Freeze

```bash
pip install cx_Freeze

# 打包
cxfreeze script.py --target-dir dist
```

---

## 文档工具

### Sphinx

```bash
pip install sphinx sphinx-rtd-theme

# 生成文档
cd docs
make html
```

### MkDocs

```bash
pip install mkdocs mkdocs-material

# 运行文档服务器
mkdocs serve
```

---

## CI/CD 工具

### pre-commit

```bash
pip install pre-commit

# 安装钩子
pre-commit install

# 手动运行
pre-commit run --all-files
```

### tox

```bash
pip install tox

# 多环境测试
tox
```

---

## Android 开发工具

### Android SDK

| 组件 | 用途 |
|------|------|
| Build Tools | 编译服务端 |
| Platform Tools | ADB |
| Android 36 SDK | 目标 API |

#### 安装方式

1. **Android Studio** (推荐)
   - 下载: https://developer.android.com/studio
   - SDK Manager 安装组件

2. **命令行工具**
   - 下载: https://developer.android.com/studio#command-tools
   - 使用 sdkmanager 安装组件

```bash
# 安装 SDK 组件
sdkmanager "platforms;android-36"
sdkmanager "build-tools;36.0.0"
sdkmanager "platform-tools"
```

### JDK

| 属性 | 值 |
|------|-----|
| **版本** | 17+ |
| **用途** | 编译 Java 代码 |

```bash
# 检查版本
java -version

# 应输出: openjdk version "17.x.x" 或更高
```

---

## 网络工具

### Wireshark (调试)

```bash
# 抓包分析
wireshark -k -i any -f "udp port 27185"
```

### netcat (调试)

```bash
# 测试 TCP 连接
nc -zv <device-ip> 27184

# 测试 UDP
nc -u -zv <device-ip> 27185
```

---

## 推荐开发环境配置

### requirements-dev.txt

```txt
# Testing
pytest>=8.0.0
pytest-cov
pytest-asyncio

# Code Quality
black>=24.0.0
mypy>=1.8.0
pylint
isort

# Debugging
ipython
debugpy

# Documentation
sphinx
sphinx-rtd-theme

# CI/CD
pre-commit
tox
```

### pyproject.toml (推荐)

```toml
[tool.black]
line-length = 100
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

---

## 相关文档

- [python.md](python.md) - Python 核心依赖
- [system.md](system.md) - 系统依赖
