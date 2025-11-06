#!/bin/bash
# Nuitka 打包脚本 (Linux/Mac)

echo "==================================="
echo "Cullinan Nuitka 打包脚本"
echo "==================================="
echo ""

APP_NAME="cullinan_test"
MAIN_FILE="examples/packaging_test.py"

# 检查 Nuitka 是否安装
if ! command -v nuitka3 &> /dev/null && ! command -v nuitka &> /dev/null; then
    echo "错误: Nuitka 未安装"
    echo "请运行: pip install nuitka"
    exit 1
fi

NUITKA_CMD="nuitka3"
if ! command -v nuitka3 &> /dev/null; then
    NUITKA_CMD="nuitka"
fi

echo "选择打包模式:"
echo "1) Standalone (推荐)"
echo "2) Onefile"
read -p "请输入选项 (1/2): " mode

if [ "$mode" = "1" ]; then
    MODE="--standalone"
    MODE_NAME="Standalone"
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

$NUITKA_CMD $MODE \
    --enable-plugin=pylint-warnings \
    --include-package=cullinan \
    --include-package-data=cullinan \
    --output-dir=dist_nuitka \
    --assume-yes-for-downloads \
    --show-progress \
    --show-memory \
    $MAIN_FILE

if [ $? -eq 0 ]; then
    echo ""
    echo "==================================="
    echo "打包成功!"
    echo "==================================="

    if [ "$mode" = "1" ]; then
        echo "可执行文件位置: dist_nuitka/packaging_test.dist/"
        echo "运行命令: cd dist_nuitka/packaging_test.dist && ./packaging_test"
    else
        echo "可执行文件位置: dist_nuitka/packaging_test"
        echo "运行命令: ./dist_nuitka/packaging_test"
    fi
else
    echo ""
    echo "打包失败，请检查错误信息"
    exit 1
fi

