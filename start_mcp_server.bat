@echo off
REM 启动 Scrcpy HTTP MCP 服务器
REM Start Scrcpy HTTP MCP Server

cd /d "%~dp0"

echo ================================================
echo   Scrcpy HTTP MCP Server
echo ================================================
echo.

REM 检查端口 3359 是否可用
netstat -ano | findstr ":3359" >nul 2>&1
if %errorlevel% equ 0 (
    echo [警告] 端口 3359 已被占用
    echo.
    netstat -ano | findstr ":3359"
    echo.
    choice /C YN /M "是否继续尝试启动 (Y/N)?"
    if errorlevel 2 exit /b 1
)

echo 启动服务器...
echo.

python scrcpy_http_mcp_server.py --connect --audio --audio-dup --preview

pause
