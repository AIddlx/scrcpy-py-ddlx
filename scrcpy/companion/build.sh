#!/usr/bin/env bash
#
# Build scrcpy companion app (Quick Settings Tile)
# Minimal build script without Gradle
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$SCRIPT_DIR/app"
BUILD_DIR="$SCRIPT_DIR/build"

# Android SDK paths
ANDROID_HOME="${ANDROID_HOME:-${LOCALAPPDATA:-$HOME}/Android/Sdk}"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    ANDROID_HOME="${ANDROID_HOME:-C:/Users/$USER/AppData/Local/Android/Sdk}"
fi

PLATFORM="${ANDROID_PLATFORM:-34}"
BUILD_TOOLS="${ANDROID_BUILD_TOOLS:-34.0.0}"
ANDROID_JAR="$ANDROID_HOME/platforms/android-$PLATFORM/android.jar"
BUILD_TOOLS_DIR="$ANDROID_HOME/build-tools/$BUILD_TOOLS"
AAPT2="$BUILD_TOOLS_DIR/aapt2"
D8="$BUILD_TOOLS_DIR/d8"
ZIPALIGN="$BUILD_TOOLS_DIR/zipalign"
APKSIGNER="$BUILD_TOOLS_DIR/apksigner"

echo "=== Building Scrcpy Companion ==="
echo "ANDROID_HOME: $ANDROID_HOME"
echo "Platform: android-$PLATFORM"
echo "Build-tools: $BUILD_TOOLS"

# Check tools exist
if [[ ! -f "$ANDROID_JAR" ]]; then
    echo "ERROR: android.jar not found at $ANDROID_JAR"
    exit 1
fi

# Clean and create build dirs
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"/{gen,classes,dex,compiled_res,apk}

# Step 1: Copy resources from source
echo ""
echo "[1/6] Copying resources..."
mkdir -p "$BUILD_DIR/res"

# Copy all resources from source directory
if [[ -d "$APP_DIR/src/main/res" ]]; then
    cp -r "$APP_DIR/src/main/res/"* "$BUILD_DIR/res/" 2>/dev/null || true
fi

# Ensure minimum resources exist
mkdir -p "$BUILD_DIR/res/values"
if [[ ! -f "$BUILD_DIR/res/values/strings.xml" ]]; then
    cat > "$BUILD_DIR/res/values/strings.xml" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Scrcpy Companion</string>
    <string name="tile_label">Scrcpy</string>
</resources>
EOF
fi

# Step 2: Compile resources with aapt2
echo "[2/6] Compiling resources..."

# Use --dir to compile entire resource directory
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows: aapt2 has path issues, use --dir with proper path
    "$AAPT2" compile --dir "$BUILD_DIR/res" -o "$BUILD_DIR/compiled_res/compiled.zip" 2>&1
else
    # Unix: direct compilation
    "$AAPT2" compile --dir "$BUILD_DIR/res" -o "$BUILD_DIR/compiled_res/compiled.zip"
fi

# Step 3: Link resources and generate R.java
echo "[3/6] Linking resources..."

# Copy AndroidManifest.xml from source
if [[ -f "$APP_DIR/src/main/AndroidManifest.xml" ]]; then
    cp "$APP_DIR/src/main/AndroidManifest.xml" "$BUILD_DIR/AndroidManifest.xml"
else
    echo "ERROR: AndroidManifest.xml not found"
    exit 1
fi

"$AAPT2" link -o "$BUILD_DIR/apk/base.apk" \
    --manifest "$BUILD_DIR/AndroidManifest.xml" \
    -I "$ANDROID_JAR" \
    --java "$BUILD_DIR/gen" \
    --auto-add-overlay \
    "$BUILD_DIR/compiled_res/compiled.zip"

# Step 4: Compile Java sources
echo "[4/6] Compiling Java sources..."

# Create source directory and copy Java files
mkdir -p "$BUILD_DIR/src/com/genymobile/scrcpy/companion"
if [[ -d "$APP_DIR/src/main/java/com/genymobile/scrcpy/companion" ]]; then
    cp "$APP_DIR/src/main/java/com/genymobile/scrcpy/companion/"*.java "$BUILD_DIR/src/com/genymobile/scrcpy/companion/"
fi

# Find all java files
SOURCES=$(find "$BUILD_DIR/src" -name "*.java")
R_JAVA=$(find "$BUILD_DIR/gen" -name "*.java")

javac -encoding UTF-8 \
    -bootclasspath "$ANDROID_JAR" \
    -source 1.8 -target 1.8 \
    -d "$BUILD_DIR/classes" \
    $SOURCES $R_JAVA 2>/dev/null || {
    # Fallback for Windows javac
    javac -encoding UTF-8 \
        -bootclasspath "$ANDROID_JAR" \
        -source 1.8 -target 1.8 \
        -d "$BUILD_DIR/classes" \
        "$BUILD_DIR/src/com/genymobile/scrcpy/companion/"*.java \
        "$BUILD_DIR/gen/com/genymobile/scrcpy/companion/R.java"
}

