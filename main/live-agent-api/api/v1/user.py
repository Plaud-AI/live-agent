from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infra import get_db
from services.user_service import user_service
from utils.response import success_response
from api.auth import get_current_user_id
from schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    PasswordUpdateRequest,
    UserInfo,
    UserProfileResponse,
    UserProfileUpdateRequest,
)

router = APIRouter()


@router.post("/register", summary="Register a new user")
async def register(
    request: UserRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account
    
    - **username**: 3-50 characters, must be unique
    - **password**: 6-128 characters
    """
    await user_service.register(
        db=db,
        username=request.username,
        password=request.password
    )
    return success_response(message="Registration successful")


@router.post("/login", summary="User login")
async def login(
    request: UserLoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login and get JWT token
    
    Returns token that should be used as Bearer token in subsequent requests.
    """
    result = await user_service.login(
        db=db,
        username=request.username,
        password=request.password
    )
    return success_response(data=result.model_dump())


@router.get("/info", summary="Get current user info")
async def get_user_info(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current authenticated user's information
    
    Requires Bearer token authentication.
    """
    user = await user_service.get_user_info(db=db, user_id=current_user_id)
    return success_response(data=UserInfo.model_validate(user).model_dump())


@router.post("/password", summary="Update password")
async def update_password(
    request: PasswordUpdateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's password
    
    Requires Bearer token authentication.
    """
    await user_service.update_password(
        db=db,
        user_id=current_user_id,
        old_password=request.old_password,
        new_password=request.new_password
    )
    return success_response(message="Password updated successfully")


@router.post("/logout", summary="User logout")
async def logout(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout current user
    
    Note: JWT tokens are stateless. This endpoint is a placeholder
    for future token blacklist implementation.
    """
    # For now, this is a no-op since JWTs are stateless
    # In production, you might want to implement token blacklisting
    return success_response(message="Logout successful")


@router.get("/profile", summary="Get user profile")
async def get_user_profile(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的完整 Profile 信息
    
    Returns:
        - user_id: 用户唯一标识
        - display_name: 显示名称
        - introduction: 用户简介
        - avatar_url: 头像 URL
        - email: 邮箱
        - created_at: 创建时间
        - updated_at: 更新时间
    """
    user = await user_service.get_user_info(db=db, user_id=current_user_id)
    return success_response(data=UserProfileResponse.model_validate(user).model_dump())


@router.put("/profile", summary="Update user profile")
async def update_user_profile(
    request: UserProfileUpdateRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前用户的 Profile 信息
    
    Request Body:
        - display_name: 显示名称 (可选, 最大100字符)
        - introduction: 用户简介 (可选, 最大500字符)
    
    Returns:
        更新后的用户 Profile
    """
    user = await user_service.update_profile(
        db=db,
        user_id=current_user_id,
        display_name=request.display_name,
        introduction=request.introduction
    )
    return success_response(data=UserProfileResponse.model_validate(user).model_dump())



