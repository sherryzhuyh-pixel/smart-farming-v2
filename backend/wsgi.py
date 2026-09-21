#!/usr/bin/env python3
"""
PythonAnywhere WSGI 入口文件
使用 asgiref.WsgiToAsgi 将 FastAPI ASGI 应用适配为 WSGI
"""
import sys
import os

# 添加项目路径（根据 PythonAnywhere 用户名修改）
# 例如：/home/yourusername/smart-farming-v2/backend
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 导入 FastAPI 应用
from app.main import app  # noqa: E402

# ASGI -> WSGI 适配
from asgiref.wsgi import WsgiToAsgi  # noqa: E402

application = WsgiToAsgi(app)
