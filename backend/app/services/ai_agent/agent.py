"""
Core AI Agent untuk Ko-Desain
Menggunakan Claude API dengan tool use
"""
import anthropic
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import uuid

from app.config import settings
from app.services.ai_agent.prompts import PhasePrompts
from app.services.ai_agent.tools import CODESIGN_TOOLS, get_tools_for_phase
from app.services.voice.tts import EmotionalTTSService
from app.models.schemas import AIMessageResponse, SessionPhase


class CoDesignAgent:
    """
    AI Agent untuk memfasilitasi sesi ko-desain

    Agent ini bertanggung jawab untuk:
    - Memfasilitasi diskusi antara designer dan user tunanetra
    - Menangkap dan mengorganisasi insight
    - Membantu membuat empathy map dan journey map
    - Memberikan saran desain yang aksesibel
    """

    def __init__(
        self,
        voice_service: Optional[EmotionalTTSService] = None,
        mongodb=None
    ):
        """
        Initialize AI Agent

        Args:
            voice_service: Service untuk TTS dengan emosi
            mongodb: MongoDB client untuk menyimpan data
        """
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.voice_service = voice_service or EmotionalTTSService()
        self.mongodb = mongodb
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.CLAUDE_MAX_TOKENS

    async def process_message(
        self,
        session_id: str,
        message: str,
        sender_role: str,
        current_phase: str,
        context: Optional[Dict[str, Any]] = None,
        request_tts: bool = True
    ) -> AIMessageResponse:
        """
        Proses pesan dan generate respons

        Args:
            session_id: ID sesi ko-desain
            message: Pesan dari user
            sender_role: Role pengirim (designer/vi_user)
            current_phase: Fase saat ini
            context: Konteks tambahan (artifacts, history, dll)
            request_tts: Apakah perlu generate TTS

        Returns:
            AIMessageResponse dengan respons dan optional TTS audio
        """
        # Get system prompt untuk fase ini
        system_prompt = PhasePrompts.get_prompt(current_phase)

        # Build context untuk Claude
        enhanced_context = self._build_context(
            session_id=session_id,
            sender_role=sender_role,
            current_phase=current_phase,
            context=context
        )

        # Combine system prompt dengan context
        full_system = f"{system_prompt}\n\nKONTEKS SESI:\n{enhanced_context}"

        # Get relevant tools
        tools = get_tools_for_phase(current_phase)

        # Call Claude API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=full_system,
            tools=tools,
            messages=[
                {
                    "role": "user",
                    "content": f"[{sender_role.upper()}]: {message}"
                }
            ]
        )

        # Process response
        response_text = ""
        tools_used = []
        tool_results = []

        for content_block in response.content:
            if content_block.type == "text":
                response_text = content_block.text
            elif content_block.type == "tool_use":
                # Process tool call
                tool_name = content_block.name
                tool_input = content_block.input
                tools_used.append(tool_name)

                # Execute tool and store result
                tool_result = await self._execute_tool(
                    session_id=session_id,
                    tool_name=tool_name,
                    tool_input=tool_input
                )
                tool_results.append({
                    "tool": tool_name,
                    "input": tool_input,
                    "result": tool_result
                })

        # Detect emotion dari response untuk TTS
        emotion = self._detect_emotion(response_text, current_phase)

        # Generate TTS jika diminta
        tts_audio_url = None
        if request_tts and response_text:
            tts_audio_url = await self.voice_service.text_to_speech_emotional(
                text=response_text,
                emotion=emotion,
                language="id-ID"
            )

        # Extract suggestions dari response
        suggestions = self._extract_suggestions(response_text, tool_results)

        # Log interaction
        await self._log_interaction(
            session_id=session_id,
            phase=current_phase,
            message=message,
            sender_role=sender_role,
            response=response_text,
            tools_used=tools_used,
            tool_results=tool_results
        )

        return AIMessageResponse(
            response=response_text,
            suggestions=suggestions,
            tools_used=tools_used,
            tts_audio_url=tts_audio_url,
            emotion_detected=emotion
        )

    def _build_context(
        self,
        session_id: str,
        sender_role: str,
        current_phase: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build context string untuk Claude"""
        context_parts = [
            f"Session ID: {session_id}",
            f"Fase Saat Ini: {current_phase}",
            f"Pengirim Pesan: {sender_role}"
        ]

        if context:
            if "participants" in context:
                participants = ", ".join([
                    f"{p['name']} ({p['role']})"
                    for p in context["participants"]
                ])
                context_parts.append(f"Participants: {participants}")

            if "empathy_map" in context:
                context_parts.append(f"Empathy Map saat ini: {json.dumps(context['empathy_map'], indent=2)}")

            if "journey_map" in context:
                context_parts.append(f"Journey Map saat ini: {json.dumps(context['journey_map'], indent=2)}")

            if "recent_insights" in context:
                insights = "\n".join([f"- {i}" for i in context["recent_insights"]])
                context_parts.append(f"Insight Terbaru:\n{insights}")

        return "\n".join(context_parts)

    async def _execute_tool(
        self,
        session_id: str,
        tool_name: str,
        tool_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute tool call dan simpan hasilnya

        Args:
            session_id: ID sesi
            tool_name: Nama tool
            tool_input: Input untuk tool

        Returns:
            Hasil eksekusi tool
        """
        result = {
            "success": True,
            "tool": tool_name,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Store tool execution result ke MongoDB
        if self.mongodb:
            tool_doc = {
                "session_id": session_id,
                "tool_name": tool_name,
                "input": tool_input,
                "executed_at": datetime.utcnow()
            }

            if tool_name == "capture_insight":
                await self.mongodb.interaction_logs.insert_one({
                    **tool_doc,
                    "type": "insight",
                    "insight_type": tool_input.get("insight_type"),
                    "content": tool_input.get("content"),
                    "source": tool_input.get("source")
                })
                result["message"] = f"Insight '{tool_input.get('insight_type')}' berhasil dicatat"

            elif tool_name == "add_to_empathy_map":
                await self.mongodb.artifacts.update_one(
                    {"session_id": session_id, "artifact_type": "empathy_map"},
                    {
                        "$push": {
                            f"content.{tool_input.get('category')}": {
                                "text": tool_input.get("content"),
                                "source": tool_input.get("source"),
                                "timestamp": datetime.utcnow()
                            }
                        }
                    },
                    upsert=True
                )
                result["message"] = f"Item ditambahkan ke empathy map kategori '{tool_input.get('category')}'"

            elif tool_name == "add_to_journey_map":
                await self.mongodb.artifacts.update_one(
                    {"session_id": session_id, "artifact_type": "user_journey_map"},
                    {
                        "$push": {
                            "content.stages": {
                                "name": tool_input.get("stage"),
                                "order": tool_input.get("stage_order"),
                                "touchpoint": tool_input.get("touchpoint"),
                                "action": tool_input.get("action"),
                                "thought": tool_input.get("thought"),
                                "emotion": tool_input.get("emotion"),
                                "pain_point": tool_input.get("pain_point"),
                                "opportunity": tool_input.get("opportunity"),
                                "accessibility_note": tool_input.get("accessibility_note"),
                                "timestamp": datetime.utcnow()
                            }
                        }
                    },
                    upsert=True
                )
                result["message"] = f"Stage '{tool_input.get('stage')}' ditambahkan ke journey map"

            elif tool_name == "suggest_design_element":
                await self.mongodb.artifacts.update_one(
                    {"session_id": session_id, "artifact_type": "design_suggestions"},
                    {
                        "$push": {
                            "content.elements": {
                                "type": tool_input.get("element_type"),
                                "name": tool_input.get("name"),
                                "description": tool_input.get("description"),
                                "accessibility_features": tool_input.get("accessibility_features", []),
                                "audio_feedback": tool_input.get("audio_feedback"),
                                "haptic_feedback": tool_input.get("haptic_feedback"),
                                "rationale": tool_input.get("rationale"),
                                "timestamp": datetime.utcnow()
                            }
                        }
                    },
                    upsert=True
                )
                result["message"] = f"Saran desain '{tool_input.get('name')}' berhasil disimpan"

            elif tool_name == "mediate_disagreement":
                await self.mongodb.interaction_logs.insert_one({
                    **tool_doc,
                    "type": "mediation",
                    "topic": tool_input.get("topic"),
                    "compromise": tool_input.get("suggested_compromise")
                })
                result["message"] = "Mediasi berhasil dicatat"

            else:
                # Generic tool execution
                await self.mongodb.interaction_logs.insert_one(tool_doc)
                result["message"] = f"Tool '{tool_name}' berhasil dieksekusi"

        return result

    def _detect_emotion(self, text: str, phase: str) -> str:
        """
        Deteksi emosi yang sesuai untuk TTS berdasarkan konten dan fase

        Args:
            text: Teks respons
            phase: Fase ko-desain saat ini

        Returns:
            Nama emosi untuk TTS
        """
        text_lower = text.lower()

        # Check for question
        if "?" in text or "apakah" in text_lower or "bagaimana" in text_lower:
            return "questioning"

        # Check for empathetic content
        empathy_keywords = [
            "memahami", "terima kasih", "penting", "menghargai",
            "perasaan", "pengalaman", "kesulitan", "tantangan"
        ]
        if any(kw in text_lower for kw in empathy_keywords):
            return "empathy"

        # Check for encouraging content
        encourage_keywords = [
            "bagus", "hebat", "baik sekali", "tepat", "benar",
            "setuju", "ide bagus", "saran yang bagus"
        ]
        if any(kw in text_lower for kw in encourage_keywords):
            return "encouraging"

        # Check for excited/discovery content
        excited_keywords = [
            "menarik", "insight baru", "penemuan", "aha",
            "penting sekali", "kunci"
        ]
        if any(kw in text_lower for kw in excited_keywords):
            return "excited"

        # Default based on phase
        phase_emotions = {
            "shared_framing": "empathy",
            "perspective_exchange": "encouraging",
            "meaning_negotiation": "neutral",
            "reflection_iteration": "empathy",
            "complete": "encouraging"
        }

        return phase_emotions.get(phase, "neutral")

    def _extract_suggestions(
        self,
        response_text: str,
        tool_results: List[Dict]
    ) -> List[str]:
        """Extract suggestions dari response dan tool results"""
        suggestions = []

        # Extract from tool results
        for result in tool_results:
            if result.get("tool") == "suggest_design_element":
                inp = result.get("input", {})
                suggestions.append(
                    f"{inp.get('element_type')}: {inp.get('name')} - {inp.get('description')}"
                )

        # Simple extraction from text (bisa ditingkatkan dengan NLP)
        if "saran" in response_text.lower() or "rekomendasi" in response_text.lower():
            # Cari bullet points atau numbered items
            lines = response_text.split("\n")
            for line in lines:
                line = line.strip()
                if line.startswith(("- ", "• ", "* ", "1.", "2.", "3.")):
                    suggestions.append(line.lstrip("- •*123456789.").strip())

        return suggestions[:5]  # Limit to 5 suggestions

    async def _log_interaction(
        self,
        session_id: str,
        phase: str,
        message: str,
        sender_role: str,
        response: str,
        tools_used: List[str],
        tool_results: List[Dict]
    ):
        """Log interaction ke MongoDB untuk research"""
        if self.mongodb:
            await self.mongodb.interaction_logs.insert_one({
                "session_id": session_id,
                "phase": phase,
                "interaction_type": "ai_response",
                "actor": {
                    "role": sender_role
                },
                "data": {
                    "user_message": message,
                    "ai_response": response,
                    "tools_used": tools_used,
                    "tool_results": tool_results
                },
                "timestamp": datetime.utcnow()
            })

    async def generate_synthesis(
        self,
        session_id: str,
        artifact_type: str,
        interaction_data: List[Dict]
    ) -> Dict[str, Any]:
        """
        Generate synthesis untuk artifact berdasarkan interaction data

        Args:
            session_id: ID sesi
            artifact_type: Tipe artifact (empathy_map, user_journey_map)
            interaction_data: Data interaksi yang akan disintesis

        Returns:
            Hasil sintesis
        """
        if artifact_type == "empathy_map":
            prompt = self._build_empathy_map_synthesis_prompt(interaction_data)
        elif artifact_type == "user_journey_map":
            prompt = self._build_journey_map_synthesis_prompt(interaction_data)
        else:
            prompt = f"Sintesis data untuk {artifact_type}:\n{json.dumps(interaction_data)}"

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return {
            "session_id": session_id,
            "artifact_type": artifact_type,
            "synthesis": response.content[0].text,
            "generated_at": datetime.utcnow().isoformat()
        }

    def _build_empathy_map_synthesis_prompt(self, data: List[Dict]) -> str:
        """Build prompt untuk sintesis empathy map"""
        return f"""
        Berdasarkan data interaksi berikut dari sesi ko-desain dengan user tunanetra,
        buatlah empathy map yang komprehensif dalam format JSON.

        Data interaksi:
        {json.dumps(data, indent=2)}

        Format output JSON dengan kategori:
        - says: Apa yang dikatakan user tentang pengalaman mereka
        - thinks: Apa yang mungkin dipikirkan user (inference)
        - does: Tindakan yang dilakukan user
        - feels: Emosi yang dirasakan user
        - hears: Audio feedback yang diterima/diharapkan (khusus tunanetra)
        - touches: Interaksi haptic yang digunakan/diharapkan (khusus tunanetra)

        Setiap item harus memiliki 'text' dan 'source'.
        """

    def _build_journey_map_synthesis_prompt(self, data: List[Dict]) -> str:
        """Build prompt untuk sintesis journey map"""
        return f"""
        Berdasarkan data interaksi berikut dari sesi ko-desain,
        buatlah user journey map untuk proses pembayaran mobile oleh user tunanetra.

        Data interaksi:
        {json.dumps(data, indent=2)}

        Format output JSON dengan struktur:
        - persona_name: "User Tunanetra"
        - scenario: Deskripsi skenario pembayaran
        - stages: Array of stages, masing-masing berisi:
          - name: Nama stage
          - touchpoints: Array touchpoints
          - actions: Array aksi user
          - thoughts: Array pikiran user
          - emotions: Deskripsi emosi
          - pain_points: Array hambatan
          - opportunities: Array peluang improvement
          - accessibility_notes: Catatan aksesibilitas khusus
        """


# Singleton instance
_agent_instance: Optional[CoDesignAgent] = None


def get_agent(
    voice_service: Optional[EmotionalTTSService] = None,
    mongodb=None
) -> CoDesignAgent:
    """Get or create agent instance"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = CoDesignAgent(
            voice_service=voice_service,
            mongodb=mongodb
        )
    return _agent_instance
