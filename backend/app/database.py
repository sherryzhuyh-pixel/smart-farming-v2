"""
数据库模块（SQLite/SQLAlchemy 已移除）
保留兼容性 shim，使现有 routers / models 仍可导入
后续 Phase 2-4 迁移业务路由后，可彻底移除 shim
"""
from datetime import datetime, timezone
from typing import Any, Generator


# ── 兼容性 shim：Session 类型 stub ──
class Session:
    """SQLAlchemy Session 兼容 stub，仅供类型注解使用。
    实际调用时会抛出 RuntimeError，提示应使用 RepositoryFactory。
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError(
            "SQLite/SQLAlchemy 已移除。请使用 RepositoryFactory 替代 Session。"
        )

    def __getattr__(self, name: str) -> Any:
        raise RuntimeError(
            "SQLite/SQLAlchemy 已移除。请使用 RepositoryFactory 替代 Session。"
        )


# ── 兼容性 shim：declarative_base stub ──
class _DeclarativeBaseMeta(type):
    def __new__(mcs, name, bases, namespace):
        return type.__new__(mcs, name, bases, namespace)


class _Base(metaclass=_DeclarativeBaseMeta):
    """SQLAlchemy declarative_base 兼容 stub"""

    __tablename__ = ""
    metadata = None
    registry = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError(
            "SQLite/SQLAlchemy 已移除。请使用 RepositoryFactory 替代 ORM 模型。"
        )


def declarative_base() -> type:
    return _Base


Base = _Base


# ── 兼容性 shim：engine / SessionLocal stub ──
class _Engine:
    """SQLAlchemy engine 兼容 stub"""

    def __getattr__(self, name: str) -> Any:
        raise RuntimeError(
            "SQLite/SQLAlchemy 已移除。请使用 RepositoryFactory 替代。"
        )


engine = _Engine()


class _SessionLocal:
    """SQLAlchemy sessionmaker 兼容 stub"""

    def __call__(self, *args: Any, **kwargs: Any) -> Session:
        raise RuntimeError(
            "SQLite/SQLAlchemy 已移除。请使用 RepositoryFactory 替代。"
        )


SessionLocal = _SessionLocal()


# ── 兼容性 shim：get_db 生成器 stub ──
def get_db() -> Generator[Any, None, None]:
    """原 SQLAlchemy Session 依赖注入的兼容 stub。"""
    raise RuntimeError(
        "SQLite/SQLAlchemy 已移除。请使用 get_repositories() 替代 get_db()。"
    )


# ── 辅助函数 ──

def format_datetime(dt: datetime | None) -> str | None:
    """将 datetime 格式化为 ISO 8601 字符串"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def now_iso() -> str:
    """获取当前时间的 ISO 8601 字符串"""
    return datetime.now(timezone.utc).isoformat()
