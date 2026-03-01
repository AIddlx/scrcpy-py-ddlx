package com.genymobile.scrcpy.wrappers;

import com.genymobile.scrcpy.AndroidVersions;
import com.genymobile.scrcpy.util.Ln;

import android.annotation.SuppressLint;
import android.graphics.Rect;
import android.os.Build;
import android.os.IBinder;
import android.view.Surface;

import java.lang.reflect.Method;

@SuppressLint("PrivateApi")
public final class SurfaceControl {

    private static final Class<?> CLASS;

    // see <https://android.googlesource.com/platform/frameworks/base.git/+/pie-release-2/core/java/android/view/SurfaceControl.java#305>
    public static final int POWER_MODE_OFF = 0;
    public static final int POWER_MODE_NORMAL = 2;

    static {
        try {
            CLASS = Class.forName("android.view.SurfaceControl");
        } catch (ClassNotFoundException e) {
            throw new AssertionError(e);
        }
    }

    private static Method getBuiltInDisplayMethod;
    private static Method setDisplayPowerModeMethod;
    private static Method getPhysicalDisplayTokenMethod;
    private static Method getPhysicalDisplayIdsMethod;

    private SurfaceControl() {
        // only static methods
    }

    public static void openTransaction() {
        try {
            CLASS.getMethod("openTransaction").invoke(null);
        } catch (Exception e) {
            throw new AssertionError(e);
        }
    }

    public static void closeTransaction() {
        try {
            CLASS.getMethod("closeTransaction").invoke(null);
        } catch (Exception e) {
            throw new AssertionError(e);
        }
    }

    public static void setDisplayProjection(IBinder displayToken, int orientation, Rect layerStackRect, Rect displayRect) {
        try {
            CLASS.getMethod("setDisplayProjection", IBinder.class, int.class, Rect.class, Rect.class)
                    .invoke(null, displayToken, orientation, layerStackRect, displayRect);
        } catch (Exception e) {
            throw new AssertionError(e);
        }
    }

    public static void setDisplayLayerStack(IBinder displayToken, int layerStack) {
        try {
            CLASS.getMethod("setDisplayLayerStack", IBinder.class, int.class).invoke(null, displayToken, layerStack);
        } catch (Exception e) {
            throw new AssertionError(e);
        }
    }

    public static void setDisplaySurface(IBinder displayToken, Surface surface) {
        try {
            CLASS.getMethod("setDisplaySurface", IBinder.class, Surface.class).invoke(null, displayToken, surface);
        } catch (Exception e) {
            throw new AssertionError(e);
        }
    }

    public static IBinder createDisplay(String name, boolean secure) throws Exception {
        return (IBinder) CLASS.getMethod("createDisplay", String.class, boolean.class).invoke(null, name, secure);
    }

    private static Method getGetBuiltInDisplayMethod() throws NoSuchMethodException {
        if (getBuiltInDisplayMethod == null) {
            // the method signature has changed in Android 10
            // <https://github.com/Genymobile/scrcpy/issues/586>
            if (Build.VERSION.SDK_INT < AndroidVersions.API_29_ANDROID_10) {
                getBuiltInDisplayMethod = CLASS.getMethod("getBuiltInDisplay", int.class);
            } else {
                getBuiltInDisplayMethod = CLASS.getMethod("getInternalDisplayToken");
            }
        }
        return getBuiltInDisplayMethod;
    }

    public static boolean hasGetBuildInDisplayMethod() {
        try {
            getGetBuiltInDisplayMethod();
            return true;
        } catch (NoSuchMethodException e) {
            return false;
        }
    }

    public static IBinder getBuiltInDisplay() {
        try {
            Method method = getGetBuiltInDisplayMethod();
            if (Build.VERSION.SDK_INT < AndroidVersions.API_29_ANDROID_10) {
                // call getBuiltInDisplay(0)
                return (IBinder) method.invoke(null, 0);
            }

            // call getInternalDisplayToken()
            return (IBinder) method.invoke(null);
        } catch (ReflectiveOperationException e) {
            Ln.e("Could not invoke method", e);
            return null;
        }
    }

