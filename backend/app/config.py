from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    APP_NAME: str = "AI智慧养殖系统V2.0"
    APP_VERSION: str = "2.0.0"
    API_V2_PREFIX: str = "/api/v2"
    DEBUG: bool = False

    # Database - 支持 DATABASE_URL 直接配置，或分字段配置
    DATABASE_URL: str = "sqlite:///./smart_farming.db"

    # MySQL 分字段配置（当 DATABASE_URL 未设置或需要MySQL时使用）
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "ai_breeding_v2"
    DB_CHARSET: str = "utf8mb4"

    # JWT Authentication
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    # CORS
    CORS_ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Admin credentials (for first-run seed)
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = ""

    @property
    def DATABASE_URL_EFFECTIVE(self) -> str:
        """返回最终生效的数据库连接URL"""
        # 如果 DATABASE_URL 不是默认的SQLite本地路径，直接用它
        if self.DATABASE_URL and not self.DATABASE_URL.endswith("./smart_farming.db"):
            return self.DATABASE_URL
        # 如果设置了 DB_PASSWORD，优先使用 MySQL
        if self.DB_PASSWORD:
            return (
                f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
                f"?charset={self.DB_CHARSET}"
            )
        # 默认使用 SQLite
        return self.DATABASE_URL

    @property
    def IS_SQLITE(self) -> bool:
        return self.DATABASE_URL_EFFECTIVE.startswith("sqlite")

    @property
    def CORS_ORIGINS_LIST(self) -> list:
        origins = [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]
        return origins if origins else []

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    return settings
