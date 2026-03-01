# SystemWrappers (服务端)

> **目录**: `wrappers/`
> **文件**: 12 个 Java 文件
> **功能**: Android 系统 API 包装

---

## 文件清单

| 文件 | 职责 |
|------|------|
| `ServiceManager.java` | 服务管理器入口 |
| `ActivityManager.java` | 活动管理器 |
| `ClipboardManager.java` | 剪贴板管理器 |
| `DisplayManager.java` | 显示管理器 |
| `DisplayControl.java` | 显示控制 |
| `DisplayWindowListener.java` | 显示窗口监听器 |
| `InputManager.java` | 输入管理器 |
| `PowerManager.java` | 电源管理器 |
| `StatusBarManager.java` | 状态栏管理器 |
| `WindowManager.java` | 窗口管理器 |
| `SurfaceControl.java` | Surface 控制 |
| `ContentProvider.java` | 内容提供者 |

---

## ServiceManager

服务管理器入口，获取所有系统服务。

```java
public final class ServiceManager {
    private static final ServiceManager INSTANCE = new ServiceManager();

    // 获取服务实例
    public static ActivityManager getActivityManager()
    public static ClipboardManager getClipboardManager()
    public static DisplayManager getDisplayManager()
    public static InputManager getInputManager()
    public static PowerManager getPowerManager()
    public static WindowManager getWindowManager()
    public static StatusBarManager getStatusBarManager()
    public static SurfaceControl getSurfaceControl()
}
```

### 使用示例

```java
// 获取显示信息
DisplayInfo info = ServiceManager.getDisplayManager().getDisplayInfo(displayId);

// 设置剪贴板
ServiceManager.getClipboardManager().setText(text);

// 注入按键
ServiceManager.getInputManager().injectKeyEvent(event);
```

---

## DisplayManager

显示管理器。

```java
public final class DisplayManager {
    // 获取显示信息
    public DisplayInfo getDisplayInfo(int displayId)

    // 获取所有显示 ID
    public int[] getDisplayIds()

    // 注册显示监听器
    public void registerDisplayListener(DisplayListener listener)

    // 刷新显示信息
    public void refreshDisplayInfo()
}
```

### DisplayInfo

```java
public class DisplayInfo {
    private final Size size;
    private final int rotation;
    private final int densityDpi;
    private final String name;
    private final long aliveTime;

    public Size getSize() { return size; }
    public int getRotation() { return rotation; }
    public int getDensityDpi() { return densityDpi; }
}
```

---

## DisplayControl

显示电源控制。

```java
public final class DisplayControl {
    // 设置显示电源状态
    public static void setDisplayPower(int displayId, boolean on)

    // 获取显示电源状态
    public static boolean isDisplayOn(int displayId)
}
```

---

## InputManager

输入管理器。

```java
public final class InputManager {
    // 注入按键事件
    public boolean injectKeyEvent(KeyEvent event, int mode)

    // 注入触摸事件
    public boolean injectMotionEvent(MotionEvent event, int mode)

    // 注入输入事件
    public boolean injectInputEvent(InputEvent event, int mode)

    // 注入模式
    public static final int INJECT_INPUT_EVENT_MODE_ASYNC = 0;
    public static final int INJECT_INPUT_EVENT_MODE_WAIT_FOR_FINISH = 1;
    public static final int INJECT_INPUT_EVENT_MODE_WAIT_FOR_RESULT = 2;
}
```

---

## ClipboardManager

剪贴板管理器。

```java
public final class ClipboardManager {
    // 获取剪贴板文本
    public String getText()

    // 设置剪贴板文本
    public void setText(CharSequence text)

    // 检查是否有内容
    public boolean hasText()

    // 添加变化监听器
    public void addPrimaryClipChangedListener(OnPrimaryClipChangedListener listener)
}
```

---

## PowerManager

电源管理器。

```java
public final class PowerManager {
    // 获取电源服务
    private PowerManager() {
        mManager = ServiceManager.getService("power");
    }

    // 唤醒设备
    public void wakeUp(long time)

    // 保持唤醒
    public WakeLock newWakeLock(int levelAndFlags, String tag)

    // 检查屏幕状态
    public boolean isScreenOn()
}
```

---

## WindowManager

窗口管理器。

```java
public final class WindowManager {
    // 显示常量
    public static final int DISPLAY_IME_POLICY_LOCAL = 0;
    public static final int DISPLAY_IME_POLICY_FALLBACK_DISPLAY = 1;
    public static final int DISPLAY_IME_POLICY_HIDE = 2;

    // 获取窗口服务
    public WindowManager() {
        mManager = ServiceManager.getService("window");
    }

    // 冻结/解冻屏幕旋转
    public void freezeRotation(int rotation)
    public void thawRotation()

    // 设置显示 IME 策略
    public void setDisplayImePolicy(int displayId, int policy)

    // 获取显示 ID
    public int getDisplayId()
}
```

---

## StatusBarManager

状态栏管理器。

```java
public final class StatusBarManager {
    // 展开通知面板
    public void expandNotificationsPanel()

    // 展开设置面板
    public void expandSettingsPanel()

    // 收起面板
    public void collapsePanels()
}
```

---

## ActivityManager

活动管理器。

```java
public final class ActivityManager {
    // 获取应用列表
    public List<DeviceApp> getApps()

    // 启动应用
    public boolean startApp(String packageName, String activityName)

    // 强制停止应用
    public void forceStopPackage(String packageName)
}
```

---

## SurfaceControl

Surface 控制 (底层显示操作)。

```java
public final class SurfaceControl {
    // 创建显示
    public static int createDisplay(String name, boolean secure)

    // 销毁显示
    public static void destroyDisplay(int displayId)

    // 设置显示层
    public static void setDisplayLayerStack(int displayId, int layerStack)

    // 设置显示投影
    public static void setDisplayProjection(int displayId, int orientation,
                                            Rect layerStackRect, Rect displayRect)
}
```

---

## ContentProvider

内容提供者包装。

```java
public final class ContentProvider {
    // 查询
    public Cursor query(Uri uri, String[] projection,
                        String selection, String[] selectionArgs,
                        String sortOrder)

    // 插入
    public Uri insert(Uri uri, ContentValues values)

    // 更新
    public int update(Uri uri, ContentValues values,
                      String selection, String[] selectionArgs)

    // 删除
    public int delete(Uri uri, String selection, String[] selectionArgs)
}
```

---

## DisplayWindowListener

显示窗口状态监听。

```java
public class DisplayWindowListener {
    // 注册监听器
    public void register(int displayId)

    // 注销监听器
    public void unregister()

    // 回调接口
    public interface OnDisplayWindowListener {
        void onWindowStackChanged(int displayId);
    }
}
```

---

## 服务获取方式

```java
// 通过 ServiceManager 获取系统服务
Object service = ServiceManager.getService("activity");

// 使用反射调用隐藏 API
Method method = service.getClass().getMethod("methodName", ...);
method.invoke(service, args);
```

---

## 相关文档

- [Device.md](Device.md) - 设备操作
- [Controller.md](ControlProtocol.md) - 控制器
- [ServerCore.md](ServerCore.md) - 服务端核心
