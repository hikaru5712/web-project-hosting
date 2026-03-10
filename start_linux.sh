#!/bin/bash

# web项目托管平台启动脚本（Linux）
echo "===================================="
echo " Django web项目托管平台启动脚本"
echo "===================================="

# 检查 Python 是否安装
echo "检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到 Python 环境，请先安装 Python 3.11 或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "Python 版本: $PYTHON_VERSION"
echo "Python 环境正常"

# 检查依赖是否安装
echo "检查项目依赖..."
if ! python3 -m pip list | grep -q "Django"; then
    echo "正在安装项目依赖..."
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "依赖安装失败，请检查网络连接"
        exit 1
    fi
    echo "依赖安装成功"
fi

# 启动开发服务器
echo "启动 Django 开发服务器..."
echo "访问地址：http://127.0.0.1:8000/"
echo "管理后台：http://127.0.0.1:8000/admin/"
echo "用户名：admin"
echo "密码：admin123"
echo "===================================="
echo "按 Ctrl+C 停止服务器"
echo "===================================="

python3 manage.py runserver
