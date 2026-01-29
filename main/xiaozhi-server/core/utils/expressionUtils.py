"""
GIF 表情处理工具模块
负责从 LLM 回复中提取表情标签并发送给客户端
"""

import re
import json
from typing import Optional, Tuple
from core.utils.expression_manager import expression_manager

TAG = __name__

# 表情标签正则：匹配 [expr:表情名] 格式（支持中文）
EXPRESSION_PATTERN = re.compile(r'\[expr:([^\]]+)\]')


def extract_expression(text: str) -> Tuple[Optional[str], str]:
    """
    从文本中提取表情标签
    
    Args:
        text: 原始文本，可能包含 [expr:xxx] 格式的标签
        
    Returns:
        (expression_name, clean_text): 表情名称 和 去除标签后的文本
        如果没有找到有效表情，返回 (None, 原文本)
    
    Examples:
        >>> extract_expression("[expr:开心]今天天气真好！")
        ("开心", "今天天气真好！")
        
        >>> extract_expression("今天天气真好！")
        (None, "今天天气真好！")
        
        >>> extract_expression("[expr:无效表情]你好")
        ("平静", "你好")  # 无效表情返回默认表情
    """
    match = EXPRESSION_PATTERN.search(text)
    if match:
        expression_name = match.group(1).strip()
        # 去除表情标签，保留其他文本
        clean_text = EXPRESSION_PATTERN.sub('', text, count=1).strip()
        
        # 验证表情是否有效
        if expression_manager.is_valid_expression(expression_name):
            return expression_name, clean_text
        else:
            # 无效表情，使用默认表情
            return expression_manager.default_expression, clean_text
    
    return None, text


def has_expression_tag(text: str) -> bool:
    """
    检查文本中是否包含表情标签
    
    Args:
        text: 要检查的文本
        
    Returns:
        bool: 是否包含 [expr:xxx] 格式的标签
    """
    return bool(EXPRESSION_PATTERN.search(text))


def has_incomplete_expression_tag(text: str) -> bool:
    """
    检查文本中是否有不完整的表情标签（正在流式输出中）
    
    Args:
        text: 要检查的文本
        
    Returns:
        bool: 是否包含不完整的标签（如 "[expr:" 或 "[expr:开"）
    """
    # 检查是否有 [expr: 开头但没有闭合的 ]
    if '[expr:' in text:
        last_open = text.rfind('[expr:')
        # 检查这个开头之后是否有闭合
        remaining = text[last_open:]
        if ']' not in remaining:
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
        
        await conn.websocket.send(json.dumps(message, ensure_ascii=False))
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
    
    Args:
        text: 原始文本
        
    Returns:
        去除所有 [expr:xxx] 标签后的文本
    """
    return EXPRESSION_PATTERN.sub('', text).strip()


def get_default_expression() -> str:
    """获取默认表情名称"""
    return expression_manager.default_expression


