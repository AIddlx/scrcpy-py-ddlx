# 网络模式认证功能设计文档

> 分析日期: 2026-02-28
> 状态: 设计阶段，待实施

---

## 一、背景

当前网络模式（`--push` + 网络连接）存在安全隐患：
- 任何人知道 IP 和端口就可以连接
- 可以注入控制命令（触摸、按键等）
- 可以获取屏幕内容
- 可以操作文件

需要添加认证机制保护网络连接。

---

## 二、认证方案

### 2.1 选型结论

经过对比分析，选择 **HMAC-SHA256 Challenge-Response** 方案：

| 方案 | 复杂度 | 安全性 | 延迟 | 结论 |
|------|--------|--------|------|------|
| HMAC Challenge-Response | 低 | 高 | ~5-10ms | ✅ 选择 |
| SCRAM | 中 | 更高 | ~15-20ms | 过度设计 |
| TLS-PSK | 高 | 最高 | ~50-100ms | 过于复杂 |

### 2.2 认证流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    HMAC Challenge-Response 流程                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  客户端 (Python)                          服务端 (Java)         │
│    │                                         │                  │
│    │──── 1. TCP 连接 ─────────────────────>│                  │
│    │                                         │                  │
│    │<─── 2. CHALLENGE (32 bytes) ───────────│ 生成随机数        │
│    │                                         │                  │
│    │  3. 计算 HMAC                          │                  │
│    │     response = HMAC(key, challenge)    │                  │
│    │                                         │                  │
│    │──── 4. RESPONSE (32 bytes) ──────────>│                  │
│    │                                         │                  │
│    │                                         │ 5. 验证 HMAC     │
│    │                                         │                  │
│    │<─── 6. AUTH_RESULT (1 byte) ───────────│ 0=失败, 1=成功   │
│    │                                         │                  │
│    │──── 7. 正常通信 ─────────────────────>│                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 密钥分发流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    密钥分发流程 (ADB 通道)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  客户端 (Python)                          设备 (Android)        │
│    │                                         │                  │
│    │  1. 生成 auth_key (32 bytes)           │                  │
│    │     secrets.token_bytes(32)            │                  │
│    │                                         │                  │
│    │  2. 保存到本地                          │                  │
│    │     ~/.config/scrcpy-py-ddlx/keys/     │                  │
│    │                                         │                  │
│    │  3. adb push auth.key ────────────────>│                  │
│    │     /data/local/tmp/scrcpy-auth.key    │                  │
│    │                                         │                  │
│    │  4. adb shell app_process ... ────────>│                  │
│    │     --auth-key-file=/data/.../auth.key │                  │
│    │                                         │                  │
│    │                                         │ 5. 读取密钥      │
│    │                                         │ 6. 删除文件      │
│    │                                         │ 7. 内存中保存    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、协议设计

### 3.1 消息类型

使用 0xF0-0xF2 范围，避免与现有消息冲突：

| 类型 | 编号 | 方向 | 大小 | 描述 |
|------|------|------|------|------|
| TYPE_CHALLENGE | 0xF0 | Server→Client | 33 bytes | 随机挑战数 |
| TYPE_RESPONSE | 0xF1 | Client→Server | 33 bytes | HMAC 签名 |
| TYPE_AUTH_RESULT | 0xF2 | Server→Client | 2+ bytes | 认证结果 |

### 3.2 消息格式

**TYPE_CHALLENGE (Server → Client)**:
```
偏移   字段       大小    描述
----   ----       ----    ----
0      type       1       = 0xF0
1      challenge  32      随机数
```

**TYPE_RESPONSE (Client → Server)**:
```
偏移   字段       大小    描述
----   ----       ----    ----
0      type       1       = 0xF1
1      response   32      HMAC-SHA256 结果
```

**TYPE_AUTH_RESULT (Server → Client)**:
```
偏移   字段        大小    描述
----   ----        ----    ----
0      type        1       = 0xF2
1      result      1       0=失败, 1=成功
2      error_len   2       错误消息长度 (可选)
4+     error_msg   N       错误消息 (可选)
```

### 3.3 版本协商

为确保向后兼容，需要版本协商机制：

```python
# 客户端连接时发送版本
CLIENT_VERSION = 4  # v1.4 = 支持认证
socket.send(bytes([CLIENT_VERSION]))

# 服务端响应
server_version = socket.recv(1)[0]

if server_version >= 4:
    # 执行认证
    handle_auth()
else:
    # 跳过认证
    logger.warning("Server does not support auth")
```

---

## 四、代码改动清单

### 4.1 Python 客户端

| 文件 | 改动类型 | 风险 | 改动内容 |
|------|---------|------|----------|
| `core/auth.py` | 🆕 新增 | 🟢 低 | 密钥生成/存储/HMAC 计算 |
| `core/adb.py` | ✏️ 修改 | 🟢 低 | 添加 `push_auth_key()` |
| `client/connection.py` | ✏️ 修改 | 🟡 中 | `setup_network_mode()` 添加认证 |
| `client/client.py` | ✏️ 修改 | 🟡 中 | 整合认证到 push 流程 |
| `core/protocol.py` | ✏️ 修改 | 🟢 低 | 新增消息类型常量 |
| `core/device_msg.py` | ✏️ 修改 | 🟢 低 | 解析 CHALLENGE/AUTH_RESULT |

### 4.2 Java 服务端

