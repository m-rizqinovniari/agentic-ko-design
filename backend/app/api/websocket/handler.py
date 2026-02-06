"""
WebSocket handler untuk real-time collaboration
"""
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set, Optional, Any
import json
from datetime import datetime
from uuid import uuid4

from app.core.security import verify_token
from app.core.redis_client import redis_client
from app.services.ai_agent import CoDesignAgent
from app.services.voice import EmotionalTTSService, WhisperSTTService


class ConnectionManager:
    """
    Manage WebSocket connections untuk sessions

    Handles:
    - Connection lifecycle
    - Message routing
    - Presence tracking
    - Broadcasting
    """

    def __init__(self):
        # session_id -> {user_id -> WebSocket}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # session_id -> set of user_ids
        self.session_participants: Dict[str, Set[str]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: str,
        user_info: dict
    ):
        """Accept connection dan add ke session"""
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
            self.session_participants[session_id] = set()

        self.active_connections[session_id][user_id] = websocket
        self.session_participants[session_id].add(user_id)

        # Update Redis presence
        await redis_client.add_participant(session_id, user_id)
        await redis_client.set_presence(session_id, user_id, {
            "status": "active",
            "name": user_info.get("name", ""),
            "role": user_info.get("role", ""),
            "connected_at": datetime.utcnow().isoformat()
        })

        # Broadcast user joined
        await self.broadcast_to_session(
            session_id,
            {
                "type": "user_joined",
                "payload": {
                    "user_id": user_id,
                    "name": user_info.get("name", ""),
                    "role": user_info.get("role", "")
                },
                "timestamp": datetime.utcnow().isoformat()
            },
            exclude_user=user_id
        )

        # Send current participants to new user
        participants = []
        for uid in self.session_participants[session_id]:
            presence = await redis_client.get_presence(session_id, uid)
            if presence:
                participants.append({
                    "user_id": uid,
                    **presence
                })

        await self.send_to_user(session_id, user_id, {
            "type": "session_state",
            "payload": {
                "participants": participants,
                "your_id": user_id
            }
        })

    async def disconnect(self, session_id: str, user_id: str):
        """Remove connection dari session"""
        if session_id in self.active_connections:
            self.active_connections[session_id].pop(user_id, None)
            self.session_participants[session_id].discard(user_id)

            # Cleanup empty sessions
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
                del self.session_participants[session_id]

        # Update Redis
        await redis_client.remove_participant(session_id, user_id)

        # Broadcast user left
        await self.broadcast_to_session(
            session_id,
            {
                "type": "user_left",
                "payload": {"user_id": user_id},
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    async def broadcast_to_session(
        self,
        session_id: str,
        message: dict,
        exclude_user: Optional[str] = None
    ):
        """Broadcast message ke semua users dalam session"""
        if session_id not in self.active_connections:
            return

        message_json = json.dumps(message)

        for user_id, websocket in self.active_connections[session_id].items():
            if user_id != exclude_user:
                try:
                    await websocket.send_text(message_json)
                except Exception as e:
                    print(f"Error sending to {user_id}: {e}")

    async def send_to_user(self, session_id: str, user_id: str, message: dict):
        """Send message ke specific user"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id].get(user_id)
            if websocket:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    print(f"Error sending to {user_id}: {e}")

    def get_session_users(self, session_id: str) -> Set[str]:
        """Get all users dalam session"""
        return self.session_participants.get(session_id, set())


# Global connection manager
manager = ConnectionManager()


class SessionWebSocketHandler:
    """
    Handler untuk WebSocket messages dalam session
    """

    def __init__(self, mongodb=None):
        self.manager = manager
        self.ai_agent = None
        self.tts_service = EmotionalTTSService()
        self.stt_service = WhisperSTTService()
        self.mongodb = mongodb

    async def _get_ai_agent(self):
        """Lazy initialize AI agent"""
        if self.ai_agent is None:
            self.ai_agent = CoDesignAgent(
                voice_service=self.tts_service,
                mongodb=self.mongodb
            )
        return self.ai_agent

    async def handle_message(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: str,
        user_info: dict,
        data: dict
    ):
        """
        Handle incoming WebSocket message

        Args:
            websocket: WebSocket connection
            session_id: Session ID
            user_id: User ID
            user_info: User info dari token
            data: Message data
        """
        msg_type = data.get("type", "")
        payload = data.get("payload", {})

        handlers = {
            "ping": self._handle_ping,
            "presence_update": self._handle_presence_update,
            "typing_start": self._handle_typing_start,
            "typing_stop": self._handle_typing_stop,
            "chat_message": self._handle_chat_message,
            "voice_input": self._handle_voice_input,
            "ai_message": self._handle_ai_message,
            "crdt_update": self._handle_crdt_update,
            "phase_advance": self._handle_phase_advance,
        }

        handler = handlers.get(msg_type)
        if handler:
            await handler(websocket, session_id, user_id, user_info, payload)
        else:
            await self.manager.send_to_user(session_id, user_id, {
                "type": "error",
                "payload": {"message": f"Unknown message type: {msg_type}"}
            })

    async def _handle_ping(self, websocket, session_id, user_id, user_info, payload):
        """Handle ping message"""
        await self.manager.send_to_user(session_id, user_id, {
            "type": "pong",
            "payload": {"timestamp": datetime.utcnow().isoformat()}
        })

    async def _handle_presence_update(self, websocket, session_id, user_id, user_info, payload):
        """Handle presence update"""
        await redis_client.set_presence(session_id, user_id, {
            "status": payload.get("status", "active"),
            "cursor": payload.get("cursor"),
            "active_element": payload.get("active_element"),
            "updated_at": datetime.utcnow().isoformat()
        })

        # Broadcast to others
        await self.manager.broadcast_to_session(
            session_id,
            {
                "type": "presence_update",
                "payload": {
                    "user_id": user_id,
                    **payload
                }
            },
            exclude_user=user_id
        )

    async def _handle_typing_start(self, websocket, session_id, user_id, user_info, payload):
        """Handle typing start"""
        await redis_client.set_typing(session_id, user_id)
        await self.manager.broadcast_to_session(
            session_id,
            {
                "type": "typing_start",
                "payload": {"user_id": user_id, "name": user_info.get("name")}
            },
            exclude_user=user_id
        )

    async def _handle_typing_stop(self, websocket, session_id, user_id, user_info, payload):
        """Handle typing stop"""
        await redis_client.clear_typing(session_id, user_id)
        await self.manager.broadcast_to_session(
            session_id,
            {
                "type": "typing_stop",
                "payload": {"user_id": user_id}
            },
            exclude_user=user_id
        )

    async def _handle_chat_message(self, websocket, session_id, user_id, user_info, payload):
        """Handle regular chat message"""
        message = {
            "type": "chat_message",
            "payload": {
                "message_id": str(uuid4()),
                "user_id": user_id,
                "name": user_info.get("name"),
                "role": user_info.get("role"),
                "content": payload.get("content", ""),
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        # Broadcast to all including sender
        await self.manager.broadcast_to_session(session_id, message)

        # Log interaction
        if self.mongodb:
            await self.mongodb.interaction_logs.insert_one({
                "session_id": session_id,
                "interaction_type": "chat_message",
                "actor": {"user_id": user_id, "role": user_info.get("role")},
                "data": {"content": payload.get("content")},
                "timestamp": datetime.utcnow()
            })

    async def _handle_voice_input(self, websocket, session_id, user_id, user_info, payload):
        """Handle voice input (audio untuk STT)"""
        audio_data = payload.get("audio")  # Base64 encoded audio
        request_tts = payload.get("request_tts", True)

        if not audio_data:
            return

        # Decode dan transcribe
        import base64
        audio_bytes = base64.b64decode(audio_data)

        result = await self.stt_service.transcribe_bytes(audio_bytes)
        transcript = result.get("transcript", "")

        if transcript:
            # Broadcast transcript
            await self.manager.broadcast_to_session(session_id, {
                "type": "voice_transcript",
                "payload": {
                    "user_id": user_id,
                    "name": user_info.get("name"),
                    "transcript": transcript,
                    "confidence": result.get("confidence", 0)
                }
            })

            # Forward to AI if requested
            if payload.get("forward_to_ai", True):
                await self._handle_ai_message(
                    websocket, session_id, user_id, user_info,
                    {"message": transcript, "request_tts": request_tts}
                )

    async def _handle_ai_message(self, websocket, session_id, user_id, user_info, payload):
        """Handle message to AI agent"""
        message = payload.get("message", "")
        request_tts = payload.get("request_tts", True)
        current_phase = payload.get("current_phase", "shared_framing")

        if not message:
            return

        # Notify AI is processing
        await self.manager.broadcast_to_session(session_id, {
            "type": "ai_processing",
            "payload": {"status": "thinking"}
        })

        # Get AI response
        agent = await self._get_ai_agent()
        response = await agent.process_message(
            session_id=session_id,
            message=message,
            sender_role=user_info.get("role", "designer"),
            current_phase=current_phase,
            context=payload.get("context"),
            request_tts=request_tts
        )

        # Broadcast AI response
        await self.manager.broadcast_to_session(session_id, {
            "type": "ai_response",
            "payload": {
                "response": response.response,
                "suggestions": response.suggestions,
                "tools_used": response.tools_used,
                "tts_audio_url": response.tts_audio_url,
                "emotion": response.emotion_detected,
                "in_reply_to": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        })

    async def _handle_crdt_update(self, websocket, session_id, user_id, user_info, payload):
        """Handle CRDT update untuk collaborative editing"""
        # Forward CRDT update ke semua participants
        await self.manager.broadcast_to_session(
            session_id,
            {
                "type": "crdt_update",
                "payload": {
                    "artifact_id": payload.get("artifact_id"),
                    "update": payload.get("update"),  # Base64 Y.js update
                    "origin": user_id
                }
            },
            exclude_user=user_id
        )

    async def _handle_phase_advance(self, websocket, session_id, user_id, user_info, payload):
        """Handle phase advance request"""
        # This would typically update the database
        # For now, just broadcast the phase change

        new_phase = payload.get("new_phase")

        await self.manager.broadcast_to_session(session_id, {
            "type": "phase_changed",
            "payload": {
                "new_phase": new_phase,
                "triggered_by": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        })


async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str,
    mongodb=None
):
    """
    WebSocket endpoint untuk session

    Args:
        websocket: WebSocket connection
        session_id: Session ID dari path
        token: JWT token dari query param
    """
    # Verify token
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        user_info = {
            "name": payload.get("name"),
            "role": payload.get("role"),
            "email": payload.get("email")
        }
    except Exception as e:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Connect
    handler = SessionWebSocketHandler(mongodb=mongodb)
    await manager.connect(websocket, session_id, user_id, user_info)

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            # Handle message
            await handler.handle_message(
                websocket, session_id, user_id, user_info, data
            )

    except WebSocketDisconnect:
        await manager.disconnect(session_id, user_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        await manager.disconnect(session_id, user_id)
