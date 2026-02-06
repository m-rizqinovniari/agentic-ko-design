"""
Redis client untuk caching, pub/sub, dan session management
"""
import redis.asyncio as redis
from typing import Optional, Any
import json

from app.config import settings


class RedisClient:
    """Redis client wrapper dengan utility methods"""

    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None

    async def connect(self):
        """Connect to Redis"""
        self.client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        self.pubsub = self.client.pubsub()
        print("Connected to Redis")

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.close()
        if self.client:
            await self.client.close()
            print("Disconnected from Redis")

    # Session Presence Methods
    async def add_participant(self, session_id: str, user_id: str) -> None:
        """Tambah participant ke session"""
        await self.client.sadd(f"session:{session_id}:participants", user_id)

    async def remove_participant(self, session_id: str, user_id: str) -> None:
        """Hapus participant dari session"""
        await self.client.srem(f"session:{session_id}:participants", user_id)

    async def get_participants(self, session_id: str) -> set:
        """Get semua participants dalam session"""
        return await self.client.smembers(f"session:{session_id}:participants")

    async def set_presence(self, session_id: str, user_id: str, data: dict) -> None:
        """Set presence data untuk user dalam session"""
        key = f"session:{session_id}:presence:{user_id}"
        await self.client.hset(key, mapping=data)
        await self.client.expire(key, 300)  # 5 minutes TTL

    async def get_presence(self, session_id: str, user_id: str) -> dict:
        """Get presence data untuk user"""
        return await self.client.hgetall(f"session:{session_id}:presence:{user_id}")

    # Pub/Sub Methods
    async def publish(self, channel: str, message: dict) -> None:
        """Publish message ke channel"""
        await self.client.publish(channel, json.dumps(message))

    async def subscribe(self, channel: str):
        """Subscribe ke channel"""
        await self.pubsub.subscribe(channel)

    async def unsubscribe(self, channel: str):
        """Unsubscribe dari channel"""
        await self.pubsub.unsubscribe(channel)

    # Cache Methods
    async def cache_set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set cache dengan TTL (default 1 jam)"""
        if isinstance(value, dict):
            value = json.dumps(value)
        await self.client.setex(key, ttl, value)

    async def cache_get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        value = await self.client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def cache_delete(self, key: str) -> None:
        """Delete cache"""
        await self.client.delete(key)

    # Typing Indicator
    async def set_typing(self, session_id: str, user_id: str) -> None:
        """Set user sebagai sedang mengetik"""
        await self.client.sadd(f"session:{session_id}:typing", user_id)
        await self.client.expire(f"session:{session_id}:typing", 5)

    async def clear_typing(self, session_id: str, user_id: str) -> None:
        """Clear typing indicator"""
        await self.client.srem(f"session:{session_id}:typing", user_id)

    async def get_typing_users(self, session_id: str) -> set:
        """Get users yang sedang mengetik"""
        return await self.client.smembers(f"session:{session_id}:typing")


redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Dependency untuk mendapatkan Redis client"""
    return redis_client
