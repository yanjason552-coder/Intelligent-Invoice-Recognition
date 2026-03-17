@echo off
REM 修复并重新部署批处理文件
REM 用于修复Docker镜像拉取问题后重新部署

chcp 65001 >nul
echo ==========================================
echo 修复Docker镜像问题并重新部署
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

echo 找到Git Bash，准备执行修复和部署...
echo.
echo 此脚本将:
echo   1. 上传修复脚本到服务器
echo   2. 配置Docker镜像加速器
echo   3. 重新构建镜像
echo   4. 重新部署服务
echo.
echo 提示: 需要输入服务器密码: 6b3fPk9n!
echo.
pause

REM 获取当前目录的Unix路径
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "UNIX_PATH=%SCRIPT_DIR%"
set "UNIX_PATH=%UNIX_PATH:\=/%"
set "UNIX_PATH=%UNIX_PATH:C:=/c%"
set "UNIX_PATH=%UNIX_PATH:c:=/c%"

REM 上传修复脚本
echo [1/4] 上传修复脚本...
"%GIT_BASH%" -c "scp -P 50518 scripts/aliyun/fix-docker-mirror.sh scripts/aliyun/retry-build.sh root@8.145.33.61:/tmp/"

REM 执行修复和重新部署
echo [2/4] 配置Docker镜像加速器...
echo [3/4] 重新构建镜像...
echo [4/4] 重新部署服务...
"%GIT_BASH%" -c "ssh -p 50518 root@8.145.33.61 'chmod +x /tmp/fix-docker-mirror.sh /tmp/retry-build.sh && bash /tmp/fix-docker-mirror.sh && cd /opt/invoice-app && bash /tmp/retry-build.sh && docker compose -f docker-compose.yml -f docker-compose.production.external-db.yml --profile no-db up -d redis prestart backend frontend adminer && docker compose ps'"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==========================================
    echo 修复和部署完成！
    echo ==========================================
) else (
    echo.
    echo ==========================================
    echo 修复过程中出现错误
    echo ==========================================
    echo 请查看上方的错误信息
    echo 详细说明请参考: FIX_DEPLOYMENT.md
)

pause