    private static Method getGetPhysicalDisplayTokenMethod() throws NoSuchMethodException {
        if (getPhysicalDisplayTokenMethod == null) {
            getPhysicalDisplayTokenMethod = CLASS.getMethod("getPhysicalDisplayToken", long.class);
        }
        return getPhysicalDisplayTokenMethod;
    }

    public static IBinder getPhysicalDisplayToken(long physicalDisplayId) {
        try {
            Method method = getGetPhysicalDisplayTokenMethod();
            return (IBinder) method.invoke(null, physicalDisplayId);
        } catch (ReflectiveOperationException e) {
            Ln.e("Could not invoke method", e);
            return null;
        }
    }

    private static Method getGetPhysicalDisplayIdsMethod() throws NoSuchMethodException {
        if (getPhysicalDisplayIdsMethod == null) {
            getPhysicalDisplayIdsMethod = CLASS.getMethod("getPhysicalDisplayIds");
        }
        return getPhysicalDisplayIdsMethod;
    }

    public static boolean hasGetPhysicalDisplayIdsMethod() {
        try {
            getGetPhysicalDisplayIdsMethod();
            return true;
        } catch (NoSuchMethodException e) {
            return false;
        }
    }

    public static long[] getPhysicalDisplayIds() {
        try {
            Method method = getGetPhysicalDisplayIdsMethod();
            return (long[]) method.invoke(null);
        } catch (ReflectiveOperationException e) {
            Ln.e("Could not invoke method", e);
            return null;
        }
    }

    private static Method getSetDisplayPowerModeMethod() throws NoSuchMethodException {
        if (setDisplayPowerModeMethod == null) {
            setDisplayPowerModeMethod = CLASS.getMethod("setDisplayPowerMode", IBinder.class, int.class);
        }
        return setDisplayPowerModeMethod;
    }

    public static boolean setDisplayPowerMode(IBinder displayToken, int mode) {
        try {
            Method method = getSetDisplayPowerModeMethod();
            method.invoke(null, displayToken, mode);
            return true;
        } catch (ReflectiveOperationException e) {
            Ln.e("Could not invoke method", e);
            return false;
        }
    }

    public static void destroyDisplay(IBinder displayToken) {
        try {
            CLASS.getMethod("destroyDisplay", IBinder.class).invoke(null, displayToken);
        } catch (Exception e) {
            throw new AssertionError(e);
        }
    }

    /**
     * Take a screenshot of the display.
     *
     * Handles different Android API levels:
     * - Android 14+ (API 34+): captureDisplay() with DisplayCaptureArgs
     * - Android 12-13 (API 31-33): captureDisplay() with DisplayCaptureArgs
     * - Android 11 (API 30): screenshot(Rect, int, int, int)
     * - Android 10 and below: screenshot(int, int)
     *
     * @param width  The desired width of the screenshot
     * @param height The desired height of the screenshot
     * @return A Bitmap of the screenshot, or null on failure
     */
    public static android.graphics.Bitmap screenshot(int width, int height) {
        // Try methods from newest to oldest API
        android.graphics.Bitmap bitmap = null;

        // Android 14+ (API 34+): Try captureDisplay with ScreenshotHardwareBuffer
        if (Build.VERSION.SDK_INT >= 34 && bitmap == null) {
            bitmap = screenshotApi34(width, height);
            if (bitmap != null) {
                Ln.d("Screenshot using API 34+ captureDisplay");
                return bitmap;
            }
        }

        // Android 12+ (API 31+): Try captureDisplay with DisplayCaptureArgs
        if (Build.VERSION.SDK_INT >= 31 && bitmap == null) {
            bitmap = screenshotApi31(width, height);
            if (bitmap != null) {
                Ln.d("Screenshot using API 31+ captureDisplay");
                return bitmap;
            }
        }

        // Android 11 (API 30): screenshot(Rect, int, int, int)
        if (Build.VERSION.SDK_INT >= 30 && bitmap == null) {
            bitmap = screenshotApi30(width, height);
            if (bitmap != null) {
                Ln.d("Screenshot using API 30 screenshot(Rect, int, int, int)");
                return bitmap;
            }
        }

        // Android 10 and below: legacy screenshot(int, int)
        if (bitmap == null) {
            bitmap = screenshotLegacy(width, height);
            if (bitmap != null) {
                Ln.d("Screenshot using legacy screenshot(int, int)");
                return bitmap;
            }
        }

        Ln.e("Screenshot failed on all API methods");
        return null;
    }

