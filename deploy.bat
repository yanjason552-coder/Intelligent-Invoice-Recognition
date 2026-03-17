@echo off
REM 自动化部署批处理文件
REM 用于启动Git Bash并执行部署脚本

chcp 65001 >nul
echo ==========================================
echo 智能发票识别系统 - 自动化部署
echo ==========================================
echo.

REM 检查Git Bash是否安装
set "GIT_BASH_PATH="

REM 常见的Git Bash安装路径
if exist "C:\Program Files\Git\bin\bash.exe" (
    set "GIT_BASH_PATH=C:\Program Files\Git\bin\bash.exe"
) else if exist "C:\Program Files (x86)\Git\bin\bash.exe" (
    set "GIT_BASH_PATH=C:\Program Files (x86)\Git\bin\bash.exe"
) else if exist "%LOCALAPPDATA%\Programs\Git\bin\bash.exe" (
    set "GIT_BASH_PATH=%LOCALAPPDATA%\Programs\Git\bin\bash.exe"
) else (
    REM 尝试从PATH中查找
    where bash.exe >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        set "GIT_BASH_PATH=bash.exe"
    )
)

if "%GIT_BASH_PATH%"=="" (
    echo [错误] 未找到Git Bash
    echo.
    echo 请安装Git for Windows:
    echo   https://git-scm.com/download/win
    echo.
    echo 或者手动执行以下步骤:
    echo   1. 打开Git Bash
    echo   2. 执行: bash scripts/aliyun/deploy-commands.sh
    echo.
    pause
    exit /b 1
)

echo [信息] 找到Git Bash: %GIT_BASH_PATH%
echo.

REM 获取当前脚本所在目录
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM 转换为Unix路径格式
set "UNIX_PATH=%SCRIPT_DIR%"
set "UNIX_PATH=%UNIX_PATH:\=/%"
set "UNIX_PATH=%UNIX_PATH:C:=/c%"
set "UNIX_PATH=%UNIX_PATH:c:=/c%"

echo [信息] 项目目录: %SCRIPT_DIR%
echo [信息] 准备执行部署脚本...
echo.
echo ==========================================
echo 开始部署
echo ==========================================
echo.
echo 提示: 部署过程中需要输入服务器密码
echo 密码: 6b3fPk9n!
echo.
echo 按任意键继续，或按Ctrl+C取消...
pause >nul
echo.

REM 执行部署脚本
"%GIT_BASH_PATH%" -c "cd '%UNIX_PATH%' && bash scripts/aliyun/deploy-commands.sh"

REM 检查执行结果
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==========================================
    echo 部署完成！
    echo ==========================================
    echo.
    echo 访问地址:
    echo   前端: http://8.145.33.61:5173
    echo   API文档: http://8.145.33.61:8000/docs
    echo   API健康检查: http://8.145.33.61:8000/api/v1/utils/health-check/
    echo.
) else (
    echo.
    echo ==========================================
    echo 部署过程中出现错误
    echo ==========================================
    echo.
    echo 请检查:
    echo   1. 网络连接是否正常
    echo   2. 服务器密码是否正确
    echo   3. 查看上方的错误信息
    echo.
    echo 详细说明请参考: EXECUTE_DEPLOY.md
    echo.
)

pause

