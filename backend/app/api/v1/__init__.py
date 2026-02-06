"""API v1 module"""
from fastapi import APIRouter
from .auth import router as auth_router
from .sessions import router as sessions_router
from .artifacts import router as artifacts_router
from .ai import router as ai_router
from .voice import router as voice_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(sessions_router, prefix="/sessions", tags=["Sessions"])
router.include_router(artifacts_router, prefix="/artifacts", tags=["Artifacts"])
router.include_router(ai_router, prefix="/ai", tags=["AI Agent"])
router.include_router(voice_router, prefix="/voice", tags=["Voice Services"])
