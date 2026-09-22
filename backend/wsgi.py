#!/usr/bin/env python3
"""
PythonAnywhere ASGI 入口文件
PythonAnywhere 已支持原生 ASGI（2023-09 起），直接导出 FastAPI app
"""
import sys
import os

# 添加项目路径（根据 PythonAnywhere 用户名修改）
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 生产环境默认配置（PythonAnywhere 部署时使用）
# 注：以下凭据仅限当前项目使用
os.environ.setdefault("LARK_APP_ID", "cli_aad1811323789bd8")
os.environ.setdefault("LARK_APP_SECRET", "wX1K0Hrssj4LLfJ6psYjuXo4KTlcbOfA")
os.environ.setdefault("LARK_BASE_TOKEN", "Oi1ObtIzLa7U8issGOGcO4JSneg")
os.environ.setdefault("JWT_SECRET_KEY", "wHi_b-wglggDEP9bSbfWWCH5Vuo6H0wcKycQ4zIMxwuvTAj3n1sNxutsZFphDeOvv8xdAL3AwJEJAToYmPwfKA")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "120")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "https://sherryzhuyh-pixel.github.io/smart-farming-v2,https://sherryzhuyh-pixel.github.io")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD_HASH", "$2b$12$FiT00zOtLzsmqmb14lvZBe9irr.NwzYIpxHLKzG/fOSddRmAdM2jq")
os.environ.setdefault("CACHE_DIR", "./cache")
os.environ.setdefault("CACHE_SIZE_LIMIT", "52428800")
os.environ.setdefault("DEBUG", "false")

# 导入 FastAPI ASGI 应用
from app.main import app  # noqa: E402

# PythonAnywhere ASGI 配置直接使用此 app 对象
# 在 Web 配置页面选择 "ASGI" 模式并指向此文件
