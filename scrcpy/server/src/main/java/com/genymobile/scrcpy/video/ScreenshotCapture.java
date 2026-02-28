package com.genymobile.scrcpy.video;

import com.genymobile.scrcpy.Options;
import com.genymobile.scrcpy.control.PositionMapper;
import com.genymobile.scrcpy.device.ConfigurationException;
import com.genymobile.scrcpy.device.Device;
import com.genymobile.scrcpy.device.DisplayInfo;
import com.genymobile.scrcpy.device.Size;
import com.genymobile.scrcpy.util.Ln;
import com.genymobile.scrcpy.wrappers.ServiceManager;
import com.genymobile.scrcpy.wrappers.SurfaceControl;

import android.graphics.Bitmap;
import android.graphics.PixelFormat;
import android.graphics.Rect;
import android.media.Image;
import android.media.ImageReader;
import android.os.Handler;
import android.os.Looper;
import android.view.Surface;

import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

/**
 * A capture component specifically for screenshots.
 * Creates a VirtualDisplay outputting to ImageReader, no encoding involved.
 */
public class ScreenshotCapture {

    private static final int IMAGE_FORMAT = PixelFormat.RGBA_8888;
    private static final int MAX_IMAGES = 2;

    private final Options options;
    private final int displayId;

    private ImageReader imageReader;
    private android.os.IBinder display;
    private Size videoSize;

    private final Lock frameLock = new ReentrantLock();
    private final Condition frameCondition = frameLock.newCondition();
    private Image pendingFrame;
    private boolean frameReady = false;

    public ScreenshotCapture(Options options) {
        this.options = options;
        this.displayId = options.getDisplayId();
        if (this.displayId == Device.DISPLAY_ID_NONE) {
            throw new IllegalArgumentException("Display ID must be specified for screenshot capture");
        }
    }

    /**
     * Initialize the capture. Creates VirtualDisplay outputting to ImageReader.
     */
    public void init() throws ConfigurationException {
        try {
            // Get display info
            DisplayInfo displayInfo = ServiceManager.getDisplayManager().getDisplayInfo(displayId);
            if (displayInfo == null) {
                throw new ConfigurationException("Display " + displayId + " not found");
            }

            Size displaySize = displayInfo.getSize();
            videoSize = computeVideoSize(displaySize, options.getMaxSize());

            Ln.i("ScreenshotCapture: creating ImageReader " + videoSize.getWidth() + "x" + videoSize.getHeight());

            // Create ImageReader
            imageReader = ImageReader.newInstance(
                videoSize.getWidth(),
                videoSize.getHeight(),
                IMAGE_FORMAT,
                MAX_IMAGES
            );

            // Set up frame listener
            Handler handler = new Handler(Looper.getMainLooper());
            imageReader.setOnImageAvailableListener(new ImageReader.OnImageAvailableListener() {
                @Override
                public void onImageAvailable(ImageReader reader) {
                    frameLock.lock();
                    try {
                        if (pendingFrame != null) {
                            pendingFrame.close();
                        }
                        pendingFrame = reader.acquireLatestImage();
                        frameReady = true;
                        frameCondition.signalAll();
                    } finally {
                        frameLock.unlock();
                    }
                }
            }, handler);

            // Create display using SurfaceControl API
            display = SurfaceControl.createDisplay("scrcpy_screenshot", false);
            if (display == null) {
                throw new ConfigurationException("Failed to create display for screenshot");
            }

            // Configure display (must be in a transaction)
            Surface surface = imageReader.getSurface();
            int layerStack = displayInfo.getLayerStack();
            Rect displayRect = new Rect(0, 0, videoSize.getWidth(), videoSize.getHeight());
            Rect deviceRect = new Rect(0, 0, displaySize.getWidth(), displaySize.getHeight());

            SurfaceControl.openTransaction();
            try {
                SurfaceControl.setDisplaySurface(display, surface);
                SurfaceControl.setDisplayLayerStack(display, layerStack);
                SurfaceControl.setDisplayProjection(display, 0, deviceRect, displayRect);
            } finally {
                SurfaceControl.closeTransaction();
            }

            Ln.i("ScreenshotCapture initialized: " + videoSize.getWidth() + "x" + videoSize.getHeight());

        } catch (ConfigurationException e) {
            throw e;
        } catch (Exception e) {
            throw new ConfigurationException("Failed to initialize ScreenshotCapture: " + e.getMessage());
        }
    }

