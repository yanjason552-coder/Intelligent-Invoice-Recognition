@echo off
REM 立即执行修复 - 批处理文件

chcp 65001 >nul
echo ==========================================
echo Docker镜像问题修复
echo ==========================================
echo.

REM 查找Git Bash
set "GIT_BASH="
if exist "C:\Users\IT0598\AppData\Local\Programs\Git\bin\bash.exe" set "GIT_BASH=C:\Users\IT0598\AppData\Local\Programs\Git\bin\bash.exe"
if exist "C:\Program Files\Git\bin\bash.exe" set "GIT_BASH=C:\Program Files\Git\bin\bash.exe"
if exist "C:\Program Files (x86)\Git\bin\bash.exe" set "GIT_BASH=C:\Program Files (x86)\Git\bin\bash.exe"

if "%GIT_BASH%"=="" (
    echo 错误: 未找到Git Bash
    echo.
    echo 请手动执行:
    echo   1. 打开PuTTY连接到 8.145.33.61:50518
    echo   2. 执行修复命令（见SERVER_FIX_COMMANDS.txt）
    pause
    exit /b 1
)

echo 找到Git Bash: %GIT_BASH%
echo.
echo 正在启动Git Bash...
echo.
echo 请在Git Bash中执行以下命令:
echo.
echo   ssh -p 50518 root@8.145.33.61
echo   密码: 6b3fPk9n!
echo.
echo   然后在服务器上执行:
echo   cd /opt
echo   git clone https://github.com/yanjason552-coder/Intelligent-Invoice-Recognition.git invoice-app 2^>^&1 ^|^| (cd invoice-app ^&^& git pull)
echo   cd invoice-app
echo   bash scripts/aliyun/fix-and-retry-deploy.sh
echo.
echo ==========================================
echo.

REM 启动Git Bash
start "" "%GIT_BASH%" --login -i

echo Git Bash已启动！
echo 请按照上述命令执行修复
echo.
pause

