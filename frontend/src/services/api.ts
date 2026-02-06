/**
 * API Service untuk komunikasi dengan backend
 */
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth APIs
export const authApi = {
  register: (data: { email: string; name: string; password: string; role: string }) =>
    api.post('/auth/register', data),

  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),

  getMe: () => api.get('/auth/me'),

  updateAccessibility: (preferences: any) =>
    api.patch('/auth/me/accessibility', preferences),
};

// Session APIs
export const sessionApi = {
  list: () => api.get('/sessions'),

  create: (data: { name: string; description?: string; experimentMode?: string }) =>
    api.post('/sessions', data),

  get: (id: string) => api.get(`/sessions/${id}`),

  start: (id: string) => api.post(`/sessions/${id}/start`),

  advance: (id: string) => api.post(`/sessions/${id}/advance`),

  join: (id: string, role: string) =>
    api.post(`/sessions/${id}/participants/join`, { role }),

  leave: (id: string) => api.delete(`/sessions/${id}/participants/leave`),
};

// AI APIs
export const aiApi = {
  sendMessage: (sessionId: string, data: { message: string; context?: any; requestTts?: boolean }) =>
    api.post(`/ai/sessions/${sessionId}/message`, data),

  synthesize: (sessionId: string, data: { targetArtifactType: string }) =>
    api.post(`/ai/sessions/${sessionId}/synthesize`, data),

  getSuggestions: (sessionId: string) =>
    api.get(`/ai/sessions/${sessionId}/suggestions`),

  getInsights: (sessionId: string) =>
    api.get(`/ai/sessions/${sessionId}/insights`),
};

// Artifact APIs
export const artifactApi = {
  list: (sessionId: string) => api.get(`/artifacts/sessions/${sessionId}`),

  create: (sessionId: string, data: { artifactType: string; name: string }) =>
    api.post(`/artifacts/sessions/${sessionId}`, data),

  get: (id: string) => api.get(`/artifacts/${id}`),

  update: (id: string, content: any) => api.patch(`/artifacts/${id}`, content),

  export: (id: string, format: string = 'json') =>
    api.get(`/artifacts/${id}/export?format=${format}`),
};

// Voice APIs
export const voiceApi = {
  textToSpeech: (data: { text: string; voice?: string; speed?: number; emotion?: string }) =>
    api.post('/voice/tts', data),

  speechToText: (formData: FormData) =>
    api.post('/voice/stt', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  getVoices: () => api.get('/voice/voices'),

  getEmotions: () => api.get('/voice/emotions'),
};

export default api;
