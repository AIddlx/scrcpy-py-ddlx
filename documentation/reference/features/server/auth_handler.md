# 认证处理器 (AuthHandler.java)

> HMAC-SHA256 Challenge-Response 认证

---

## 文件位置

```
scrcpy/server/src/main/java/com/genymobile/scrcpy/AuthHandler.java
```

---

## 概述

v1.4 新增的网络认证功能，确保只有授权客户端可以连接。

---

## 认证流程

```
┌──────────┐                              ┌──────────┐
│  Client  │                              │  Server  │
└──────────┘                              └──────────┘
     │                                          │
     │  1. 密钥通过 ADB 推送                     │
     │─────────────────────────────────────────►│
     │                                          │
     │  2. TCP 连接                             │
     │─────────────────────────────────────────►│
     │                                          │
     │  3. Challenge (32 bytes 随机数)          │
     │◄─────────────────────────────────────────│
     │                                          │
     │  4. Response (HMAC-SHA256)               │
     │─────────────────────────────────────────►│
     │                                          │
     │  5. Auth Result                          │
     │◄─────────────────────────────────────────│
     │                                          │
     │  6. 密钥自动删除                          │
     │                                          │
```

---

## 消息类型

| 类型 | 值 | 方向 |
|------|-----|------|
| `TYPE_CHALLENGE` | 0xF0 | Server → Client |
| `TYPE_RESPONSE` | 0xF1 | Client → Server |
| `TYPE_AUTH_RESULT` | 0xF2 | Server → Client |

---

## 核心方法

```java
public class AuthHandler {
    // 加载密钥
    public static byte[] loadAuthKey(String path);

    // 生成 Challenge
    public static byte[] generateChallenge();

    // 验证 Response
    public static boolean verifyResponse(
        byte[] challenge,
        byte[] response,
        byte[] key
    );

    // 处理认证
    public boolean authenticate(InputStream in, OutputStream out);
}
```

---

## 安全特性

| 特性 | 说明 |
|------|------|
| 密钥长度 | 256 bits |
| 随机数 | `SecureRandom` |
| 哈希 | HMAC-SHA256 |
| 密钥存储 | `/data/local/tmp/` (用后删除) |

---

## 相关文档

- [网络认证](../connection/auth.md)
- [认证设计](../../../development/AUTH_DESIGN.md)
