# 日志调用统计报告

> 统计日期：2026-03-02
> 目的：分析各模块的日志分布，为日志级别优化提供依据

---

## 总体汇总

| 模块/目录 | print | logger.debug | logger.info | logger.warning | logger.error | Ln/Log.d | Ln/Log.i | Ln/Log.w | Ln/Log.e | 总计 |
|----------|-------|--------------|-------------|----------------|--------------|----------|----------|----------|----------|------|
| tests_gui/test_network_direct.py | 175 | 0 | 0 | 0 | 0 | - | - | - | - | 177 |
| scrcpy_http_mcp_server.py | 94 | 25 | 36 | 15 | 103 | - | - | - | - | 274 |
| scrcpy_py_ddlx/ | 72 | 257 | 338 | 323 | 0* | - | - | - | - | 1064 |
| server (Java) | - | - | - | - | - | 121 | 71 | 49 | 113 | 361 |
| companion (Java) | - | - | - | - | - | 6 | 0 | 2 | 2 | 10 |
| **总计** | **341** | **282** | **374** | **338** | **103** | **127** | **71** | **51** | **115** | **1886** |

*注: scrcpy_py_ddlx 使用 `logger.exception` 1 处而非 `logger.error`

---

## 详细统计

### 1. tests_gui/test_network_direct.py

| 日志类型 | 数量 |
|---------|------|
| print() | 175 |
| logging.getLogger | 2 |
| **总计** | **177** |

**说明**：测试脚本，大量使用 print() 输出测试信息，不使用 logger。

---

### 2. scrcpy_http_mcp_server.py

| 日志类型 | 数量 |
|---------|------|
| print() | 94 |
| logger.debug | 25 |
| logger.info | 36 |
| logger.warning | 15 |
| logger.error | 103 |
| logging.getLogger | 1 |
| **总计** | **274** |

**说明**：主 HTTP MCP 服务，logger.error 最多（103处），主要用于错误处理。

---

### 3. scrcpy_py_ddlx/ 目录 (所有 Python 文件)

| 日志类型 | 数量 |
|---------|------|
| print() | 72 |
| logger.debug | 257 |
| logger.info | 338 |
| logger.warning | 323 |
| logger.error | 0 |
| logger.exception | 1 |
| logging.getLogger | 73 |
| **总计** | **1064** |

#### 调用最多的文件 (logger 调用 TOP 6)

| 文件 | 调用次数 |
|------|---------|
| `client/client.py` | 180 |
| `preview_process.py` | 46 |
| `core/player/video/opengl_widget.py` | 45 |
| `core/demuxer/udp_video.py` | 28 |
| `core/player/video/video_window.py` | 26 |
| `core/decoder/decoder_process.py` | 25 |

#### 分布详情

| 日志类型 | 文件数 |
|---------|--------|
| print() | 53 个文件 |
| logger.debug | 40 个文件 |
| logger.info | 46 个文件 |
| logger.warning | 47 个文件 |

---

### 4. scrcpy/server/src/main/java/ (服务端 Java)

| 日志类型 | 数量 |
|---------|------|
| Ln.d (DEBUG) | 120 |
| Ln.i (INFO) | 70 |
| Ln.w (WARN) | 47 |
| Ln.e (ERROR) | 112 |
| Ln.v (VERBOSE) | 7 |
| Log.d (android.util.Log) | 1 |
| Log.i (android.util.Log) | 1 |
| Log.w (android.util.Log) | 2 |
| Log.e (android.util.Log) | 1 |
| **总计** | **361** |

**说明**：使用自定义的 `Ln` 类（定义在 `util/Ln.java`），它同时写入 Android Log 和控制台输出。

#### 调用最多的文件 (Ln 调用 TOP 6)

| 文件 | 调用次数 |
|------|---------|
| `Controller.java` | 41 |
| `Server.java` | 37 |
| `SurfaceEncoder.java` | 28 |
| `AudioEncoder.java` | 23 |
| `CleanUp.java` | 16 |
| `DesktopConnection.java` | 16 |

---

### 5. scrcpy/companion/app/src/main/java/ (Companion Java)

| 日志类型 | 数量 |
|---------|------|
| Log.d (DEBUG) | 6 |
| Log.w (WARN) | 2 |
| Log.e (ERROR) | 2 |
| **总计** | **10** |

