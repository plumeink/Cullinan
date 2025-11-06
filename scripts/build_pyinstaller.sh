#!/bin/bash
# PyInstaller 打包脚本 (Linux/Mac)

echo "==================================="
echo "Cullinan PyInstaller 打包脚本"
echo "==================================="
echo ""

APP_NAME="cullinan_test"
MAIN_FILE="examples/packaging_test.py"

# 检查 PyInstaller 是否安装
if ! command -v pyinstaller &> /dev/null; then
    echo "错误: PyInstaller 未安装"
    echo "请运行: pip install pyinstaller"
    exit 1
fi

echo "选择打包模式:"
echo "1) Onedir (推荐)"
echo "2) Onefile"
read -p "请输入选项 (1/2): " mode

if [ "$mode" = "1" ]; then
    MODE="--onedir"
    MODE_NAME="Onedir"
elif [ "$mode" = "2" ]; then
    MODE="--onefile"
    MODE_NAME="Onefile"
else
    echo "无效选项"
    exit 1
fi

echo ""
echo "开始打包 ($MODE_NAME 模式)..."
echo ""

pyinstaller $MODE \
    --hidden-import=cullinan \
    --hidden-import=cullinan.application \
    --hidden-import=cullinan.controller \
    --hidden-import=cullinan.service \
    --collect-all=cullinan \
    --name=$APP_NAME \
    --clean \
    --noconfirm \
    --distpath=dist_pyinstaller \
    $MAIN_FILE

if [ $? -eq 0 ]; then
    echo ""
    echo "==================================="
    echo "打包成功!"
    echo "==================================="

    if [ "$mode" = "1" ]; then
        echo "可执行文件位置: dist_pyinstaller/$APP_NAME/"
        echo "运行命令: cd dist_pyinstaller/$APP_NAME && ./$APP_NAME"
    else
        echo "可执行文件位置: dist_pyinstaller/$APP_NAME"
        echo "运行命令: ./dist_pyinstaller/$APP_NAME"
    fi
else
    echo ""
    echo "打包失败，请检查错误信息"
    exit 1
fi

