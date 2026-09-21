"""AI智慧养殖系统V2.0 - FastAPI 应用入口"""
import logging
from fastapi import FastAPI, Request, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.config import get_settings
from app.database import get_db
from app.auth import get_current_user
from app.routers import batches, growth, performance, pilot, finance, profit, traceability, inventory, config, auth

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
    description="AI智慧养殖系统V2.0 后端API - 模块化单体架构",
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
    logger.exception("Unhandled exception at %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"code": 500, "message": "服务器内部错误"},
    )


# Public routes (no auth required)
public_router = APIRouter()
app.include_router(auth.router, prefix=settings.API_V2_PREFIX)

# Protected routes (auth required)
# Use dependencies on include_router to protect all endpoints
dependencies = [Depends(get_current_user)] if not settings.DEBUG else []

api_prefix = settings.API_V2_PREFIX
app.include_router(batches.router, prefix=api_prefix, dependencies=dependencies)
app.include_router(growth.router, prefix=api_prefix, dependencies=dependencies)
app.include_router(performance.router, prefix=api_prefix, dependencies=dependencies)
app.include_router(pilot.router, prefix=api_prefix, dependencies=dependencies)
app.include_router(finance.router, prefix=api_prefix, dependencies=dependencies)
app.include_router(profit.router, prefix=api_prefix, dependencies=dependencies)
app.include_router(traceability.router, prefix=api_prefix, dependencies=dependencies)
app.include_router(inventory.router, prefix=api_prefix, dependencies=dependencies)
app.include_router(config.router, prefix=api_prefix, dependencies=dependencies)


@app.get("/")
def root():
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "ok", "timestamp": time.time()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
