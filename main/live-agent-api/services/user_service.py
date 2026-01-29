from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from repositories import UserModel, User
from utils.exceptions import NotFoundException, ConflictException, UnauthorizedException
from utils.security import hash_password, verify_password, generate_jwt_token
from utils.ulid import generate_user_id
from schemas.user import LoginResponse, UserInfo
from config import settings


class UserService:
    """User service layer"""
    
    async def register(
        self, 
        db: AsyncSession, 
        username: str, 
        password: str
    ) -> None:
        """
        Register a new user
        
        Args:
            db: Database session
            username: Username
            password: Plain text password
            
        Raises:
            ConflictException: If username is already taken
        """
        # Check if username is taken
        if await User.is_username_taken(db, username):
            raise ConflictException("Username already exists")
        
        # Hash password
        hashed_password = hash_password(password)
        
        # Generate user_id
        user_id = generate_user_id()
        
        # Create user
        await User.create(
            db=db,
            user_id=user_id,
            username=username,
            hashed_password=hashed_password
        )
    
    async def login(
        self, 
        db: AsyncSession, 
        username: str, 
        password: str
    ) -> LoginResponse:
        """
        Login user and return JWT token
        
        Args:
            db: Database session
            username: Username
            password: Plain text password
            
        Returns:
            LoginResponse with token and user info
            
        Raises:
            UnauthorizedException: If credentials are invalid
        """
        # Get user by username
        user = await User.get_by_username(db, username)
        if not user:
            raise UnauthorizedException("Invalid username or password")
        
        # Verify password
        if not verify_password(password, user.password):
            raise UnauthorizedException("Invalid username or password")
        
        # Generate JWT token
        token = generate_jwt_token(user.user_id, user.username)
        
        # Calculate expire time in seconds
        expire_seconds = settings.TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        
        # Build user info
        user_info = UserInfo(
            user_id=user.user_id,
            username=user.username,
            created_at=user.created_at
        )
        
        return LoginResponse(
            token=token,
            expire=expire_seconds,
            user=user_info
        )
    
    async def logout(self, db: AsyncSession, token: str) -> None:
        """
        Logout user (placeholder for token blacklist)
        
        Args:
            db: Database session
            token: JWT token
        """
        # For now, this is a placeholder
        # In production, you might want to implement token blacklisting
        pass
    
    async def update_password(
        self,
        db: AsyncSession,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> None:
        """
        Update user password
        
        Args:
            db: Database session
            user_id: User ID
            old_password: Current password
            new_password: New password
            
        Raises:
            NotFoundException: If user not found
            UnauthorizedException: If old password is incorrect
        """
        # Get user
        user = await User.get_by_user_id(db, user_id)
        if not user:
            raise NotFoundException("User not found")
        
        # Verify old password
        if not verify_password(old_password, user.password):
            raise UnauthorizedException("Current password is incorrect")
        
        # Hash and update new password
        new_hashed_password = hash_password(new_password)
        await User.update_password(db, user_id, new_hashed_password)
    
    async def get_user_info(
        self,
        db: AsyncSession,
        user_id: str
    ) -> UserModel:
        """
        Get user information
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            UserModel
            
        Raises:
            NotFoundException: If user not found
        """
        user = await User.get_by_user_id(db, user_id)
        if not user:
            raise NotFoundException("User not found")
        return user


# Singleton instance
user_service = UserService()



