# PowerShell 环境诊断脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PowerShell 环境诊断" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 PowerShell 版本
Write-Host "1. PowerShell 版本:" -ForegroundColor Yellow
$PSVersionTable | Format-List
Write-Host ""

# 2. 检查脚本文件编码
Write-Host "2. 检查脚本文件:" -ForegroundColor Yellow
$scriptFiles = @("test_api.ps1", "test_api_v2.ps1", "test_basic.ps1")
foreach ($file in $scriptFiles) {
    if (Test-Path $file) {
        $content = Get-Content $file -Raw -Encoding UTF8
        $ampersandPattern = [char]38
        $hasAmpersand = $content.Contains($ampersandPattern)
        Write-Host "  $file : " -NoNewline
        if ($hasAmpersand) {
            Write-Host "包含特殊字符" -ForegroundColor Red
        } else {
            Write-Host "不包含特殊字符" -ForegroundColor Green
        }
    } else {
        Write-Host "  $file : 文件不存在" -ForegroundColor Gray
    }
}
Write-Host ""

# 3. 测试基本脚本解析
Write-Host "3. 测试基本脚本解析:" -ForegroundColor Yellow
try {
    $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content "test_basic.ps1" -Raw), [ref]$null)
    Write-Host "  test_basic.ps1: 解析成功" -ForegroundColor Green
} catch {
    Write-Host "  test_basic.ps1: 解析失败 - $($_.Exception.Message)" -ForegroundColor Red
}

try {
    $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content "test_api_v2.ps1" -Raw), [ref]$null)
    Write-Host "  test_api_v2.ps1: 解析成功" -ForegroundColor Green
} catch {
    Write-Host "  test_api_v2.ps1: 解析失败 - $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 4. 测试字符代码
Write-Host "4. 测试字符代码:" -ForegroundColor Yellow
$testChar = [char]38
Write-Host "  [char]38 = '$testChar'" -ForegroundColor Gray
Write-Host "  字符代码测试: 成功" -ForegroundColor Green
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  诊断完成" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

