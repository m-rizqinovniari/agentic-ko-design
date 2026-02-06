# Ko-Desain Platform

Platform agentic untuk memfasilitasi ko-desain 3 pihak (AI Agent, UI/UX Designer, User Tunanetra) dalam mendesain aplikasi pembayaran mobile yang aksesibel.

## Overview

Sistem ini mendukung proses ko-desain dengan 4 fase:
1. **Shared Framing** - User tunanetra menjelaskan pengalaman, designer simulasi non-visual
2. **Pertukaran Perspektif** - Membuat empathy map dan journey map bersama
3. **Negosiasi Makna** - Menyepakati pemahaman, membuat sketsa desain
4. **Refleksi & Iterasi** - Review dan perbaikan desain

## Tech Stack

| Komponen | Teknologi |
|----------|-----------|
| Backend | Python + FastAPI |
| Frontend | React + TypeScript + Vite |
| LLM | Claude API (Anthropic) |
| TTS | Edge TTS + SSML (emosi) |
| STT | Whisper API |
| Database | PostgreSQL + MongoDB + Redis |
| Real-time | WebSocket + Y.js CRDT |
| Bahasa | Bahasa Indonesia |

## Project Structure

```
agent-ko-design/
├── backend/
│   ├── app/
│   │   ├── api/              # REST API endpoints
│   │   │   ├── v1/           # API v1 routes
│   │   │   └── websocket/    # WebSocket handlers
│   │   ├── core/             # Core utilities (DB, security, Redis)
│   │   ├── models/           # SQLAlchemy & Pydantic models
│   │   ├── services/         # Business logic
│   │   │   ├── ai_agent/     # Claude AI integration
│   │   │   └── voice/        # TTS/STT services
│   │   └── main.py           # FastAPI app entry
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── accessibility/  # Voice interface, screen reader
│   │   │   ├── artifacts/      # Empathy map, journey map
│   │   │   └── session/        # Session room
│   │   ├── hooks/            # Custom hooks
│   │   ├── services/         # API clients
│   │   └── types/            # TypeScript types
│   └── package.json
├── docker-compose.yml
└── PLAN-AGENTIC-KODESAIN.md  # Detailed implementation plan
```

## Quick Start

### Option A: Cloud Database (Recommended - No Docker Required)

#### Prerequisites
- Python 3.11+
- Node.js 18+
- Account cloud database gratis:
  - [Supabase](https://supabase.com) - PostgreSQL
  - [MongoDB Atlas](https://mongodb.com/atlas) - MongoDB
  - [Upstash](https://upstash.com) - Redis
  - [Anthropic Console](https://console.anthropic.com) - Claude API

#### Setup

1. **Ikuti panduan [SETUP-CLOUD.md](SETUP-CLOUD.md)** untuk membuat database cloud

2. **Edit `backend/.env`** dan masukkan credentials:
   ```env
   POSTGRES_HOST=db.xxxxx.supabase.co
   POSTGRES_PASSWORD=your-supabase-password
   MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/kodesain_artifacts
   REDIS_URL=rediss://default:xxxxx@xxx.upstash.io:6379
   ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
   ```

3. **Jalankan setup script (Windows)**
   ```bash
   setup-local.bat
   ```

4. **Jalankan aplikasi**

   Terminal 1 - Backend:
   ```bash
   run-backend.bat
   ```

   Terminal 2 - Frontend:
   ```bash
   run-frontend.bat
   ```

### Option B: Docker (Full Local)

#### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Anthropic API Key

#### Setup

```bash
# Copy environment file
cp backend/.env.example backend/.env
# Edit .env and add ANTHROPIC_API_KEY

# Start all services
docker-compose up -d

# Start frontend
cd frontend && npm install && npm run dev
```

### Access

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Features

### For User Tunanetra (VI User)
- Full keyboard navigation
- Screen reader support (ARIA live regions)
- Voice input (STT) untuk berbicara
- Voice output (TTS) dengan emosi
- Audio feedback untuk semua aksi

### For UI/UX Designer
- Collaborative canvas untuk sketsa
- Real-time editing dengan Y.js CRDT
- Template empathy map & journey map
- AI suggestions untuk desain aksesibel

### For Research
- Mode experiment (with AI vs without AI)
- Interaction logging
- Metrics tracking
- Comparison reports

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/me` - Get current user

### Sessions
- `GET /api/v1/sessions` - List sessions
- `POST /api/v1/sessions` - Create session
- `POST /api/v1/sessions/{id}/start` - Start session
- `POST /api/v1/sessions/{id}/advance` - Advance phase

### AI Agent
- `POST /api/v1/ai/sessions/{id}/message` - Send message to AI
- `POST /api/v1/ai/sessions/{id}/synthesize` - Request artifact synthesis
- `GET /api/v1/ai/sessions/{id}/suggestions` - Get AI suggestions

### Voice
- `POST /api/v1/voice/tts` - Text to Speech
- `POST /api/v1/voice/stt` - Speech to Text

### WebSocket
- `ws://host/ws/session/{session_id}?token={jwt}` - Real-time session

## Keyboard Shortcuts (Voice Interface)

| Shortcut | Action |
|----------|--------|
| Alt+V | Toggle voice input |
| Alt+S | Stop/Start TTS |
| Alt+R | Repeat last response |
| Alt+H | Help |
| Escape | Cancel |

## Environment Variables

```env
# Required
ANTHROPIC_API_KEY=your-api-key

# Database
POSTGRES_HOST=localhost
POSTGRES_DB=kodesain
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request
