@echo off
REM Nuitka 打包脚本 (Windows)

echo ===================================
echo Cullinan Nuitka 打包脚本
echo ===================================
echo.

set APP_NAME=cullinan_test
set MAIN_FILE=examples\packaging_test.py

REM 检查 Nuitka 是否安装
nuitka --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Nuitka 未安装
    echo 请运行: pip install nuitka
    exit /b 1
)

echo 选择打包模式:
echo 1) Standalone (推荐)
echo 2) Onefile
set /p mode=请输入选项 (1/2):

if "%mode%"=="1" (
    set MODE=--standalone
    set MODE_NAME=Standalone
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

nuitka %MODE% ^
    --enable-plugin=pylint-warnings ^
    --include-package=cullinan ^
    --include-package-data=cullinan ^
    --include-module=examples.test_controller ^
    --output-dir=dist_nuitka ^
    --assume-yes-for-downloads ^
    --show-progress ^
    --show-memory ^
    --windows-console-mode=attach ^
    %MAIN_FILE%

if %errorlevel% equ 0 (
    echo.
    echo ===================================
    echo 打包成功!
    echo ===================================

    if "%mode%"=="1" (
        echo 可执行文件位置: dist_nuitka\packaging_test.dist\
        echo 运行命令: cd dist_nuitka\packaging_test.dist ^&^& packaging_test.exe
    ) else (
        echo 可执行文件位置: dist_nuitka\packaging_test.exe
        echo 运行命令: dist_nuitka\packaging_test.exe
    )
) else (
    echo.
    echo 打包失败，请检查错误信息
    exit /b 1
)

