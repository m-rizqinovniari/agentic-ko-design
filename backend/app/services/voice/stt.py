"""
Speech-to-Text Service menggunakan Whisper
"""
import whisper
import os
import tempfile
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import aiofiles
import httpx

from app.config import settings


class WhisperSTTService:
    """
    Speech-to-Text Service menggunakan OpenAI Whisper

    Mendukung:
    - Transcription dari file audio
    - Transcription dari URL
    - Bahasa Indonesia
    - Word-level timestamps
    """

    def __init__(self, model_name: str = None):
        """
        Initialize Whisper STT Service

        Args:
            model_name: Nama model Whisper (tiny, base, small, medium, large)
        """
        self.model_name = model_name or settings.WHISPER_MODEL
        self.model = None
        self._model_loaded = False

    def _load_model(self):
        """Lazy load Whisper model"""
        if not self._model_loaded:
            print(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            self._model_loaded = True
            print("Whisper model loaded successfully")

    async def transcribe_file(
        self,
        file_path: str,
        language: str = "id"
    ) -> Dict[str, Any]:
        """
        Transcribe audio file

        Args:
            file_path: Path ke file audio
            language: Kode bahasa (id untuk Indonesia)

        Returns:
            Dict dengan transcript dan metadata
        """
        self._load_model()

        # Run Whisper in thread pool untuk tidak block event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.model.transcribe(
                file_path,
                language=language,
                task="transcribe",
                verbose=False
            )
        )

        return {
            "transcript": result["text"].strip(),
            "language": result.get("language", language),
            "confidence": self._calculate_confidence(result),
            "segments": self._process_segments(result.get("segments", [])),
            "duration": result.get("segments", [{}])[-1].get("end", 0) if result.get("segments") else 0
        }

    async def transcribe_url(
        self,
        audio_url: str,
        language: str = "id"
    ) -> Dict[str, Any]:
        """
        Transcribe audio dari URL

        Args:
            audio_url: URL ke file audio
            language: Kode bahasa

        Returns:
            Dict dengan transcript dan metadata
        """
        # Download audio ke temp file
        async with httpx.AsyncClient() as client:
            response = await client.get(audio_url)
            response.raise_for_status()

            # Save ke temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name

        try:
            # Transcribe
            result = await self.transcribe_file(tmp_path, language)
            return result
        finally:
            # Cleanup temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    async def transcribe_bytes(
        self,
        audio_bytes: bytes,
        language: str = "id",
        format: str = "mp3"
    ) -> Dict[str, Any]:
        """
        Transcribe audio dari bytes

        Args:
            audio_bytes: Audio data dalam bytes
            language: Kode bahasa
            format: Format audio (mp3, wav, etc)

        Returns:
            Dict dengan transcript dan metadata
        """
        # Save bytes ke temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            result = await self.transcribe_file(tmp_path, language)
            return result
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _calculate_confidence(self, result: Dict) -> float:
        """
        Calculate overall confidence score dari hasil Whisper

        Args:
            result: Whisper result dict

        Returns:
            Confidence score 0-1
        """
        segments = result.get("segments", [])
        if not segments:
            return 0.0

        # Whisper tidak memberikan confidence langsung,
        # tapi kita bisa estimate dari no_speech_prob dan avg_logprob
        total_confidence = 0
        for seg in segments:
            # Lower no_speech_prob = higher confidence
            no_speech = seg.get("no_speech_prob", 0.5)
            # Higher avg_logprob (less negative) = higher confidence
            avg_logprob = seg.get("avg_logprob", -1)

            # Normalize logprob ke 0-1 range (typical range -2 to 0)
            logprob_score = min(1, max(0, (avg_logprob + 2) / 2))

            # Combine scores
            seg_confidence = (1 - no_speech) * 0.3 + logprob_score * 0.7
            total_confidence += seg_confidence

        return total_confidence / len(segments)

    def _process_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Process segments untuk output yang lebih clean

        Args:
            segments: Raw segments dari Whisper

        Returns:
            Processed segments
        """
        processed = []
        for seg in segments:
            processed.append({
                "start": round(seg.get("start", 0), 2),
                "end": round(seg.get("end", 0), 2),
                "text": seg.get("text", "").strip(),
                "words": [
                    {
                        "word": w.get("word", ""),
                        "start": round(w.get("start", 0), 2),
                        "end": round(w.get("end", 0), 2)
                    }
                    for w in seg.get("words", [])
                ] if "words" in seg else []
            })
        return processed

    async def detect_language(self, file_path: str) -> str:
        """
        Detect bahasa dari audio file

        Args:
            file_path: Path ke audio file

        Returns:
            Detected language code
        """
        self._load_model()

        loop = asyncio.get_event_loop()
        audio = await loop.run_in_executor(
            None,
            lambda: whisper.load_audio(file_path)
        )
        audio = whisper.pad_or_trim(audio)

        mel = await loop.run_in_executor(
            None,
            lambda: whisper.log_mel_spectrogram(audio).to(self.model.device)
        )

        _, probs = await loop.run_in_executor(
            None,
            lambda: self.model.detect_language(mel)
        )

        detected_lang = max(probs, key=probs.get)
        return detected_lang

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """
        Get list of supported languages

        Returns:
            List of language info
        """
        # Whisper supports 99 languages
        # Here are the most relevant ones for this application
        return [
            {"code": "id", "name": "Indonesian", "native": "Bahasa Indonesia"},
            {"code": "en", "name": "English", "native": "English"},
            {"code": "jv", "name": "Javanese", "native": "Basa Jawa"},
            {"code": "su", "name": "Sundanese", "native": "Basa Sunda"},
            {"code": "ms", "name": "Malay", "native": "Bahasa Melayu"},
        ]


# Singleton instance
_stt_instance: Optional[WhisperSTTService] = None


def get_stt_service() -> WhisperSTTService:
    """Get or create STT service instance"""
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = WhisperSTTService()
    return _stt_instance
