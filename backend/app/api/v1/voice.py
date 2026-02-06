"""
Voice service endpoints (TTS/STT)
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
import os
import tempfile

from app.core.security import get_current_user
from app.services.voice import EmotionalTTSService, WhisperSTTService
from app.models.schemas import TTSRequest, TTSResponse, STTRequest, STTResponse
from app.config import settings

router = APIRouter()


@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(
    request: TTSRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Convert text ke speech dengan emosi

    Args:
        request: TTS request dengan text, voice, emotion, dll

    Returns:
        TTSResponse dengan URL audio
    """
    tts_service = EmotionalTTSService()

    audio_url = await tts_service.text_to_speech_emotional(
        text=request.text,
        emotion=request.emotion or "neutral",
        voice_gender=request.voice,
        speed_multiplier=request.speed
    )

    if not audio_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gagal generate audio"
        )

    # Estimate duration (rough estimate: ~150 words per minute)
    word_count = len(request.text.split())
    duration_ms = int((word_count / 150) * 60 * 1000 / request.speed)

    return TTSResponse(
        audio_url=audio_url,
        duration_ms=duration_ms,
        format=request.format
    )


@router.post("/stt", response_model=STTResponse)
async def speech_to_text(
    audio: UploadFile = File(...),
    language: str = "id",
    current_user: dict = Depends(get_current_user)
):
    """
    Convert speech ke text

    Args:
        audio: Audio file
        language: Bahasa (default: id untuk Indonesia)

    Returns:
        STTResponse dengan transcript
    """
    # Validate file type
    allowed_types = ["audio/mpeg", "audio/wav", "audio/mp3", "audio/webm", "audio/ogg"]
    if audio.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type tidak didukung. Gunakan: {', '.join(allowed_types)}"
        )

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        content = await audio.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        stt_service = WhisperSTTService()
        result = await stt_service.transcribe_file(tmp_path, language=language)

        return STTResponse(
            transcript=result["transcript"],
            confidence=result["confidence"],
            language=result["language"],
            segments=result["segments"]
        )

    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.post("/stt/url", response_model=STTResponse)
async def speech_to_text_from_url(
    request: STTRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Convert speech ke text dari URL

    Args:
        request: STT request dengan audio URL

    Returns:
        STTResponse dengan transcript
    """
    if not request.audio_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="audio_url diperlukan"
        )

    stt_service = WhisperSTTService()
    result = await stt_service.transcribe_url(
        audio_url=request.audio_url,
        language=request.language
    )

    return STTResponse(
        transcript=result["transcript"],
        confidence=result["confidence"],
        language=result["language"],
        segments=result["segments"]
    )


@router.get("/voices")
async def get_available_voices(
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of available TTS voices

    Returns:
        List of voices dengan info
    """
    tts_service = EmotionalTTSService()
    voices = await tts_service.get_available_voices()

    return {
        "voices": voices,
        "default_male": settings.TTS_VOICE_MALE,
        "default_female": settings.TTS_VOICE_FEMALE
    }


@router.get("/emotions")
async def get_supported_emotions(
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of supported emotions untuk TTS

    Returns:
        Dict of emotions dan deskripsinya
    """
    tts_service = EmotionalTTSService()
    emotions = tts_service.get_supported_emotions()

    return {"emotions": emotions}


@router.get("/languages")
async def get_supported_languages(
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of supported languages untuk STT

    Returns:
        List of languages
    """
    stt_service = WhisperSTTService()
    languages = stt_service.get_supported_languages()

    return {"languages": languages}
