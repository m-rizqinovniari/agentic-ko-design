"""
User model untuk SQLAlchemy
"""
from sqlalchemy import Column, String, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """Role user dalam sistem"""
    DESIGNER = "designer"
    VI_USER = "vi_user"  # Visually Impaired User
    RESEARCHER = "researcher"
    ADMIN = "admin"


class User(Base):
    """Model User"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.DESIGNER)

    # Accessibility preferences untuk VI users
    accessibility_preferences = Column(JSON, default={
        "tts_enabled": True,
        "tts_voice": "female",
        "tts_speed": 1.0,
        "stt_enabled": True,
        "high_contrast": False,
        "screen_reader_optimized": True,
        "keyboard_navigation": True,
        "audio_feedback": True
    })

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<User {self.email}>"
