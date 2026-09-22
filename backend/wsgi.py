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

# 导入 FastAPI ASGI 应用
from app.main import app  # noqa: E402

# PythonAnywhere ASGI 配置直接使用此 app 对象
# 在 Web 配置页面选择 "ASGI" 模式并指向此文件
