# PythonAnywhere 部署指南

## 前置条件
- PythonAnywhere 账户：andrewzeng
- GitHub 仓库：https://github.com/sherryzhuyh-pixel/smart-farming-v2

## 步骤 1：打开 Bash 控制台

1. 登录 https://www.pythonanywhere.com/user/andrewzeng/
2. 点击 **Consoles** → **Start a new console** → **Bash**

## 步骤 2：执行部署命令

在 Bash 控制台中逐行执行：

```bash
cd ~
git clone https://github.com/sherryzhuyh-pixel/smart-farming-v2.git
cd smart-farming-v2/backend
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 步骤 3：创建 .env 文件

```bash
cat > .env << 'EOF'
LARK_APP_ID=cli_aad1811323789bd8
LARK_APP_SECRET=你的飞书应用密钥
LARK_BASE_TOKEN=Oi1ObtIzLa7U8issGOGcO4JSneg
JWT_SECRET_KEY=你的JWT密钥（用python -c "import secrets; print(secrets.token_urlsafe(64))"生成）
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=120
CORS_ALLOWED_ORIGINS=https://sherryzhuyh-pixel.github.io/smart-farming-v2,https://sherryzhuyh-pixel.github.io
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=你的密码哈希（用python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('你的密码'))"生成）
CACHE_DIR=./cache
CACHE_SIZE_LIMIT=52428800
DEBUG=false
EOF
```

## 步骤 4：创建 Web 应用

1. 点击 **Web** 标签
2. 点击 **Add a new web app**
3. 选择 **Manual configuration**
4. 选择 **Python 3.11**
5. 点击 **Next**

## 步骤 5：配置 ASGI

在 Web 配置页面：

- **Source code**: `/home/andrewzeng/smart-farming-v2/backend`
- **Working directory**: `/home/andrewzeng/smart-farming-v2/backend`
- **WSGI configuration file**: 点击路径链接打开编辑器，替换为：

```python
import sys
path = '/home/andrewzeng/smart-farming-v2/backend'
if path not in sys.path:
    sys.path.append(path)

from app.main import app
```

- 在 **Virtualenv** 部分填入：`/home/andrewzeng/smart-farming-v2/backend/venv`

## 步骤 6：设置环境变量

在 Web 配置页面底部找到 **Environment variables**，添加以下变量：

| Variable | Value |
|---|---|
| LARK_APP_ID | cli_aad1811323789bd8 |
| LARK_APP_SECRET | （你的飞书应用密钥） |
| LARK_BASE_TOKEN | Oi1ObtIzLa7U8issGOGcO4JSneg |
| JWT_SECRET_KEY | （你的JWT密钥） |
| JWT_ALGORITHM | HS256 |
| JWT_ACCESS_TOKEN_EXPIRE_MINUTES | 120 |
| CORS_ALLOWED_ORIGINS | https://sherryzhuyh-pixel.github.io/smart-farming-v2,https://sherryzhuyh-pixel.github.io |
| ADMIN_USERNAME | admin |
| ADMIN_PASSWORD_HASH | （你的密码哈希） |
| DEBUG | false |

## 步骤 7：配置静态文件（可选）

如需托管前端静态文件（替代 GitHub Pages）：

在 **Static files** 部分添加：
- URL: `/`
- Directory: `/home/andrewzeng/smart-farming-v2/frontend/dist`

## 步骤 8：重启应用

点击 **Reload** 按钮重启 Web 应用。

## 验证

访问 https://andrewzeng.pythonanywhere.com/api/v2/health 应返回：
```json
{"status": "ok"}
```

## 访问地址

- **后端 API**: https://andrewzeng.pythonanywhere.com/api/v2
- **前端页面**: https://sherryzhuyh-pixel.github.io/smart-farming-v2/
- **管理员账号**: admin / admin123

## 更新代码

后续更新时，在 Bash 控制台执行：
```bash
cd ~/smart-farming-v2
git pull origin main
cd backend
source venv/bin/activate
pip install -r requirements.txt
```
然后在 Web 页面点击 **Reload**。
