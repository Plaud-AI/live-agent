"""
Time utility module
Provides unified time retrieval with timezone support
"""

import cnlunar
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Optional
from zoneinfo import ZoneInfo


WEEKDAY_MAP = {
    "Monday": "星期一",
    "Tuesday": "星期二", 
    "Wednesday": "星期三",
    "Thursday": "星期四",
    "Friday": "星期五",
    "Saturday": "星期六",
    "Sunday": "星期日",
}


def parse_timezone(tz_str: str):
    """Parse timezone string and return tzinfo object
    
    Supports formats:
    - IANA timezone: 'Asia/Shanghai', 'America/New_York'
    - UTC offset: 'UTC+8', 'UTC-7', '+8', '-5'
    """
    if not tz_str:
        return ZoneInfo("Asia/Shanghai")
    
    tz_str = tz_str.strip()
    upper_tz = tz_str.upper()
    
    # Try UTC offset format: UTC+8, UTC-7, +8, -5
    if upper_tz.startswith("UTC") or tz_str.startswith("+") or tz_str.startswith("-"):
        try:
            offset_str = upper_tz.replace("UTC", "").strip()
            if not offset_str or offset_str == "0":
                return dt_timezone.utc
            
            if ":" in offset_str:
                parts = offset_str.split(":")
                hours = int(parts[0])
                minutes = int(parts[1]) if len(parts) > 1 else 0
            else:
                hours = int(offset_str)
                minutes = 0
            
            return dt_timezone(timedelta(hours=hours, minutes=minutes))
        except (ValueError, TypeError):
            pass
    
    # Try IANA timezone format
    try:
        return ZoneInfo(tz_str)
    except Exception:
        return ZoneInfo("Asia/Shanghai")


def get_current_time(tz_str: Optional[str] = None) -> str:
    """Get current time string (format: HH:MM)"""
    tz = parse_timezone(tz_str) if tz_str else None
    return datetime.now(tz).strftime("%H:%M")


def get_current_date(tz_str: Optional[str] = None) -> str:
    """Get today's date string (format: YYYY-MM-DD)"""
    tz = parse_timezone(tz_str) if tz_str else None
    return datetime.now(tz).strftime("%Y-%m-%d")


def get_current_weekday(tz_str: Optional[str] = None) -> str:
    """Get current weekday in Chinese"""
    tz = parse_timezone(tz_str) if tz_str else None
    now = datetime.now(tz)
    return WEEKDAY_MAP[now.strftime("%A")]


def get_current_lunar_date(tz_str: Optional[str] = None) -> str:
    """Get lunar date string"""
    try:
        tz = parse_timezone(tz_str) if tz_str else None
        now = datetime.now(tz)
        # cnlunar needs naive datetime, convert to local time
        if now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        today_lunar = cnlunar.Lunar(now, godType="8char")
        return "%s年%s%s" % (
            today_lunar.lunarYearCn,
            today_lunar.lunarMonthCn[:-1],
            today_lunar.lunarDayCn,
        )
    except Exception:
        return "农历获取失败"


def get_current_time_info(tz_str: Optional[str] = None) -> tuple:
    """Get current time info with timezone support
    
    Returns: (current_time, today_date, today_weekday, lunar_date)
    """
    current_time = get_current_time(tz_str)
    today_date = get_current_date(tz_str)
    today_weekday = get_current_weekday(tz_str)
    lunar_date = get_current_lunar_date(tz_str)
    
    return current_time, today_date, today_weekday, lunar_date
