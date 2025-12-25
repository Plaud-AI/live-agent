from datetime import datetime
from enum import Enum
from typing import Optional, List, Tuple
from sqlalchemy import String, Text, TIMESTAMP, ForeignKey, Index, select, func, update
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB

from infra.database import Base, utc_now


# ==================== Enums ====================

class VoiceCategory(str, Enum):
    """Voice category enum"""
    CLONE = "clone"       # User cloned voice
    LIBRARY = "library"   # Preset voice library


class VoiceProvider(str, Enum):
    """TTS provider enum"""
    FISHSPEECH = "fishspeech"
    MINIMAX = "minimax"


class GenderTag(str, Enum):
    """Gender tag for filtering"""
    MALE = "male"
    FEMALE = "female"


class AgeTag(str, Enum):
    """Age tag for filtering"""
    YOUTH = "youth"
    YOUNG_ADULT = "young_adult"
    ADULT = "adult"
    MIDDLE_AGED = "middle_aged"
    SENIOR = "senior"


# System user ID for voice library voices
SYSTEM_VOICE_LIBRARY_OWNER = "system_voice_library"


# ==================== ORM Model ====================

class VoiceModel(Base):
    __tablename__ = "voices"

    # Primary key (auto increment)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Business primary key (voice_{ulid} format)
    voice_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    
    # Provider-specific voice ID (Fish Audio ID, MiniMax ID, etc.)
    reference_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Foreign key to user table (user_id) - system user for library voices
    owner_id: Mapped[str] = mapped_column(
        String(50), 
        ForeignKey("user.user_id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # Voice category: clone or library
    category: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default=VoiceCategory.CLONE.value
    )
    
    # TTS provider: fishspeech or minimax
    provider: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default=VoiceProvider.FISHSPEECH.value
    )
    
    # Voice info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    desc: Mapped[str] = mapped_column(Text, nullable=False)
    
    # JSONB tags for filtering: {gender, age, language, style, accent, description}
    tags: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    
    # Audio sample information
    sample_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    
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
        Index('idx_voices_reference_id', 'reference_id'),
        Index('idx_voices_owner_id', 'owner_id'),
        Index('idx_voices_category', 'category'),
        Index('idx_voices_provider', 'provider'),
        Index('idx_voices_created_at', 'created_at'),
        Index('idx_voices_library_lookup', 'category', 'provider'),
    )

    def __repr__(self):
        return f"<VoiceModel(id={self.id}, voice_id={self.voice_id}, name={self.name})>"


# ==================== Repository (CRUD Operations) ====================

