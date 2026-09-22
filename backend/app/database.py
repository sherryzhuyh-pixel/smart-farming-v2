"""
数据库模块（SQLite/SQLAlchemy 已移除）
保留日期/时间辅助函数供应用层使用
"""
from datetime import datetime, timezone


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