# Step 5: Convert to DEX
echo "[5/6] Converting to DEX..."
# Create jar from all class files (including inner classes)
cd "$BUILD_DIR/classes"
jar cf "$BUILD_DIR/classes.jar" com
cd "$SCRIPT_DIR"

# Check if d8 is a script (Windows) or binary
if [[ -f "${D8}.bat" ]]; then
    # Windows: use d8.bat
    D8="${D8}.bat"
fi

"$D8" --output "$BUILD_DIR/dex" \
    --lib "$ANDROID_JAR" \
    "$BUILD_DIR/classes.jar"

# Step 6: Create final APK
echo "[6/6] Creating APK..."
cd "$BUILD_DIR/apk"
cp ../dex/classes.dex .

# Use available zip tool
if command -v zip &> /dev/null; then
    zip -r -q "../scrcpy-companion-unsigned.apk" classes.dex AndroidManifest.xml resources.arsc res/ 2>/dev/null || \
        zip -r -q "../scrcpy-companion-unsigned.apk" classes.dex
elif command -v 7z &> /dev/null; then
    7z a -tzip "../scrcpy-companion-unsigned.apk" classes.dex AndroidManifest.xml resources.arsc res/ > /dev/null 2>&1 || \
        7z a -tzip "../scrcpy-companion-unsigned.apk" classes.dex > /dev/null 2>&1
else
    # Use PowerShell on Windows
    powershell -Command "Compress-Archive -Path classes.dex,AndroidManifest.xml,resources.arsc,res -DestinationPath ../scrcpy-companion-unsigned.zip -Force" 2>/dev/null || \
    powershell -Command "Compress-Archive -Path classes.dex -DestinationPath ../scrcpy-companion-unsigned.zip -Force"
    mv ../scrcpy-companion-unsigned.zip ../scrcpy-companion-unsigned.apk 2>/dev/null || true
fi

# Align and sign
$ZIPALIGN -f 4 "$BUILD_DIR/scrcpy-companion-unsigned.apk" "$BUILD_DIR/scrcpy-companion-aligned.apk"

# Try to sign with debug keystore
DEBUG_KEYSTORE="$HOME/.android/debug.keystore"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    DEBUG_KEYSTORE="$USERPROFILE/.android/debug.keystore"
    # Windows needs .bat extension for apksigner
    if [[ -f "${APKSIGNER}.bat" ]]; then
        APKSIGNER="${APKSIGNER}.bat"
    fi
fi

if [[ -f "$DEBUG_KEYSTORE" ]]; then
    echo "Signing with debug keystore: $DEBUG_KEYSTORE"
    "$APKSIGNER" sign --ks "$DEBUG_KEYSTORE" --ks-pass pass:android \
        --out "$SCRIPT_DIR/scrcpy-companion.apk" \
        "$BUILD_DIR/scrcpy-companion-aligned.apk" && echo "[OK] Signed with debug key" || {
        echo "[ERROR] Failed to sign APK"
        cp "$BUILD_DIR/scrcpy-companion-aligned.apk" "$SCRIPT_DIR/scrcpy-companion.apk"
        echo "[FALLBACK] Copied unsigned APK (may not install)"
    }
else
    # Create debug keystore if needed
    echo "Creating new debug keystore..."
    keytool -genkey -v -keystore "$BUILD_DIR/debug.keystore" \
        -alias androiddebugkey -storepass android -keypass android \
        -keyalg RSA -keysize 2048 -validity 10000 \
        -dname "CN=Android Debug,O=Android,C=US"

    "$APKSIGNER" sign --ks "$BUILD_DIR/debug.keystore" \
        --ks-pass pass:android --key-pass pass:android \
        --out "$SCRIPT_DIR/scrcpy-companion.apk" \
        "$BUILD_DIR/scrcpy-companion-aligned.apk" && echo "[OK] Signed with new debug key" || {
        echo "[ERROR] Failed to sign APK"
        cp "$BUILD_DIR/scrcpy-companion-aligned.apk" "$SCRIPT_DIR/scrcpy-companion.apk"
        echo "[FALLBACK] Copied unsigned APK (may not install)"
    }
fi

# Clean up
rm -rf "$BUILD_DIR"

echo ""
echo "=== Build Complete ==="
echo "Output: $SCRIPT_DIR/scrcpy-companion.apk"
echo ""
echo "Installation:"
echo "  1. adb install scrcpy-companion.apk"
echo "  2. Pull down notification shade"
echo "  3. Edit Quick Settings (pencil icon)"
echo "  4. Find 'Scrcpy' and drag to active tiles"
echo "  5. Tap tile to start/stop server"
