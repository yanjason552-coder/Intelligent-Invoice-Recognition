@echo off
chcp 65001 >nul
echo ========================================
echo   启动后端服务
echo ========================================
echo.

REM 使用 PowerShell 绕过执行策略运行脚本
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& {Set-Location '%CD%'; .\start-backend.ps1}"

pause




