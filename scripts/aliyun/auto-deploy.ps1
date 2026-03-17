# 自动化部署脚本 - PowerShell版本
# 方式一：一键部署

$SERVER_IP = "8.145.33.61"
$SSH_PORT = "50518"
$SSH_USER = "root"
$SSH_PASSWORD = "6b3fPk9n!"

Write-Host "==========================================" -ForegroundColor Green
Write-Host "开始自动化部署 - 方式一" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "服务器: $SERVER_IP`:$SSH_PORT" -ForegroundColor Cyan
Write-Host ""

# 检查必要的工具
Write-Host "[检查] 检查必要工具..." -ForegroundColor Yellow

$hasSSH = $false
$hasSCP = $false

if (Get-Command ssh -ErrorAction SilentlyContinue) {
    $hasSSH = $true
    Write-Host "  ✓ SSH已安装" -ForegroundColor Green
} else {
    Write-Host "  ✗ SSH未安装" -ForegroundColor Red
}

if (Get-Command scp -ErrorAction SilentlyContinue) {
    $hasSCP = $true
    Write-Host "  ✓ SCP已安装" -ForegroundColor Green
} else {
    Write-Host "  ✗ SCP未安装" -ForegroundColor Red
}

if (-not ($hasSSH -and $hasSCP)) {
    Write-Host ""
    Write-Host "错误: 需要SSH和SCP工具" -ForegroundColor Red
    Write-Host "请安装以下之一:" -ForegroundColor Yellow
    Write-Host "  1. Git for Windows (包含SSH/SCP)"
    Write-Host "  2. OpenSSH for Windows"
    Write-Host "  3. PuTTY (包含pscp和plink)"
    Write-Host ""
    Write-Host "或者使用Git Bash执行以下命令:" -ForegroundColor Cyan
    Write-Host "  scp -P $SSH_PORT scripts/aliyun/server-deploy.sh root@$SERVER_IP`:/tmp/"
    Write-Host "  ssh -p $SSH_PORT root@$SERVER_IP 'chmod +x /tmp/server-deploy.sh && bash /tmp/server-deploy.sh'"
    exit 1
}

# 步骤1: 上传部署脚本
Write-Host ""
Write-Host "[1/3] 上传部署脚本到服务器..." -ForegroundColor Yellow

$scriptPath = "scripts\aliyun\server-deploy.sh"
if (-not (Test-Path $scriptPath)) {
    Write-Host "错误: 部署脚本不存在: $scriptPath" -ForegroundColor Red
    exit 1
}

try {
    # 使用scp上传脚本
    $scpCommand = "scp -P $SSH_PORT -o StrictHostKeyChecking=no `"$scriptPath`" ${SSH_USER}@${SERVER_IP}:/tmp/server-deploy.sh"
    Write-Host "执行: $scpCommand" -ForegroundColor Gray
    
    # 由于需要密码，提示用户手动执行
    Write-Host ""
    Write-Host "由于需要输入密码，请手动执行以下命令:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "步骤1: 上传脚本" -ForegroundColor Cyan
    Write-Host "  scp -P $SSH_PORT scripts/aliyun/server-deploy.sh root@$SERVER_IP`:/tmp/" -ForegroundColor White
    Write-Host "  密码: $SSH_PASSWORD" -ForegroundColor Gray
    Write-Host ""
    Write-Host "步骤2: 连接服务器并执行" -ForegroundColor Cyan
    Write-Host "  ssh -p $SSH_PORT root@$SERVER_IP" -ForegroundColor White
    Write-Host "  密码: $SSH_PASSWORD" -ForegroundColor Gray
    Write-Host ""
    Write-Host "步骤3: 在服务器上执行部署" -ForegroundColor Cyan
    Write-Host "  chmod +x /tmp/server-deploy.sh" -ForegroundColor White
    Write-Host "  bash /tmp/server-deploy.sh" -ForegroundColor White
    Write-Host ""
    
    # 尝试使用expect或直接执行（如果配置了SSH密钥）
    Write-Host "或者，如果您已配置SSH密钥，可以执行:" -ForegroundColor Yellow
    Write-Host "  scp -P $SSH_PORT scripts/aliyun/server-deploy.sh root@$SERVER_IP`:/tmp/" -ForegroundColor White
    Write-Host "  ssh -p $SSH_PORT root@$SERVER_IP 'chmod +x /tmp/server-deploy.sh && bash /tmp/server-deploy.sh'" -ForegroundColor White
    
} catch {
    Write-Host "上传失败: $_" -ForegroundColor Red
    Write-Host "请手动上传脚本" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "部署说明" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "由于Windows环境限制，请按照以下步骤执行:" -ForegroundColor Yellow
Write-Host ""
Write-Host "方法A: 使用Git Bash (推荐)" -ForegroundColor Cyan
Write-Host "  1. 打开Git Bash"
Write-Host "  2. 执行以下命令:"
Write-Host ""
Write-Host "    # 上传脚本"
Write-Host "    scp -P $SSH_PORT scripts/aliyun/server-deploy.sh root@$SERVER_IP`:/tmp/" -ForegroundColor White
Write-Host ""
Write-Host "    # 连接并执行"
Write-Host "    ssh -p $SSH_PORT root@$SERVER_IP 'chmod +x /tmp/server-deploy.sh && bash /tmp/server-deploy.sh'" -ForegroundColor White
Write-Host ""
Write-Host "方法B: 直接在服务器上执行" -ForegroundColor Cyan
Write-Host "  1. 使用SSH客户端连接: $SERVER_IP`:$SSH_PORT"
Write-Host "  2. 在服务器上执行:"
Write-Host ""
Write-Host "    cd /opt" -ForegroundColor White
Write-Host "    git clone https://github.com/yanjason552-coder/Intelligent-Invoice-Recognition.git invoice-app" -ForegroundColor White
Write-Host "    cd invoice-app" -ForegroundColor White
Write-Host "    chmod +x scripts/aliyun/server-deploy.sh" -ForegroundColor White
Write-Host "    bash scripts/aliyun/server-deploy.sh" -ForegroundColor White
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green

