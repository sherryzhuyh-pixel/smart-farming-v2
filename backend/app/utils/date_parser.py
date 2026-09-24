"""日期解析工具：兼容 ISO 字符串和 Unix 时间戳（毫秒/秒）"""
from datetime import date, datetime, timezone


def parse_date(val) -> date | None:
    """将 Feishu Base 返回的日期值解析为 date 对象。

    支持格式：
    - Unix 毫秒时间戳（如 1798646400000）
    - Unix 秒时间戳（如 1798646400）
    - ISO 日期字符串（如 "2026-09-23"）
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        ts = val / 1000.0 if val > 1e10 else val
        return datetime.fromtimestamp(ts, tz=timezone.utc).date()
    s = str(val).strip()
    if s.isdigit():
        n = int(s)
        ts = n / 1000.0 if n > 1e10 else n
        return datetime.fromtimestamp(ts, tz=timezone.utc).date()
    return date.fromisoformat(s)
