#!/usr/bin/env python3
"""
文档结构生成脚本
根据现有的文档文件生成新的目录结构和导航文件
"""

import os
import shutil
from pathlib import Path
import re

def create_directory_structure(base_path):
    """创建新的文档目录结构"""
    dirs = [
        "docs/getting-started",
        "docs/user-guide/modes",
        "docs/user-guide/features",
        "docs/api-reference/client",
        "docs/api-reference/client/configuration",
        "docs/api-reference/client/connection",
        "docs/api-reference/mcp/http",
        "docs/api-reference/mcp/gui",
        "docs/api-reference/protocol",
        "docs/development",
        "docs/development/architecture",
        "docs/development/protocols",
        "docs/development/guides",
        "docs/development/internals",
        "docs/examples/basic",
        "docs/examples/advanced",
        "docs/tutorials",
        "docs/resources/changelog",
        "internal/design-decisions",
        "internal/performance",
        "internal/testing",
        "api-docs/client",
        "api-docs/mcp"
    ]

    for dir_path in dirs:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

def move_documents(src_path, dst_path, mapping):
    """移动文档文件到新位置"""
    for src_file, dst_file in mapping.items():
        src = src_path / src_file
        dst = dst_path / dst_file

        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            print(f"Moved: {src_file} -> {dst_file}")
        else:
            print(f"Warning: {src_file} not found")

def create_nav_file(base_path):
    """创建导航文件"""
    nav_content = """# 文档中心导航

> 本文档系统采用分层结构，便于快速定位信息

## 📚 文档导航

### 快速开始
- [安装指南](getting-started/installation.md) - 环境配置和安装步骤
- [快速入门](getting-started/quickstart.md) - 5分钟快速上手
- [故障排除](getting-started/troubleshooting.md) - 常见问题解决方案

### 用户指南
- [使用模式](user-guide/modes/) - 了解不同的使用方式
- [功能特性](user-guide/features/) - 详细功能介绍
- [配置说明](user-guide/configuration.md) - 配置选项详解
- [常见问题](user-guide/faq.md) - FAQ 和最佳实践

### API 参考
- [Python 客户端](api-reference/client/) - Python 客户端接口
- [MCP 接口](api-reference/mcp/) - MCP 服务器接口
- [协议文档](api-reference/protocol/) - 通信协议规范

### 开发文档
- [架构设计](development/) - 架构和设计文档
- [开发指南](development/guides/) - 开发实践指南
- [协议实现](development/protocols/) - 协议实现细节

### 示例和教程
- [基础示例](examples/basic/) - 基本使用示例
- [高级示例](examples/advanced/) - 高级功能示例
- [构建教程](tutorials/building.md) - 从源码构建

## 🔄 快速链接

- [项目主页](../../README.md)
- [贡献指南](../../CONTRIBUTING.md)
- [许可证](../../LICENSE)
"""

    nav_file = base_path / "docs" / "README.md"
    with open(nav_file, 'w', encoding='utf-8') as f:
        f.write(nav_content)
    print("Created: docs/README.md")

def create_index_files(base_path):
    """创建各个目录的索引文件"""

    # 用户模式目录索引
    modes_index = """# 使用模式

| 模式 | 说明 | 文档 |
|------|------|------|
| 直接模式 | 直接连接设备，本地解码 | [direct-test.md](direct-test.md) |
| MCP HTTP | 通过 HTTP 服务器访问 | [mcp-http.md](mcp-http.md) |
| MCP GUI | 图形界面 MCP 服务器 | [mcp-gui.md](mcp-gui.md) |
| Python API | Python 接口编程 | [python-api.md](python-api.md) |
"""

    modes_file = base_path / "docs/user-guide/modes" / "README.md"
    with open(modes_file, 'w', encoding='utf-8') as f:
        f.write(modes_index)

def main():
    base_path = Path(".")

    print("Creating new documentation structure...")

    # 创建目录结构
    create_directory_structure(base_path)

    # 创建导航文件
    create_nav_file(base_path)

    # 创建索引文件
    create_index_files(base_path)

    # 创建迁移脚本
    migration_script = """#!/bin/bash
# 文档迁移脚本
# 将旧文档移动到新位置

echo "Starting document migration..."

# 定义文件映射关系
declare -A file_mapping=(
    ["docs/user/installation.md"]="docs/getting-started/installation.md"
    ["docs/user/quickstart.md"]="docs/getting-started/quickstart.md"
    ["docs/user/troubleshooting.md"]="docs/getting-started/troubleshooting.md"
    ["docs/user/modes/direct-test.md"]="docs/user-guide/modes/direct-test.md"
    ["docs/user/modes/mcp-http.md"]="docs/user-guide/modes/mcp-http.md"
    ["docs/user/modes/mcp-gui.md"]="docs/user-guide/modes/mcp-gui.md"
    ["docs/user/modes/python-api.md"]="docs/user-guide/modes/python-api.md"
    ["docs/api/control.md"]="docs/api-reference/client/control.md"
    ["docs/api/protocol.md"]="docs/api-reference/protocol/protocol.md"
    ["docs/development/NETWORK_PIPELINE.md"]="docs/development/architecture/NETWORK_PIPELINE.md"
    ["docs/development/VIDEO_AUDIO_PIPELINE.md"]="docs/development/architecture/VIDEO_AUDIO_PIPELINE.md"
)

# 执行移动操作
for src in "${!file_mapping[@]}"; do
    dst="${file_mapping[$src]}"
    if [ -f "$src" ]; then
        mkdir -p "$(dirname "$dst")"
        mv "$src" "$dst"
        echo "Moved: $src -> $dst"
    else
        echo "Warning: $src not found"
    fi
done

echo "Migration completed!"
"""

    with open(base_path / "scripts" / "migrate_docs.sh", 'w') as f:
        f.write(migration_script)

    print("\nDone! Documentation structure created.")
    print("\nNext steps:")
    print("1. Run scripts/migrate_docs.sh to move existing documents")
    print("2. Update all internal links")
    print("3. Add missing documentation")
    print("4. Set up automation tools (Sphinx, MkDocs)")

if __name__ == "__main__":
    main()