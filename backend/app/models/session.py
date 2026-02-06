"""
Co-Design Session models untuk SQLAlchemy
"""
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class SessionPhase(str, enum.Enum):
    """Fase dalam proses ko-desain"""
    SETUP = "setup"
    SHARED_FRAMING = "shared_framing"
    PERSPECTIVE_EXCHANGE = "perspective_exchange"
    MEANING_NEGOTIATION = "meaning_negotiation"
    REFLECTION_ITERATION = "reflection_iteration"
    COMPLETE = "complete"


class ExperimentMode(str, enum.Enum):
    """Mode experiment untuk penelitian"""
    WITH_AI = "with_ai"
    WITHOUT_AI = "without_ai"
    CONTROL = "control"


class ParticipantRole(str, enum.Enum):
    """Role participant dalam session"""
    DESIGNER = "designer"
    VI_USER = "vi_user"
    AI_AGENT = "ai_agent"
    OBSERVER = "observer"


class CoDesignSession(Base):
    """Model untuk Co-Design Session"""
    __tablename__ = "codesign_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Current phase dalam proses ko-desain
    current_phase = Column(
        SQLEnum(SessionPhase),
        nullable=False,
        default=SessionPhase.SETUP
    )

    # Mode untuk penelitian (with AI vs without AI)
    experiment_mode = Column(
        SQLEnum(ExperimentMode),
        nullable=False,
        default=ExperimentMode.WITH_AI
    )

    # Link ke experiment group untuk perbandingan
    experiment_group_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Konfigurasi session
    config = Column(JSON, default={
        "ai_enabled": True,
        "ai_proactive_suggestions": True,
        "ai_auto_synthesis": True,
        "tts_for_vi_users": True,
        "record_interactions": True,
        "phase_time_limits": {
            "shared_framing": 1800,
            "perspective_exchange": 2700,
            "meaning_negotiation": 2700,
            "reflection_iteration": 3600
        }
    })

    # State snapshot untuk recovery
    state_snapshot = Column(JSON, default={})

    # Timestamps
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    participants = relationship("SessionParticipant", back_populates="session")
    phase_transitions = relationship("PhaseTransition", back_populates="session")

    def __repr__(self):
        return f"<CoDesignSession {self.name}>"


class SessionParticipant(Base):
    """Model untuk participant dalam session"""
    __tablename__ = "session_participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("codesign_sessions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Role dalam session ini
    role_in_session = Column(
        SQLEnum(ParticipantRole),
        nullable=False,
        default=ParticipantRole.OBSERVER
    )

    # Timestamps
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    left_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    session = relationship("CoDesignSession", back_populates="participants")

    def __repr__(self):
        return f"<SessionParticipant {self.user_id} in {self.session_id}>"


class PhaseTransition(Base):
    """Model untuk tracking transisi fase (untuk research)"""
    __tablename__ = "phase_transitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("codesign_sessions.id", ondelete="CASCADE"), nullable=False)

    from_phase = Column(SQLEnum(SessionPhase), nullable=True)
    to_phase = Column(SQLEnum(SessionPhase), nullable=False)

    # Siapa yang trigger transisi (NULL jika automatic)
    triggered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    transition_reason = Column(Text, nullable=True)

    transitioned_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    session = relationship("CoDesignSession", back_populates="phase_transitions")

    def __repr__(self):
        return f"<PhaseTransition {self.from_phase} -> {self.to_phase}>"
