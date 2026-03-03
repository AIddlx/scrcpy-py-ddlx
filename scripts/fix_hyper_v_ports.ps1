# 释放 Windows Hyper-V 保留端口 - 需要以管理员身份运行
# Release ports from Windows Hyper-V reserved range
#
# 用途:
#   - MCP HTTP Server: 3359
#   - scrcpy: 27183-27186 (discovery/control/video/audio)
#
# Usage:
#   右键 PowerShell -> 以管理员身份运行 -> 执行此脚本

param(
    [int[]]$Ports = @(3359, 27183, 27184, 27185, 27186),
    [switch]$DryRun
)

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  释放 Windows Hyper-V 保留端口" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

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

Write-Host "目标端口: $($Ports -join ', ')" -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "[DRY RUN] 仅检查，不修改" -ForegroundColor Yellow
}
Write-Host ""

# 检查当前保留的端口范围
Write-Host "[1/4] 检查当前保留端口范围..." -ForegroundColor Yellow
$excludedRanges = netsh interface ipv4 show excludedportrange protocol=tcp
Write-Host $excludedRanges
Write-Host ""

# 检查哪些目标端口在保留范围内
$conflictPorts = @()
foreach ($port in $Ports) {
    # 解析保留范围并检查端口是否在其中
    $inRange = $false
    $lines = $excludedRanges -split "`n"
    foreach ($line in $lines) {
        if ($line -match "(\d+)\s+(\d+)") {
            $start = [int]$matches[1]
            $end = [int]$matches[2]
            if ($port -ge $start -and $port -le $end) {
                $inRange = $true
                Write-Host "  端口 $port 在保留范围 $start-$end 内" -ForegroundColor Red
                break
            }
        }
    }
    if (-not $inRange) {
        Write-Host "  端口 $port 可用" -ForegroundColor Green
    } else {
        $conflictPorts += $port
    }
}

if ($conflictPorts.Count -eq 0) {
    Write-Host ""
    Write-Host "所有目标端口都可用，无需修复!" -ForegroundColor Green
    Read-Host "按 Enter 键退出"
    exit 0
}

Write-Host ""
Write-Host "发现 $($conflictPorts.Count) 个端口冲突需要修复" -ForegroundColor Yellow

if ($DryRun) {
    Write-Host ""
    Write-Host "[DRY RUN] 跳过修改步骤" -ForegroundColor Yellow
    Read-Host "按 Enter 键退出"
    exit 0
}

# 停止 WinNAT 服务
Write-Host ""
Write-Host "[2/4] 停止 WinNAT 服务..." -ForegroundColor Yellow
try {
    net stop winnat 2>$null
    Write-Host "      WinNAT 服务已停止" -ForegroundColor Green
} catch {
    Write-Host "      WinNAT 服务未运行或停止失败" -ForegroundColor Yellow
}

# 添加端口到排除列表
Write-Host ""
Write-Host "[3/4] 添加端口到排除列表..." -ForegroundColor Yellow
foreach ($port in $conflictPorts) {
    try {
        # 先删除（如果已存在）
        netsh int ipv4 delete excludedportrange protocol=tcp startport=$port numberofports=1 store=persistent 2>$null

        # 添加新的排除
        netsh int ipv4 add excludedportrange protocol=tcp startport=$port numberofports=1 store=persistent
        Write-Host "      端口 $port 已添加" -ForegroundColor Green
    } catch {
        Write-Host "      端口 $port 添加失败: $_" -ForegroundColor Red
    }
}

# 重启 WinNAT 服务
Write-Host ""
Write-Host "[4/4] 重启 WinNAT 服务..." -ForegroundColor Yellow
try {
    net start winnat 2>$null
    Write-Host "      WinNAT 服务已重启" -ForegroundColor Green
} catch {
    Write-Host "      WinNAT 服务启动失败" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  完成!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# 验证
Write-Host ""
Write-Host "验证端口状态:" -ForegroundColor Cyan
foreach ($port in $Ports) {
    $found = netsh interface ipv4 show excludedportrange protocol=tcp | Select-String "\b$port\b"
    if ($found) {
        Write-Host "  端口 $port : 已排除 (可用)" -ForegroundColor Green
    } else {
        Write-Host "  端口 $port : 未排除" -ForegroundColor Yellow
    }
}

Write-Host ""
Read-Host "按 Enter 键退出"
