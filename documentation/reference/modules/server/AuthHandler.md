# AuthHandler

> **文件**: `AuthHandler.java`
> **功能**: HMAC-SHA256 Challenge-Response 认证处理器

---

## 概述

`AuthHandler` 实现网络模式的认证流程，使用 HMAC-SHA256 确保只有授权客户端可以连接。

---

## 认证流程

```
┌──────────┐                              ┌──────────┐
│  Client  │                              │  Server  │
└──────────┘                              └──────────┘
     │                                          │
     │  1. 密钥通过 ADB 推送到                    │
     │     /data/local/tmp/scrcpy-auth.key      │
     │                                          │
     │  2. TCP 连接建立                          │
     │─────────────────────────────────────────►│
     │                                          │
     │  3. Challenge (32 bytes 随机数)           │
     │     TYPE_CHALLENGE (0xF0)                │
     │◄─────────────────────────────────────────│
     │                                          │
     │  4. Response (HMAC-SHA256)               │
     │     TYPE_RESPONSE (0xF1)                 │
     │─────────────────────────────────────────►│
     │                                          │
     │  5. Auth Result (1 byte)                 │
     │     TYPE_AUTH_RESULT (0xF2)              │
     │◄─────────────────────────────────────────│
     │     0x01 = 成功, 0x00 = 失败              │
     │                                          │
     │  6. 认证成功后删除密钥文件                  │
     │                                          │
```

---

## 核心方法

```java
public class AuthHandler {
    // 从文件加载密钥
    public static byte[] loadAuthKey(String path);

    // 生成随机 Challenge
    public static byte[] generateChallenge();

    // 验证 Response
    public static boolean verifyResponse(
        byte[] challenge,
        byte[] response,
        byte[] key
    );

    // 执行完整认证流程
    public boolean authenticate(
        InputStream in,
        OutputStream out,
        byte[] key
    );
}
```

---

## 消息格式

### TYPE_CHALLENGE (0xF0)

```
[type: 1B][challenge: 32B]

type: 0xF0
challenge: 32 字节随机数 (SecureRandom)
```

### TYPE_RESPONSE (0xF1)

```
[type: 1B][response: 32B]

type: 0xF1
response: HMAC-SHA256(challenge, key)
```

### TYPE_AUTH_RESULT (0xF2)

```
[type: 1B][result: 1B]

type: 0xF2
result: 0x01 = 成功, 0x00 = 失败
```

---

## 安全特性

| 特性 | 实现 |
|------|------|
| 密钥长度 | 256 bits (32 bytes) |
| 随机数生成 | `SecureRandom` |
| 哈希算法 | HMAC-SHA256 |
| 密钥存储 | `/data/local/tmp/` |
| 密钥清理 | 认证后自动删除 |

---

## 配置

服务端启动参数：
```bash
auth_key_file=/data/local/tmp/scrcpy-auth.key
```

---

## 相关文档

- [auth.md](../../client/auth.md) - 客户端认证模块
- [AUTH_DESIGN.md](../../../../development/AUTH_DESIGN.md) - 认证设计文档
