from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "AI智慧养殖系统V2.0"
    APP_VERSION: str = "2.0.0"
    API_V2_PREFIX: str = "/api/v2"
    DEBUG: bool = False

    # ── 飞书开放平台配置 ──
    LARK_APP_ID: str = ""
    LARK_APP_SECRET: str = ""
    LARK_BASE_TOKEN: str = ""

    # ── 缓存配置 ──
    CACHE_DIR: str = "./cache"
    CACHE_SIZE_LIMIT: int = 50 * 1024 * 1024  # 50MB

    # ── JWT Authentication ──
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # ── CORS ──
    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ── 初始管理员（启动时自动创建，如果 users 表为空） ──
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD_HASH: str = ""

    @property
    def CORS_ORIGINS_LIST(self) -> list:
        origins = [
            o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(",") if o.strip()
        ]
        return origins if origins else []

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    return settings
