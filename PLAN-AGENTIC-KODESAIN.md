# Plan: Agentic Ko-Desain untuk Aplikasi Pembayaran Mobile Tunanetra

## Overview

Membangun sistem agentic berbasis web untuk memfasilitasi ko-desain 3 pihak (AI Agent, UI/UX Designer, User Tunanetra) dalam mendesain aplikasi pembayaran mobile yang aksesibel.

## Tech Stack

| Komponen | Teknologi |
|----------|-----------|
| Backend | Python + FastAPI |
| Frontend | React/Vue.js |
| LLM | Claude API |
| TTS | Edge TTS + SSML (emosi) |
| STT | Whisper API |
| Database | PostgreSQL + MongoDB + Redis |
| Real-time | WebSocket + Y.js CRDT |
| Bahasa | Bahasa Indonesia |

---

## Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  Designer UI    │  │  VI User UI     │  │  Observer UI    │         │
│  │  (Visual Canvas)│  │  (Screen Reader │  │  (Research      │         │
│  │                 │  │   + TTS/STT)    │  │   Analytics)    │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
│           └────────────────────┼────────────────────┘                   │
│                    ┌───────────▼───────────┐                            │
│                    │  Shared: Y.js CRDT    │                            │
│                    │  + WebSocket Client   │                            │
│                    └───────────┬───────────┘                            │
└────────────────────────────────┼────────────────────────────────────────┘
                                 │ WSS/HTTPS
