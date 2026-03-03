#!/usr/bin/env python3
"""
API 文档自动生成脚本
使用 Sphinx 自动生成 Python 客户端和 MCP 接口的 API 文档
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List

class APIDocGenerator:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.docs_path = base_path / "api-docs"
        self.client_path = base_path / "scrcpy_py_ddlx"
        self.mcp_path = base_path / "scrcpy_mcp_gui.py"  # MCP 主文件

    def generate_sphinx_docs(self, source_dir: Path, output_dir: Path, name: str):
        """生成 Sphinx 文档"""
        print(f"Generating {name} API documentation...")

        # 创建临时 Sphinx 目录
        temp_dir = self.base_path / "temp_sphinx"
        temp_dir.mkdir(exist_ok=True)

        # 复制模板文件
        template_dir = self.base_path / "templates" / "sphinx"
        if template_dir.exists():
            subprocess.run(["cp", "-r", str(template_dir), str(temp_dir / "conf")])

        # 创建 conf.py
        conf_content = f"""
# {name} API Documentation
import os
import sys

# Add source directory to path
sys.path.insert(0, r"{source_dir}")

# Sphinx extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

# Theme
html_theme = "sphinx_rtd_theme"

# Autodoc settings
autodoc_default_options = {{
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__"
}}

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_private_with_doc = False

# Intersphinx mapping
intersphinx_mapping = {{
    "python": ("https://docs.python.org/3", None),
}}

# Paths
html_static_path = ["_static"]
templates_path = ["_templates"]
"""

        with open(temp_dir / "conf.py", "w") as f:
            f.write(conf_content)

        # 创建主索引文件
        index_content = f"""
# {name} API Documentation

.. automodule:: {name}
   :members:
   :undoc-members:
   :show-inheritance:

API Reference
=============

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   modules
"""

        with open(temp_dir / "index.rst", "w") as f:
            f.write(index_content)

        # 创建模块索引
        modules_index = "API Reference\n==============\n\n"
        modules_index += ".. toctree::\n   :maxdepth: 4:\n\n"

        # 自动发现 Python 模块
        for root, dirs, files in os.walk(source_dir):
            if "__init__.py" in files:
                rel_path = Path(root).relative_to(source_dir)
                module_name = str(rel_path).replace(os.sep, ".")

                if not module_name.startswith("."):
                    modules_index += f"   {module_name}\n"

        with open(temp_dir / "modules.rst", "w") as f:
            f.write(modules_index)

        # 运行 Sphinx
        subprocess.run([
            "sphinx-build",
            "-b", "html",
            str(temp_dir),
            str(output_dir)
        ], check=True)

        # 清理临时目录
        subprocess.run(["rm", "-rf", str(temp_dir)])

        print(f"Generated {name} API docs in {output_dir}")

    def generate_mkdocs_docs(self):
        """使用 MkDocs 生成文档"""
        print("Generating MkDocs documentation...")

        # 创建 mkdocs.yml
        mkdocs_content = """
site_name: scrcpy-py-ddlx API Documentation
site_description: API documentation for scrcpy-py-ddlx
nav:
  - Home: index.md
  - Python Client:
    - client.md
    - configuration.md
    - connection.md
  - MCP Interface:
    - http.md
    - gui.md

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            docstring_style: google
            show_source: true
            show_root_heading: true

theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.top
    - search.highlight
    - search.share
  logo: assets/logo.png
  favicon: assets/favicon.png
"""

        with open(self.base_path / "mkdocs.yml", "w") as f:
            f.write(mkdocs_content)

        # 创建 API 文档内容
        # Client API
        client_content = """
# Python Client API

The main client classes and interfaces for scrcpy-py-ddlx.

## Core Classes

### ScrcpyClient

The main client class for device connection and control.

```python
from scrcpy_py_ddlx.client.client import ScrcpyClient

client = ScrcpyClient()
client.connect("device_ip", port=3359)
```

## Configuration

### Config

Configuration class for client settings.

```python
from scrcpy_py_ddlx.core.config import Config

config = Config(
    video_codec="h264",
    audio_codec="aac",
    bitrate="1m"
)
```

## Connection

### ConnectionManager

Manages device connections and reconnections.

"""

        client_file = self.docs_path / "client.md"
        with open(client_file, "w") as f:
            f.write(client_content)

        print("Generated MkDocs documentation")

    def generate_protocol_docs(self):
        """生成协议文档"""
        print("Generating protocol documentation...")

        protocol_dir = self.docs_path / "protocol"

        # 创建协议文档
        protocol_content = """
# Protocol Documentation

## UDP Protocol

### Packet Structure

| Field | Size (bytes) | Description |
|-------|--------------|-------------|
| Header | 24 | Packet header with metadata |
| Payload | Variable | Actual data |

### Control Messages

| Message ID | Description |
|------------|-------------|
| 0x01 | Connect request |
| 0x02 | Connect response |
| 0x03 | Frame data |
| 0x04 | Control command |

## MCP Protocol

### HTTP API

#### Endpoints

- `GET /api/status` - Get server status
- `POST /api/connect` - Connect to device
- `POST /api/disconnect` - Disconnect from device

### WebSocket API

#### Messages

- `connect` - Connection request
- `disconnect` - Disconnection request
- `frame` - Frame data
- `control` - Control command
"""

        protocol_file = protocol_dir / "PROTOCOL_SPEC.md"
        with open(protocol_file, "w") as f:
            f.write(protocol_content)

        print("Generated protocol documentation")

    def generate_all(self, dry_run: bool = False):
        """生成所有 API 文档"""
        if dry_run:
            print("Dry run: Would generate documentation")
            return

        # 清理输出目录
        if self.docs_path.exists():
            subprocess.run(["rm", "-rf", str(self.docs_path)])
        self.docs_path.mkdir(parents=True)

        # 生成客户端文档
        if self.client_path.exists():
            self.generate_sphinx_docs(
                self.client_path,
                self.docs_path / "client",
                "scrcpy-py-ddlx-client"
            )

        # 生成 MCP 文档
        if self.mcp_path.exists():
            self.generate_mkdocs_docs()

        # 生成协议文档
        self.generate_protocol_docs()

        print("API documentation generation completed!")

def main():
    base_path = Path(".")
    generator = APIDocGenerator(base_path)

    # 解析命令行参数
    dry_run = "--dry-run" in sys.argv

    generator.generate_all(dry_run)

if __name__ == "__main__":
    main()