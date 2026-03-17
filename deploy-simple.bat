@echo off
REM 简化版部署批处理文件
REM 直接启动Git Bash并执行部署

chcp 65001 >nul
echo ==========================================
echo 启动Git Bash执行部署
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

echo 找到Git Bash，正在启动...
echo.
echo 提示: 部署过程中需要输入服务器密码
echo 密码: 6b3fPk9n!
echo.
pause

REM 启动Git Bash并执行部署脚本
"%GIT_BASH%" scripts/aliyun/deploy-commands.sh

pause

