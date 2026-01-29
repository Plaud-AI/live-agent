"""Authentication service for multi-provider authentication"""
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Literal
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.user import UserModel, User
from repositories.auth import (
    UserOAuth, UserOAuthModel,
    EmailVerificationToken, EmailVerificationTokenModel,
    RefreshToken, RefreshTokenModel
)
from infra.oauth import google_oauth, apple_oauth
from infra.email import email_service
from infra.firebase import firebase_auth, FirebaseUserInfo
from utils.exceptions import (
    NotFoundException, ConflictException, 
    UnauthorizedException, BadRequestException
)
from utils.security import hash_password, verify_password, generate_jwt_token
from utils.ulid import generate_user_id
from schemas.auth import (
    AuthTokenResponse, AuthUserInfo,
    GoogleUserInfo, AppleUserInfo
)
from config import settings


class AuthService:
    """Authentication service supporting multiple providers"""
    
    # ==================== Token Generation ====================
    
    def _generate_tokens(
        self, 
        user: UserModel, 
        provider: Literal["email", "google", "apple", "firebase"]
    ) -> tuple[str, str, int]:
        """Generate access token and refresh token"""
        # Access token
        access_token = generate_jwt_token(user.user_id, user.username)
        
        # Refresh token - random string
        refresh_token = secrets.token_urlsafe(32)
        
        # Expiry in seconds
        expires_in = settings.TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        
        return access_token, refresh_token, expires_in
    
    def _build_auth_response(
        self,
        user: UserModel,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        provider: Literal["email", "google", "apple", "firebase"]
    ) -> AuthTokenResponse:
        """Build authentication response"""
        user_info = AuthUserInfo(
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            email_verified=user.email_verified,
            auth_provider=provider,
            created_at=user.created_at
        )
        
        return AuthTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            user=user_info
        )
    
    async def _save_refresh_token(
        self,
        db: AsyncSession,
        user_id: str,
        refresh_token: str,
        device_info: Optional[dict] = None
    ) -> None:
        """Save refresh token to database"""
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await RefreshToken.create(
            db=db,
            user_id=user_id,
            token=refresh_token,
            expires_at=expires_at,
            device_info=device_info
        )
    
    # ==================== Email Authentication ====================
    
    async def register_with_email(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        display_name: Optional[str] = None
    ) -> dict:
        """Register a new user with email and password"""
        # Check if email is taken
        if await User.is_email_taken(db, email):
            raise ConflictException("Email already registered")
        
        # Generate user ID and username
        user_id = generate_user_id()
        username = f"user_{user_id[-8:]}"  # Use last 8 chars of user_id
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Create user
        user = await User.create_email_user(
            db=db,
            user_id=user_id,
            username=username,
            email=email,
            hashed_password=hashed_password,
            display_name=display_name
        )
        
        # Create OAuth record for email provider
        await UserOAuth.create(
            db=db,
            user_id=user_id,
            provider="email",
            provider_user_id=email,
            provider_email=email
        )
        
        # Generate verification token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS
        )
        
        await EmailVerificationToken.create(
            db=db,
            email=email,
            token=token,
            token_type="verification",
            expires_at=expires_at,
            user_id=user_id
        )
        
        # Send verification email
        await email_service.send_verification_email(
            to_email=email,
            verification_token=token,
            user_name=display_name
        )
        
        return {
            "message": "Registration successful. Please check your email to verify your account.",
            "email": email
        }
    
    async def login_with_email(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        device_info: Optional[dict] = None
    ) -> AuthTokenResponse:
        """Login with email and password"""
        # Get user by email
        user = await User.get_by_email(db, email)
        if not user:
            raise UnauthorizedException("Invalid email or password")
        
        # Check if user has password (might be OAuth-only user)
        if not user.password:
            raise UnauthorizedException(
                "This account uses social login. Please sign in with Google or Apple."
            )
        
        # Verify password
        if not verify_password(password, user.password):
            raise UnauthorizedException("Invalid email or password")
        
        # Check email verification
        if not user.email_verified:
            raise UnauthorizedException(
                "Please verify your email address before logging in"
            )
        
        # Generate tokens
        access_token, refresh_token, expires_in = self._generate_tokens(user, "email")
        
        # Save refresh token
        await self._save_refresh_token(db, user.user_id, refresh_token, device_info)
        
        return self._build_auth_response(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            provider="email"
        )
    
    async def verify_email(
        self,
        db: AsyncSession,
        token: str
    ) -> dict:
        """Verify email with token"""
        # Get valid token
        token_obj = await EmailVerificationToken.get_valid_token(
            db, token, "verification"
        )
        
        if not token_obj:
            raise BadRequestException("Invalid or expired verification token")
        
        # Mark email as verified
        if token_obj.user_id:
            await User.verify_email(db, token_obj.user_id)
        
        # Mark token as used
        await EmailVerificationToken.mark_used(db, token)
        
        return {
            "message": "Email verified successfully",
            "email": token_obj.email
        }
    
    async def resend_verification_email(
        self,
        db: AsyncSession,
        email: str
    ) -> dict:
        """Resend verification email"""
        user = await User.get_by_email(db, email)
        if not user:
            # Don't reveal if email exists
            return {"message": "If the email exists, a verification link has been sent"}
        
        if user.email_verified:
            raise BadRequestException("Email is already verified")
        
        # Invalidate previous tokens
        await EmailVerificationToken.invalidate_previous_tokens(
            db, email, "verification"
        )
        
        # Generate new token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS
        )
        
        await EmailVerificationToken.create(
            db=db,
            email=email,
            token=token,
            token_type="verification",
            expires_at=expires_at,
            user_id=user.user_id
        )
        
        # Send verification email
        await email_service.send_verification_email(
            to_email=email,
            verification_token=token,
            user_name=user.display_name
        )
        
        return {"message": "Verification email sent"}
    
    async def forgot_password(
        self,
        db: AsyncSession,
        email: str
    ) -> dict:
        """Send password reset email"""
        user = await User.get_by_email(db, email)
        
        # Always return success to prevent email enumeration
        if not user:
            return {"message": "If the email exists, a password reset link has been sent"}
        
        # Check if user has password (OAuth users can't reset password)
        if not user.password:
            return {"message": "If the email exists, a password reset link has been sent"}
        
        # Invalidate previous reset tokens
        await EmailVerificationToken.invalidate_previous_tokens(
            db, email, "password_reset"
        )
        
        # Generate reset token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=settings.PASSWORD_RESET_EXPIRE_HOURS
        )
        
        await EmailVerificationToken.create(
            db=db,
            email=email,
            token=token,
            token_type="password_reset",
            expires_at=expires_at,
            user_id=user.user_id
        )
        
        # Send password reset email
        await email_service.send_password_reset_email(
            to_email=email,
            reset_token=token,
            user_name=user.display_name
        )
        
        return {"message": "If the email exists, a password reset link has been sent"}
    
    async def reset_password(
        self,
        db: AsyncSession,
        token: str,
        new_password: str
    ) -> dict:
        """Reset password with token"""
        # Get valid token
        token_obj = await EmailVerificationToken.get_valid_token(
            db, token, "password_reset"
        )
        
        if not token_obj or not token_obj.user_id:
            raise BadRequestException("Invalid or expired reset token")
        
        # Hash new password
        hashed_password = hash_password(new_password)
        
        # Update password
        await User.update_password(db, token_obj.user_id, hashed_password)
        
        # Mark token as used
        await EmailVerificationToken.mark_used(db, token)
        
        # Revoke all refresh tokens for security
        await RefreshToken.revoke_all_for_user(db, token_obj.user_id)
        
        return {"message": "Password reset successfully"}
    
    # ==================== Google OAuth ====================
    
    async def login_with_google(
        self,
        db: AsyncSession,
        id_token: str,
        device_info: Optional[dict] = None
    ) -> AuthTokenResponse:
        """Login or register with Google"""
        # Verify Google ID token
        google_user = await google_oauth.verify_id_token(id_token)
        if not google_user:
            raise UnauthorizedException("Invalid Google token")
        
        # Check if OAuth connection exists
        oauth_conn = await UserOAuth.get_by_provider(
            db, "google", google_user.sub
        )
        
        if oauth_conn:
            # Existing user - get user and login
            user = await User.get_by_user_id(db, oauth_conn.user_id)
            if not user:
                raise NotFoundException("User not found")
        else:
            # New user - check if email already exists
            existing_user = await User.get_by_email(db, google_user.email)
            
            if existing_user:
                # Link Google account to existing user
                user = existing_user
                await UserOAuth.create(
                    db=db,
                    user_id=user.user_id,
                    provider="google",
                    provider_user_id=google_user.sub,
                    provider_email=google_user.email,
                    provider_data=google_user.model_dump()
                )
                # Update email verification status
                if google_user.email_verified and not user.email_verified:
                    await User.verify_email(db, user.user_id)
            else:
                # Create new user
                user_id = generate_user_id()
                username = f"google_{user_id[-8:]}"
                
                user = await User.create_oauth_user(
                    db=db,
                    user_id=user_id,
                    username=username,
                    email=google_user.email,
                    email_verified=google_user.email_verified,
                    display_name=google_user.name,
                    avatar_url=google_user.picture
                )
                
                # Create OAuth connection
                await UserOAuth.create(
                    db=db,
                    user_id=user_id,
                    provider="google",
                    provider_user_id=google_user.sub,
                    provider_email=google_user.email,
                    provider_data=google_user.model_dump()
                )
        
        # Generate tokens
        access_token, refresh_token, expires_in = self._generate_tokens(user, "google")
        
        # Save refresh token
        await self._save_refresh_token(db, user.user_id, refresh_token, device_info)
        
        return self._build_auth_response(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            provider="google"
        )
    
    # ==================== Apple OAuth ====================
    
    async def login_with_apple(
        self,
        db: AsyncSession,
        id_token: str,
        user_info: Optional[dict] = None,
        device_info: Optional[dict] = None
    ) -> AuthTokenResponse:
        """Login or register with Apple"""
        # Verify Apple ID token
        apple_user = await apple_oauth.verify_id_token(id_token, user_info)
        if not apple_user:
            raise UnauthorizedException("Invalid Apple token")
        
        # Check if OAuth connection exists
        oauth_conn = await UserOAuth.get_by_provider(
            db, "apple", apple_user.sub
        )
        
        if oauth_conn:
            # Existing user - get user and login
            user = await User.get_by_user_id(db, oauth_conn.user_id)
            if not user:
                raise NotFoundException("User not found")
        else:
            # New user
            user_id = generate_user_id()
            username = f"apple_{user_id[-8:]}"
            
            # Apple may not provide email if user chose to hide it
            email = apple_user.email
            email_verified = apple_user.email_verified if apple_user.email_verified is not None else False
            
            # Check if email exists and link accounts
            if email:
                existing_user = await User.get_by_email(db, email)
                if existing_user:
                    user = existing_user
                    await UserOAuth.create(
                        db=db,
                        user_id=user.user_id,
                        provider="apple",
                        provider_user_id=apple_user.sub,
                        provider_email=email,
                        provider_data=apple_user.model_dump()
                    )
                    if email_verified and not user.email_verified:
                        await User.verify_email(db, user.user_id)
                else:
                    # Create new user
                    user = await User.create_oauth_user(
                        db=db,
                        user_id=user_id,
                        username=username,
                        email=email,
                        email_verified=email_verified,
                        display_name=apple_user.name
                    )
                    
                    await UserOAuth.create(
                        db=db,
                        user_id=user_id,
                        provider="apple",
                        provider_user_id=apple_user.sub,
                        provider_email=email,
                        provider_data=apple_user.model_dump()
                    )
            else:
                # No email provided - create user without email
                user = await User.create_oauth_user(
                    db=db,
                    user_id=user_id,
                    username=username,
                    display_name=apple_user.name
                )
                
                await UserOAuth.create(
                    db=db,
                    user_id=user_id,
                    provider="apple",
                    provider_user_id=apple_user.sub,
                    provider_data=apple_user.model_dump()
                )
        
        # Generate tokens
        access_token, refresh_token, expires_in = self._generate_tokens(user, "apple")
        
        # Save refresh token
        await self._save_refresh_token(db, user.user_id, refresh_token, device_info)
        
        return self._build_auth_response(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            provider="apple"
        )
    
    # ==================== Firebase Authentication ====================
    
    async def login_with_firebase(
        self,
        db: AsyncSession,
        firebase_token: str,
        provider_hint: Optional[str] = None,
        device_info: Optional[dict] = None
    ) -> AuthTokenResponse:
        """
        Login or register with Firebase Authentication.
        
        This method verifies the Firebase ID token and creates/updates the user
        in our database. It supports all Firebase auth providers (email, Google, Apple).
        
        Args:
            db: Database session
            firebase_token: Firebase ID token from the client
            provider_hint: Optional provider hint ('email', 'google', 'apple')
            device_info: Optional device information
            
        Returns:
            AuthTokenResponse with access token and user info
        """
        # Verify Firebase ID token
        firebase_user = await firebase_auth.verify_id_token(firebase_token)
        if not firebase_user:
            raise UnauthorizedException("Invalid Firebase token")
        
        # Determine the effective provider
        # Use the provider from Firebase token, or fallback to hint
        effective_provider = firebase_user.provider
        if effective_provider == "firebase" and provider_hint:
            effective_provider = provider_hint
        
        # Map provider to our internal format
        internal_provider: Literal["email", "google", "apple", "firebase"] = "firebase"
        if effective_provider in ["email", "password"]:
            internal_provider = "email"
        elif effective_provider == "google":
            internal_provider = "google"
        elif effective_provider == "apple":
            internal_provider = "apple"
        
        # Check if OAuth connection exists (using Firebase UID)
        oauth_conn = await UserOAuth.get_by_provider(
            db, "firebase", firebase_user.uid
        )
        
        if oauth_conn:
            # Existing user - get user and login
            user = await User.get_by_user_id(db, oauth_conn.user_id)
            if not user:
                raise NotFoundException("User not found")
            
            # Update user info if changed
            if firebase_user.name and user.display_name != firebase_user.name:
                await User.update_display_name(db, user.user_id, firebase_user.name)
                user.display_name = firebase_user.name
            if firebase_user.picture and user.avatar_url != firebase_user.picture:
                await User.update_avatar_url(db, user.user_id, firebase_user.picture)
                user.avatar_url = firebase_user.picture
                
        else:
            # New user - check if email already exists
            existing_user = None
            if firebase_user.email:
                existing_user = await User.get_by_email(db, firebase_user.email)
            
            if existing_user:
                # Link Firebase account to existing user
                user = existing_user
                await UserOAuth.create(
                    db=db,
                    user_id=user.user_id,
                    provider="firebase",
                    provider_user_id=firebase_user.uid,
                    provider_email=firebase_user.email,
                    provider_data={
                        "uid": firebase_user.uid,
                        "email": firebase_user.email,
                        "email_verified": firebase_user.email_verified,
                        "name": firebase_user.name,
                        "picture": firebase_user.picture,
                        "original_provider": firebase_user.provider
                    }
                )
                # Update email verification status
                if firebase_user.email_verified and not user.email_verified:
                    await User.verify_email(db, user.user_id)
            else:
                # Create new user
                user_id = generate_user_id()
                username = f"fb_{user_id[-8:]}"
                
                user = await User.create_oauth_user(
                    db=db,
                    user_id=user_id,
                    username=username,
                    email=firebase_user.email,
                    email_verified=firebase_user.email_verified,
                    display_name=firebase_user.name,
                    avatar_url=firebase_user.picture
                )
                
                # Create OAuth connection
                await UserOAuth.create(
                    db=db,
                    user_id=user_id,
                    provider="firebase",
                    provider_user_id=firebase_user.uid,
                    provider_email=firebase_user.email,
                    provider_data={
                        "uid": firebase_user.uid,
                        "email": firebase_user.email,
                        "email_verified": firebase_user.email_verified,
                        "name": firebase_user.name,
                        "picture": firebase_user.picture,
                        "original_provider": firebase_user.provider
                    }
                )
        
        # Generate tokens
        access_token, refresh_token, expires_in = self._generate_tokens(user, internal_provider)
        
        # Save refresh token
        await self._save_refresh_token(db, user.user_id, refresh_token, device_info)
        
        return self._build_auth_response(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            provider=internal_provider
        )
    
    # ==================== Token Management ====================
    
    async def refresh_access_token(
        self,
        db: AsyncSession,
        refresh_token: str,
        device_info: Optional[dict] = None
    ) -> AuthTokenResponse:
        """Refresh access token using refresh token"""
        # Validate refresh token
        token_obj = await RefreshToken.get_valid_token(db, refresh_token)
        if not token_obj:
            raise UnauthorizedException("Invalid or expired refresh token")
        
        # Get user
        user = await User.get_by_user_id(db, token_obj.user_id)
        if not user:
            raise NotFoundException("User not found")
        
        # Revoke old refresh token
        await RefreshToken.revoke(db, refresh_token)
        
        # Determine provider from OAuth connections
        oauth_conns = await UserOAuth.get_by_user_id(db, user.user_id)
        provider: Literal["email", "google", "apple", "firebase"] = "email"
        if oauth_conns:
            # Use the first non-email provider, or email if that's all there is
            for conn in oauth_conns:
                if conn.provider in ["google", "apple", "firebase"]:
                    provider = conn.provider  # type: ignore
                    break
        
        # Generate new tokens
        access_token, new_refresh_token, expires_in = self._generate_tokens(user, provider)
        
        # Save new refresh token
        await self._save_refresh_token(db, user.user_id, new_refresh_token, device_info)
        
        return self._build_auth_response(
            user=user,
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=expires_in,
            provider=provider
        )
    
    async def logout(
        self,
        db: AsyncSession,
        refresh_token: Optional[str] = None,
        user_id: Optional[str] = None,
        logout_all: bool = False
    ) -> dict:
        """Logout user - revoke refresh token(s)"""
        if logout_all and user_id:
            # Revoke all refresh tokens for user
            count = await RefreshToken.revoke_all_for_user(db, user_id)
            return {"message": f"Logged out from {count} session(s)"}
        elif refresh_token:
            # Revoke specific refresh token
            await RefreshToken.revoke(db, refresh_token)
            return {"message": "Logged out successfully"}
        else:
            return {"message": "No action taken"}


# Singleton instance
auth_service = AuthService()