| 文件 | 改动类型 | 风险 | 改动内容 |
|------|---------|------|----------|
| `control/AuthHandler.java` | 🆕 新增 | 🟢 低 | Challenge-Response 处理 |
| `Options.java` | ✏️ 修改 | 🟢 低 | `authKeyFile` 字段 |
| `Server.java` | ✏️ 修改 | 🟡 中 | 读取密钥文件 |
| `device/DesktopConnection.java` | ✏️ 修改 | 🔴 高 | 连接流程插入认证 |
| `control/DeviceMessage.java` | ✏️ 修改 | 🟢 低 | 消息类型常量 |
| `control/DeviceMessageWriter.java` | ✏️ 修改 | 🟡 中 | 序列化认证消息 |
| `control/ControlMessageReader.java` | ✏️ 修改 | 🟡 中 | 解析 RESPONSE |

### 4.3 文档

| 文件 | 改动内容 |
|------|----------|
| `docs/PROTOCOL_SPEC.md` | 添加认证消息定义 |
| `CLAUDE.md` | 版本历史 v1.4 |

---

## 五、风险评估

### 5.1 风险矩阵

| 风险 | 等级 | 影响 | 预防措施 |
|------|------|------|----------|
| DesktopConnection 改动 | 🔴 高 | 旧客户端无法连接 | 版本协商，跳过认证 |
| 认证模块故障 | 🟡 中 | 连接失败 | `--no-auth` 降级选项 |
| 连接超时增加 | 🟡 中 | 用户体验下降 | 调整超时 (~5-10ms) |
| 密钥文件损坏 | 🟢 低 | 需要重新配对 | 原子写入，提供重新配对 |

### 5.2 项目失能预防

| 场景 | 预防措施 |
|------|----------|
| 认证代码 bug 导致所有连接失败 | 认证模块完全隔离，提供 `--no-auth` |
| 旧版本无法连接 | 版本协商，旧版跳过认证 |
| ADB 模式被错误认证 | ADB 模式强制跳过认证 |

---

## 六、测试策略

### 6.1 单元测试

```python
# tests/test_auth_*.py

# 密钥生成
test_key_length()          # 32 字节
test_key_randomness()      # 足够随机
test_key_entropy()         # 熵值检查

# HMAC 计算
test_hmac_correctness()    # 与标准库一致
test_hmac_deterministic()  # 相同输入相同输出
test_hmac_key_sensitivity() # 密钥微小变化导致不同结果

# 文件操作
test_keyfile_write_read()  # 写入后读取一致
test_keyfile_permissions() # 权限 600
test_keyfile_delete()      # 删除后不存在
```

### 6.2 集成测试

```python
# tests/test_auth_integration.py

test_successful_auth()     # 正确密钥通过认证
test_failed_auth()         # 错误密钥拒绝
test_auth_timeout()        # 超时处理
test_replay_attack()       # 重放攻击防护
```

### 6.3 兼容性测试

| 场景 | 客户端 | 服务端 | 预期行为 |
|------|--------|--------|----------|
| 新+新 | v1.4+ | v1.4+ | 完整认证 |
| 旧+新 | <v1.4 | v1.4+ | 跳过认证 |
| 新+旧 | v1.4+ | <v1.4 | 跳过认证 |
| ADB模式 | 任意 | 任意 | 跳过认证 |

### 6.4 回归测试清单

- [ ] 网络模式视频播放
- [ ] 网络模式音频播放
- [ ] 控制命令（触摸、按键）
- [ ] 文件传输（上传/下载）
- [ ] 截图功能
- [ ] 心跳机制 (PING/PONG)

---

## 七、实施计划

### Phase 1: 基础设施 (2天)
- [ ] 创建 `core/auth.py` 模块
- [ ] 修改 `adb.py` 添加 `push_auth_key()`
- [ ] 修改 `Options.java` 添加 `authKeyFile`
- [ ] 单元测试

### Phase 2: 协议层 (1天)
- [ ] 修改 `protocol.py` 添加消息类型
- [ ] 修改 `DeviceMessage.java` / `DeviceMessageWriter.java`
- [ ] 修改 `ControlMessage.java` / `ControlMessageReader.java`
- [ ] 更新 `PROTOCOL_SPEC.md`

### Phase 3: 服务端认证 (2天)
- [ ] 创建 `AuthHandler.java`
- [ ] 修改 `Server.java` 读取密钥
- [ ] 修改 `DesktopConnection.java` 插入认证
- [ ] 实现版本协商

### Phase 4: 客户端认证 (2天)
- [ ] 修改 `connection.py` 添加认证流程
- [ ] 修改 `client.py` 整合认证
- [ ] 修改 `device_msg.py` 解析认证消息
- [ ] 兼容性处理

### Phase 5: 测试与集成 (2天)
- [ ] 回归测试
- [ ] 兼容性测试
- [ ] 文档更新

---

## 八、安全考虑

### 8.1 密钥安全
- 密钥使用 CSPRNG 生成 (`secrets.token_bytes`)
- 本地存储权限 600
- 服务端读取后立即删除文件
- 不在日志中打印密钥

### 8.2 认证安全
- Challenge 随机生成，防止重放
- HMAC-SHA256 单向性，密钥不传输
- 超时机制防止恶意连接

### 8.3 降级安全
- `--no-auth` 仅用于调试
- 生产环境应启用认证
- ADB 模式依赖 ADB 自身认证

---

## 九、参考资料

- [HMAC - Wikipedia](https://en.wikipedia.org/wiki/HMAC)
- [RFC 2104 - HMAC: Keyed-Hashing for Message Authentication](https://tools.ietf.org/html/rfc2104)
- [SCRAM (RFC 5802)](https://tools.ietf.org/html/rfc5802) - 参考但未采用
- [TLS-PSK (RFC 4279)](https://tools.ietf.org/html/rfc4279) - 未来可选

---

## 十、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-02-28 | 初始设计文档 |
