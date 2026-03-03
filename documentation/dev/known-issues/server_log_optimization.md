# 服务端日志性能优化

## 问题描述

服务端高频日志（UDP 发送、FEC 数据包、心跳等）即使在 INFO 级别下也会产生性能开销，因为 Java 字符串拼接在方法调用前就执行了。

## 分析

```java
// 即使 logLevel=INFO，字符串拼接仍会执行
Ln.v("UDP sent: " + packetSize + " bytes to " + clientAddress);
```

## 已完成

1. **默认日志级别改为 INFO** (`Options.java:26`)
   ```java
   private Ln.Level logLevel = Ln.Level.INFO;
   ```

2. **高频日志从 `Ln.d()` 改为 `Ln.v()`**
   - UdpMediaSender.java - 9 处
   - SimpleXorFecEncoder.java - 1 处
   - Controller.java - 1 处（心跳日志）

3. **添加 `if (Ln.isEnabled(VERBOSE))` 包装**
   - UdpMediaSender.java - 已添加
   - SimpleXorFecEncoder.java - 已添加
   - Controller.java - 已添加

## 待完成

1. **构建并推送服务端进行测试**
   - 使用 `scrcpy/release/deploy_server.sh --verbose` 验证
   - 确认 VERBOSE 日志正常输出
   - 确认 INFO 级别下无性能开销

## 调试推送服务端技巧

Git Bash 中使用 adb push 需要设置 `MSYS_NO_PATHCONV=1` 防止路径转换：

```bash
export MSYS_NO_PATHCONV=1
adb push scrcpy-server /data/local/tmp/scrcpy-server.apk
```

或使用部署脚本：
```bash
cd scrcpy/release
bash deploy_server.sh --verbose
```

## 相关文件

- `scrcpy/server/src/main/java/com/genymobile/scrcpy/Options.java` - 默认日志级别
- `scrcpy/server/src/main/java/com/genymobile/scrcpy/udp/UdpMediaSender.java` - UDP 发送日志
- `scrcpy/server/src/main/java/com/genymobile/scrcpy/udp/SimpleXorFecEncoder.java` - FEC 日志
- `scrcpy/server/src/main/java/com/genymobile/scrcpy/control/Controller.java` - 心跳日志
- `scrcpy/release/deploy_server.sh` - 部署脚本
