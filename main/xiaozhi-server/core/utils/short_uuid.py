"""
Short UUID Generator

Provides a compact UUID generation utility.
"""

import uuid


def shortuuid(prefix: str = "") -> str:
    """
    Generate a short UUID string with optional prefix.
    
    Args:
        prefix: Optional prefix string
        
    Returns:
        str: Short UUID string (prefix + 12 hex chars)
    """
    return prefix + str(uuid.uuid4().hex)[:12]