#### 文件分布

| 文件 | 调用次数 |
|------|---------|
| `UdpClient.java` | 9 |
| `ScrcpyTileService.java` | 1 |

---

## 日志级别分布图

```
Python 模块 (共 1515 处):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print()      [341] ████████████████████████████████████
logger.debug [282] ███████████████████████████████
logger.info  [374] █████████████████████████████████████
logger.warn  [338] ██████████████████████████████████
logger.error [103] ███████████

Java 模块 (共 371 处):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEBUG (Ln.d/Log.d) [127] ████████████████████████████████████████████████████
INFO  (Ln.i/Log.i) [ 71] █████████████████████████
WARN  (Ln.w/Log.w) [ 51] ███████████████████
ERROR (Ln.e/Log.e) [115] █████████████████████████████████████████████
VERBOSE (Ln.v)    [  7] ██
```

---

## 优化建议

### 1. 日志级别控制（已实现）

优先级从高到低：

```
1. 环境变量 SCRCPY_DEBUG=1        → DEBUG（开发者全量日志）
2. 环境变量 SCRCPY_LOG_LEVEL=X    → 指定级别
3. 命令行参数 --log-level=X       → 指定级别
4. 默认值 WARNING                  → 普通用户最少日志
```

**开发者（你）**：
```bash
# 方式 1：强制开启全量日志
export SCRCPY_DEBUG=1
python scrcpy_http_mcp_server.py

# 方式 2：指定级别
export SCRCPY_LOG_LEVEL=DEBUG
python scrcpy_http_mcp_server.py
```

**普通用户（默认）**：
```bash
# 无需任何配置，自动使用 WARNING 级别
python scrcpy_http_mcp_server.py
```

**用户可调**：
```bash
# 查看更多信息
python scrcpy_http_mcp_server.py --log-level=INFO

# 调试模式
python scrcpy_http_mcp_server.py --log-level=DEBUG

# 保留更多日志文件
python scrcpy_http_mcp_server.py --log-keep=10
```

### 2. 环境变量说明

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `SCRCPY_DEBUG` | 强制 DEBUG 级别 | `SCRCPY_DEBUG=1` |
| `SCRCPY_LOG_LEVEL` | 指定日志级别 | `SCRCPY_LOG_LEVEL=INFO` |
| `SCRCPY_LOG_KEEP` | 保留日志文件数 | `SCRCPY_LOG_KEEP=5` |

### 3. 日志文件保留

默认保留最近 **3** 个会话日志文件。可通过以下方式修改：

```bash
# 环境变量
export SCRCPY_LOG_KEEP=10

# 命令行参数
python scrcpy_http_mcp_server.py --log-keep=10
```

### 4. 高频日志优化

| 文件 | 日志数 | 建议 |
|------|--------|------|
| `client/client.py` | 180 | 将 DEBUG 日志改为条件输出或移除 |
| `preview_process.py` | 46 | 检查每帧日志，考虑使用速率限制 |
| `Controller.java` | 41 | 检查高频控制日志 |
| `Server.java` | 37 | 检查启动日志是否过多 |

### 2. 日志级别调整

当前问题：
- **DEBUG 日志过多**（257 + 127 = 384 处）可能在生产环境产生大量输出
- **logger.warning 数量过多**（323 处），部分可能是可预期的状态

建议：
```python
# 生产环境使用 INFO 级别
logging.basicConfig(level=logging.INFO)

# 或动态控制
if os.environ.get('SCRCPY_DEBUG'):
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
```

### 3. print() 迁移

| 模块 | print 数量 | 优先级 |
|------|-----------|--------|
| test_network_direct.py | 175 | 低（测试脚本）|
| scrcpy_http_mcp_server.py | 94 | 高（用户输出）|
| scrcpy_py_ddlx/ | 72 | 中 |

**注意**：`scrcpy_http_mcp_server.py` 中的部分 print() 是**有意为之**的用户友好输出，不应迁移到 logger。

---

## 相关文档

- [LOGIC.md](mcp_http_server/MCP_HTTP_SERVER_LOGIC.md) - MCP HTTP Server 工作逻辑
- [STARTUP_FLOW_REFACTOR.md](mcp_http_server/STARTUP_FLOW_REFACTOR.md) - 启动流程重构

---

*此文档由自动化脚本生成，用于日志优化参考。*
