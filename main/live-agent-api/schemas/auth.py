"""Authentication schemas for OAuth and email login"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, EmailStr


# ==================== Request Schemas ====================

class EmailRegisterRequest(BaseModel):
    """Email registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)


class EmailLoginRequest(BaseModel):
    """Email login request"""
    email: EmailStr
    password: str


class EmailVerifyRequest(BaseModel):
    """Email verification request"""
    token: str


class ResendVerificationRequest(BaseModel):
    """Resend verification email request"""
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    """Forgot password request"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


class GoogleLoginRequest(BaseModel):
    """Google OAuth login request"""
    id_token: str  # ID token from Google Sign-In


class AppleLoginRequest(BaseModel):
    """Apple OAuth login request"""
    id_token: str  # ID token from Sign in with Apple
    authorization_code: Optional[str] = None
    user_info: Optional[dict] = None  # First-time user info from Apple


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class FirebaseLoginRequest(BaseModel):
    """Firebase authentication login request"""
    firebase_token: str  # Firebase ID token from client
    provider: Optional[str] = None  # Optional: 'email', 'google', 'apple' (auto-detected from token)


# ==================== Response Schemas ====================

class AuthUserInfo(BaseModel):
    """Authenticated user information"""
    user_id: str
    email: Optional[str] = None
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    email_verified: bool = False
    auth_provider: Literal["email", "google", "apple", "firebase"]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuthTokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds
    user: AuthUserInfo


class SimpleMessageResponse(BaseModel):
    """Simple message response"""
    message: str


class EmailVerificationStatus(BaseModel):
    """Email verification status"""
    email: str
    verified: bool
    message: str


# ==================== OAuth Provider User Info ====================

class GoogleUserInfo(BaseModel):
    """User info from Google OAuth"""
    sub: str  # Google user ID
    email: str
    email_verified: bool
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None


class AppleUserInfo(BaseModel):
    """User info from Apple Sign In"""
    sub: str  # Apple user ID
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    is_private_email: Optional[bool] = None
    name: Optional[str] = None  # Only available on first sign-in


# ==================== Internal Schemas ====================

class OAuthProviderData(BaseModel):
    """OAuth provider data stored in database"""
    provider: Literal["google", "apple", "email", "firebase"]
    provider_user_id: str
    provider_email: Optional[str] = None
    raw_data: Optional[dict] = None


class FirebaseUserInfo(BaseModel):
    """User info from Firebase ID token"""
    uid: str  # Firebase UID
    email: Optional[str] = None
    email_verified: bool = False
    name: Optional[str] = None
    picture: Optional[str] = None
    provider: str = "firebase"  # The original sign-in provider


