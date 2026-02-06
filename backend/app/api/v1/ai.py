"""
AI Agent endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import Optional

from app.core.security import get_current_user
from app.core.database import get_mongodb
from app.services.ai_agent import CoDesignAgent
from app.services.voice import EmotionalTTSService
from app.models.schemas import (
    AIMessageRequest,
    AIMessageResponse,
    AISynthesisRequest,
    AISynthesisResponse
)

router = APIRouter()


@router.post("/sessions/{session_id}/message", response_model=AIMessageResponse)
async def send_message_to_ai(
    session_id: UUID,
    message: AIMessageRequest,
    current_user: dict = Depends(get_current_user),
    mongodb=Depends(get_mongodb)
):
    """
    Kirim pesan ke AI agent dalam session

    Args:
        session_id: ID session
        message: Pesan dan context

    Returns:
        AIMessageResponse dengan respons AI dan optional TTS
    """
    # Get current phase from session (simplified - in real impl, fetch from DB)
    current_phase = message.context.get("current_phase", "shared_framing") if message.context else "shared_framing"

    # Initialize AI agent
    tts_service = EmotionalTTSService()
    agent = CoDesignAgent(voice_service=tts_service, mongodb=mongodb)

    # Process message
    response = await agent.process_message(
        session_id=str(session_id),
        message=message.message,
        sender_role=current_user.get("role", "designer"),
        current_phase=current_phase,
        context=message.context,
        request_tts=message.request_tts
    )

    return response


@router.post("/sessions/{session_id}/synthesize", response_model=AISynthesisResponse)
async def synthesize_artifact(
    session_id: UUID,
    request: AISynthesisRequest,
    current_user: dict = Depends(get_current_user),
    mongodb=Depends(get_mongodb)
):
    """
    Request AI untuk mensintesis artifact dari data interaksi

    Args:
        session_id: ID session
        request: Synthesis request dengan target artifact type

    Returns:
        AISynthesisResponse dengan status dan hasil
    """
    # Get interaction data from MongoDB
    interactions = []
    async for doc in mongodb.interaction_logs.find({"session_id": str(session_id)}):
        interactions.append(doc)

    if not interactions:
        return AISynthesisResponse(
            synthesis_id="",
            status="failed",
            result=None,
            insights=["Tidak ada data interaksi untuk disintesis"]
        )

    # Initialize agent
    agent = CoDesignAgent(mongodb=mongodb)

    # Generate synthesis
    result = await agent.generate_synthesis(
        session_id=str(session_id),
        artifact_type=request.target_artifact_type.value,
        interaction_data=interactions
    )

    return AISynthesisResponse(
        synthesis_id=f"synth_{session_id}_{request.target_artifact_type.value}",
        status="complete",
        result=result,
        insights=result.get("key_insights", []) if isinstance(result, dict) else []
    )


@router.get("/sessions/{session_id}/suggestions")
async def get_ai_suggestions(
    session_id: UUID,
    phase: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    mongodb=Depends(get_mongodb)
):
    """
    Get AI suggestions berdasarkan current context

    Args:
        session_id: ID session
        phase: Current phase (optional)

    Returns:
        List of suggestions
    """
    # Get recent insights
    insights = []
    async for doc in mongodb.interaction_logs.find(
        {"session_id": str(session_id), "type": "insight"}
    ).sort("timestamp", -1).limit(10):
        insights.append(doc.get("content", ""))

    # Get design suggestions
    suggestions_doc = await mongodb.artifacts.find_one({
        "session_id": str(session_id),
        "artifact_type": "design_suggestions"
    })

    design_suggestions = []
    if suggestions_doc and "content" in suggestions_doc:
        elements = suggestions_doc["content"].get("elements", [])
        for elem in elements[-5:]:  # Get last 5
            design_suggestions.append({
                "type": elem.get("type"),
                "name": elem.get("name"),
                "description": elem.get("description"),
                "rationale": elem.get("rationale")
            })

    return {
        "recent_insights": insights,
        "design_suggestions": design_suggestions,
        "phase": phase
    }


@router.get("/sessions/{session_id}/insights")
async def get_session_insights(
    session_id: UUID,
    current_user: dict = Depends(get_current_user),
    mongodb=Depends(get_mongodb)
):
    """
    Get all insights yang telah di-capture untuk session

    Args:
        session_id: ID session

    Returns:
        Categorized insights
    """
    insights = {
        "pain_points": [],
        "needs": [],
        "emotions": [],
        "behaviors": []
    }

    async for doc in mongodb.interaction_logs.find({
        "session_id": str(session_id),
        "type": "insight"
    }):
        insight_type = doc.get("insight_type", "")
        content = doc.get("content", "")
        source = doc.get("source", "")

        item = {
            "content": content,
            "source": source,
            "timestamp": doc.get("executed_at")
        }

        if insight_type == "pain_point":
            insights["pain_points"].append(item)
        elif insight_type == "need":
            insights["needs"].append(item)
        elif insight_type == "emotion":
            insights["emotions"].append(item)
        elif insight_type == "behavior":
            insights["behaviors"].append(item)

    return insights
