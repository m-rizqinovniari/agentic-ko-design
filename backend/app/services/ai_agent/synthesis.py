"""
Artifact Synthesis Service
Generate empathy maps dan journey maps dari interaction data
"""
import anthropic
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from app.config import settings


class ArtifactSynthesizer:
    """
    Service untuk mensintesis artifacts dari data interaksi

    Menggunakan Claude untuk:
    - Generate empathy map dari percakapan
    - Generate user journey map dari pengalaman yang diceritakan
    - Extract key insights
    - Identify accessibility considerations
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL

    async def synthesize_empathy_map(
        self,
        session_id: str,
        interactions: List[Dict],
        existing_map: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Synthesize empathy map dari data interaksi

        Args:
            session_id: Session ID
            interactions: List of interaction logs
            existing_map: Existing empathy map to enhance

        Returns:
            Complete empathy map dengan semua kategori
        """
        # Prepare interaction summary
        interaction_text = self._prepare_interactions_for_synthesis(interactions)

        existing_context = ""
        if existing_map:
            existing_context = f"\n\nEmpathy map yang sudah ada:\n{json.dumps(existing_map, indent=2)}\n\nTambahkan insight baru ke map yang sudah ada."

        prompt = f"""
Berdasarkan data interaksi berikut dari sesi ko-desain dengan user tunanetra untuk aplikasi pembayaran mobile, buatlah atau update empathy map.

DATA INTERAKSI:
{interaction_text}
{existing_context}

Buatlah empathy map dalam format JSON dengan struktur berikut. Setiap kategori berisi array of objects dengan 'text' dan 'source'.

Kategori empathy map (khusus untuk user tunanetra):
1. **says**: Apa yang dikatakan user secara langsung tentang pengalaman mereka
2. **thinks**: Apa yang mungkin dipikirkan user (inference dari konteks)
3. **does**: Tindakan yang dilakukan user saat menggunakan aplikasi
4. **feels**: Emosi yang dirasakan (frustasi, senang, cemas, dll)
5. **hears**: Audio feedback yang diterima atau diharapkan user (TTS, sound cues, screen reader)
6. **touches**: Interaksi haptic/tactile (gestures, vibration feedback, braille display)

Untuk setiap item, tentukan source: "vi_user" (dari user tunanetra langsung), "designer" (dari pengamatan designer), atau "ai_observation" (inference AI).

Output HANYA JSON, tanpa penjelasan tambahan.

Contoh format:
{{
  "says": [
    {{"text": "Saya kesulitan menemukan tombol konfirmasi", "source": "vi_user"}},
    {{"text": "Screen reader terlalu cepat membaca nominal", "source": "vi_user"}}
  ],
  "thinks": [
    {{"text": "Apakah transaksi ini sudah berhasil?", "source": "ai_observation"}}
  ],
  "does": [
    {{"text": "Menggunakan VoiceOver untuk navigasi", "source": "vi_user"}}
  ],
  "feels": [
    {{"text": "Cemas saat melakukan transfer nominal besar", "source": "vi_user"}}
  ],
  "hears": [
    {{"text": "Ingin konfirmasi audio setelah transaksi", "source": "vi_user"}}
  ],
  "touches": [
    {{"text": "Mengharapkan haptic feedback saat tombol ditekan", "source": "designer"}}
  ]
}}
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON response
        try:
            result = json.loads(response.content[0].text)
        except json.JSONDecodeError:
            # Fallback structure
            result = {
                "says": [],
                "thinks": [],
                "does": [],
                "feels": [],
                "hears": [],
                "touches": [],
                "raw_response": response.content[0].text
            }

        result["session_id"] = session_id
        result["generated_at"] = datetime.utcnow().isoformat()
        result["interaction_count"] = len(interactions)

        return result

    async def synthesize_journey_map(
        self,
        session_id: str,
        interactions: List[Dict],
        scenario: str = "Melakukan pembayaran mobile"
    ) -> Dict[str, Any]:
        """
        Synthesize user journey map dari data interaksi

        Args:
            session_id: Session ID
            interactions: List of interaction logs
            scenario: Skenario yang di-mapping

        Returns:
            Complete journey map dengan stages
        """
        interaction_text = self._prepare_interactions_for_synthesis(interactions)

        prompt = f"""
Berdasarkan data interaksi berikut dari sesi ko-desain dengan user tunanetra, buatlah user journey map untuk skenario: "{scenario}"

DATA INTERAKSI:
{interaction_text}

Buatlah journey map dalam format JSON dengan struktur berikut:

