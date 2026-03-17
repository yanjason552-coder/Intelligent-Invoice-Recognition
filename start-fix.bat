@echo off
REM 启动Git Bash并显示修复命令
REM 用户可以在Git Bash中复制执行

chcp 65001 >nul
echo ==========================================
echo Docker镜像问题修复
echo ==========================================
echo.

REM 查找Git Bash
set "GIT_BASH="
if exist "C:\Program Files\Git\bin\bash.exe" set "GIT_BASH=C:\Program Files\Git\bin\bash.exe"
if exist "C:\Program Files (x86)\Git\bin\bash.exe" set "GIT_BASH=C:\Program Files (x86)\Git\bin\bash.exe"
if exist "%LOCALAPPDATA%\Programs\Git\bin\bash.exe" set "GIT_BASH=%LOCALAPPDATA%\Programs\Git\bin\bash.exe"

if "%GIT_BASH%"=="" (
    echo 错误: 未找到Git Bash
    echo 请安装Git for Windows: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo 找到Git Bash，准备启动...
echo.
echo ==========================================
echo 修复步骤
echo ==========================================
echo.
echo 步骤1: 连接服务器
echo   ssh -p 50518 root@8.145.33.61
echo   密码: 6b3fPk9n!
echo.
echo 步骤2: 在服务器上执行以下命令:
echo.
echo   cd /opt
echo   git clone https://github.com/yanjason552-coder/Intelligent-Invoice-Recognition.git invoice-app 2^>^&1 ^|^| (cd invoice-app ^&^& git pull)
echo   cd invoice-app
echo   bash scripts/aliyun/fix-and-retry-deploy.sh
echo.
echo ==========================================
echo.
echo 按任意键启动Git Bash...
pause >nul

REM 启动Git Bash并显示命令提示
start "%GIT_BASH%" --login -i

echo.
echo Git Bash已启动！
echo 请在Git Bash中执行上述命令
echo.
pause

