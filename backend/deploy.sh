#!/bin/bash
# PythonAnywhere 部署脚本
# 在 PythonAnywhere Bash 控制台中运行：bash deploy.sh

set -e

echo "=== AI智慧养殖系统 V2.0 - PythonAnywhere 部署 ==="

# 1. 克隆代码
echo "[1/5] 克隆代码..."
cd ~
if [ -d "smart-farming-v2" ]; then
    echo "目录已存在，拉取最新代码..."
    cd smart-farming-v2 && git pull origin main
else
    git clone https://github.com/sherryzhuyh-pixel/smart-farming-v2.git
    cd smart-farming-v2
fi

# 2. 创建虚拟环境
echo "[2/5] 创建虚拟环境..."
cd backend
python3.11 -m venv venv
source venv/bin/activate

# 3. 安装依赖
echo "[3/5] 安装依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. 创建 .env 文件（如果用户已填写 .env.example）
echo "[4/5] 检查环境变量配置..."
if [ ! -f ".env" ]; then
    echo "警告：.env 文件不存在，请复制 .env.example 并填入实际值"
    cp .env.example .env
    echo "请编辑 .env 文件填入飞书凭证和 JWT 密钥后重新运行此脚本"
    exit 1
fi

# 5. 验证配置
echo "[5/5] 验证配置..."
python -c "from app.config import get_settings; s=get_settings(); print('配置验证通过')" || {
    echo "配置验证失败，请检查 .env 文件"
    exit 1
}

echo ""
echo "=== 部署完成 ==="
echo "下一步：在 PythonAnywhere Web 配置页面设置 ASGI 应用"
echo "  - 工作目录：/home/$USER/smart-farming-v2/backend"
echo "  - ASGI 文件：/home/$USER/smart-farming-v2/backend/wsgi.py"
echo "  - Python 版本：3.11"
echo ""
echo "然后在 Environment variables 中添加 .env 中的所有变量"