{{
  "persona_name": "User Tunanetra",
  "scenario": "{scenario}",
  "stages": [
    {{
      "name": "Nama Stage",
      "order": 1,
      "touchpoints": ["list touchpoints"],
      "actions": ["aksi yang dilakukan"],
      "thoughts": ["pikiran user"],
      "emotions": "deskripsi emosi (positif/netral/negatif)",
      "pain_points": ["hambatan yang dialami"],
      "opportunities": ["peluang improvement"],
      "accessibility_notes": ["catatan aksesibilitas khusus untuk tunanetra"]
    }}
  ],
  "key_insights": ["insight kunci dari journey"],
  "critical_moments": ["momen kritis yang perlu perhatian khusus"]
}}

Identifikasi stages yang relevan untuk pembayaran mobile, misalnya:
1. Membuka Aplikasi
2. Navigasi ke Fitur Pembayaran
3. Input Penerima/Tujuan
4. Input Nominal
5. Review Transaksi
6. Konfirmasi & Autentikasi
7. Hasil Transaksi

Untuk setiap stage, fokus pada pengalaman non-visual:
- Bagaimana user tunanetra berinteraksi?
- Feedback audio/haptic apa yang diterima/diharapkan?
- Hambatan apa yang muncul tanpa visual?

Output HANYA JSON, tanpa penjelasan tambahan.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            result = json.loads(response.content[0].text)
        except json.JSONDecodeError:
            result = {
                "persona_name": "User Tunanetra",
                "scenario": scenario,
                "stages": [],
                "raw_response": response.content[0].text
            }

        result["session_id"] = session_id
        result["generated_at"] = datetime.utcnow().isoformat()

        return result

    async def extract_design_recommendations(
        self,
        session_id: str,
        empathy_map: Dict,
        journey_map: Dict
    ) -> Dict[str, Any]:
        """
        Extract design recommendations dari empathy map dan journey map

        Args:
            session_id: Session ID
            empathy_map: Empathy map data
            journey_map: Journey map data

        Returns:
            Design recommendations
        """
        prompt = f"""
Berdasarkan empathy map dan journey map berikut untuk aplikasi pembayaran mobile bagi user tunanetra, berikan rekomendasi desain yang spesifik dan actionable.

EMPATHY MAP:
{json.dumps(empathy_map, indent=2)}

JOURNEY MAP:
{json.dumps(journey_map, indent=2)}

Berikan rekomendasi dalam format JSON:

{{
  "high_priority": [
    {{
      "element": "nama elemen/fitur",
      "recommendation": "rekomendasi spesifik",
      "addresses_pain_point": "pain point yang dijawab",
      "accessibility_features": ["fitur aksesibilitas yang diperlukan"],
      "audio_feedback": "deskripsi audio feedback",
      "haptic_feedback": "deskripsi haptic feedback"
    }}
  ],
  "medium_priority": [...],
  "nice_to_have": [...],
  "general_principles": [
    "prinsip desain aksesibel yang harus diterapkan"
  ],
  "testing_recommendations": [
    "rekomendasi untuk testing dengan user tunanetra"
  ]
}}

Fokus pada:
1. Navigasi yang bisa dilakukan dengan screen reader
2. Audio feedback yang jelas dan informatif
3. Haptic feedback yang meaningful
4. Konfirmasi transaksi yang aman dan jelas
5. Error handling yang accessible

Output HANYA JSON.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        try:
            result = json.loads(response.content[0].text)
        except json.JSONDecodeError:
            result = {
                "high_priority": [],
                "medium_priority": [],
                "nice_to_have": [],
                "raw_response": response.content[0].text
            }

        result["session_id"] = session_id
        result["generated_at"] = datetime.utcnow().isoformat()

        return result

    def _prepare_interactions_for_synthesis(self, interactions: List[Dict]) -> str:
        """Prepare interactions untuk prompt"""
        formatted = []

        for interaction in interactions:
            actor = interaction.get("actor", {})
            data = interaction.get("data", {})
            interaction_type = interaction.get("interaction_type", "")

            if interaction_type == "chat_message":
                formatted.append(
                    f"[{actor.get('role', 'unknown')}]: {data.get('content', '')}"
                )
            elif interaction_type == "voice_transcript":
                formatted.append(
                    f"[{actor.get('role', 'unknown')} - voice]: {data.get('transcript', '')}"
                )
            elif interaction_type == "insight":
                formatted.append(
                    f"[INSIGHT - {data.get('insight_type', '')}]: {data.get('content', '')} (source: {data.get('source', '')})"
                )
            elif interaction_type == "ai_response":
                formatted.append(
                    f"[AI Agent]: {data.get('ai_response', '')[:500]}..."
                )

        return "\n".join(formatted[-50:])  # Limit to last 50 interactions


# Singleton
_synthesizer: Optional[ArtifactSynthesizer] = None


def get_synthesizer() -> ArtifactSynthesizer:
    global _synthesizer
    if _synthesizer is None:
        _synthesizer = ArtifactSynthesizer()
    return _synthesizer
