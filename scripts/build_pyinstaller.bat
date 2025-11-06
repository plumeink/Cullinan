@echo off
REM PyInstaller 打包脚本 (Windows)

echo ===================================
echo Cullinan PyInstaller 打包脚本
echo ===================================
echo.

set APP_NAME=cullinan_test
set MAIN_FILE=examples\packaging_test.py

REM 检查 PyInstaller 是否安装
pyinstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: PyInstaller 未安装
    echo 请运行: pip install pyinstaller
    exit /b 1
)

echo 选择打包模式:
echo 1) Onedir (推荐)
echo 2) Onefile
set /p mode=请输入选项 (1/2):

if "%mode%"=="1" (
    set MODE=--onedir
    set MODE_NAME=Onedir
) else if "%mode%"=="2" (
    set MODE=--onefile
    set MODE_NAME=Onefile
) else (
    echo 无效选项
    exit /b 1
)

echo.
echo 开始打包 (%MODE_NAME% 模式^)...
echo.

pyinstaller %MODE% ^
    --hidden-import=cullinan ^
    --hidden-import=cullinan.application ^
    --hidden-import=cullinan.controller ^
    --hidden-import=cullinan.service ^
    --collect-all=cullinan ^
    --name=%APP_NAME% ^
    --clean ^
    --noconfirm ^
    --distpath=dist_pyinstaller ^
    %MAIN_FILE%

if %errorlevel% equ 0 (
    echo.
    echo ===================================
    echo 打包成功!
    echo ===================================

    if "%mode%"=="1" (
        echo 可执行文件位置: dist_pyinstaller\%APP_NAME%\
        echo 运行命令: cd dist_pyinstaller\%APP_NAME% ^&^& %APP_NAME%.exe
    ) else (
        echo 可执行文件位置: dist_pyinstaller\%APP_NAME%.exe
        echo 运行命令: dist_pyinstaller\%APP_NAME%.exe
    )
) else (
    echo.
    echo 打包失败，请检查错误信息
    exit /b 1
)

