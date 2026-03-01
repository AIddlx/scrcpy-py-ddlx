# Android/Java 依赖

> 服务端 Android 项目依赖

---

## 构建系统

### Gradle

| 属性 | 值 |
|------|-----|
| **插件** | com.android.tools.build:gradle |
| **版本** | 8.13.1 |
| **用途** | Android 构建系统 |

### 仓库

```groovy
repositories {
    google()
    mavenCentral()
}
```

---

## Android SDK

| 属性 | 值 |
|------|-----|
| **compileSdk** | 36 |
| **minSdk** | 21 (Android 5.0) |
| **targetSdk** | 36 |

### 版本兼容性

| API Level | Android 版本 | 支持 |
|-----------|-------------|------|
| 21 | 5.0 Lollipop | ✅ 最低 |
| 29 | 10 | ✅ FEC/虚拟显示 |
| 30 | 11 | ✅ 低延迟模式 |
| 31 | 12 | ✅ 摄像头镜像 |
| 36 | 15 | ✅ 目标版本 |

---

## Java 依赖

### 测试依赖

```groovy
dependencies {
    testImplementation 'junit:junit:4.13.2'
}
```

| 库 | 版本 | 用途 |
|---|------|------|
| JUnit | 4.13.2 | 单元测试 |

**说明**:
- 服务端代码主要是 Android SDK API 调用
- 无第三方运行时依赖
- 仅使用 JUnit 进行测试

---

## Android SDK API 使用

### 媒体 API

| API | 用途 | 最低版本 |
|-----|------|---------|
| MediaCodec | 视频/音频编码 | 21 |
| MediaProjection | 屏幕捕获 | 21 |
| AudioRecord | 音频录制 | 21 |
| AudioPlaybackCapture | 播放捕获 | 29 |

### 显示 API

| API | 用途 | 最低版本 |
|-----|------|---------|
| VirtualDisplay | 虚拟显示器 | 21 |
| DisplayManager | 显示管理 | 21 |
| SurfaceControl | Surface 控制 | 21 |

### 输入 API

| API | 用途 | 最低版本 |
|-----|------|---------|
| InputManager | 输入注入 | 21 |
| MotionEvent | 触摸事件 | 21 |
| KeyEvent | 按键事件 | 21 |

### 摄像头 API

| API | 用途 | 最低版本 |
|-----|------|---------|
| CameraManager | 摄像头管理 | 21 |
| CameraDevice | 摄像头设备 | 31 (镜像) |

---

## 编译配置

### build.gradle (server)

```groovy
apply plugin: 'com.android.application'

android {
    namespace = 'com.genymobile.scrcpy'
    compileSdk 36

    defaultConfig {
        applicationId = "com.genymobile.scrcpy"
        minSdkVersion 21
        targetSdkVersion 36
        versionCode 30304
        versionName "3.3.4"
    }

    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }

    buildFeatures {
        buildConfig = true
        aidl = true
    }
}

dependencies {
    testImplementation 'junit:junit:4.13.2'
}
```

---

## 构建命令

### 编译服务端

```bash
cd scrcpy
./gradlew assembleRelease
```

### 输出位置

```
scrcpy/server/build/outputs/apk/release/server-release.apk
```

### 推送到设备

```bash
adb push server-release.apk /data/local/tmp/scrcpy-server.jar
```

---

## Java 版本

| 属性 | 值 |
|------|-----|
| **Java 版本** | 17+ |
| **目标字节码** | Java 11 (Android 兼容) |

---

## ProGuard 规则

```proguard
# 保持 scrcpy 类
-keep class com.genymobile.scrcpy.** { *; }

# 保持 JNI 方法
-keepclasseswithmembernames class * {
    native <methods>;
}
```

---

## 相关文档

- [system.md](system.md) - ADB 和系统工具
- [../wiki/server/README.md](../wiki/server/README.md) - 服务端文档