┌────────────────────────────────┼────────────────────────────────────────┐
│                        API GATEWAY (Nginx)                               │
└────────────────────────────────┼────────────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────────────┐
│                       APPLICATION LAYER                                  │
│  ┌─────────────────────────────▼─────────────────────────────┐          │
│  │              FastAPI Application Server                    │          │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │          │
│  │  │ REST API    │  │ WebSocket   │  │ Background      │   │          │
│  │  │ - Sessions  │  │ - Real-time │  │ Tasks (Celery)  │   │          │
│  │  │ - Artifacts │  │ - CRDT Sync │  │ - TTS Gen       │   │          │
│  │  │ - Users     │  │ - Presence  │  │ - AI Analysis   │   │          │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘   │          │
│  └───────────────────────────────────────────────────────────┘          │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────┐          │
│  │              AI AGENT SERVICE                              │          │
│  │  ┌─────────────────┐  ┌─────────────────────────────────┐│          │
│  │  │ Claude API      │  │ Agent Orchestrator              ││          │
│  │  │ - Streaming     │  │ - State Machine (4 Phases)      ││          │
│  │  │ - Tool Use      │  │ - Tool Execution                ││          │
│  │  └─────────────────┘  └─────────────────────────────────┘│          │
│  │  ┌─────────────────┐  ┌─────────────────────────────────┐│          │
│  │  │ Data Capture    │  │ Synthesis Engine                ││          │
│  │  │ - Interaction   │  │ - Empathy Map Generation        ││          │
│  │  │ - Annotation    │  │ - Journey Map Generation        ││          │
│  │  └─────────────────┘  └─────────────────────────────────┘│          │
│  └───────────────────────────────────────────────────────────┘          │
│                                                                          │
│  ┌───────────────────────────────────────────────────────────┐          │
│  │              VOICE SERVICE                                 │          │
│  │  ┌─────────────────┐  ┌─────────────────────────────────┐│          │
│  │  │ TTS (Edge TTS)  │  │ STT (Whisper)                   ││          │
│  │  │ - SSML Emotion  │  │ - Real-time Streaming           ││          │
│  │  │ - ID Voices     │  │ - Bahasa Indonesia              ││          │
│  │  └─────────────────┘  └─────────────────────────────────┘│          │
│  └───────────────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
┌────────────────────────────────┼────────────────────────────────────────┐
│                          DATA LAYER                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ PostgreSQL  │  │ Redis       │  │ MongoDB     │  │ MinIO/S3    │    │
│  │ - Users     │  │ - Sessions  │  │ - Artifacts │  │ - Audio     │    │
│  │ - Research  │  │ - Pub/Sub   │  │ - CRDT Docs │  │ - Assets    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Flow Ko-Desain (4 Fase)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     FLOW PROSES KO-DESAIN                                │
└─────────────────────────────────────────────────────────────────────────┘

    FASE 1: SHARED FRAMING
    ┌─────────────────────────────────────────────────────────────────────┐
    │  User Tunanetra:                                                    │
    │  - Menjelaskan pengalaman non-visual (via voice → STT)             │
    │  - Mendemonstrasikan hambatan interaksi                             │
    │                                                                     │
    │  UI/UX Designer:                                                    │
    │  - Simulasi penggunaan non-visual (blindfold mode)                 │
    │  - Mencatat struktur tugas dan hambatan                            │
    │                                                                     │
    │  AI Agent:                                                          │
    │  - Menangkap semua interaksi (voice transcript, actions)           │
    │  - Mengorganisasi data sebagai basis refleksi                      │
    │  - Memberikan TTS feedback untuk user tunanetra                    │
    └─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    FASE 2: PERTUKARAN PERSPEKTIF
    ┌─────────────────────────────────────────────────────────────────────┐
    │  Semua Pihak:                                                       │
    │  - Berbagi pemahaman dari pengalaman bersama                       │
    │  - Mengklarifikasi perspektif masing-masing                        │
    │                                                                     │
    │  Kolaborasi:                                                        │
    │  - Menyusun Empathy Map bersama                                    │
    │    (Says, Thinks, Does, Feels + Hears, Touches)                    │
    │  - Menyusun User Journey Map                                       │
    │                                                                     │
    │  AI Agent:                                                          │
    │  - Memfasilitasi diskusi                                           │
    │  - Mengisi template artifact berdasarkan data fase 1               │
    │  - Menyarankan insight yang mungkin terlewat                       │
    └─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    FASE 3: NEGOSIASI MAKNA
    ┌─────────────────────────────────────────────────────────────────────┐
    │  Semua Pihak:                                                       │
    │  - Review artifact yang telah dibuat                               │
    │  - Menyepakati pemahaman empatik bersama                           │
    │  - Mengidentifikasi poin konsensus dan perbedaan                   │
    │                                                                     │
    │  Output:                                                            │
    │  - Sketsa solusi desain awal                                       │
    │  - Prioritas fitur aksesibilitas                                   │
    │                                                                     │
    │  AI Agent:                                                          │
    │  - Mediasi perbedaan perspektif                                    │
    │  - Menyarankan kompromi/solusi                                     │
    │  - Generate sketsa desain berdasarkan kesepakatan                  │
    └─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
    FASE 4: REFLEKSI & ITERASI
    ┌─────────────────────────────────────────────────────────────────────┐
    │  Semua Pihak:                                                       │
    │  - Refleksi terhadap perubahan pemahaman                           │
    │  - Review dan perbaiki sketsa desain                               │
    │  - Validasi dengan user tunanetra                                  │
    │                                                                     │
    │  Output:                                                            │
    │  - Sketsa desain final                                             │
    │  - Mock-up (untuk tahap selanjutnya)                               │
    │  - Dokumentasi insight dan lessons learned                         │
    │                                                                     │
    │  AI Agent:                                                          │
    │  - Generate laporan perubahan pemahaman                            │
    │  - Identifikasi area improvement                                   │
    │  - Export semua artifact                                           │
    └─────────────────────────────────────────────────────────────────────┘
```

---

## Implementasi Step-by-Step

### Phase 1: Setup & Infrastructure (Week 1-2)

#### 1.1 Project Setup
```
codesign-platform/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/v1/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   └── workers/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── stores/
│   └── package.json
└── docker-compose.yml
```

#### 1.2 Database Schema (PostgreSQL)
```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) CHECK (role IN ('designer', 'vi_user', 'researcher')),
    accessibility_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Co-Design Sessions
