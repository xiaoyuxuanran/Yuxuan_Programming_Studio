@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 羽轩教学API - 手机与电脑需要连接同一教学局域网
echo 输入Python解释器路径，可使用羽轩安装目录中的 runtime\python3.13.16\python.exe
set /p "COURSE_PYTHON=直接回车使用系统python，或填写python.exe完整路径: "
if not defined COURSE_PYTHON set "COURSE_PYTHON=python"
"%COURSE_PYTHON%" teaching_server.py --host 0.0.0.0 %*
pause
