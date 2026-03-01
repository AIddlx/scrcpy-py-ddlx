# 认证机制

> HMAC-SHA256 Challenge-Response

---

## 概述

v1.4 版本引入的网络安全认证机制。

### 为什么需要认证

```
无认证:
  任何知道设备 IP 的人都可以连接

有认证:
  只有持有密钥的客户端才能连接
```

---

## 认证流程

```
客户端                              服务端
   │                                  │
   │ ──────── Connect ────────────>  │
   │                                  │
   │ <────── CHALLENGE (32B) ─────── │
   │                                  │
   │     生成 RESPONSE:               │
   │     HMAC-SHA256(key, challenge) │
   │                                  │
   │ ─────── RESPONSE (32B) ───────> │
   │                                  │
   │                        验证 RESPONSE
   │                                  │
   │ <── AUTH_RESULT (success) ───── │
   │                                  │
   │         正常通信开始             │
```

---

## 密钥管理

### 密钥生成

```python
from scrcpy_py_ddlx.core.auth import generate_auth_key

# 生成 32 字节随机密钥
key = generate_auth_key()  # os.urandom(32)
```

### 密钥存储

```
本地存储位置:
  ~/.config/scrcpy-py-ddlx/auth_keys/{serial}.key
  ~/.config/scrcpy-py-ddlx/auth_keys/{ip}.key

设备存储位置:
  /data/local/tmp/scrcpy-auth.key
```

### 密钥分发

```bash
# 1. 生成密钥 (自动)
# 2. 保存到本地
# 3. 通过 ADB 推送到设备
# 4. 服务端读取后删除 (单次使用)
```

---

## 命令行使用

### 启用认证 (默认)

```bash
python test_network_direct.py --ip 192.168.1.100
# 默认 --auth 启用
```

### 禁用认证

```bash
python test_network_direct.py --ip 192.168.1.100 --no-auth
```

### Hot-Connect 自动发现

```bash
# 自动发现并连接（无需指定 IP）
python test_network_direct.py --hot-connect

# 指定 IP 直接连接
python test_network_direct.py --hot-connect --ip 192.168.1.100
```

### 指定密钥路径

```bash
python test_network_direct.py --ip 192.168.1.100 --auth-key /path/to/key
```

---

## `--no-auth` 参数行为

`--no-auth` 完全控制客户端和服务端的认证行为：

| 阶段 | 行为 |
|------|------|
| 服务端启动 | 不添加 `auth_key_file` 参数，服务端不要求认证 |
| 客户端连接 | 不加载本地密钥，不响应认证挑战 |

### 连接结果矩阵

| 服务端 | 客户端 | 结果 |
|--------|--------|------|
| 认证模式 (默认) | 认证模式 (默认) | ✅ 连接成功 |
| 认证模式 (默认) | `--no-auth` | ❌ 认证失败 |
| `--no-auth` | 认证模式 (默认) | ✅ 连接成功 (服务端不要求) |
| `--no-auth` | `--no-auth` | ✅ 连接成功 |

### 认证失败错误

```
[ERROR] Authentication failed: Server requires authentication but no auth key provided
       (use --auth or connect to server started with --no-auth)
```

### 代码实现

```python
# config.py
auth_enabled: bool = True  # ClientConfig 参数

# client.py
if auth_enabled:
    auth_key = load_auth_key(host)  # 加载密钥
else:
    logger.info("Authentication disabled by config")

# connection.py
if first_byte == 0xF0:  # 服务端要求认证
    if auth_key is not None:
        perform_auth(socket, auth_key)  # 认证
    else:
        raise AuthError("Server requires authentication but no auth key provided")
```

---

## 协议消息

### 类型定义

| 类型 | 值 | 方向 |
|------|-----|------|
| CHALLENGE | 0xF0 | Server → Client |
| RESPONSE | 0xF1 | Client → Server |
| AUTH_RESULT | 0xF2 | Server → Client |

### 消息格式

```
CHALLENGE:
  [type: 1B][random: 32B]

RESPONSE:
  [type: 1B][hmac: 32B]

AUTH_RESULT:
  [type: 1B][success: 1B]
```

---

## 实现细节

### 客户端

```python
import hmac
import hashlib

def compute_response(key: bytes, challenge: bytes) -> bytes:
    """计算 HMAC-SHA256 响应"""
    return hmac.new(key, challenge, hashlib.sha256).digest()
```

### 服务端 (AuthHandler.java)

```java
public class AuthHandler {
    public boolean verify(byte[] challenge, byte[] response) {
        byte[] expected = HmacUtils.hmacSha256(authKey, challenge);
        return Arrays.equals(expected, response);
    }
}
```

---

## 安全考虑

### 密钥安全

- 密钥在设备上读取后立即删除
- 本地密钥存储在用户目录
- 密钥仅用于可信网络

### 已知限制

- 传输未加密 (明文)
- 仅防止未授权连接
- 不防止中间人攻击

### 建议

- 公共网络使用 ADB + USB 模式
- 私有网络可使用网络模式 + 认证

---

## 相关文档

- [network.md](network.md) - 网络模式
- [overview.md](overview.md) - 功能概览
