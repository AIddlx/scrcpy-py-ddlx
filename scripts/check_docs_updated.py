#!/usr/bin/env python3
"""
Git Hook 检查脚本
在提交前检查文档是否需要更新
"""

import os
import sys
import subprocess
from pathlib import Path

def get_staged_files():
    """获取暂存的文档文件"""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "--", "*.md"],
        capture_output=True, text=True
    )
    return result.stdout.strip().split('\n') if result.stdout else []

def check_documentation_changes(staged_files):
    """检查文档变更"""
    doc_changes = []
    api_changes = []

    for file in staged_files:
        file_path = Path(file)

        if file_path.parts[0] == "docs":
            doc_changes.append(file)
            if "api" in file_path.parts:
                api_changes.append(file)

    return doc_changes, api_changes

def check_api_sync(doc_changes):
    """检查 API 文档是否需要同步更新"""
    api_files = []
    for file in doc_changes:
        if "scrcpy_py_ddlx" in file or "api" in file:
            api_files.append(file)

    if api_files:
        print("\n⚠️  API 文件已修改，需要更新 API 文档:")
        for file in api_files:
            print(f"  - {file}")
        print("\n运行以下命令生成 API 文档:")
        print("  python scripts/generate_api_docs.py")
        return True
    return False

def check_links_updated(doc_changes):
    """检查链接是否需要更新"""
    for file in doc_changes:
        print(f"\n📝 检查文档: {file}")
        # 这里可以添加链接检查逻辑
        # 例如：检查相对链接是否正确
        pass

def main():
    print("🔍 Checking documentation updates...")

    # 获取暂存的文档文件
    staged_files = get_staged_files()

    if not staged_files:
        print("No markdown files staged.")
        sys.exit(0)

    print(f"\nFound {len(staged_files)} staged markdown files:")
    for file in staged_files:
        print(f"  - {file}")

    # 检查文档变更
    doc_changes, api_changes = check_documentation_changes(staged_files)

    if doc_changes:
        print(f"\n📚 {len(doc_changes)} documentation files changed")

        # 检查 API 同步
        if check_api_sync(doc_changes):
            print("\nPlease update API documentation before committing.")
            sys.exit(1)

        # 检查链接
        check_links_updated(doc_changes)

    print("\n✅ Documentation check passed!")

if __name__ == "__main__":
    main()