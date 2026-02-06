"""
Database connections untuk PostgreSQL dan MongoDB
"""
import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from motor.motor_asyncio import AsyncIOMotorClient
from typing import AsyncGenerator

from app.config import settings


# PostgreSQL - SQLAlchemy Async
# Detect if using cloud database (Supabase) by checking host
is_cloud_db = "supabase" in settings.POSTGRES_HOST.lower()

# SSL context for cloud databases
connect_args = {}
if is_cloud_db:
    # Supabase requires SSL
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=5,  # Reduced for cloud free tier
    max_overflow=10,
    connect_args=connect_args
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    """Base class untuk SQLAlchemy models"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency untuk mendapatkan database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# MongoDB - Motor Async
class MongoDB:
    """MongoDB client wrapper"""

    client: AsyncIOMotorClient = None
    db = None

    async def connect(self):
        """Connect to MongoDB"""
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.MONGODB_DB]
        print(f"Connected to MongoDB: {settings.MONGODB_DB}")

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")

    @property
    def artifacts(self):
        """Collection untuk artifacts (empathy maps, journey maps, etc.)"""
        return self.db.artifacts

    @property
    def interaction_logs(self):
        """Collection untuk interaction logs"""
        return self.db.interaction_logs

    @property
    def ai_agent_state(self):
        """Collection untuk AI agent state"""
        return self.db.ai_agent_state


mongodb = MongoDB()


async def get_mongodb():
    """Dependency untuk mendapatkan MongoDB instance"""
    return mongodb
