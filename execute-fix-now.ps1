# 执行修复的PowerShell脚本

$bashPath = "C:\Users\IT0598\AppData\Local\Programs\Git\bin\bash.exe"

if (Test-Path $bashPath) {
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "启动Git Bash执行修复" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    
    # 创建临时脚本文件
    $fixScript = @'
#!/bin/bash
echo "=========================================="
echo "Docker镜像问题修复"
echo "=========================================="
echo ""
echo "请执行以下命令连接服务器:"
echo "ssh -p 50518 root@8.145.33.61"
echo "密码: 6b3fPk9n!"
echo ""
echo "然后在服务器上执行以下命令:"
echo ""
echo "cd /opt"
echo "git clone https://github.com/yanjason552-coder/Intelligent-Invoice-Recognition.git invoice-app 2>&1 || (cd invoice-app && git pull)"
echo "cd invoice-app"
echo "bash scripts/aliyun/fix-and-retry-deploy.sh"
echo ""
echo "或者查看 SERVER_FIX_COMMANDS.txt 文件获取完整命令"
echo ""
echo "=========================================="
echo ""
echo "按任意键打开Git Bash..."
read -n 1
'@
    
    $tempFile = [System.IO.Path]::GetTempFileName() + ".sh"
    $fixScript | Out-File -FilePath $tempFile -Encoding UTF8 -NoNewline
    
    Write-Host "正在启动Git Bash..." -ForegroundColor Yellow
    Start-Process -FilePath $bashPath -ArgumentList $tempFile
    
    Write-Host ""
    Write-Host "Git Bash已启动！" -ForegroundColor Green
    Write-Host "请按照提示执行修复命令" -ForegroundColor Yellow
    
} else {
    Write-Host "错误: 未找到Git Bash" -ForegroundColor Red
    Write-Host ""
    Write-Host "请手动执行以下步骤:" -ForegroundColor Yellow
    Write-Host "1. 打开PuTTY或其他SSH客户端" -ForegroundColor Cyan
    Write-Host "2. 连接到: 8.145.33.61:50518" -ForegroundColor Cyan
    Write-Host "3. 用户名: root, 密码: 6b3fPk9n!" -ForegroundColor Cyan
    Write-Host "4. 执行修复命令（见SERVER_FIX_COMMANDS.txt）" -ForegroundColor Cyan
}

