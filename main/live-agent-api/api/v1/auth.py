"""Authentication API routes for multi-provider authentication"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from infra import get_db
from services.auth_service import auth_service
from utils.response import success_response
from api.auth import get_current_user_id
from schemas.auth import (
    EmailRegisterRequest,
    EmailLoginRequest,
    EmailVerifyRequest,
    ResendVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    GoogleLoginRequest,
    AppleLoginRequest,
    FirebaseLoginRequest,
    RefreshTokenRequest,
)

router = APIRouter()


def _get_device_info(request: Request) -> dict:
    """Extract device info from request"""
    return {
        "user_agent": request.headers.get("user-agent"),
        "ip": request.client.host if request.client else None,
        "platform": request.headers.get("sec-ch-ua-platform"),
    }


# ==================== Email Authentication ====================

@router.post("/email/register", summary="Register with email")
async def register_with_email(
    request: EmailRegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user with email and password.
    
    A verification email will be sent to complete the registration.
    
    - **email**: Valid email address
    - **password**: 8-128 characters
    - **display_name**: Optional display name
    """
    result = await auth_service.register_with_email(
        db=db,
        email=request.email,
        password=request.password,
        display_name=request.display_name
    )
    return success_response(data=result)


@router.post("/email/login", summary="Login with email")
async def login_with_email(
    request: EmailLoginRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.
    
    Returns access token and refresh token.
    Email must be verified before login.
    """
    device_info = _get_device_info(http_request)
    result = await auth_service.login_with_email(
        db=db,
        email=request.email,
        password=request.password,
        device_info=device_info
    )
    return success_response(data=result.model_dump())


@router.post("/email/verify", summary="Verify email address")
async def verify_email(
    request: EmailVerifyRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify email address with verification token.
    
    The token is sent to the user's email during registration.
    """
    result = await auth_service.verify_email(
        db=db,
        token=request.token
    )
    return success_response(data=result)


@router.post("/email/resend-verification", summary="Resend verification email")
async def resend_verification(
    request: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Resend email verification link.
    
    Only works for unverified accounts.
    """
    result = await auth_service.resend_verification_email(
        db=db,
        email=request.email
    )
    return success_response(data=result)


@router.post("/email/forgot-password", summary="Request password reset")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request a password reset email.
    
    For security, always returns success even if email doesn't exist.
    """
    result = await auth_service.forgot_password(
        db=db,
        email=request.email
    )
    return success_response(data=result)


@router.post("/email/reset-password", summary="Reset password")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password with reset token.
    
    The token is sent to the user's email from forgot-password request.
    """
    result = await auth_service.reset_password(
        db=db,
        token=request.token,
        new_password=request.new_password
    )
    return success_response(data=result)


# ==================== Google OAuth ====================

@router.post("/google/login", summary="Login with Google")
async def login_with_google(
    request: GoogleLoginRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login or register with Google Sign-In.
    
    Requires ID token from Google Sign-In SDK.
    Will create a new account if one doesn't exist.
    """
    device_info = _get_device_info(http_request)
    result = await auth_service.login_with_google(
        db=db,
        id_token=request.id_token,
        device_info=device_info
    )
    return success_response(data=result.model_dump())


# ==================== Apple OAuth ====================

@router.post("/apple/login", summary="Login with Apple")
async def login_with_apple(
    request: AppleLoginRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login or register with Sign in with Apple.
    
    Requires ID token from Sign in with Apple SDK.
    Will create a new account if one doesn't exist.
    
    Note: User info (name) is only provided by Apple on first sign-in.
    """
    device_info = _get_device_info(http_request)
    result = await auth_service.login_with_apple(
        db=db,
        id_token=request.id_token,
        user_info=request.user_info,
        device_info=device_info
    )
    return success_response(data=result.model_dump())


# ==================== Firebase Authentication ====================

@router.post("/firebase/login", summary="Login with Firebase")
async def login_with_firebase(
    request: FirebaseLoginRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login or register with Firebase Authentication.
    
    Supports all Firebase auth providers (Email, Google, Apple).
    Requires Firebase ID token from Firebase Auth SDK.
    Will create a new account if one doesn't exist.
    
    - **firebase_token**: Firebase ID token from client SDK
    - **provider**: Optional hint ('email', 'google', 'apple') - auto-detected from token
    """
    device_info = _get_device_info(http_request)
    result = await auth_service.login_with_firebase(
        db=db,
        firebase_token=request.firebase_token,
        provider_hint=request.provider,
        device_info=device_info
    )
    return success_response(data=result.model_dump())


# ==================== Token Management ====================

@router.post("/refresh", summary="Refresh access token")
async def refresh_token(
    request: RefreshTokenRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Returns new access token and new refresh token.
    The old refresh token will be invalidated.
    """
    device_info = _get_device_info(http_request)
    result = await auth_service.refresh_access_token(
        db=db,
        refresh_token=request.refresh_token,
        device_info=device_info
    )
    return success_response(data=result.model_dump())


@router.post("/logout", summary="Logout")
async def logout(
    request: RefreshTokenRequest,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout and invalidate refresh token.
    """
    result = await auth_service.logout(
        db=db,
        refresh_token=request.refresh_token
    )
    return success_response(data=result)


@router.post("/logout/all", summary="Logout from all devices")
async def logout_all(
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout from all devices by invalidating all refresh tokens.
    """
    result = await auth_service.logout(
        db=db,
        user_id=current_user_id,
        logout_all=True
    )
    return success_response(data=result)