CREATE TABLE codesign_sessions (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    current_phase VARCHAR(50) DEFAULT 'setup',
    experiment_mode VARCHAR(50) DEFAULT 'with_ai',
    config JSONB DEFAULT '{}',
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Phase Transitions (untuk research)
CREATE TABLE phase_transitions (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES codesign_sessions(id),
    from_phase VARCHAR(50),
    to_phase VARCHAR(50),
    triggered_by UUID REFERENCES users(id),
    transitioned_at TIMESTAMP DEFAULT NOW()
);
```

#### 1.3 Dependencies (requirements.txt)
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
websockets==12.0
anthropic==0.18.0
edge-tts==6.1.9
openai-whisper==20231117
sqlalchemy==2.0.25
motor==3.3.2
redis==5.0.1
celery==5.3.6
ypy-websocket==0.12.1
pydantic==2.6.0
python-jose[cryptography]==3.3.0
```

---

### Phase 2: Core Backend Services (Week 3-4)

#### 2.1 AI Agent Service
**File: `backend/app/services/ai_agent/agent.py`**

```python
class CoDesignAgent:
    """AI Agent untuk memfasilitasi ko-desain"""

    def __init__(self, claude_client, voice_service):
        self.claude = claude_client
        self.voice = voice_service
        self.phase_prompts = self._load_phase_prompts()

    async def process_message(
        self,
        session_id: str,
        message: str,
        sender_role: str,
        request_tts: bool = False
    ) -> AIResponse:
        """Proses pesan dan generate respons dengan TTS opsional"""

        context = await self.get_session_context(session_id)
        system_prompt = self.phase_prompts[context.current_phase]

        response = await self.claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system_prompt,
            messages=self._build_messages(context, message)
        )

        response_text = response.content[0].text

        # Generate TTS dengan emosi untuk user tunanetra
        tts_audio = None
        if request_tts:
            emotion = self._detect_emotion(response_text, context)
            tts_audio = await self.voice.text_to_speech_emotional(
                text=response_text,
                emotion=emotion,
                language="id-ID"
            )

        return AIResponse(
            text=response_text,
            tts_audio_url=tts_audio
        )
```

#### 2.2 Voice Service dengan Emosi (Edge TTS + SSML)
**File: `backend/app/services/voice/tts.py`**

```python
import edge_tts

class EmotionalTTSService:
    """TTS dengan dukungan emosi menggunakan SSML"""

    EMOTIONS_SSML = {
        "empathy": '<prosody rate="slow" pitch="-5%">',
        "encouraging": '<prosody rate="medium" pitch="+5%">',
        "questioning": '<prosody rate="medium" pitch="+10%">',
        "neutral": '',
        "excited": '<prosody rate="fast" pitch="+15%">',
    }

    # Voice Indonesia dari Edge TTS
    VOICES = {
        "male": "id-ID-ArdiNeural",
        "female": "id-ID-GadisNeural"
    }

    async def text_to_speech_emotional(
        self,
        text: str,
        emotion: str = "neutral",
        voice_gender: str = "female",
        language: str = "id-ID"
    ) -> str:
        """Generate audio dengan emosi menggunakan SSML"""

        voice = self.VOICES.get(voice_gender, self.VOICES["female"])
        ssml_tag = self.EMOTIONS_SSML.get(emotion, "")
        close_tag = "</prosody>" if ssml_tag else ""

        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{language}">
            <voice name="{voice}">
                {ssml_tag}{text}{close_tag}
            </voice>
        </speak>
        """

        communicate = edge_tts.Communicate(ssml, voice)
        audio_path = f"/tmp/audio_{uuid4()}.mp3"
        await communicate.save(audio_path)

        # Upload ke storage dan return URL
        return await self.upload_audio(audio_path)
```

#### 2.3 WebSocket Handler untuk Real-time
**File: `backend/app/api/websocket/handler.py`**

```python
from fastapi import WebSocket
from ypy_websocket import WebsocketServer

class SessionWebSocketHandler:
    """Handler untuk real-time collaboration"""

    async def handle_connection(self, websocket: WebSocket, session_id: str):
        await websocket.accept()

        while True:
            data = await websocket.receive_json()

            match data["type"]:
                case "voice_input":
                    # Proses voice ke STT
                    transcript = await self.stt.transcribe(data["audio"])
                    # Kirim ke AI agent
                    response = await self.agent.process_message(
                        session_id, transcript, data["sender_role"],
                        request_tts=data.get("request_tts", True)
                    )
                    await self.broadcast_response(session_id, response)

                case "crdt_update":
                    # Sync artifact edit ke semua participant
                    await self.broadcast_crdt(session_id, data["update"])

                case "phase_advance":
                    # Advance ke fase berikutnya
                    await self.advance_phase(session_id)
```

---

### Phase 3: Frontend Implementation (Week 5-6)

#### 3.1 Komponen Utama

**1. Designer Interface**
- Canvas untuk menggambar sketsa
- Collaborative editing (Y.js)
- Template empathy map & journey map

**2. VI User Interface (Aksesibel)**
- Full keyboard navigation
- Screen reader support (ARIA)
- Voice input/output
- Audio feedback untuk semua aksi

**3. Observer Interface (Research)**
- Live monitoring session
- Metrics dashboard
- Recording playback

#### 3.2 Accessibility Implementation
**File: `frontend/src/components/accessibility/VoiceInterface.tsx`**

```typescript
const VoiceInterface: React.FC = () => {
  const [isListening, setIsListening] = useState(false);
  const { sendVoice, playTTS } = useWebSocket();

  // Keyboard shortcuts
  useKeyboardShortcuts({
    'Alt+V': () => toggleVoiceInput(),
    'Alt+S': () => stopTTS(),
    'Alt+R': () => repeatLastResponse(),
    'Alt+H': () => announceHelp(),
  });

  // ARIA live region untuk announcements
  return (
    <div role="application" aria-label="Voice Interface">
      <div role="status" aria-live="polite" id="status-announcer" />
      <div role="alert" aria-live="assertive" id="alert-announcer" />

      <button
        onClick={toggleVoiceInput}
        aria-pressed={isListening}
        aria-label={isListening ? "Berhenti bicara" : "Mulai bicara"}
      >
        {isListening ? "🎤 Mendengarkan..." : "🎤 Tekan untuk bicara"}
      </button>
    </div>
  );
};
```

---

### Phase 4: AI Agent Tools & Synthesis (Week 7-8)

#### 4.1 Claude Tools untuk Ko-Desain
```python
CODESIGN_TOOLS = [
    {
        "name": "capture_insight",
        "description": "Tangkap insight dari interaksi user",
        "input_schema": {
            "type": "object",
            "properties": {
                "insight_type": {"enum": ["pain_point", "need", "emotion", "behavior"]},
                "content": {"type": "string"},
                "source": {"enum": ["vi_user", "designer", "observation"]},
                "empathy_category": {"enum": ["says", "thinks", "does", "feels", "hears", "touches"]}
            }
        }
    },
    {
        "name": "add_to_journey_map",
        "description": "Tambahkan touchpoint ke journey map",
        "input_schema": {
            "type": "object",
            "properties": {
                "stage": {"type": "string"},
                "touchpoint": {"type": "string"},
                "emotion": {"type": "string"},
                "pain_point": {"type": "string"},
                "accessibility_note": {"type": "string"}
            }
        }
    },
    {
        "name": "suggest_design_element",
        "description": "Sarankan elemen desain berdasarkan insight",
        "input_schema": {
            "type": "object",
            "properties": {
                "element_type": {"enum": ["button", "navigation", "feedback", "confirmation"]},
                "description": {"type": "string"},
                "accessibility_feature": {"type": "string"},
                "rationale": {"type": "string"}
            }
        }
    },
    {
        "name": "mediate_disagreement",
        "description": "Mediasi perbedaan perspektif",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "perspective_a": {"type": "string"},
                "perspective_b": {"type": "string"},
                "suggested_compromise": {"type": "string"}
            }
        }
    }
]
```

#### 4.2 Empathy Map Generator
```python
async def generate_empathy_map(self, session_id: str) -> EmpathyMap:
    """Generate empathy map dari data interaksi"""

    interactions = await self.get_session_interactions(session_id)

    prompt = f"""
    Berdasarkan interaksi berikut dari sesi ko-desain dengan user tunanetra,
    buatlah empathy map yang komprehensif:

    {interactions}

    Format output sebagai JSON dengan kategori:
    - says: Apa yang dikatakan user
    - thinks: Apa yang mungkin dipikirkan user
    - does: Apa yang dilakukan user
    - feels: Emosi yang dirasakan user
    - hears: Feedback audio yang diterima (untuk tunanetra)
    - touches: Interaksi haptic (untuk tunanetra)
    """

    response = await self.claude.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
    )

    return EmpathyMap.parse_raw(response.content[0].text)
```

---

### Phase 5: Research & Comparison (Week 9-10)

#### 5.1 Experiment Mode
```python
class ExperimentManager:
    """Manage paired sessions for with-AI vs without-AI comparison"""

    async def create_experiment_pair(self, name: str):
        """Buat pasangan sesi untuk perbandingan"""

        group_id = uuid4()

        # Sesi TANPA AI (control)
        control = await self.create_session(
            name=f"{name} - Tanpa AI",
            experiment_mode="without_ai",
            config={"ai_enabled": False}
        )

        # Sesi DENGAN AI (treatment)
        treatment = await self.create_session(
            name=f"{name} - Dengan AI",
            experiment_mode="with_ai",
            config={"ai_enabled": True}
        )

        return ExperimentPair(
            group_id=group_id,
            control_session=control,
            treatment_session=treatment
        )

    async def generate_comparison_report(self, group_id: str):
        """Generate laporan perbandingan"""

        return ComparisonReport(
            time_metrics={...},
            interaction_metrics={...},
            artifact_quality={...},
            collaboration_patterns={...}
        )
```

---

## Metrics untuk Research

| Kategori | Metrik | Deskripsi |
|----------|--------|-----------|
| Waktu | Duration per phase | Waktu yang dihabiskan di setiap fase |
| Interaksi | Turn-taking balance | Keseimbangan partisipasi antar pihak |
| Artifact | Empathy map completeness | Kelengkapan empathy map |
| Artifact | Journey map detail | Detail dan kedalaman journey map |
| Kolaborasi | Cross-references | Frekuensi referensi silang antar partisipan |
| Aksesibilitas | Accessibility mentions | Jumlah pertimbangan aksesibilitas |

---

## Verification Plan

### 1. Unit Tests
```bash
pytest backend/tests/ -v
```

### 2. Integration Tests
- Test WebSocket connection dan CRDT sync
- Test AI agent response dengan TTS
- Test phase transitions

### 3. End-to-End Testing
1. Jalankan docker-compose untuk semua services
2. Buat session baru dengan 3 user (designer, vi_user, observer)
3. Test flow lengkap 4 fase ko-desain
4. Verifikasi:
   - TTS berfungsi untuk user tunanetra
   - Real-time sync berfungsi
   - Artifact tersimpan dengan benar
   - AI memberikan respons yang kontekstual

### 4. Accessibility Testing
- Test dengan screen reader (NVDA/VoiceOver)
- Test keyboard-only navigation
- Test voice input/output flow

---

## Files yang Perlu Dibuat

### Backend Critical Files
1. `backend/app/main.py` - FastAPI app entry point
2. `backend/app/services/ai_agent/agent.py` - Core AI agent
3. `backend/app/services/voice/tts.py` - Edge TTS dengan emosi
4. `backend/app/services/voice/stt.py` - Whisper STT
5. `backend/app/api/websocket/handler.py` - WebSocket handler
6. `backend/app/api/v1/sessions.py` - Session endpoints
7. `backend/app/models/schemas.py` - Pydantic models

### Frontend Critical Files
1. `frontend/src/components/session/SessionRoom.tsx` - Main session UI
2. `frontend/src/components/artifacts/EmpathyMap.tsx` - Empathy map editor
3. `frontend/src/components/artifacts/JourneyMap.tsx` - Journey map editor
4. `frontend/src/components/accessibility/VoiceInterface.tsx` - Voice I/O
5. `frontend/src/hooks/useWebSocket.ts` - WebSocket hook
6. `frontend/src/hooks/useYjs.ts` - Y.js CRDT hook

---

## Summary

Sistem ini memungkinkan:
1. **Ko-desain 3 pihak** dengan fasilitasi AI agent
2. **Aksesibilitas penuh** untuk user tunanetra via TTS/STT
3. **Real-time collaboration** menggunakan WebSocket + Y.js
4. **Penelitian komparatif** dengan mode with-AI vs without-AI
5. **Artifact generation** (empathy maps, journey maps) secara kolaboratif
