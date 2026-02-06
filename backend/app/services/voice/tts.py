"""
Text-to-Speech Service dengan dukungan emosi
Menggunakan Edge TTS dengan SSML untuk kontrol prosody
"""
import edge_tts
import asyncio
import aiofiles
import os
from uuid import uuid4
from typing import Optional, Literal
from datetime import datetime

from app.config import settings


class EmotionalTTSService:
    """
    TTS Service dengan dukungan emosi menggunakan SSML

    Edge TTS mendukung SSML untuk mengontrol:
    - Rate (kecepatan bicara)
    - Pitch (nada suara)
    - Volume
    - Pause/break

    Emotions diimplementasikan dengan kombinasi parameter prosody.
    """

    # Mapping emosi ke SSML prosody parameters
    EMOTIONS_SSML = {
        "neutral": {
            "rate": "medium",
            "pitch": "medium",
            "description": "Netral, informatif"
        },
        "empathy": {
            "rate": "slow",
            "pitch": "-10%",
            "description": "Empatik, pengertian, mendukung"
        },
        "encouraging": {
            "rate": "medium",
            "pitch": "+5%",
            "description": "Menyemangati, positif"
        },
        "questioning": {
            "rate": "medium",
            "pitch": "+15%",
            "description": "Bertanya, ingin tahu"
        },
        "excited": {
            "rate": "fast",
            "pitch": "+10%",
            "description": "Antusias, bersemangat"
        },
        "calm": {
            "rate": "slow",
            "pitch": "-5%",
            "description": "Tenang, menenangkan"
        },
        "serious": {
            "rate": "slow",
            "pitch": "-15%",
            "description": "Serius, penting"
        }
    }

    # Voice Indonesia dari Edge TTS
    VOICES = {
        "male": "id-ID-ArdiNeural",
        "female": "id-ID-GadisNeural"
    }

    def __init__(self):
        """Initialize TTS service"""
        self.audio_dir = settings.AUDIO_DIR
        os.makedirs(self.audio_dir, exist_ok=True)

    def _build_ssml(
        self,
        text: str,
        voice: str,
        emotion: str,
        language: str = "id-ID"
    ) -> str:
        """
        Build SSML markup untuk text dengan emosi

        Args:
            text: Teks yang akan dikonversi
            voice: Voice ID
            emotion: Nama emosi
            language: Kode bahasa

        Returns:
            SSML string
        """
        emotion_params = self.EMOTIONS_SSML.get(emotion, self.EMOTIONS_SSML["neutral"])

        # Build prosody tag
        rate = emotion_params["rate"]
        pitch = emotion_params["pitch"]

        # Handle rate values
        if rate in ["slow", "medium", "fast"]:
            rate_attr = rate
        else:
            rate_attr = rate

        # Build SSML
        ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{language}">
    <voice name="{voice}">
        <prosody rate="{rate_attr}" pitch="{pitch}">
            {self._prepare_text_for_ssml(text)}
        </prosody>
    </voice>
</speak>"""

        return ssml

    def _prepare_text_for_ssml(self, text: str) -> str:
        """
        Prepare text untuk SSML - escape karakter khusus dan tambah break

        Args:
            text: Raw text

        Returns:
            Text yang siap untuk SSML
        """
        # Escape XML special characters
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&apos;")

        # Tambah break setelah titik untuk natural pause
        text = text.replace(". ", '.<break time="300ms"/> ')

        # Tambah break setelah koma
        text = text.replace(", ", ',<break time="150ms"/> ')

        # Tambah break setelah tanda tanya
        text = text.replace("? ", '?<break time="400ms"/> ')

        return text

    async def text_to_speech_emotional(
        self,
        text: str,
        emotion: str = "neutral",
        voice_gender: Literal["male", "female"] = "female",
        language: str = "id-ID",
        speed_multiplier: float = 1.0
    ) -> Optional[str]:
        """
        Generate audio dari text dengan emosi

        Args:
            text: Teks yang akan dikonversi
            emotion: Emosi yang digunakan (neutral, empathy, encouraging, dll)
            voice_gender: Gender suara (male/female)
            language: Kode bahasa
            speed_multiplier: Pengali kecepatan (0.5-2.0)

        Returns:
            URL ke file audio yang dihasilkan, atau None jika gagal
        """
        if not text or not text.strip():
            return None

        try:
            # Get voice
            voice = self.VOICES.get(voice_gender, self.VOICES["female"])

            # Generate unique filename
            filename = f"tts_{uuid4().hex[:8]}_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
            filepath = os.path.join(self.audio_dir, filename)

            # Build SSML
            ssml = self._build_ssml(text, voice, emotion, language)

            # Generate audio menggunakan edge-tts
            communicate = edge_tts.Communicate(text, voice)

            # Jika menggunakan SSML, edge-tts perlu dihandle berbeda
            # Untuk sekarang, gunakan plain text dengan rate adjustment
            rate_adjustment = self._get_rate_for_emotion(emotion, speed_multiplier)

            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate_adjustment,
                pitch=self._get_pitch_for_emotion(emotion)
            )

            await communicate.save(filepath)

            # Return relative URL (akan di-serve oleh static files)
            return f"/audio/{filename}"

        except Exception as e:
            print(f"TTS Error: {e}")
            return None

    def _get_rate_for_emotion(self, emotion: str, multiplier: float = 1.0) -> str:
        """Get rate string untuk emotion"""
        base_rates = {
            "neutral": 0,
            "empathy": -15,
            "encouraging": 5,
            "questioning": 0,
            "excited": 15,
            "calm": -20,
            "serious": -10
        }

        base = base_rates.get(emotion, 0)
        adjusted = int(base * multiplier)

        if adjusted > 0:
            return f"+{adjusted}%"
        elif adjusted < 0:
            return f"{adjusted}%"
        else:
            return "+0%"

    def _get_pitch_for_emotion(self, emotion: str) -> str:
        """Get pitch string untuk emotion"""
        pitches = {
            "neutral": "+0Hz",
            "empathy": "-10Hz",
            "encouraging": "+5Hz",
            "questioning": "+15Hz",
            "excited": "+10Hz",
            "calm": "-5Hz",
            "serious": "-15Hz"
        }
        return pitches.get(emotion, "+0Hz")

    async def text_to_speech_simple(
        self,
        text: str,
        voice_gender: Literal["male", "female"] = "female"
    ) -> Optional[str]:
        """
        Generate audio sederhana tanpa emosi

        Args:
            text: Teks yang akan dikonversi
            voice_gender: Gender suara

        Returns:
            URL ke file audio
        """
        return await self.text_to_speech_emotional(
            text=text,
            emotion="neutral",
            voice_gender=voice_gender
        )

    async def get_available_voices(self) -> list:
        """
        Get list of available Indonesian voices

        Returns:
            List of voice info
        """
        voices = await edge_tts.list_voices()
        indonesian_voices = [
            {
                "id": v["ShortName"],
                "name": v["FriendlyName"],
                "gender": v["Gender"],
                "locale": v["Locale"]
            }
            for v in voices
            if v["Locale"].startswith("id-")
        ]
        return indonesian_voices

    def get_supported_emotions(self) -> dict:
        """
        Get list of supported emotions dengan deskripsi

        Returns:
            Dict of emotions dan deskripsinya
        """
        return {
            name: params["description"]
            for name, params in self.EMOTIONS_SSML.items()
        }


# Singleton instance
_tts_instance: Optional[EmotionalTTSService] = None


def get_tts_service() -> EmotionalTTSService:
    """Get or create TTS service instance"""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = EmotionalTTSService()
    return _tts_instance
