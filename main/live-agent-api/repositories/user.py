from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, TIMESTAMP, Index, select, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from infra.database import Base, utc_now


# ==================== ORM Model ====================

class UserModel(Base):
    __tablename__ = "user"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # User unique identifier (external)
    user_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # User credentials and info
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Nullable for OAuth users
    
    # Extended user info for OAuth
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
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
        Index('idx_user_userid', 'user_id', unique=True),
        Index('idx_user_username', 'username', unique=True),
    )

    def __repr__(self):
        return f"<UserModel(id={self.id}, user_id={self.user_id})>"


# ==================== Repository (CRUD Operations) ====================

class User:
    """
    User Repository - Handles all database operations
    """

    @staticmethod
    async def get_by_user_id(db: AsyncSession, user_id: str) -> Optional[UserModel]:
        """Get user by user_id"""
        result = await db.execute(select(UserModel).where(UserModel.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[UserModel]:
        """Get user by username"""
        result = await db.execute(select(UserModel).where(UserModel.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: str,
        username: str,
        hashed_password: str
    ) -> UserModel:
        """Create a new user"""
        user = UserModel(
            user_id=user_id,
            username=username,
            password=hashed_password,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update_password(
        db: AsyncSession,
        user_id: str,
        new_hashed_password: str
    ) -> Optional[UserModel]:
        """Update user password"""
        user = await User.get_by_user_id(db, user_id)
        if not user:
            return None
        
        user.password = new_hashed_password
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def is_username_taken(db: AsyncSession, username: str) -> bool:
        """Check if username is already taken"""
        user = await User.get_by_username(db, username)
        return user is not None

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[UserModel]:
        """Get user by email"""
        result = await db.execute(select(UserModel).where(UserModel.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def is_email_taken(db: AsyncSession, email: str) -> bool:
        """Check if email is already taken"""
        user = await User.get_by_email(db, email)
        return user is not None

    @staticmethod
    async def create_oauth_user(
        db: AsyncSession,
        user_id: str,
        username: str,
        email: Optional[str] = None,
        email_verified: bool = False,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> UserModel:
        """Create a new OAuth user (no password)"""
        user = UserModel(
            user_id=user_id,
            username=username,
            password=None,
            email=email,
            email_verified=email_verified,
            display_name=display_name,
            avatar_url=avatar_url
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def create_email_user(
        db: AsyncSession,
        user_id: str,
        username: str,
        email: str,
        hashed_password: str,
        display_name: Optional[str] = None
    ) -> UserModel:
        """Create a new user with email and password"""
        user = UserModel(
            user_id=user_id,
            username=username,
            email=email,
            password=hashed_password,
            email_verified=False,
            display_name=display_name
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def verify_email(db: AsyncSession, user_id: str) -> Optional[UserModel]:
        """Mark user's email as verified"""
        user = await User.get_by_user_id(db, user_id)
        if not user:
            return None
        user.email_verified = True
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        user_id: str,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Optional[UserModel]:
        """Update user profile"""
        user = await User.get_by_user_id(db, user_id)
        if not user:
            return None
        if display_name is not None:
            user.display_name = display_name
        if avatar_url is not None:
            user.avatar_url = avatar_url
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update_display_name(
        db: AsyncSession,
        user_id: str,
        display_name: str
    ) -> Optional[UserModel]:
        """Update user display name"""
        user = await User.get_by_user_id(db, user_id)
        if not user:
            return None
        user.display_name = display_name
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update_avatar_url(
        db: AsyncSession,
        user_id: str,
        avatar_url: str
    ) -> Optional[UserModel]:
        """Update user avatar URL"""
        user = await User.get_by_user_id(db, user_id)
        if not user:
            return None
        user.avatar_url = avatar_url
        await db.commit()
        await db.refresh(user)
        return user


