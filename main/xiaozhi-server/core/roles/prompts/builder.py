"""
模块化系统提示词构建器
负责构建完整的系统提示词，包括 Profile、System Context、User Persona 等模块
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from zoneinfo import ZoneInfo
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()

# 加载模板文件
_ROLE_TPL = Path(__file__).resolve().parent / "role.md"
_USER_PERSONA_TPL = Path(__file__).resolve().parent / "user_persona.md"
_LANG_DIR = Path(__file__).resolve().parent / "languages"

ROLE_TEXT = _ROLE_TPL.read_text(encoding="utf-8")
USER_PERSONA_TEXT = _USER_PERSONA_TPL.read_text(encoding="utf-8")

LANG_MAP: Dict[str, str] = {}
for p in _LANG_DIR.glob("*.md"):
    LANG_MAP[p.stem] = p.read_text(encoding="utf-8")

# 星期几中英文映射
WEEKDAY_MAP = {
    "Monday": "星期一",
    "Tuesday": "星期二",
    "Wednesday": "星期三",
    "Thursday": "星期四",
    "Friday": "星期五",
    "Saturday": "星期六",
    "Sunday": "星期日",
}


def _parse_timezone(tz_str: str) -> tuple:
    """Parse timezone string and return (tzinfo, display_name)
    
    Supports formats:
    - IANA timezone: 'Asia/Shanghai', 'America/New_York'
    - UTC offset: 'UTC+8', 'UTC-7', '+8', '-5'
    
    Returns:
        (tzinfo object, display string for prompt)
    """
    from datetime import timezone as dt_timezone, timedelta
    
    if not tz_str:
        return ZoneInfo("UTC"), "UTC"
    
    tz_str = tz_str.strip()
    
    # Try UTC offset format first: UTC+8, UTC-7, +8, -5
    upper_tz = tz_str.upper()
    if upper_tz.startswith("UTC") or tz_str.startswith("+") or tz_str.startswith("-"):
        try:
            # Remove "UTC" prefix if present
            offset_str = upper_tz.replace("UTC", "").strip()
            if not offset_str or offset_str == "0":
                return dt_timezone.utc, "UTC"
            
            # Parse hours (and optional minutes)
            if ":" in offset_str:
                parts = offset_str.split(":")
                hours = int(parts[0])
                minutes = int(parts[1]) if len(parts) > 1 else 0
            else:
                hours = int(offset_str)
                minutes = 0
            
            # Create timezone with offset
            offset = timedelta(hours=hours, minutes=minutes)
            tz = dt_timezone(offset)
            
            # Format display name
            sign = "+" if hours >= 0 else ""
            display = f"UTC{sign}{hours}" if minutes == 0 else f"UTC{sign}{hours}:{abs(minutes):02d}"
            return tz, display
        except (ValueError, TypeError):
            pass
    
    # Try IANA timezone format
    try:
        return ZoneInfo(tz_str), tz_str
    except Exception:
        logger.bind(tag=TAG).warning(f"Invalid timezone: {tz_str}, using UTC")
        return ZoneInfo("UTC"), "UTC"


def _build_system_context(
    timezone: str,
    language: str,
    today_date: Optional[str] = None,
    today_weekday: Optional[str] = None,
    lunar_date: Optional[str] = None,
    local_address: Optional[str] = None,
    weather_info: Optional[str] = None,
    device_id: Optional[str] = None,
) -> str:
    """构建系统上下文部分（时间、时区、语言、位置、天气等）
    
    Args:
        timezone: timezone string:
                  - IANA format: 'Asia/Shanghai', 'America/New_York'
                  - UTC offset: 'UTC+8', 'UTC-7', '+8', '-5'
        language: language code ('zh' or 'en')
        today_date: today's date (optional, auto-calculated if not provided)
        today_weekday: today's weekday (optional, auto-calculated if not provided)
        lunar_date: today's lunar date (optional)
        local_address: user's location (optional)
        weather_info: weather information (optional)
        device_id: device ID (optional)
        
    Returns:
        formatted system context string
    """
    tz, tz_display = _parse_timezone(timezone)

    now = datetime.now(tz)
    
    # 如果未提供日期信息，则自动计算
    if not today_date:
        day = now.strftime("%d")
        month = now.strftime("%B")
        year = now.strftime("%Y")
        today_date = f"{day} {month} {year}"
    
    if not today_weekday:
        day_of_week = now.strftime("%A")
        if language == "zh":
            today_weekday = WEEKDAY_MAP.get(day_of_week, day_of_week)
        else:
            today_weekday = day_of_week
    
    # 格式化时间
    time_str = now.strftime("%H:%M")
    
    # 构建系统上下文规则
    system_rules = []
    
    formatted_datetime = f"{now.strftime('%A')}, {time_str} {today_date} ({tz_display})"
    system_rules.append(f"- The user started this conversation on {formatted_datetime}")
    if local_address:
        system_rules.append(f"- User location: {local_address}")
    if weather_info:
        system_rules.append(f"- Local weather forecast: {weather_info}")
    if device_id:
        system_rules.append(f"- Device ID: {device_id}")
    system_rules.append(f"- Your current language is: **{language}**")

    return "\n".join(system_rules)


def build_user_persona_prompt(user_persona: str) -> str:
    """构建用户画像提示词
    
    Args:
        user_persona: 用户画像信息（通常是从 memory 模块获取的要点列表）
        
    Returns:
        格式化后的用户画像提示词字符串
    """
    if not user_persona:
        return ""

    return USER_PERSONA_TEXT.format(user_persona=user_persona.strip())


def build_system_prompt(
    profile: str,
    timezone: str = "Asia/Shanghai",
    language: str = "zh",
    user_persona: Optional[str] = None,
    today_date: Optional[str] = None,
    today_weekday: Optional[str] = None,
    lunar_date: Optional[str] = None,
    local_address: Optional[str] = None,
    weather_info: Optional[str] = None,
    device_id: Optional[str] = None,
    **kwargs
) -> str:
    """构建完整的系统提示词
    
    Args:
        profile: 用户自定义的角色配置（从 config.yaml 的 prompt 字段获取）
        timezone: 时区字符串（如 'Asia/Shanghai', 'America/New_York'），默认 'Asia/Shanghai'
        language: 语言代码（'zh' 或 'en'），默认 'zh'
        user_persona: 可选的用户画像信息（从 memory 模块获取）
        today_date: 今天日期（可选，如未提供则自动计算）
        today_weekday: 今天星期几（可选，如未提供则自动计算）
        lunar_date: 今天农历（可选）
        local_address: 用户所在城市（可选）
        weather_info: 天气信息（可选）
        device_id: 设备ID（可选）
        **kwargs: 其他参数（用于兼容性）
        
    Returns:
        完整的系统提示词字符串
    """
    # Step 1: Profile 内容
    profile_content = profile
    
    # Step 2: 构建系统上下文
    system_context = _build_system_context(
        timezone=timezone,
        language=language,
        today_date=today_date,
        today_weekday=today_weekday,
        lunar_date=lunar_date,
        local_address=local_address,
        weather_info=weather_info,
        device_id=device_id,
    )
    
    # Step 3: 构建用户记忆块（可选）
    user_memory_block = ""
    if user_persona:
        user_memory_block = user_persona.strip()
    
    # Step 4: 获取语言特定提示
    language_specific_prompt = LANG_MAP.get(language, "")
    
    # Step 5: 填充主模板
    template_vars = {
        "profile": profile,
        "system_context": system_context,
        "user_memory_block": user_memory_block,
    }
    
    # Step 6: 填充模板
    try:
        system_prompt = ROLE_TEXT.format(**template_vars)
    except KeyError as e:
        logger.bind(tag=TAG).error(f"Template variable missing: {e}")
        system_prompt = profile_content
    
    logger.bind(tag=TAG).debug(f"Built system prompt: {system_prompt}")
    
    return system_prompt
