# auth.py

> **文件**: `core/auth.py`
> **功能**: HMAC-SHA256 Challenge-Response 认证

---

## 概述

`auth.py` 实现客户端认证逻辑，与 `AuthHandler.java` 配合完成网络模式认证。

---

## 常量

```python
AUTH_KEY_SIZE = 32       # 256 bits
AUTH_CHALLENGE_SIZE = 32 # 256 bits
AUTH_RESPONSE_SIZE = 32  # HMAC-SHA256 输出

DEFAULT_REMOTE_KEY_PATH = "/data/local/tmp/scrcpy-auth.key"
AUTH_KEY_DIR = "~/.config/scrcpy-py-ddlx/auth_keys/"
```

---

## 核心函数

```python
# 生成随机密钥
def generate_auth_key() -> bytes

# 保存密钥到本地
def save_auth_key(device_id: str, key: bytes) -> Path

# 加载密钥
def load_auth_key(device_id: str) -> Optional[bytes]

# 推送密钥到设备
def push_key_to_device(device_serial: str, key: bytes,
                       remote_path: str = DEFAULT_REMOTE_KEY_PATH) -> bool

# 计算 HMAC 响应
def compute_response(challenge: bytes, key: bytes) -> bytes

# 执行认证流程
def perform_authentication(connection, key: bytes) -> bool
```

---

## 认证流程

```python
# 1. 生成/加载密钥
key = load_auth_key(device_id) or generate_auth_key()
save_auth_key(device_id, key)

# 2. 推送密钥到设备
push_key_to_device(device_serial, key)

# 3. 连接后执行认证
# 3.1 接收 Challenge
challenge = receive_challenge(connection)
# challenge = 32 bytes 随机数

# 3.2 计算 Response
response = compute_response(challenge, key)
# response = HMAC-SHA256(challenge, key)

# 3.3 发送 Response
send_response(connection, response)

# 3.4 接收结果
result = receive_auth_result(connection)
# result = 0x01 (成功) 或 0x00 (失败)
```

---

## 消息类型

| 类型 | 值 | 方向 |
|------|-----|------|
| TYPE_CHALLENGE | 0xF0 | Server → Client |
| TYPE_RESPONSE | 0xF1 | Client → Server |
| TYPE_AUTH_RESULT | 0xF2 | Server → Client |

---

## 密钥存储

### 本地存储

```
~/.config/scrcpy-py-ddlx/auth_keys/
├── {device_serial}.key
├── {device_ip}.key
└── ...
```

### 设备端存储

```
/data/local/tmp/scrcpy-auth.key
```

密钥在认证后被自动删除。

---

## 安全特性

| 特性 | 实现 |
|------|------|
| 密钥生成 | `secrets.token_bytes()` |
| 哈希算法 | HMAC-SHA256 |
| 文件权限 | 0o600 (仅所有者可读写) |
| 密钥清理 | 设备端自动删除 |

---

## 相关文档

- [AuthHandler.md](../server/AuthHandler.md) - 服务端认证
- [AUTH_DESIGN.md](../../../development/AUTH_DESIGN.md) - 认证设计
