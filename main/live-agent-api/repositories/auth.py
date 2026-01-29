"""Authentication repositories for OAuth and email verification"""
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Integer, Boolean, TIMESTAMP, Index, select, Text, and_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from infra.database import Base, utc_now


# ==================== ORM Models ====================

class UserOAuthModel(Base):
    """OAuth provider connections for users"""
    __tablename__ = "user_oauth"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        default=utc_now, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        default=utc_now, 
        onupdate=utc_now, 
        nullable=False
    )

    __table_args__ = (
        Index('idx_user_oauth_user_id', 'user_id'),
        Index('idx_user_oauth_provider', 'provider'),
        Index('uk_user_oauth_provider', 'provider', 'provider_user_id', unique=True),
    )


class EmailVerificationTokenModel(Base):
    """Email verification tokens"""
    __tablename__ = "email_verification_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    token_type: Mapped[str] = mapped_column(String(20), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        default=utc_now, 
        nullable=False
    )

    __table_args__ = (
        Index('idx_email_tokens_email', 'email'),
        Index('idx_email_tokens_token', 'token'),
    )


class RefreshTokenModel(Base):
    """Refresh tokens for extended sessions"""
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    device_info: Mapped[dict] = mapped_column(JSONB, default=dict)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        default=utc_now, 
        nullable=False
    )

    __table_args__ = (
        Index('idx_refresh_tokens_user_id', 'user_id'),
        Index('idx_refresh_tokens_token', 'token'),
    )


# ==================== Repositories ====================

class UserOAuth:
    """Repository for OAuth connections"""

    @staticmethod
    async def get_by_provider(
        db: AsyncSession, 
        provider: str, 
        provider_user_id: str
    ) -> Optional[UserOAuthModel]:
        """Get OAuth connection by provider and provider user ID"""
        result = await db.execute(
            select(UserOAuthModel).where(
                and_(
                    UserOAuthModel.provider == provider,
                    UserOAuthModel.provider_user_id == provider_user_id
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user_id(
        db: AsyncSession, 
        user_id: str
    ) -> List[UserOAuthModel]:
        """Get all OAuth connections for a user"""
        result = await db.execute(
            select(UserOAuthModel).where(UserOAuthModel.user_id == user_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: str,
        provider: str,
        provider_user_id: str,
        provider_email: Optional[str] = None,
        provider_data: Optional[dict] = None
    ) -> UserOAuthModel:
        """Create a new OAuth connection"""
        oauth = UserOAuthModel(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=provider_email,
            provider_data=provider_data or {}
        )
        db.add(oauth)
        await db.commit()
        await db.refresh(oauth)
        return oauth

    @staticmethod
    async def delete(db: AsyncSession, user_id: str, provider: str) -> bool:
        """Delete OAuth connection"""
        result = await db.execute(
            select(UserOAuthModel).where(
                and_(
                    UserOAuthModel.user_id == user_id,
                    UserOAuthModel.provider == provider
                )
            )
        )
        oauth = result.scalar_one_or_none()
        if oauth:
            await db.delete(oauth)
            await db.commit()
            return True
        return False


class EmailVerificationToken:
    """Repository for email verification tokens"""

    @staticmethod
    async def get_by_token(
        db: AsyncSession, 
        token: str
    ) -> Optional[EmailVerificationTokenModel]:
        """Get token by token string"""
        result = await db.execute(
            select(EmailVerificationTokenModel).where(
                EmailVerificationTokenModel.token == token
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_valid_token(
        db: AsyncSession, 
        token: str, 
        token_type: str
    ) -> Optional[EmailVerificationTokenModel]:
        """Get valid (not expired, not used) token"""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(EmailVerificationTokenModel).where(
                and_(
                    EmailVerificationTokenModel.token == token,
                    EmailVerificationTokenModel.token_type == token_type,
                    EmailVerificationTokenModel.expires_at > now,
                    EmailVerificationTokenModel.used_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        email: str,
        token: str,
        token_type: str,
        expires_at: datetime,
        user_id: Optional[str] = None
    ) -> EmailVerificationTokenModel:
        """Create a new verification token"""
        verification = EmailVerificationTokenModel(
            user_id=user_id,
            email=email,
            token=token,
            token_type=token_type,
            expires_at=expires_at
        )
        db.add(verification)
        await db.commit()
        await db.refresh(verification)
        return verification

    @staticmethod
    async def mark_used(db: AsyncSession, token: str) -> bool:
        """Mark token as used"""
        token_obj = await EmailVerificationToken.get_by_token(db, token)
        if token_obj:
            token_obj.used_at = datetime.now(timezone.utc)
            await db.commit()
            return True
        return False

    @staticmethod
    async def invalidate_previous_tokens(
        db: AsyncSession, 
        email: str, 
        token_type: str
    ) -> None:
        """Invalidate all previous tokens for an email"""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(EmailVerificationTokenModel).where(
                and_(
                    EmailVerificationTokenModel.email == email,
                    EmailVerificationTokenModel.token_type == token_type,
                    EmailVerificationTokenModel.used_at.is_(None)
                )
            )
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.used_at = now
        await db.commit()


class RefreshToken:
    """Repository for refresh tokens"""

    @staticmethod
    async def get_valid_token(
        db: AsyncSession, 
        token: str
    ) -> Optional[RefreshTokenModel]:
        """Get valid (not expired, not revoked) refresh token"""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(RefreshTokenModel).where(
                and_(
                    RefreshTokenModel.token == token,
                    RefreshTokenModel.expires_at > now,
                    RefreshTokenModel.revoked_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: str,
        token: str,
        expires_at: datetime,
        device_info: Optional[dict] = None
    ) -> RefreshTokenModel:
        """Create a new refresh token"""
        refresh = RefreshTokenModel(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            device_info=device_info or {}
        )
        db.add(refresh)
        await db.commit()
        await db.refresh(refresh)
        return refresh

    @staticmethod
    async def revoke(db: AsyncSession, token: str) -> bool:
        """Revoke a refresh token"""
        result = await db.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.token == token)
        )
        token_obj = result.scalar_one_or_none()
        if token_obj:
            token_obj.revoked_at = datetime.now(timezone.utc)
            await db.commit()
            return True
        return False

    @staticmethod
    async def revoke_all_for_user(db: AsyncSession, user_id: str) -> int:
        """Revoke all refresh tokens for a user"""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(RefreshTokenModel).where(
                and_(
                    RefreshTokenModel.user_id == user_id,
                    RefreshTokenModel.revoked_at.is_(None)
                )
            )
        )
        tokens = result.scalars().all()
        count = 0
        for token in tokens:
            token.revoked_at = now
            count += 1
        await db.commit()
        return count


