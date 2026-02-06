"""
Pydantic schemas untuk API request/response
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from uuid import UUID
from enum import Enum


# ==================== Enums ====================

class UserRole(str, Enum):
    DESIGNER = "designer"
    VI_USER = "vi_user"
    RESEARCHER = "researcher"
    ADMIN = "admin"


class SessionPhase(str, Enum):
    SETUP = "setup"
    SHARED_FRAMING = "shared_framing"
    PERSPECTIVE_EXCHANGE = "perspective_exchange"
    MEANING_NEGOTIATION = "meaning_negotiation"
    REFLECTION_ITERATION = "reflection_iteration"
    COMPLETE = "complete"


class ExperimentMode(str, Enum):
    WITH_AI = "with_ai"
    WITHOUT_AI = "without_ai"
    CONTROL = "control"


class ArtifactType(str, Enum):
    EMPATHY_MAP = "empathy_map"
    USER_JOURNEY_MAP = "user_journey_map"
    DESIGN_SKETCH = "design_sketch"
    MOCKUP = "mockup"


# ==================== User Schemas ====================

class AccessibilityPreferences(BaseModel):
    """Preferensi aksesibilitas untuk user tunanetra"""
    tts_enabled: bool = True
    tts_voice: Literal["male", "female"] = "female"
    tts_speed: float = Field(1.0, ge=0.5, le=2.0)
    stt_enabled: bool = True
    high_contrast: bool = False
    screen_reader_optimized: bool = True
    keyboard_navigation: bool = True
    audio_feedback: bool = True


class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole = UserRole.DESIGNER


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    accessibility_preferences: Optional[AccessibilityPreferences] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: UUID
    accessibility_preferences: AccessibilityPreferences
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ==================== Session Schemas ====================

class SessionConfig(BaseModel):
    """Konfigurasi session"""
    ai_enabled: bool = True
    ai_proactive_suggestions: bool = True
    ai_auto_synthesis: bool = True
    tts_for_vi_users: bool = True
    record_interactions: bool = True
    phase_time_limits: Dict[str, int] = Field(default_factory=lambda: {
        "shared_framing": 1800,
        "perspective_exchange": 2700,
        "meaning_negotiation": 2700,
        "reflection_iteration": 3600
    })


class SessionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    experiment_mode: ExperimentMode = ExperimentMode.WITH_AI
    experiment_group_id: Optional[UUID] = None
    config: SessionConfig = SessionConfig()


class SessionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[SessionConfig] = None


class ParticipantResponse(BaseModel):
    id: UUID
    user_id: UUID
    role_in_session: str
    joined_at: datetime

    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    current_phase: SessionPhase
    experiment_mode: ExperimentMode
    experiment_group_id: Optional[UUID]
    config: SessionConfig
    participants: List[ParticipantResponse] = []
    created_by: UUID
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    id: UUID
    name: str
    current_phase: SessionPhase
    experiment_mode: ExperimentMode
    participant_count: int = 0
    created_at: datetime


# ==================== Artifact Schemas ====================

class EmpathyMapItem(BaseModel):
    text: str
    source: Literal["vi_user", "designer", "ai_observation"]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EmpathyMapContent(BaseModel):
    """Konten Empathy Map - extended untuk tunanetra"""
    says: List[EmpathyMapItem] = []
    thinks: List[EmpathyMapItem] = []
    does: List[EmpathyMapItem] = []
    feels: List[EmpathyMapItem] = []
    hears: List[EmpathyMapItem] = []  # Khusus untuk pengalaman audio tunanetra
    touches: List[EmpathyMapItem] = []  # Khusus untuk pengalaman haptic tunanetra


class JourneyStage(BaseModel):
    """Stage dalam User Journey Map"""
    name: str
    touchpoints: List[str] = []
    actions: List[str] = []
    thoughts: List[str] = []
    emotions: str = ""
    pain_points: List[str] = []
    opportunities: List[str] = []
    accessibility_notes: List[str] = []  # Catatan aksesibilitas khusus


class UserJourneyContent(BaseModel):
    """Konten User Journey Map"""
    persona_name: str = "User Tunanetra"
    scenario: str = ""
    stages: List[JourneyStage] = []


class ArtifactCreate(BaseModel):
    artifact_type: ArtifactType
    name: str
    initial_content: Optional[Dict[str, Any]] = None


class AISynthesis(BaseModel):
    """Hasil sintesis AI untuk artifact"""
    summary: str
    key_insights: List[str] = []
    accessibility_considerations: List[str] = []
    suggested_improvements: List[str] = []
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ArtifactResponse(BaseModel):
    id: str
    session_id: UUID
    artifact_type: ArtifactType
    name: str
    phase_created: SessionPhase
    content: Dict[str, Any]
    ai_synthesis: Optional[AISynthesis] = None
    created_at: datetime
    updated_at: datetime
    created_by: UUID


# ==================== AI Agent Schemas ====================

class AIMessageRequest(BaseModel):
    """Request untuk mengirim pesan ke AI agent"""
    message: str
    context: Optional[Dict[str, Any]] = None
    request_tts: bool = True  # Default true untuk aksesibilitas


class AIMessageResponse(BaseModel):
    """Response dari AI agent"""
    response: str
    suggestions: List[str] = []
    tools_used: List[str] = []
    tts_audio_url: Optional[str] = None
    emotion_detected: Optional[str] = None


class AISynthesisRequest(BaseModel):
    """Request untuk AI synthesis artifact"""
    target_artifact_type: ArtifactType
    include_phases: List[SessionPhase] = [SessionPhase.SHARED_FRAMING, SessionPhase.PERSPECTIVE_EXCHANGE]
    focus_areas: Optional[List[str]] = None


class AISynthesisResponse(BaseModel):
    synthesis_id: str
    status: Literal["pending", "processing", "complete", "failed"]
    result: Optional[Dict[str, Any]] = None
    insights: List[str] = []


# ==================== Voice Schemas ====================

class TTSRequest(BaseModel):
    """Request untuk Text-to-Speech"""
    text: str
    voice: Literal["male", "female"] = "female"
    speed: float = Field(1.0, ge=0.5, le=2.0)
    emotion: Optional[Literal["neutral", "empathy", "encouraging", "questioning", "excited"]] = "neutral"
    format: Literal["mp3", "wav", "ogg"] = "mp3"


class TTSResponse(BaseModel):
    """Response dari TTS service"""
    audio_url: str
    duration_ms: int
    format: str


class STTRequest(BaseModel):
    """Request untuk Speech-to-Text"""
    audio_url: Optional[str] = None
    language: str = "id"  # Bahasa Indonesia


class STTResponse(BaseModel):
    """Response dari STT service"""
    transcript: str
    confidence: float
    language: str
    segments: List[Dict[str, Any]] = []


# ==================== WebSocket Schemas ====================

class WebSocketMessage(BaseModel):
    """Format pesan WebSocket"""
    type: str
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_id: Optional[str] = None


class PresenceUpdate(BaseModel):
    """Update presence user"""
    user_id: UUID
    status: Literal["active", "idle", "away"]
    cursor: Optional[Dict[str, Any]] = None
    active_element: Optional[str] = None


class CRDTUpdate(BaseModel):
    """Update CRDT untuk collaborative editing"""
    artifact_id: str
    update: str  # Base64 encoded Y.js update
    origin: UUID


# ==================== Research Schemas ====================

class ExperimentPairCreate(BaseModel):
    """Create paired sessions untuk experiment"""
    name: str
    description: Optional[str] = None


class ExperimentPairResponse(BaseModel):
    group_id: UUID
    name: str
    control_session_id: UUID
    treatment_session_id: UUID
    created_at: datetime


class ComparisonMetrics(BaseModel):
    """Metrics perbandingan with-AI vs without-AI"""
    time_metrics: Dict[str, Any]
    interaction_metrics: Dict[str, Any]
    artifact_metrics: Dict[str, Any]
    collaboration_metrics: Dict[str, Any]


class ResearchReport(BaseModel):
    """Laporan penelitian"""
    experiment_group_id: UUID
    comparison: ComparisonMetrics
    insights: List[str]
    generated_at: datetime
