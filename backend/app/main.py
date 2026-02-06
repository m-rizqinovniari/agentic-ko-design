"""
Main FastAPI Application Entry Point
Ko-Desain Platform untuk Aplikasi Pembayaran Mobile Tunanetra
"""
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.config import settings
from app.core.database import engine, Base, mongodb
from app.core.redis_client import redis_client
from app.api.v1 import router as api_v1_router
from app.api.websocket import websocket_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events

    Startup:
    - Create database tables
    - Connect to MongoDB
    - Connect to Redis

    Shutdown:
    - Close connections
    """
    # Startup
    print("=" * 50)
    print("Starting Ko-Desain Platform...")
    print("=" * 50)

    # Create directories first
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.AUDIO_DIR, exist_ok=True)
    print("[OK] Upload directories created")

    # Check Anthropic API key
    if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY.startswith("sk-ant-api03-xxxxx"):
        print("[WARNING] ANTHROPIC_API_KEY tidak dikonfigurasi!")
        print("          AI Agent tidak akan berfungsi.")
        print("          Edit backend/.env dan masukkan API key dari https://console.anthropic.com")

    # Create PostgreSQL tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("[OK] PostgreSQL connected & tables created")
    except Exception as e:
        print(f"[ERROR] PostgreSQL connection failed: {e}")
        print("        Pastikan credentials di .env sudah benar.")
        print("        Lihat SETUP-CLOUD.md untuk panduan Supabase.")

    # Connect MongoDB
    try:
        await mongodb.connect()
        print("[OK] MongoDB connected")
    except Exception as e:
        print(f"[ERROR] MongoDB connection failed: {e}")
        print("        Pastikan MONGODB_URL di .env sudah benar.")
        print("        Lihat SETUP-CLOUD.md untuk panduan MongoDB Atlas.")

    # Connect Redis
    try:
        await redis_client.connect()
        print("[OK] Redis connected")
    except Exception as e:
        print(f"[ERROR] Redis connection failed: {e}")
        print("        Pastikan REDIS_URL di .env sudah benar.")
        print("        Lihat SETUP-CLOUD.md untuk panduan Upstash.")

    print("=" * 50)
    print("Ko-Desain Platform started!")
    print("API Docs: http://localhost:8000/docs")
    print("=" * 50)

    yield

    # Shutdown
    print("Shutting down Ko-Desain Platform...")
    await mongodb.disconnect()
    await redis_client.disconnect()
    print("Ko-Desain Platform stopped")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## Ko-Desain Platform

    Platform untuk memfasilitasi ko-desain 3 pihak:
    - **AI Agent**: Memfasilitasi diskusi dan menangkap insight
    - **UI/UX Designer**: Merancang solusi desain
    - **User Tunanetra**: Memberikan perspektif dan pengalaman

    ### Fitur Utama
    - Real-time collaboration dengan WebSocket
    - AI-powered facilitation dengan Claude API
    - Text-to-Speech dengan emosi untuk aksesibilitas
    - Speech-to-Text untuk input suara
    - Collaborative artifact editing (Empathy Map, Journey Map)
    - Research comparison mode (with AI vs without AI)
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for audio
app.mount("/audio", StaticFiles(directory=settings.AUDIO_DIR), name="audio")

# API routes
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


# WebSocket endpoint
@app.websocket("/ws/session/{session_id}")
async def websocket_session(
    websocket: WebSocket,
    session_id: str,
    token: str
):
    """
    WebSocket endpoint untuk real-time collaboration dalam session

    Connect dengan: ws://host/ws/session/{session_id}?token={jwt_token}
    """
    from app.core.database import mongodb as mongo_instance
    await websocket_endpoint(websocket, session_id, token, mongodb=mongo_instance)


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint dengan info aplikasi"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "Ko-Desain Platform untuk Aplikasi Pembayaran Mobile Tunanetra",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
