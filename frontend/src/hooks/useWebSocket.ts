/**
 * WebSocket hook untuk real-time collaboration
 */
import { useEffect, useRef, useCallback, useState } from 'react';
import type { WebSocketMessage, PresenceData } from '../types';

interface UseWebSocketOptions {
  sessionId: string;
  token: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  participants: PresenceData[];
  sendMessage: (type: string, payload: any) => void;
  sendChatMessage: (content: string) => void;
  sendVoiceInput: (audioData: string, requestTts?: boolean) => void;
  sendAIMessage: (message: string, context?: any) => void;
  sendPresenceUpdate: (data: Partial<PresenceData>) => void;
  sendTypingStart: () => void;
  sendTypingStop: () => void;
}

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const { sessionId, token, onMessage, onConnect, onDisconnect, onError } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number>();
  const [isConnected, setIsConnected] = useState(false);
  const [participants, setParticipants] = useState<PresenceData[]>([]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    const wsUrl = `${WS_BASE_URL}/ws/session/${sessionId}?token=${token}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      onConnect?.();

      // Send ping every 30 seconds
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping', payload: {} }));
        }
      }, 30000);

      ws.onclose = () => {
        clearInterval(pingInterval);
      };
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        handleMessage(message);
        onMessage?.(message);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      onError?.(error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      onDisconnect?.();

      // Reconnect after 3 seconds
      reconnectTimeoutRef.current = window.setTimeout(() => {
        console.log('Attempting to reconnect...');
        connect();
      }, 3000);
    };
  }, [sessionId, token, onConnect, onDisconnect, onError, onMessage]);

  // Handle incoming messages
  const handleMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'session_state':
        setParticipants(message.payload.participants || []);
        break;

      case 'user_joined':
        setParticipants(prev => [...prev, message.payload]);
        // Announce for screen reader
        announceToScreenReader(`${message.payload.name} bergabung sebagai ${message.payload.role}`);
        break;

      case 'user_left':
        setParticipants(prev => prev.filter(p => p.userId !== message.payload.user_id));
        break;

      case 'presence_update':
        setParticipants(prev =>
          prev.map(p =>
            p.userId === message.payload.user_id
              ? { ...p, ...message.payload }
              : p
          )
        );
        break;

      case 'ai_response':
        // Play TTS if available
        if (message.payload.tts_audio_url) {
          playAudio(message.payload.tts_audio_url);
        }
        break;

      case 'phase_changed':
        announceToScreenReader(`Fase berubah ke ${formatPhaseName(message.payload.new_phase)}`);
        break;
    }
  }, []);

  // Send message
  const sendMessage = useCallback((type: string, payload: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type,
        payload,
        timestamp: new Date().toISOString()
      }));
    }
  }, []);

  // Convenience methods
  const sendChatMessage = useCallback((content: string) => {
    sendMessage('chat_message', { content });
  }, [sendMessage]);

  const sendVoiceInput = useCallback((audioData: string, requestTts = true) => {
    sendMessage('voice_input', {
      audio: audioData,
      request_tts: requestTts,
      forward_to_ai: true
    });
  }, [sendMessage]);

  const sendAIMessage = useCallback((message: string, context?: any) => {
    sendMessage('ai_message', {
      message,
      context,
      request_tts: true
    });
  }, [sendMessage]);

  const sendPresenceUpdate = useCallback((data: Partial<PresenceData>) => {
    sendMessage('presence_update', data);
  }, [sendMessage]);

  const sendTypingStart = useCallback(() => {
    sendMessage('typing_start', {});
  }, [sendMessage]);

  const sendTypingStop = useCallback(() => {
    sendMessage('typing_stop', {});
  }, [sendMessage]);

  // Connect on mount
  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);

  return {
    isConnected,
    participants,
    sendMessage,
    sendChatMessage,
    sendVoiceInput,
    sendAIMessage,
    sendPresenceUpdate,
    sendTypingStart,
    sendTypingStop
  };
}

// Helper functions
function announceToScreenReader(message: string) {
  const announcer = document.getElementById('status-announcer');
  if (announcer) {
    announcer.textContent = message;
  }
}

function playAudio(url: string) {
  const audio = new Audio(url);
  audio.play().catch(console.error);
}

function formatPhaseName(phase: string): string {
  const names: Record<string, string> = {
    'setup': 'Persiapan',
    'shared_framing': 'Shared Framing',
    'perspective_exchange': 'Pertukaran Perspektif',
    'meaning_negotiation': 'Negosiasi Makna',
    'reflection_iteration': 'Refleksi dan Iterasi',
    'complete': 'Selesai'
  };
  return names[phase] || phase;
}

export default useWebSocket;
