@echo off
chcp 65001 >nul
cd /d %~dp0..
python backend\scripts\create_dimension_inspection_template.py
pause

