"""
Session management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.session import (
    CoDesignSession,
    SessionParticipant,
    PhaseTransition,
    SessionPhase,
    ParticipantRole
)
from app.models.schemas import (
    SessionCreate,
    SessionUpdate,
    SessionResponse,
    SessionListResponse,
    SessionConfig
)

router = APIRouter()


@router.get("", response_model=List[SessionListResponse])
async def list_sessions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List semua sessions yang bisa diakses user

    Returns:
        List of sessions
    """
    # Get sessions where user is creator or participant
    query = (
        select(CoDesignSession)
        .outerjoin(SessionParticipant)
        .where(
            (CoDesignSession.created_by == current_user["user_id"]) |
            (SessionParticipant.user_id == current_user["user_id"])
        )
        .distinct()
        .order_by(CoDesignSession.created_at.desc())
    )

    result = await db.execute(query)
    sessions = result.scalars().all()

    response = []
    for session in sessions:
        # Count participants
        count_query = select(func.count(SessionParticipant.id)).where(
            SessionParticipant.session_id == session.id
        )
        count_result = await db.execute(count_query)
        participant_count = count_result.scalar()

        response.append(SessionListResponse(
            id=session.id,
            name=session.name,
            current_phase=session.current_phase,
            experiment_mode=session.experiment_mode,
            participant_count=participant_count or 0,
            created_at=session.created_at
        ))

    return response


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: SessionCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Buat session ko-desain baru

    Args:
        session_data: Data session

    Returns:
        SessionResponse dengan session yang dibuat
    """
    # Create session
    new_session = CoDesignSession(
        name=session_data.name,
        description=session_data.description,
        experiment_mode=session_data.experiment_mode,
        experiment_group_id=session_data.experiment_group_id,
        config=session_data.config.model_dump(),
        created_by=current_user["user_id"]
    )

    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    # Add creator as participant (as designer by default or based on role)
    user_role = current_user.get("role", "designer")
    participant_role = ParticipantRole.DESIGNER
    if user_role == "vi_user":
        participant_role = ParticipantRole.VI_USER
    elif user_role == "researcher":
        participant_role = ParticipantRole.OBSERVER

    participant = SessionParticipant(
        session_id=new_session.id,
        user_id=current_user["user_id"],
        role_in_session=participant_role
    )
    db.add(participant)
    await db.commit()

    # Refresh to get participants
    await db.refresh(new_session)

    return SessionResponse(
        id=new_session.id,
        name=new_session.name,
        description=new_session.description,
        current_phase=new_session.current_phase,
        experiment_mode=new_session.experiment_mode,
        experiment_group_id=new_session.experiment_group_id,
        config=SessionConfig(**new_session.config),
        participants=[],
        created_by=new_session.created_by,
        created_at=new_session.created_at,
        started_at=new_session.started_at,
        completed_at=new_session.completed_at
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detail session

    Args:
        session_id: ID session

    Returns:
        SessionResponse dengan detail session
    """
    query = (
        select(CoDesignSession)
        .options(selectinload(CoDesignSession.participants))
        .where(CoDesignSession.id == session_id)
    )
    result = await db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session tidak ditemukan"
        )

    return SessionResponse(
        id=session.id,
        name=session.name,
        description=session.description,
        current_phase=session.current_phase,
        experiment_mode=session.experiment_mode,
        experiment_group_id=session.experiment_group_id,
        config=SessionConfig(**session.config),
        participants=[
            {
                "id": p.id,
                "user_id": p.user_id,
                "role_in_session": p.role_in_session.value,
                "joined_at": p.joined_at
            }
            for p in session.participants
        ],
        created_by=session.created_by,
        created_at=session.created_at,
        started_at=session.started_at,
        completed_at=session.completed_at
    )


@router.post("/{session_id}/start")
async def start_session(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mulai session ko-desain

    Args:
        session_id: ID session

    Returns:
        Success message
    """
    result = await db.execute(
        select(CoDesignSession).where(CoDesignSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session tidak ditemukan"
        )

    if session.current_phase != SessionPhase.SETUP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session sudah dimulai"
        )

    # Update session
    session.current_phase = SessionPhase.SHARED_FRAMING
    session.started_at = datetime.utcnow()

    # Record phase transition
    transition = PhaseTransition(
        session_id=session.id,
        from_phase=SessionPhase.SETUP,
        to_phase=SessionPhase.SHARED_FRAMING,
        triggered_by=current_user["user_id"],
        transition_reason="Session started"
    )
    db.add(transition)

    await db.commit()

    return {"message": "Session dimulai", "current_phase": "shared_framing"}


@router.post("/{session_id}/advance")
async def advance_phase(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Advance ke fase berikutnya

    Args:
        session_id: ID session

    Returns:
        New phase info
    """
    result = await db.execute(
        select(CoDesignSession).where(CoDesignSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session tidak ditemukan"
        )

    # Define phase order
    phase_order = [
        SessionPhase.SETUP,
        SessionPhase.SHARED_FRAMING,
        SessionPhase.PERSPECTIVE_EXCHANGE,
        SessionPhase.MEANING_NEGOTIATION,
        SessionPhase.REFLECTION_ITERATION,
        SessionPhase.COMPLETE
    ]

    current_index = phase_order.index(session.current_phase)

    if current_index >= len(phase_order) - 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session sudah selesai"
        )

    # Get next phase
    from_phase = session.current_phase
    to_phase = phase_order[current_index + 1]

    # Update session
    session.current_phase = to_phase

    if to_phase == SessionPhase.COMPLETE:
        session.completed_at = datetime.utcnow()

    # Record transition
    transition = PhaseTransition(
        session_id=session.id,
        from_phase=from_phase,
        to_phase=to_phase,
        triggered_by=current_user["user_id"],
        transition_reason="Manual advance"
    )
    db.add(transition)

    await db.commit()

    return {
        "message": f"Fase berubah ke {to_phase.value}",
        "from_phase": from_phase.value,
        "current_phase": to_phase.value
    }


@router.post("/{session_id}/participants/join")
async def join_session(
    session_id: UUID,
    role: ParticipantRole,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Join session sebagai participant

    Args:
        session_id: ID session
        role: Role dalam session

    Returns:
        Success message
    """
    # Check if session exists
    result = await db.execute(
        select(CoDesignSession).where(CoDesignSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session tidak ditemukan"
        )

    # Check if already participant
    result = await db.execute(
        select(SessionParticipant).where(
            SessionParticipant.session_id == session_id,
            SessionParticipant.user_id == current_user["user_id"]
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Anda sudah bergabung dalam session ini"
        )

    # Add as participant
    participant = SessionParticipant(
        session_id=session_id,
        user_id=current_user["user_id"],
        role_in_session=role
    )
    db.add(participant)
    await db.commit()

    return {"message": f"Berhasil bergabung sebagai {role.value}"}


@router.delete("/{session_id}/participants/leave")
async def leave_session(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Leave session

    Args:
        session_id: ID session

    Returns:
        Success message
    """
    result = await db.execute(
        select(SessionParticipant).where(
            SessionParticipant.session_id == session_id,
            SessionParticipant.user_id == current_user["user_id"]
        )
    )
    participant = result.scalar_one_or_none()

    if not participant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anda tidak terdaftar dalam session ini"
        )

    participant.left_at = datetime.utcnow()
    await db.commit()

    return {"message": "Berhasil keluar dari session"}
