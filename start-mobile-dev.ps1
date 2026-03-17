# 手机端开发启动脚本
# 用于快速启动服务并显示手机访问地址

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  票据上传系统 - 手机端访问配置" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# 获取本机IP地址
try {
    $ipv4Addresses = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {
        $_.InterfaceAlias -notlike "*Loopback*" -and 
        $_.IPAddress -notlike "169.254.*" -and
        $_.IPAddress -notlike "127.*"
    } | Select-Object -ExpandProperty IPAddress
    
    Write-Host "检测到的IP地址：" -ForegroundColor Yellow
    foreach ($ip in $ipv4Addresses) {
        Write-Host "  - $ip" -ForegroundColor Green
    }
    Write-Host ""
    
    # 显示访问地址
    Write-Host "手机访问地址：" -ForegroundColor Yellow
    foreach ($ip in $ipv4Addresses) {
        Write-Host "  http://$ip:5173" -ForegroundColor Green
    }
    Write-Host ""
    
} catch {
    Write-Host "无法获取IP地址，请手动查看：" -ForegroundColor Red
    Write-Host "  运行命令: ipconfig" -ForegroundColor Yellow
}

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "使用说明：" -ForegroundColor Yellow
Write-Host "1. 确保手机和电脑连接同一WiFi" -ForegroundColor White
Write-Host "2. 在手机上打开浏览器访问上述地址" -ForegroundColor White
Write-Host "3. 后端服务会自动检测局域网IP并添加到CORS" -ForegroundColor White
Write-Host "4. 如果无法访问，检查防火墙设置" -ForegroundColor White
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# 提示启动服务
Write-Host "请确保已启动以下服务：" -ForegroundColor Yellow
Write-Host "1. 后端: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor White
Write-Host "2. 前端: cd frontend && npm run dev" -ForegroundColor White
Write-Host ""

