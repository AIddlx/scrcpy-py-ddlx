# 网络认证

> 网络模式的 HMAC-SHA256 Challenge-Response 认证

---

## 概述

v1.4 新增的网络认证功能，使用 HMAC-SHA256 Challenge-Response 协议确保只有授权客户端可以连接设备。

## 认证流程

```
┌──────────┐                              ┌──────────┐
│  Client  │                              │  Server  │
└──────────┘                              └──────────┘
     │                                          │
     │  1. 生成密钥，通过 ADB 推送到设备          │
     │─────────────────────────────────────────►│
     │     adb push key /data/local/tmp/        │
     │                                          │
     │  2. 发起 TCP 连接                         │
     │─────────────────────────────────────────►│
     │                                          │
     │  3. 接收 Challenge (32 bytes 随机数)      │
     │◄─────────────────────────────────────────│
     │     TYPE_CHALLENGE (0xF0)                 │
     │                                          │
     │  4. 计算 HMAC-SHA256(challenge, key)     │
     │     发送 Response                         │
     │─────────────────────────────────────────►│
     │     TYPE_RESPONSE (0xF1)                  │
     │                                          │
     │  5. 接收认证结果                          │
     │◄─────────────────────────────────────────│
     │     TYPE_AUTH_RESULT (0xF2)               │
     │                                          │
     │  6. 密钥从设备自动删除                     │
     │◄────────────────────────────────────────►│
     │                                          │
```

## 协议消息类型

| 类型 | 值 | 方向 | 说明 |
|------|-----|------|------|
| TYPE_CHALLENGE | 0xF0 | Server → Client | 32 字节随机挑战 |
| TYPE_RESPONSE | 0xF1 | Client → Server | 32 字节 HMAC 响应 |
| TYPE_AUTH_RESULT | 0xF2 | Server → Client | 1 字节结果 (0=失败, 1=成功) |

## 密钥管理

### 密钥生成

```python
from scrcpy_py_ddlx.core.auth import generate_auth_key, save_auth_key

# 生成 32 字节随机密钥
key = generate_auth_key()

# 保存到本地 (~/.config/scrcpy-py-ddlx/auth_keys/)
save_auth_key("device_serial", key)
```

### 密钥分发

```python
from scrcpy_py_ddlx.core.auth import push_key_to_device

# 通过 ADB 推送密钥到设备
push_key_to_device("device_serial", key)
# 密钥保存在 /data/local/tmp/scrcpy-auth.key
```

### 密钥清理

- **设备端**: 认证完成后自动删除
- **客户端**: 保留在本地供下次使用

## 代码位置

| 组件 | 文件 |
|------|------|
| 客户端认证 | `core/auth.py` |
| 服务端认证 | `AuthHandler.java` |

## 安全特性

| 特性 | 说明 |
|------|------|
| 密钥长度 | 256 bits (32 bytes) |
| 随机数生成 | `secrets.token_bytes()` (密码学安全) |
| 哈希算法 | HMAC-SHA256 |
| Challenge 长度 | 256 bits |
| 密钥存储权限 | 0o600 (仅所有者可读写) |
| 单次使用 | 密钥在设备上用后即删 |

## 使用方式

```python
from scrcpy_py_ddlx import Client

# 自动处理认证
client = Client(
    device="192.168.1.100:5555",
    network_mode=True,
    enable_auth=True  # 默认启用
)
client.start()
```

## 相关文档

- [认证设计](../../../development/AUTH_DESIGN.md)
- [网络模式](network_mode.md)
