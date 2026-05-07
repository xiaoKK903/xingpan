from datetime import datetime, timezone


def utc_now() -> datetime:
    """获取当前 UTC 时间（带时区信息）
    
    替代分散在各处的 _utc_now() 和 datetime.utcnow()。
    - datetime.utcnow() 返回 naive datetime，无法与带时区的时间比较
    - 本函数返回 timezone-aware datetime，推荐使用
    """
    return datetime.now(timezone.utc)
