@echo off
setlocal enabledelayedexpansion

set ANDROID_HOME=%LOCALAPPDATA%\Android\Sdk
set BUILD_TOOLS=%ANDROID_HOME%\build-tools\34.0.0
set PLATFORM=%ANDROID_HOME%\platforms\android-34
set BUILD_DIR=%~dp0build
set APP_DIR=%~dp0app

echo === Building Scrcpy Companion (Windows CMD) ===

REM Clean and create directories
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
mkdir "%BUILD_DIR%"
mkdir "%BUILD_DIR%\gen"
mkdir "%BUILD_DIR%\classes"
mkdir "%BUILD_DIR%\dex"
mkdir "%BUILD_DIR%\compiled_res"
mkdir "%BUILD_DIR%\apk"
mkdir "%BUILD_DIR%\res\values"
mkdir "%BUILD_DIR%\res\drawable"
mkdir "%BUILD_DIR%\res\mipmap-anydpi-v26"
mkdir "%BUILD_DIR%\res\layout"

echo [1/6] Copying resources...

REM Copy all resources from source directory using xcopy
xcopy /s /e /y /q "%APP_DIR%\src\main\res\*" "%BUILD_DIR%\res\" >nul 2>&1

REM Ensure minimum resources exist if xcopy failed
if not exist "%BUILD_DIR%\res\values\strings.xml" (
    echo ^<?xml version="1.0" encoding="utf-8"?^>^<resources^>^<string name="app_name"^>Scrcpy Companion^</string^>^<string name="tile_label"^>Scrcpy^</string^>^</resources^> > "%BUILD_DIR%\res\values\strings.xml"
)

echo [2/6] Compiling resources with aapt2...

REM Use --dir to compile entire resource directory
"%BUILD_TOOLS%\aapt2.exe" compile --dir "%BUILD_DIR%\res" -o "%BUILD_DIR%\compiled_res\compiled.zip"
if errorlevel 1 goto error

echo [3/6] Linking resources...

REM Copy AndroidManifest.xml from source
if exist "%APP_DIR%\src\main\AndroidManifest.xml" (
    copy /y "%APP_DIR%\src\main\AndroidManifest.xml" "%BUILD_DIR%\AndroidManifest.xml" >nul
) else (
    echo ERROR: AndroidManifest.xml not found
    goto error
)

"%BUILD_TOOLS%\aapt2.exe" link -o "%BUILD_DIR%\apk\base.apk" --manifest "%BUILD_DIR%\AndroidManifest.xml" -I "%PLATFORM%\android.jar" --java "%BUILD_DIR%\gen" --auto-add-overlay --min-sdk-version 21 --target-sdk-version 34 "%BUILD_DIR%\compiled_res\compiled.zip"
if errorlevel 1 goto error

echo [4/6] Compiling Java...

REM Create source directory and copy Java files
if not exist "%BUILD_DIR%\src\com\genymobile\scrcpy\companion" mkdir "%BUILD_DIR%\src\com\genymobile\scrcpy\companion"
copy /y "%APP_DIR%\src\main\java\com\genymobile\scrcpy\companion\*.java" "%BUILD_DIR%\src\com\genymobile\scrcpy\companion\" >nul 2>&1

REM Find Java files and compile
set JAVA_FILES=
for %%f in ("%BUILD_DIR%\src\com\genymobile\scrcpy\companion\*.java") do (
    set JAVA_FILES=!JAVA_FILES! "%%f"
)
set JAVA_FILES=%JAVA_FILES% "%BUILD_DIR%\gen\com\genymobile\scrcpy\companion\R.java"

javac -encoding UTF-8 -bootclasspath "%PLATFORM%\android.jar" -source 1.8 -target 1.8 -d "%BUILD_DIR%\classes" %JAVA_FILES% 2>nul
if errorlevel 1 goto error

echo [5/6] Creating DEX...

pushd "%BUILD_DIR%\classes"
jar cf "%BUILD_DIR%\classes.jar" com
popd

call "%BUILD_TOOLS%\d8.bat" --output "%BUILD_DIR%\dex" --lib "%PLATFORM%\android.jar" "%BUILD_DIR%\classes.jar" 2>nul
if errorlevel 1 goto error

echo [6/6] Creating and signing APK...

cd "%BUILD_DIR%\apk"
copy /y "..\dex\classes.dex" . >nul

REM Add classes.dex to base.apk using aapt
"%BUILD_TOOLS%\aapt.exe" add "%BUILD_DIR%\apk\base.apk" classes.dex >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to add classes.dex to APK
    goto error
)

"%BUILD_TOOLS%\zipalign.exe" -f 4 "%BUILD_DIR%\apk\base.apk" "%BUILD_DIR%\companion-aligned.apk"

REM Sign with debug keystore
if exist "%USERPROFILE%\.android\debug.keystore" (
    echo Signing with debug keystore...
    call "%BUILD_TOOLS%\apksigner.bat" sign --ks "%USERPROFILE%\.android\debug.keystore" --ks-pass pass:android --out "%~dp0scrcpy-companion.apk" "%BUILD_DIR%\companion-aligned.apk"
    if errorlevel 1 (
        echo [ERROR] Failed to sign with debug keystore
        goto error
    )
    echo [OK] Signed with debug keystore
) else (
    echo Debug keystore not found, creating one...
    keytool -genkey -v -keystore "%BUILD_DIR%\debug.keystore" -alias androiddebugkey -storepass android -keypass android -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Android Debug,O=Android,C=US"
    if errorlevel 1 (
        echo [ERROR] Failed to create debug keystore
        goto error
    )
    echo Signing with new keystore...
    call "%BUILD_TOOLS%\apksigner.bat" sign --ks "%BUILD_DIR%\debug.keystore" --ks-pass pass:android --key-pass pass:android --out "%~dp0scrcpy-companion.apk" "%BUILD_DIR%\companion-aligned.apk"
    if errorlevel 1 (
        echo [ERROR] Failed to sign APK
        goto error
    )
    echo [OK] Signed with new debug keystore
)
cd "%~dp0"

echo.
echo === BUILD SUCCESSFUL ===
echo Output: %~dp0scrcpy-companion.apk
goto end

:error
echo.
echo === BUILD FAILED ===
exit /b 1

:end
