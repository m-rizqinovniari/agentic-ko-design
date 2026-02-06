/**
 * Screen Reader Announcer Component
 * Provides ARIA live regions for screen reader announcements
 */
import React, { createContext, useContext, useCallback, useState, ReactNode } from 'react';

interface AnnouncerContextType {
  announce: (message: string, priority?: 'polite' | 'assertive') => void;
  announcePolite: (message: string) => void;
  announceAssertive: (message: string) => void;
}

const AnnouncerContext = createContext<AnnouncerContextType | null>(null);

interface AnnouncerProviderProps {
  children: ReactNode;
}

export const AnnouncerProvider: React.FC<AnnouncerProviderProps> = ({ children }) => {
  const [politeMessage, setPoliteMessage] = useState('');
  const [assertiveMessage, setAssertiveMessage] = useState('');

  const announce = useCallback((message: string, priority: 'polite' | 'assertive' = 'polite') => {
    if (priority === 'assertive') {
      // Clear first to ensure re-announcement
      setAssertiveMessage('');
      setTimeout(() => setAssertiveMessage(message), 50);
    } else {
      setPoliteMessage('');
      setTimeout(() => setPoliteMessage(message), 50);
    }
  }, []);

  const announcePolite = useCallback((message: string) => {
    announce(message, 'polite');
  }, [announce]);

  const announceAssertive = useCallback((message: string) => {
    announce(message, 'assertive');
  }, [announce]);

  return (
    <AnnouncerContext.Provider value={{ announce, announcePolite, announceAssertive }}>
      {children}

      {/* Polite announcements - non-urgent updates */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        id="status-announcer"
        className="sr-only"
        style={{
          position: 'absolute',
          width: '1px',
          height: '1px',
          padding: 0,
          margin: '-1px',
          overflow: 'hidden',
          clip: 'rect(0, 0, 0, 0)',
          whiteSpace: 'nowrap',
          border: 0,
        }}
      >
        {politeMessage}
      </div>

      {/* Assertive announcements - urgent/important updates */}
      <div
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
        id="alert-announcer"
        className="sr-only"
        style={{
          position: 'absolute',
          width: '1px',
          height: '1px',
          padding: 0,
          margin: '-1px',
          overflow: 'hidden',
          clip: 'rect(0, 0, 0, 0)',
          whiteSpace: 'nowrap',
          border: 0,
        }}
      >
        {assertiveMessage}
      </div>
    </AnnouncerContext.Provider>
  );
};

export const useAnnouncer = (): AnnouncerContextType => {
  const context = useContext(AnnouncerContext);
  if (!context) {
    throw new Error('useAnnouncer must be used within an AnnouncerProvider');
  }
  return context;
};

/**
 * Hook for announcing phase changes
 */
export const usePhaseAnnouncer = () => {
  const { announceAssertive } = useAnnouncer();

  const announcePhaseChange = useCallback((phase: string) => {
    const phaseNames: Record<string, string> = {
      'setup': 'Persiapan',
      'shared_framing': 'Shared Framing - Berbagi Pengalaman',
      'perspective_exchange': 'Pertukaran Perspektif - Membuat Empathy Map',
      'meaning_negotiation': 'Negosiasi Makna - Menyepakati Desain',
      'reflection_iteration': 'Refleksi dan Iterasi',
      'complete': 'Sesi Selesai'
    };

    const phaseName = phaseNames[phase] || phase;
    announceAssertive(`Fase berubah ke: ${phaseName}`);
  }, [announceAssertive]);

  return { announcePhaseChange };
};

/**
 * Hook for announcing participant changes
 */
export const useParticipantAnnouncer = () => {
  const { announcePolite } = useAnnouncer();

  const announceJoin = useCallback((name: string, role: string) => {
    const roleNames: Record<string, string> = {
      'designer': 'Designer',
      'vi_user': 'User Tunanetra',
      'observer': 'Observer',
      'ai_agent': 'AI Agent'
    };
    const roleName = roleNames[role] || role;
    announcePolite(`${name} bergabung sebagai ${roleName}`);
  }, [announcePolite]);

  const announceLeave = useCallback((name: string) => {
    announcePolite(`${name} keluar dari sesi`);
  }, [announcePolite]);

  return { announceJoin, announceLeave };
};

/**
 * Hook for announcing AI responses
 */
export const useAIAnnouncer = () => {
  const { announcePolite, announceAssertive } = useAnnouncer();

  const announceThinking = useCallback(() => {
    announcePolite('AI sedang memproses...');
  }, [announcePolite]);

  const announceResponse = useCallback((hasTTS: boolean) => {
    if (hasTTS) {
      announcePolite('AI merespons dengan audio');
    } else {
      announcePolite('AI telah merespons');
    }
  }, [announcePolite]);

  const announceSuggestion = useCallback((suggestion: string) => {
    announceAssertive(`Saran AI: ${suggestion}`);
  }, [announceAssertive]);

  return { announceThinking, announceResponse, announceSuggestion };
};

export default AnnouncerProvider;