class Voice:
    """
    Voice Repository - Handles all database operations
    """
    
    @staticmethod
    async def get_by_voice_id(db: AsyncSession, voice_id: str) -> Optional[VoiceModel]:
        """Get voice by voice_id (business key)"""
        result = await db.execute(
            select(VoiceModel).where(VoiceModel.voice_id == voice_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_reference_id(db: AsyncSession, reference_id: str) -> Optional[VoiceModel]:
        """Get voice by provider's reference_id"""
        result = await db.execute(
            select(VoiceModel).where(VoiceModel.reference_id == reference_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_list(
        db: AsyncSession,
        owner_id: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 100
    ) -> Tuple[List[VoiceModel], Optional[str], bool]:
        """
        Get voices with cursor-based pagination
        
        Args:
            db: Database session
            owner_id: Filter by owner ID
            cursor: ISO datetime string of last item's created_at
            limit: Number of items to return
            
        Returns:
            (voices, next_cursor, has_more)
        """
        query = select(VoiceModel)
        
        if owner_id:
            # All voices accessible by user 
            query = query.where(
                VoiceModel.owner_id == owner_id
            )
        
        # Apply cursor filter if provided
        if cursor:
            try:
                cursor_time = datetime.fromisoformat(cursor)
                # Get records created before cursor time
                query = query.where(VoiceModel.created_at < cursor_time)
            except (ValueError, TypeError):
                # Invalid cursor, ignore and start from beginning
                pass
        
        # Order by created_at DESC, voice_id DESC for stable sorting
        # Fetch limit + 1 to check if there are more records
        query = query.order_by(
            VoiceModel.created_at.desc(),
            VoiceModel.voice_id.desc()
        ).limit(limit + 1)
        
        result = await db.execute(query)
        voices = list(result.scalars().all())
        
        # Check if there are more records
        has_more = len(voices) > limit
        if has_more:
            voices = voices[:limit]
        
        # Generate next cursor from last item
        next_cursor = None
        if has_more and voices:
            next_cursor = voices[-1].created_at.isoformat()
        
        return voices, next_cursor, has_more
    
    @staticmethod
    async def get_library_voices(
        db: AsyncSession,
        gender: Optional[str] = None,
        age: Optional[str] = None,
        language: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20
    ) -> Tuple[List[VoiceModel], Optional[str], bool]:
        """
        Get voice library voices with tag filtering and cursor pagination
        
        Args:
            db: Database session
            gender: Filter by gender tag (male/female)
            age: Filter by age tag (youth/young_adult/adult/middle_aged/senior)
            language: Filter by language tag (en/zh/ja/etc.)
            cursor: voice_id string for pagination (ULID-based, lexicographically sortable)
            limit: Number of items to return
            
        Returns:
            (voices, next_cursor, has_more)
        """
        query = select(VoiceModel).where(
            VoiceModel.category == VoiceCategory.LIBRARY.value
        )
        
        # Apply tag filters using JSONB operators
        if gender:
            query = query.where(VoiceModel.tags['gender'].astext == gender)
        if age:
            query = query.where(VoiceModel.tags['age'].astext == age)
        if language:
            query = query.where(VoiceModel.tags['language'].astext == language)
        
        # Apply cursor filter (voice_id based - lexicographic comparison)
        if cursor:
            query = query.where(VoiceModel.voice_id < cursor)
        
        # Order by voice_id DESC for stable pagination (ULID is time-ordered)
        query = query.order_by(
            VoiceModel.voice_id.desc()
        ).limit(limit + 1)
        
        result = await db.execute(query)
        voices = list(result.scalars().all())
        
        has_more = len(voices) > limit
        if has_more:
            voices = voices[:limit]
        
        next_cursor = None
        if has_more and voices:
            next_cursor = voices[-1].voice_id
        
        return voices, next_cursor, has_more
    
    @staticmethod
    async def count(
        db: AsyncSession,
        owner_id: Optional[str] = None
    ) -> int:
        """Count voices with owner_id"""
        stmt = (
            select(func.count())
            .select_from(VoiceModel)
            .where(VoiceModel.owner_id == owner_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def get_by_voice_and_owner(
        db: AsyncSession,
        voice_id: str,
        owner_id: str
    ) -> Optional[VoiceModel]:
        """Get voice by voice_id and owner_id"""
        stmt = (
            select(VoiceModel)
            .where(VoiceModel.voice_id == voice_id)
            .where(VoiceModel.owner_id == owner_id)
        )

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        db: AsyncSession,
        voice_id: str,
        owner_id: str,
        name: str,
        desc: str,
        reference_id: Optional[str] = None,
        category: str = VoiceCategory.CLONE.value,
        provider: str = VoiceProvider.FISHSPEECH.value,
        tags: Optional[dict] = None,
        sample_url: Optional[str] = None,
        sample_text: Optional[str] = None
    ) -> VoiceModel:
        """Create a new voice"""
        voice = VoiceModel(
            voice_id=voice_id,
            reference_id=reference_id,
            owner_id=owner_id,
            name=name,
            desc=desc,
            category=category,
            provider=provider,
            tags=tags or {},
            sample_url=sample_url,
            sample_text=sample_text
        )
        db.add(voice)
        await db.commit()
        await db.refresh(voice)
        return voice
    
    @staticmethod
    async def update(
        db: AsyncSession,
        voice_id: str,
        owner_id: str,
        name: Optional[str] = None,
        desc: Optional[str] = None
    ) -> VoiceModel:
        """Update a voice (only updates provided fields)"""
        # Build update values dict with only non-None values
        update_values = {}
        if name is not None:
            update_values['name'] = name
        if desc is not None:
            update_values['desc'] = desc
        
        # If no fields to update, just return the existing voice
        if not update_values:
            voice = await Voice.get_by_voice_and_owner(db, voice_id, owner_id)
            return voice
        
        stmt = (
            update(VoiceModel)
            .where(VoiceModel.voice_id == voice_id)
            .where(VoiceModel.owner_id == owner_id)
            .values(**update_values)
            .returning(VoiceModel)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one()
    
    @staticmethod
    async def delete(
        db: AsyncSession,
        voice_id: str,
        owner_id: str
    ) -> bool:
        """
        Delete a voice (only if owned by user)
        
        Returns:
            True if deleted, False if not found or not owned
        """
        result = await db.execute(
            select(VoiceModel).where(
                VoiceModel.voice_id == voice_id,
                VoiceModel.owner_id == owner_id
            )
        )
        voice = result.scalar_one_or_none()
        
        if not voice:
            return False
        
        await db.delete(voice)
        await db.commit()
        return True
