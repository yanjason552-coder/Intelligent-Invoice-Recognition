@echo off
REM 执行修复的批处理文件
REM 连接到服务器并执行修复

chcp 65001 >nul
echo ==========================================
echo 执行Docker镜像问题修复
echo ==========================================
echo.

REM 查找Git Bash
set "GIT_BASH="
if exist "C:\Program Files\Git\bin\bash.exe" set "GIT_BASH=C:\Program Files\Git\bin\bash.exe"
if exist "C:\Program Files (x86)\Git\bin\bash.exe" set "GIT_BASH=C:\Program Files (x86)\Git\bin\bash.exe"
if exist "%LOCALAPPDATA%\Programs\Git\bin\bash.exe" set "GIT_BASH=%LOCALAPPDATA%\Programs\Git\bin\bash.exe"

if "%GIT_BASH%"=="" (
    echo 错误: 未找到Git Bash
    echo.
    echo 请手动执行以下步骤:
    echo   1. 打开PuTTY或其他SSH客户端
    echo   2. 连接到: 8.145.33.61:50518
    echo   3. 用户名: root
    echo   4. 密码: 6b3fPk9n!
    echo   5. 执行修复命令（见SERVER_FIX_COMMANDS.txt）
    echo.
    pause
    exit /b 1
)

echo 找到Git Bash: %GIT_BASH%
echo.
echo 准备连接到服务器执行修复...
echo 提示: 需要输入服务器密码: 6b3fPk9n!
echo.
echo 按任意键继续，或按Ctrl+C取消...
pause >nul
echo.

REM 执行修复命令 - 使用简化的方式
echo 正在连接到服务器...
echo 提示: 需要输入密码: 6b3fPk9n!
echo.

REM 创建一个临时脚本文件用于SSH执行
echo cd /opt > %TEMP%\fix-remote.sh
echo git clone https://github.com/yanjason552-coder/Intelligent-Invoice-Recognition.git invoice-app 2^>^&1 ^|^| (cd invoice-app ^&^& git pull) >> %TEMP%\fix-remote.sh
echo cd invoice-app >> %TEMP%\fix-remote.sh
echo if [ -f scripts/aliyun/fix-and-retry-deploy.sh ]; then >> %TEMP%\fix-remote.sh
echo   chmod +x scripts/aliyun/fix-and-retry-deploy.sh >> %TEMP%\fix-remote.sh
echo   bash scripts/aliyun/fix-and-retry-deploy.sh >> %TEMP%\fix-remote.sh
echo else >> %TEMP%\fix-remote.sh
echo   echo "修复脚本不存在，执行基础修复..." >> %TEMP%\fix-remote.sh
echo   mkdir -p /etc/docker >> %TEMP%\fix-remote.sh
echo   echo '{"registry-mirrors":["https://docker.mirrors.ustc.edu.cn","https://hub-mirror.c.163.com","https://mirror.baidubce.com"]}' ^> /etc/docker/daemon.json >> %TEMP%\fix-remote.sh
echo   systemctl daemon-reload >> %TEMP%\fix-remote.sh
echo   systemctl restart docker >> %TEMP%\fix-remote.sh
echo   sleep 5 >> %TEMP%\fix-remote.sh
echo   docker pull python:3.10 >> %TEMP%\fix-remote.sh
echo fi >> %TEMP%\fix-remote.sh

REM 上传并执行
"%GIT_BASH%" -c "scp -P 50518 %TEMP%\fix-remote.sh root@8.145.33.61:/tmp/fix-remote.sh"
"%GIT_BASH%" -c "ssh -p 50518 root@8.145.33.61 'chmod +x /tmp/fix-remote.sh && bash /tmp/fix-remote.sh'"

REM 清理临时文件
del %TEMP%\fix-remote.sh 2>nul

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==========================================
    echo 修复完成！
    echo ==========================================
) else (
    echo.
    echo ==========================================
    echo 修复过程中出现错误
    echo ==========================================
    echo.
    echo 请查看SERVER_FIX_COMMANDS.txt文件
    echo 手动在服务器上执行修复命令
    echo.
)

pause

