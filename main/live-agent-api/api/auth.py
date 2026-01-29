"""Authentication utilities for API endpoints"""
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from utils.security import verify_jwt_token
from utils.exceptions import UnauthorizedException

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Get current user ID from JWT Bearer token (no database query)
    
    Usage:
        @router.get("/profile")
        async def get_profile(user_id: str = Depends(get_current_user_id)):
            ...
    
    Args:
        credentials: HTTP Authorization credentials (Bearer token)
    
    Returns:
        User ID extracted from token
    
    Raises:
        UnauthorizedException: If token is invalid or expired
    """
    token = credentials.credentials
    
    payload = verify_jwt_token(token)
    if not payload:
        raise UnauthorizedException("Invalid or expired token")
    
    return payload['user_id']



