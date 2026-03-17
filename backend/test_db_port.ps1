# 数据库端口连通性测试脚本 (PowerShell)
# 用于诊断数据库连接超时问题

param(
    [string]$Host = "219.151.188.129",
    [int]$Port = 50510,
    [int]$Timeout = 10
)

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "数据库端口连通性测试" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "主机: $Host" -ForegroundColor Yellow
Write-Host "端口: $Port" -ForegroundColor Yellow
Write-Host "超时: ${Timeout}秒" -ForegroundColor Yellow
Write-Host ""

# 测试1: Ping测试
Write-Host "步骤1: Ping测试" -ForegroundColor Green
Write-Host "-" * 60
$pingResult = Test-Connection -ComputerName $Host -Count 2 -Quiet
if ($pingResult) {
    $pingTime = (Test-Connection -ComputerName $Host -Count 1).ResponseTime
    Write-Host "[OK] Ping成功，延迟: ${pingTime}ms" -ForegroundColor Green
} else {
    Write-Host "[FAIL] Ping失败" -ForegroundColor Red
    exit 1
}

# 测试2: TCP端口测试
Write-Host ""
Write-Host "步骤2: TCP端口测试" -ForegroundColor Green
Write-Host "-" * 60
try {
    $result = Test-NetConnection -ComputerName $Host -Port $Port -WarningAction SilentlyContinue
    
    if ($result.TcpTestSucceeded) {
        Write-Host "[OK] 端口 $Port 可达" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] 端口 $Port 连接失败" -ForegroundColor Red
        Write-Host ""
        Write-Host "可能的原因：" -ForegroundColor Yellow
        Write-Host "  1. 防火墙阻止了连接" -ForegroundColor Yellow
        Write-Host "  2. 数据库服务器未运行或端口未监听" -ForegroundColor Yellow
        Write-Host "  3. 数据库服务器只允许特定IP访问" -ForegroundColor Yellow
        Write-Host "  4. 网络路由问题" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "[FAIL] 端口 $Port 连接失败: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[SUCCESS] 所有测试通过！" -ForegroundColor Green
