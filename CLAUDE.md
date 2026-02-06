# Claude Code 协作规范

本文档记录使用 Claude Code 协作开发 scrcpy-py-ddlx 时需要遵守的规范。

## Git Commit 规范

### 禁止事项

- ❌ **不要添加 `Co-Authored-By` 标签**
  - 不要在 commit message 中包含 `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`
  - Claude Code 的贡献不需要在 git 中特别标注

### Commit Message 格式

使用 Conventional Commits 格式：

```
<type>: <description>

<body>
```

**类型 (type):**
- `feat`: 新功能
- `fix`: Bug 修复
- `chore`: 维护性改动
- `docs`: 文档更新
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试
- `style`: 代码风格

## Requirements.txt 规范

### 编码规范

- ❌ **不要使用中文注释**
  - 中文注释在 Windows 上可能导致 GBK 编码错误
  - 使用英文注释或无注释

### GPU 渲染支持

本项目支持 OpenGL GPU 加速渲染，依赖：
- `PyOpenGL` - OpenGL Python 绑定
- `PyOpenGL_accelerate` - OpenGL 加速库

GPU 渲染可将视频码率从 3.7 Mbps 提升到 7.0+ Mbps。

## 项目架构

### 核心模块

- `scrcpy_py_ddlx/client/` - 客户端核心逻辑
- `scrcpy_py_ddlx/core/demuxer/` - 视频/音频解复用器
- `scrcpy_py_ddlx/core/decoder/` - 视频解码器
- `scrcpy_py_ddlx/core/player/` - 视频播放器（支持 OpenGL）
- `scrcpy_py_ddlx/mcp_server.py` - MCP 服务器

### 测试目录

- `tests_gui/` - GUI 测试脚本
- 测试不需要提交到仓库

## 文档存放

技术文档存放在 `C:\Project\IDEA\2\docs\scrcpy-py-ddlx\`：
- `development/` - 开发过程文档
- `archive/` - 归档文档