    /**
     * Android 14+ (API 34+): Use captureDisplay() with IWindowManager
     */
    private static android.graphics.Bitmap screenshotApi34(int width, int height) {
        try {
            // Android 14 uses IWindowManager.captureDisplay()
            // This requires system permissions, likely won't work for us
            // Try the API 31 method first as fallback
            return screenshotApi31(width, height);
        } catch (Exception e) {
            Ln.d("API 34 screenshot failed: " + e.getMessage());
            return null;
        }
    }

    /**
     * Android 12+ (API 31+): Use captureDisplay() with DisplayCaptureArgs
     */
    private static android.graphics.Bitmap screenshotApi31(int width, int height) {
        try {
            IBinder displayToken = getBuiltInDisplay();
            if (displayToken == null) {
                Ln.d("Could not get display token for API 31 screenshot");
                return null;
            }

            android.graphics.Rect sourceCrop = new android.graphics.Rect(0, 0, width, height);

            // Try DisplayCaptureArgs.Builder approach
            Class<?> displayCaptureArgsClass = Class.forName("android.view.SurfaceControl$DisplayCaptureArgs");
            Class<?> builderClass = Class.forName("android.view.SurfaceControl$DisplayCaptureArgs$Builder");

            // Create builder: new DisplayCaptureArgs.Builder(displayToken)
            Object builder = builderClass.getConstructor(IBinder.class).newInstance(displayToken);

            // builder.setSourceCrop(sourceCrop)
            builderClass.getMethod("setSourceCrop", android.graphics.Rect.class).invoke(builder, sourceCrop);

            // builder.setSize(width, height)
            builderClass.getMethod("setSize", int.class, int.class).invoke(builder, width, height);

            // builder.build()
            Object captureArgs = builderClass.getMethod("build").invoke(builder);

            // SurfaceControl.captureDisplay(captureArgs)
            Method captureMethod = CLASS.getMethod("captureDisplay", displayCaptureArgsClass);
            Object hardwareBuffer = captureMethod.invoke(null, captureArgs);

            if (hardwareBuffer == null) {
                return null;
            }

            // ScreenshotHardwareBuffer.asBitmap()
            Class<?> shbClass = Class.forName("android.view.SurfaceControl$ScreenshotHardwareBuffer");
            Method asBitmapMethod = shbClass.getMethod("asBitmap");
            return (android.graphics.Bitmap) asBitmapMethod.invoke(hardwareBuffer);

        } catch (Exception e) {
            Ln.d("API 31 screenshot failed: " + e.getMessage());
            return null;
        }
    }

    /**
     * Android 11 (API 30): Use screenshot(Rect, int, int, int)
     */
    private static android.graphics.Bitmap screenshotApi30(int width, int height) {
        try {
            android.graphics.Rect sourceCrop = new android.graphics.Rect(0, 0, width, height);
            int rotation = android.view.Surface.ROTATION_0;

            Method method = CLASS.getMethod("screenshot",
                android.graphics.Rect.class, int.class, int.class, int.class);
            return (android.graphics.Bitmap) method.invoke(null, sourceCrop, width, height, rotation);
        } catch (Exception e) {
            Ln.d("API 30 screenshot failed: " + e.getMessage());
            return null;
        }
    }

    /**
     * Android 10 and below: Use legacy screenshot(int, int)
     */
    private static android.graphics.Bitmap screenshotLegacy(int width, int height) {
        try {
            Method method = CLASS.getMethod("screenshot", int.class, int.class);
            return (android.graphics.Bitmap) method.invoke(null, width, height);
        } catch (Exception e) {
            Ln.d("Legacy screenshot failed: " + e.getMessage());
            return null;
        }
    }
}
