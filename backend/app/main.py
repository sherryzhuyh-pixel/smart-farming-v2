"""AI智慧养殖系统V2.0 - FastAPI 应用入口 (Feishu Base 版本)"""
import logging
import os
from fastapi import FastAPI, Request, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.config import get_settings
from app.auth import get_current_user, get_password_hash
from app.clients.feishu_base import FeishuBaseClient
from app.repositories import RepositoryFactory
from app.routers import (
    batches,
    growth,
    performance,
    pilot,
    finance,
    profit,
    traceability,
    inventory,
    config,
    auth,
    health,
    environment,
    feed,
    market,
)

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI智慧养殖系统V2.0 后端API - 飞书Base驱动",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS - whitelist mode
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler - NEVER leak stack traces to client
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "Unhandled exception at %s %s", request.method, request.url.path
    )
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误"},
    )


# ── 应用生命周期 ──


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化 FeishuBaseClient、Cache、RepositoryFactory"""
    # 确保缓存目录存在
    os.makedirs(settings.CACHE_DIR, exist_ok=True)

    # 初始化 FeishuBaseClient
    base_client = FeishuBaseClient(
        app_id=settings.LARK_APP_ID,
        app_secret=settings.LARK_APP_SECRET,
        base_token=settings.LARK_BASE_TOKEN,
        cache_dir=settings.CACHE_DIR,
    )

    # 初始化 RepositoryFactory
    repositories = RepositoryFactory(
        client=base_client,
        cache=base_client.cache,
    )

    app.state.base_client = base_client
    app.state.cache = base_client.cache
    app.state.repositories = repositories

    logger.info(
        "FeishuBaseClient initialized, base_token=%s...",
        settings.LARK_BASE_TOKEN[:8] if settings.LARK_BASE_TOKEN else "(empty)",
    )

    # 自动创建初始管理员（如果 users 表为空）
    await _ensure_admin_user(repositories)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    if hasattr(app.state, "repositories"):
        await app.state.repositories.close()
        logger.info("RepositoryFactory closed")


async def _ensure_admin_user(repos: RepositoryFactory):
    """启动时检查 users 表，为空则自动创建管理员"""
    try:
        users = await repos.users.list_all(limit=1)
        if users:
            logger.info("Admin user check passed (users table not empty)")
            return

        admin_username = settings.ADMIN_USERNAME
        admin_password_hash = settings.ADMIN_PASSWORD_HASH

        if not admin_password_hash:
            # 如果未提供密码哈希，生成一个默认的（仅用于开发）
            logger.warning(
                "ADMIN_PASSWORD_HASH not set, skipping auto admin creation"
            )
            return

        await repos.users.create(
            {
                "username": admin_username,
                "password_hash": admin_password_hash,
                "full_name": "Administrator",
                "role": "admin",
                "is_active": True,
                "created_at": __import__("datetime")
                .datetime.now(__import__("datetime").timezone.utc)
                .isoformat(),
            }
        )
        logger.info(
            "Auto-created admin user: %s", admin_username
        )
    except Exception as e:
        logger.warning("Failed to ensure admin user: %s", e)


# ── 路由注册 ──

# Public routes (no auth required)
app.include_router(auth.router, prefix=settings.API_V2_PREFIX)

# Protected routes (auth required) — DEBUG mode does NOT bypass auth
dependencies = [Depends(get_current_user)]

api_prefix = settings.API_V2_PREFIX
app.include_router(
    batches.router, prefix=api_prefix, dependencies=dependencies
)
app.include_router(
    growth.router, prefix=api_prefix, dependencies=dependencies
)
app.include_router(
    performance.router, prefix=api_prefix, dependencies=dependencies
)
app.include_router(
    pilot.router, prefix=api_prefix, dependencies=dependencies
)
app.include_router(
    finance.router, prefix=api_prefix, dependencies=dependencies
)
app.include_router(
    profit.router, prefix=api_prefix, dependencies=dependencies
)
app.include_router(
    traceability.router, prefix=api_prefix, dependencies=dependencies
)
app.include_router(
    inventory.router, prefix=api_prefix, dependencies=dependencies
)
app.include_router(
    config.router, prefix=api_prefix, dependencies=dependencies
)
app.include_router(
    health.router, prefix=api_prefix, dependencies=dependencies
)
app.include_router(
    environment.router, prefix=api_prefix, dependencies=dependencies
)
app.include_router(
    feed.router, prefix=api_prefix, dependencies=dependencies
)
app.include_router(
    market.router, prefix=api_prefix, dependencies=dependencies
)


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": time.time()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG
    )
