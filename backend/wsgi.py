#!/usr/bin/env python3
"""
PythonAnywhere WSGI entry - direct WSGI adapter (no uvicorn subprocess)
Uses a2wsgi to wrap FastAPI ASGI app for uWSGI compatibility
"""
import os
import sys
import subprocess

HOME = "/home/andrewzeng"
PROJECT_DIR = f"{HOME}/smart-farming-v2/backend"
VENV_PATH = f"{HOME}/.virtualenvs/smart-farming"

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
sp = os.path.join(VENV_PATH, "lib", f"python{py_ver}", "site-packages")
if sp not in sys.path and os.path.exists(sp):
    sys.path.insert(0, sp)

# Install a2wsgi if not available
pip = os.path.join(VENV_PATH, "bin", "pip")
if os.path.exists(pip):
    try:
        import a2wsgi
    except ImportError:
        subprocess.run([pip, "install", "a2wsgi"], capture_output=True, timeout=120)

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
os.environ.setdefault("CACHE_SIZE_LIMIT", "52428850")
os.environ.setdefault("DEBUG", "false")

# Import FastAPI app and wrap with WSGI adapter
from app.main import app  # noqa: E402
from a2wsgi import ASGIMiddleware  # noqa: E402

application = ASGIMiddleware(app)
