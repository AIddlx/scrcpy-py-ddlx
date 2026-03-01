# 释放端口 3359 - 需要以管理员身份运行
# Release port 3359 from Windows Hyper-V reserved range

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  释放端口 3359 (Release Port 3359)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# 检查是否以管理员身份运行
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[错误] 需要以管理员身份运行此脚本!" -ForegroundColor Red
    Write-Host ""
    Write-Host "请右键点击 PowerShell -> 以管理员身份运行" -ForegroundColor Yellow
    Write-Host "然后重新执行此脚本" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "按 Enter 键退出"
    exit 1
}

Write-Host "[1/4] 检查端口 3359 状态..." -ForegroundColor Yellow

# 检查端口是否在保留范围内
$excludedRanges = netsh interface ipv4 show excludedportrange protocol=tcp
$isExcluded = $excludedRanges | Select-String "3347\s+3446"

if ($isExcluded) {
    Write-Host "      端口 3359 在 Windows 保留范围内 (3347-3446)" -ForegroundColor Red
} else {
    Write-Host "      端口 3359 不在保留范围内" -ForegroundColor Green
}

Write-Host "[2/4] 停止 WinNAT 服务..." -ForegroundColor Yellow
try {
    net stop winnat | Out-Null
    Write-Host "      WinNAT 服务已停止" -ForegroundColor Green
} catch {
    Write-Host "      WinNAT 服务未运行或停止失败" -ForegroundColor Yellow
}

Write-Host "[3/4] 添加端口 3359 到排除列表..." -ForegroundColor Yellow
try {
    # 先尝试删除（如果已存在）
    netsh int ipv4 delete excludedportrange protocol=tcp startport=3359 numberofports=1 store=persistent 2>$null

    # 添加新的排除
    netsh int ipv4 add excludedportrange protocol=tcp startport=3359 numberofports=1 store=persistent
    Write-Host "      端口 3359 已添加到排除列表" -ForegroundColor Green
} catch {
    Write-Host "      添加失败: $_" -ForegroundColor Red
}

Write-Host "[4/4] 重启 WinNAT 服务..." -ForegroundColor Yellow
try {
    net start winnat | Out-Null
    Write-Host "      WinNAT 服务已重启" -ForegroundColor Green
} catch {
    Write-Host "      WinNAT 服务启动失败" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  完成! 端口 3359 现在可以使用了" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

# 验证
Write-Host "验证端口状态:" -ForegroundColor Cyan
netsh interface ipv4 show excludedportrange protocol=tcp | Select-String "3359"

Write-Host ""
Read-Host "按 Enter 键退出"
