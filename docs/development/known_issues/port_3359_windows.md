# Windows 端口 3359 被占用问题

> **状态**: 已解决
> **日期**: 2026-02-25
> **影响**: Windows 用户无法启动 MCP 服务器

---

## 问题描述

在 Windows 上启动 `scrcpy_http_mcp_server.py` 时，端口 3359 绑定失败：

```
ERROR: [Errno 13] error while attempting to bind on address ('127.0.0.1', 3359):
[WinError 10013] 以一种访问权限不允许的方式做了一个访问套接字的尝试。
```

## 原因

Windows Hyper-V 会保留一段端口范围供系统使用，端口 3359 正好在这个范围内：

```
协议 tcp 端口排除范围

开始端口    结束端口
----------  --------
  3347      3446      <-- 3359 在这个范围内
```

查看保留端口的命令：
```powershell
netsh interface ipv4 show excludedportrange protocol=tcp
```

---

## 解决方案

### 方法 1: 释放端口 3359 (推荐，一劳永逸)

**以管理员身份运行 PowerShell**，执行以下命令：

```powershell
# 1. 停止 WinNAT 服务
net stop winnat

# 2. 排除端口 3359，防止 Hyper-V 占用
netsh int ipv4 add excludedportrange protocol=tcp startport=3359 numberofports=1 store=persistent

# 3. 重启 WinNAT 服务
net start winnat
```

执行后，端口 3359 将永久可用。

### 方法 2: 使用脚本

项目提供了自动修复脚本：

```powershell
# 以管理员身份运行
.\fix_port_3359.ps1
```

### 方法 3: 使用其他端口 (临时方案)

如果不想修改系统配置，可以使用其他端口：

```bash
python scrcpy_http_mcp_server.py --port 3333
```

---

## 验证

执行以下命令验证端口是否可用：

```powershell
# 查看排除列表中是否有 3359
netsh interface ipv4 show excludedportrange protocol=tcp | findstr 3359

# 如果显示 "3359        3359"，说明端口已被排除保留，可以使用
```

---

## 相关文件

- `fix_port_3359.ps1` - 自动修复脚本
- `start_mcp_server.bat` - 启动服务器脚本

---

## 参考

- [Windows Hyper-V 保留端口问题](https://learn.microsoft.com/en-us/troubleshoot/windows-client/networking/tcpip-ports-excluded-range)
