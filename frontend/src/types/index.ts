/**
 * Type definitions untuk Ko-Desain Platform
 */

// User Types
export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  accessibilityPreferences: AccessibilityPreferences;
  createdAt: string;
}

export type UserRole = 'designer' | 'vi_user' | 'researcher' | 'admin';

export interface AccessibilityPreferences {
  ttsEnabled: boolean;
  ttsVoice: 'male' | 'female';
  ttsSpeed: number;
  sttEnabled: boolean;
  highContrast: boolean;
  screenReaderOptimized: boolean;
  keyboardNavigation: boolean;
  audioFeedback: boolean;
}

// Session Types
export interface Session {
  id: string;
  name: string;
  description?: string;
  currentPhase: SessionPhase;
  experimentMode: ExperimentMode;
  experimentGroupId?: string;
  config: SessionConfig;
  participants: Participant[];
  createdBy: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
}

export type SessionPhase =
  | 'setup'
  | 'shared_framing'
  | 'perspective_exchange'
  | 'meaning_negotiation'
  | 'reflection_iteration'
  | 'complete';

export type ExperimentMode = 'with_ai' | 'without_ai' | 'control';

export interface SessionConfig {
  aiEnabled: boolean;
  aiProactiveSuggestions: boolean;
  aiAutoSynthesis: boolean;
  ttsForViUsers: boolean;
  recordInteractions: boolean;
  phaseTimeLimits: Record<string, number>;
}

export interface Participant {
  id: string;
  userId: string;
  roleInSession: ParticipantRole;
  joinedAt: string;
  name?: string;
}

export type ParticipantRole = 'designer' | 'vi_user' | 'ai_agent' | 'observer';

// Artifact Types
export interface Artifact {
  id: string;
  sessionId: string;
  artifactType: ArtifactType;
  name: string;
  phaseCreated: SessionPhase;
  content: EmpathyMapContent | JourneyMapContent | DesignSketchContent;
  aiSynthesis?: AISynthesis;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
}

export type ArtifactType = 'empathy_map' | 'user_journey_map' | 'design_sketch' | 'mockup';

export interface EmpathyMapContent {
  says: EmpathyItem[];
  thinks: EmpathyItem[];
  does: EmpathyItem[];
  feels: EmpathyItem[];
  hears: EmpathyItem[];
  touches: EmpathyItem[];
}

export interface EmpathyItem {
  text: string;
  source: 'vi_user' | 'designer' | 'ai_observation';
  timestamp?: string;
}

export interface JourneyMapContent {
  personaName: string;
  scenario: string;
  stages: JourneyStage[];
}

export interface JourneyStage {
  name: string;
  order: number;
  touchpoints: string[];
  actions: string[];
  thoughts: string[];
  emotions: string;
  painPoints: string[];
  opportunities: string[];
  accessibilityNotes: string[];
}

export interface DesignSketchContent {
  elements: DesignElement[];
  canvasState?: any;
}

export interface DesignElement {
  id: string;
  type: string;
  properties: Record<string, any>;
  accessibilityAnnotations: string[];
}

export interface AISynthesis {
  summary: string;
  keyInsights: string[];
  accessibilityConsiderations: string[];
  suggestedImprovements: string[];
  generatedAt: string;
}

// AI Types
export interface AIMessage {
  message: string;
  context?: Record<string, any>;
  requestTts: boolean;
}

export interface AIResponse {
  response: string;
  suggestions: string[];
  toolsUsed: string[];
  ttsAudioUrl?: string;
  emotionDetected?: string;
}

// WebSocket Types
export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: string;
  messageId?: string;
}

export interface PresenceData {
  userId: string;
  name: string;
  role: string;
  status: 'active' | 'idle' | 'away';
  cursor?: { x: number; y: number };
  activeElement?: string;
}

// Voice Types
export interface TTSRequest {
  text: string;
  voice: 'male' | 'female';
  speed: number;
  emotion?: TTSEmotion;
  format?: 'mp3' | 'wav' | 'ogg';
}

export type TTSEmotion = 'neutral' | 'empathy' | 'encouraging' | 'questioning' | 'excited' | 'calm' | 'serious';

export interface STTResponse {
  transcript: string;
  confidence: number;
  language: string;
  segments: STTSegment[];
}

export interface STTSegment {
  start: number;
  end: number;
  text: string;
  words?: { word: string; start: number; end: number }[];
}
