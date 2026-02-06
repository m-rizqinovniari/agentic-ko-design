"""
Artifacts management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from app.core.security import get_current_user
from app.core.database import get_mongodb
from app.models.schemas import (
    ArtifactCreate,
    ArtifactResponse,
    ArtifactType,
    EmpathyMapContent,
    UserJourneyContent
)

router = APIRouter()


@router.get("/sessions/{session_id}", response_model=List[ArtifactResponse])
async def list_session_artifacts(
    session_id: UUID,
    artifact_type: Optional[ArtifactType] = None,
    current_user: dict = Depends(get_current_user),
    mongodb=Depends(get_mongodb)
):
    """
    List semua artifacts dalam session

    Args:
        session_id: ID session
        artifact_type: Filter by type (optional)

    Returns:
        List of artifacts
    """
    query = {"session_id": str(session_id)}
    if artifact_type:
        query["artifact_type"] = artifact_type.value

    artifacts = []
    async for doc in mongodb.artifacts.find(query).sort("created_at", -1):
        artifacts.append(ArtifactResponse(
            id=str(doc["_id"]),
            session_id=UUID(doc["session_id"]),
            artifact_type=doc["artifact_type"],
            name=doc.get("name", ""),
            phase_created=doc.get("phase_created", "shared_framing"),
            content=doc.get("content", {}),
            ai_synthesis=doc.get("ai_synthesis"),
            created_at=doc.get("created_at", datetime.utcnow()),
            updated_at=doc.get("updated_at", datetime.utcnow()),
            created_by=UUID(doc["created_by"]) if doc.get("created_by") else current_user["user_id"]
        ))

    return artifacts


@router.post("/sessions/{session_id}", response_model=ArtifactResponse, status_code=status.HTTP_201_CREATED)
async def create_artifact(
    session_id: UUID,
    artifact: ArtifactCreate,
    current_user: dict = Depends(get_current_user),
    mongodb=Depends(get_mongodb)
):
    """
    Buat artifact baru dalam session

    Args:
        session_id: ID session
        artifact: Data artifact

    Returns:
        ArtifactResponse dengan artifact yang dibuat
    """
    # Initialize content based on artifact type
    if artifact.artifact_type == ArtifactType.EMPATHY_MAP:
        initial_content = artifact.initial_content or EmpathyMapContent().model_dump()
    elif artifact.artifact_type == ArtifactType.USER_JOURNEY_MAP:
        initial_content = artifact.initial_content or UserJourneyContent().model_dump()
    else:
        initial_content = artifact.initial_content or {}

    doc = {
        "session_id": str(session_id),
        "artifact_type": artifact.artifact_type.value,
        "name": artifact.name,
        "phase_created": "shared_framing",  # Will be updated based on current phase
        "content": initial_content,
        "ai_synthesis": None,
        "created_by": str(current_user["user_id"]),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await mongodb.artifacts.insert_one(doc)

    return ArtifactResponse(
        id=str(result.inserted_id),
        session_id=session_id,
        artifact_type=artifact.artifact_type,
        name=artifact.name,
        phase_created="shared_framing",
        content=initial_content,
        ai_synthesis=None,
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
        created_by=current_user["user_id"]
    )


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(
    artifact_id: str,
    current_user: dict = Depends(get_current_user),
    mongodb=Depends(get_mongodb)
):
    """
    Get detail artifact

    Args:
        artifact_id: ID artifact

    Returns:
        ArtifactResponse dengan detail artifact
    """
    from bson import ObjectId

    doc = await mongodb.artifacts.find_one({"_id": ObjectId(artifact_id)})

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact tidak ditemukan"
        )

    return ArtifactResponse(
        id=str(doc["_id"]),
        session_id=UUID(doc["session_id"]),
        artifact_type=doc["artifact_type"],
        name=doc.get("name", ""),
        phase_created=doc.get("phase_created", "shared_framing"),
        content=doc.get("content", {}),
        ai_synthesis=doc.get("ai_synthesis"),
        created_at=doc.get("created_at", datetime.utcnow()),
        updated_at=doc.get("updated_at", datetime.utcnow()),
        created_by=UUID(doc["created_by"]) if doc.get("created_by") else current_user["user_id"]
    )


@router.patch("/{artifact_id}")
async def update_artifact(
    artifact_id: str,
    content: dict,
    current_user: dict = Depends(get_current_user),
    mongodb=Depends(get_mongodb)
):
    """
    Update artifact content

    Args:
        artifact_id: ID artifact
        content: New content

    Returns:
        Success message
    """
    from bson import ObjectId

    result = await mongodb.artifacts.update_one(
        {"_id": ObjectId(artifact_id)},
        {
            "$set": {
                "content": content,
                "updated_at": datetime.utcnow()
            }
        }
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact tidak ditemukan"
        )

    return {"message": "Artifact berhasil diupdate"}


@router.get("/{artifact_id}/export")
async def export_artifact(
    artifact_id: str,
    format: str = "json",
    current_user: dict = Depends(get_current_user),
    mongodb=Depends(get_mongodb)
):
    """
    Export artifact ke format tertentu

    Args:
        artifact_id: ID artifact
        format: Format export (json, pdf, png)

    Returns:
        Exported artifact data atau file
    """
    from bson import ObjectId

    doc = await mongodb.artifacts.find_one({"_id": ObjectId(artifact_id)})

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact tidak ditemukan"
        )

    if format == "json":
        return {
            "artifact_type": doc["artifact_type"],
            "name": doc.get("name", ""),
            "content": doc.get("content", {}),
            "ai_synthesis": doc.get("ai_synthesis"),
            "exported_at": datetime.utcnow().isoformat()
        }

    # For other formats (pdf, png), would need additional libraries
    # This is a placeholder
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Export ke format {format} belum diimplementasi"
    )
