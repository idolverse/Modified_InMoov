@echo off
cd /d "%~dp0"

echo 正在启动机器人面部控制系统...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请确保已安装Python 3.x
    pause
    exit /b 1
)

REM 检查必要的Python库
echo 检查必要的Python库...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo 警告: Flask库未安装，正在尝试安装...
    pip install flask
    if errorlevel 1 (
        echo 错误: 无法安装Flask库
        echo 请手动运行: pip install flask
        pause
        exit /b 1
    )
)

python -c "import serial" >nul 2>&1
if errorlevel 1 (
    echo 警告: pyserial库未安装，正在尝试安装...
    pip install pyserial
    if errorlevel 1 (
        echo 错误: 无法安装pyserial库
        echo 请手动运行: pip install pyserial
        pause
        exit /b 1
    )
)

python -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo 警告: pygame库未安装，正在尝试安装...
    pip install pygame
    if errorlevel 1 (
        echo 错误: 无法安装pygame库
        echo 请手动运行: pip install pygame
        pause
        exit /b 1
    )
)

python -c "import numpy" >nul 2>&1
if errorlevel 1 (
    echo 警告: numpy库未安装，正在尝试安装...
    pip install numpy
    if errorlevel 1 (
        echo 错误: 无法安装numpy库
        echo 请手动运行: pip install numpy
        pause
        exit /b 1
    )
)

python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo 警告: requests库未安装，正在尝试安装...
    pip install requests
    if errorlevel 1 (
        echo 错误: 无法安装requests库
        echo 请手动运行: pip install requests
        pause
        exit /b 1
    )
)

python -c "import websocket" >nul 2>&1
if errorlevel 1 (
    echo 警告: websocket-client库未安装，正在尝试安装...
    pip install websocket-client
    if errorlevel 1 (
        echo 错误: 无法安装websocket-client库
        echo 请手动运行: pip install websocket-client
        pause
        exit /b 1
    )
)

REM 检查核心文件是否存在
if not exist "web_server.py" (
    echo 错误: 找不到web_server.py文件
    pause
    exit /b 1
)

if not exist "analysis_sound.py" (
    echo 错误: 找不到analysis_sound.py文件
    pause
    exit /b 1
)

if not exist "templates" (
    echo 错误: 找不到templates文件夹
    pause
    exit /b 1
)

if not exist "templates\index.html" (
    echo 错误: 找不到templates\index.html文件
    pause
    exit /b 1
)

REM 启动Web服务器
echo ================================================================
echo                    智能语音机器人控制系统
echo ================================================================
echo 🚀 功能特色:
echo   ✓ 豆包AI智能对话
echo   ✓ 科大讯飞语音合成(TTS)
echo   ✓ 科大讯飞语音识别(ASR)
echo   ✓ Arduino舵机面部控制
echo   ✓ 现代化Web界面
echo.
echo 📍 请在浏览器中访问: http://localhost:5000
echo 💡 支持Chrome、Edge、Firefox等现代浏览器
echo 🎤 支持实时语音交互和文字聊天
echo ⚙️  支持舵机调试和参数设置
echo.
echo 🛑 按 Ctrl+C 可以停止服务器
echo ================================================================
echo.

python web_server.py

REM 如果程序异常退出，显示错误信息
if errorlevel 1 (
    echo.
    echo ❌ 程序异常退出，错误代码: %errorlevel%
    echo.
    echo 🔧 可能的解决方案:
    echo   1. 检查Python环境是否正确安装
    echo   2. 确保所有依赖库已安装
    echo   3. 检查端口5000是否被占用
    echo   4. 查看上方的错误信息
    echo.
    pause
)
