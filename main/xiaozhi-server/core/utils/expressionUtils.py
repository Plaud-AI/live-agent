"""
GIF 表情处理工具模块
负责从 LLM 回复中提取表情标签并发送给客户端
"""

import re
import json
from typing import Optional, Tuple
from core.utils.expression_manager import expression_manager

TAG = __name__

# 表情标签正则：同时支持 [expr:表情名] 和 [表情名] 两种格式
# 优先匹配 [expr:xxx] 格式，其次匹配 [xxx] 格式
EXPRESSION_PATTERN_FULL = re.compile(r'\[expr:([^\]]+)\]')  # 完整格式 [expr:xxx]
EXPRESSION_PATTERN_SIMPLE = re.compile(r'^\[([^\]]+)\]')  # 简化格式 [xxx]（仅在开头）
# 兼容两种格式的通用正则
EXPRESSION_PATTERN = re.compile(r'\[(?:expr:)?([^\]]+)\]')


def extract_expression(text: str) -> Tuple[Optional[str], str]:
    """
    从文本中提取表情标签
    
    支持两种格式：
    - [expr:表情名] - 标准格式
    - [表情名] - 简化格式（兼容 LLM 可能输出的格式）
    
    Args:
        text: 原始文本，可能包含表情标签
        
    Returns:
        (expression_name, clean_text): 表情名称 和 去除标签后的文本
        如果没有找到有效表情，返回 (None, 原文本)
    
    Examples:
        >>> extract_expression("[expr:开心]今天天气真好！")
        ("开心", "今天天气真好！")
        
        >>> extract_expression("[开心]今天天气真好！")
        ("开心", "今天天气真好！")
        
        >>> extract_expression("今天天气真好！")
        (None, "今天天气真好！")
        
        >>> extract_expression("[expr:无效表情]你好")
        ("平静", "你好")  # 无效表情返回默认表情
    """
    # 优先匹配完整格式 [expr:xxx]
    match = EXPRESSION_PATTERN_FULL.search(text)
    if match:
        expression_name = match.group(1).strip()
        clean_text = EXPRESSION_PATTERN_FULL.sub('', text, count=1).strip()
        
        if expression_manager.is_valid_expression(expression_name):
            return expression_name, clean_text
        else:
            return expression_manager.default_expression, clean_text
    
    # 其次匹配简化格式 [xxx]（仅在文本开头）
    match = EXPRESSION_PATTERN_SIMPLE.match(text)
    if match:
        expression_name = match.group(1).strip()
        # 验证是否是有效的表情名称（避免误匹配其他方括号内容）
        if expression_manager.is_valid_expression(expression_name):
            clean_text = EXPRESSION_PATTERN_SIMPLE.sub('', text, count=1).strip()
            return expression_name, clean_text
    
    return None, text


def has_expression_tag(text: str) -> bool:
    """
    检查文本中是否包含表情标签
    
    支持两种格式：
    - [expr:xxx] 完整格式
    - [xxx] 简化格式（仅在文本开头且为有效表情名时）
    
    Args:
        text: 要检查的文本
        
    Returns:
        bool: 是否包含表情标签
    """
    # 检查完整格式
    if EXPRESSION_PATTERN_FULL.search(text):
        return True
    
    # 检查简化格式（仅在开头）
    match = EXPRESSION_PATTERN_SIMPLE.match(text)
    if match:
        expression_name = match.group(1).strip()
        # 只有当是有效表情时才认为是表情标签
        return expression_manager.is_valid_expression(expression_name)
    
    return False


def has_incomplete_expression_tag(text: str) -> bool:
    """
    检查文本中是否有不完整的表情标签（正在流式输出中）
    
    支持检测两种格式的不完整标签：
    - [expr: 或 [expr:开 等不完整的完整格式
    - [ 或 [开 等不完整的简化格式（仅在开头时）
    
    Args:
        text: 要检查的文本
        
    Returns:
        bool: 是否包含不完整的标签
    """
    # 检查完整格式 [expr:xxx 是否不完整
    if '[expr:' in text:
        last_open = text.rfind('[expr:')
        remaining = text[last_open:]
        if ']' not in remaining:
            return True
    
    # 检查简化格式 [xxx 是否不完整（仅在文本开头）
    # 文本以 [ 开头但没有闭合的 ]
    if text.startswith('[') and ']' not in text:
        # 可能是正在输入的表情标签
        return True
    
    return False


async def send_expression(conn, expression_name: str):
    """
    发送表情消息给客户端
    
    Args:
        conn: 连接对象
        expression_name: 表情名称（中文）
    
    发送的消息格式:
    {
        "type": "expression",
        "expression": "开心",
        "file": "gif/开心.gif",
        "session_id": "xxx"
    }
    """
    try:
        expression_info = expression_manager.get_expression_info(expression_name)
        file_path = expression_manager.get_expression_file_path(expression_name)
        
        message = {
            "type": "expression",
            "expression": expression_name,
            "file": file_path or f"gif/{expression_name}.gif",
            "category": expression_info.get("category") if expression_info else "情绪",
            "session_id": conn.session_id,
        }
        
        # 发送表情消息
        await conn.channel.send_text(json.dumps(message, ensure_ascii=False))
        conn.logger.bind(tag=TAG).debug(f"发送表情: {expression_name}")
        
    except Exception as e:
        conn.logger.bind(tag=TAG).warning(f"发送表情失败: {e}")


async def process_expression(conn, text: str) -> str:
    """
    处理文本中的表情标签：提取、发送、返回清理后的文本
    
    这是一个便捷方法，组合了 extract_expression 和 send_expression
    
    Args:
        conn: 连接对象
        text: 原始文本
        
    Returns:
        去除表情标签后的文本
    """
    expression_name, clean_text = extract_expression(text)
    
    if expression_name:
        await send_expression(conn, expression_name)
    
    return clean_text


def remove_expression_tags(text: str) -> str:
    """
    移除文本中所有的表情标签
    
    支持移除两种格式：
    - [expr:xxx] 完整格式
    - [xxx] 简化格式（仅当 xxx 是有效表情名时）
    
    Args:
        text: 原始文本
        
    Returns:
        去除所有表情标签后的文本
    """
    # 先移除完整格式
    result = EXPRESSION_PATTERN_FULL.sub('', text)
    
    # 再移除开头的简化格式（如果是有效表情）
    match = EXPRESSION_PATTERN_SIMPLE.match(result)
    if match:
        expression_name = match.group(1).strip()
        if expression_manager.is_valid_expression(expression_name):
            result = EXPRESSION_PATTERN_SIMPLE.sub('', result, count=1)
    
    return result.strip()


def get_default_expression() -> str:
    """获取默认表情名称"""
    return expression_manager.default_expression