    /**
     * Capture a screenshot.
     *
     * @param timeoutMs Timeout in milliseconds
     * @return Bitmap of the screenshot, or null on failure
     */
    public Bitmap captureScreenshot(long timeoutMs) {
        frameLock.lock();
        try {
            // Wait for frame
            long startTime = System.currentTimeMillis();
            while (!frameReady && pendingFrame == null) {
                long elapsed = System.currentTimeMillis() - startTime;
                if (elapsed >= timeoutMs) {
                    Ln.w("ScreenshotCapture: timeout waiting for frame");
                    return null;
                }
                try {
                    frameCondition.await(timeoutMs - elapsed, java.util.concurrent.TimeUnit.MILLISECONDS);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return null;
                }
            }

            if (pendingFrame == null) {
                Ln.w("ScreenshotCapture: no frame available");
                return null;
            }

            // Convert to Bitmap
            Bitmap bitmap = imageToBitmap(pendingFrame, videoSize.getWidth(), videoSize.getHeight());
            frameReady = false;

            return bitmap;

        } finally {
            frameLock.unlock();
        }
    }

    /**
     * Get the video size.
     */
    public Size getSize() {
        return videoSize;
    }

    /**
     * Release resources.
     */
    public void release() {
        try {
            if (display != null) {
                SurfaceControl.destroyDisplay(display);
                display = null;
            }
        } catch (Exception e) {
            Ln.d("Error destroying display: " + e.getMessage());
        }

        try {
            if (imageReader != null) {
                imageReader.setOnImageAvailableListener(null, null);
                if (imageReader.getSurface() != null) {
                    imageReader.getSurface().release();
                }
                imageReader = null;
            }
        } catch (Exception e) {
            Ln.d("Error releasing ImageReader: " + e.getMessage());
        }

        try {
            if (pendingFrame != null) {
                pendingFrame.close();
                pendingFrame = null;
            }
        } catch (Exception e) {
            // ignore
        }

        Ln.i("ScreenshotCapture released");
    }

    private Size computeVideoSize(Size displaySize, int maxSize) {
        int width = displaySize.getWidth();
        int height = displaySize.getHeight();

        if (maxSize > 0 && (width > maxSize || height > maxSize)) {
            // Scale down to fit maxSize
            if (width > height) {
                height = height * maxSize / width;
                width = maxSize;
            } else {
                width = width * maxSize / height;
                height = maxSize;
            }
        }

        return new Size(width, height);
    }

    private Bitmap imageToBitmap(Image image, int width, int height) {
        if (image == null) {
            return null;
        }

        Image.Plane[] planes = image.getPlanes();
        if (planes == null || planes.length == 0) {
            return null;
        }

        try {
            Image.Plane plane = planes[0];
            java.nio.ByteBuffer buffer = plane.getBuffer();
            int pixelStride = plane.getPixelStride();
            int rowStride = plane.getRowStride();
            int rowPadding = rowStride - pixelStride * width;

            int bitmapWidth = width + (rowPadding > 0 ? rowPadding / pixelStride : 0);
            Bitmap bitmap = Bitmap.createBitmap(bitmapWidth, height, Bitmap.Config.ARGB_8888);
            buffer.rewind();
            bitmap.copyPixelsFromBuffer(buffer);

            if (rowPadding > 0 && bitmapWidth > width) {
                bitmap = Bitmap.createBitmap(bitmap, 0, 0, width, height);
            }

            return bitmap;
        } catch (Exception e) {
            Ln.e("Failed to convert Image to Bitmap: " + e.getMessage());
            return null;
        }
    }
}
