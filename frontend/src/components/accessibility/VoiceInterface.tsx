/**
 * Voice Interface Component
 * Komponen utama untuk interaksi voice (TTS/STT) khusus user tunanetra
 */
import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Mic, MicOff, Volume2, VolumeX, RotateCcw, HelpCircle } from 'lucide-react';

interface VoiceInterfaceProps {
  onTranscript: (text: string) => void;
  onVoiceData?: (audioData: string) => void;
  ttsEnabled?: boolean;
  sttEnabled?: boolean;
  language?: string;
}

// Keyboard shortcuts
const SHORTCUTS = {
  'Alt+V': 'Toggle voice input',
  'Alt+S': 'Stop/Start TTS playback',
  'Alt+R': 'Repeat last AI response',
  'Alt+H': 'Help - list all shortcuts',
  'Escape': 'Cancel current action',
};

export const VoiceInterface: React.FC<VoiceInterfaceProps> = ({
  onTranscript,
  onVoiceData,
  ttsEnabled = true,
  sttEnabled = true,
  language = 'id-ID'
}) => {
  const [isListening, setIsListening] = useState(false);
  const [isTTSPlaying, setIsTTSPlaying] = useState(false);
  const [lastResponse, setLastResponse] = useState<string>('');
  const [statusMessage, setStatusMessage] = useState<string>('');

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const recognitionRef = useRef<any>(null);

  // Initialize Web Speech API for real-time STT
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = language;

      recognitionRef.current.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((result: any) => result[0].transcript)
          .join('');

        if (event.results[event.results.length - 1].isFinal) {
          onTranscript(transcript);
          announceStatus(`Anda mengatakan: ${transcript}`);
        }
      };

      recognitionRef.current.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        announceStatus('Terjadi kesalahan dalam pengenalan suara');
      };

      recognitionRef.current.onend = () => {
        if (isListening) {
          recognitionRef.current.start();
        }
      };
    }
  }, [language, onTranscript, isListening]);

  // Keyboard shortcut handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey) {
        switch (e.key.toLowerCase()) {
          case 'v':
            e.preventDefault();
            toggleVoiceInput();
            break;
          case 's':
            e.preventDefault();
            toggleTTS();
            break;
          case 'r':
            e.preventDefault();
            repeatLastResponse();
            break;
          case 'h':
            e.preventDefault();
            announceHelp();
            break;
        }
      }
      if (e.key === 'Escape') {
        stopAllAudio();
        setIsListening(false);
        announceStatus('Semua aksi dibatalkan');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [lastResponse]);

  // Toggle voice input
  const toggleVoiceInput = useCallback(async () => {
    if (!sttEnabled) {
      announceStatus('Input suara tidak diaktifkan');
      return;
    }

    if (isListening) {
      // Stop listening
      recognitionRef.current?.stop();
      mediaRecorderRef.current?.stop();
      setIsListening(false);
      announceStatus('Input suara dihentikan');
    } else {
      // Start listening
      try {
        // Use Web Speech API for real-time
        if (recognitionRef.current) {
          recognitionRef.current.start();
          setIsListening(true);
          announceStatus('Mendengarkan... Silakan bicara');
        }

        // Also record audio for server-side processing
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          audioChunksRef.current.push(event.data);
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
          const reader = new FileReader();
          reader.readAsDataURL(audioBlob);
          reader.onloadend = () => {
            const base64Audio = (reader.result as string).split(',')[1];
            onVoiceData?.(base64Audio);
          };

          // Stop all tracks
          stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        setIsListening(true);
      } catch (error) {
        console.error('Error accessing microphone:', error);
        announceStatus('Tidak dapat mengakses mikrofon. Pastikan izin telah diberikan.');
      }
    }
  }, [isListening, sttEnabled, onVoiceData]);

  // Toggle TTS playback
  const toggleTTS = useCallback(() => {
    if (currentAudioRef.current) {
      if (isTTSPlaying) {
        currentAudioRef.current.pause();
        setIsTTSPlaying(false);
        announceStatus('Pemutaran audio dijeda');
      } else {
        currentAudioRef.current.play();
        setIsTTSPlaying(true);
        announceStatus('Melanjutkan pemutaran audio');
      }
    }
  }, [isTTSPlaying]);

  // Play TTS audio
  const playTTS = useCallback((audioUrl: string, text?: string) => {
    if (!ttsEnabled) return;

    stopAllAudio();

    const audio = new Audio(audioUrl);
    currentAudioRef.current = audio;

    audio.onplay = () => setIsTTSPlaying(true);
    audio.onended = () => {
      setIsTTSPlaying(false);
      announceStatus('Audio selesai');
    };
    audio.onerror = () => {
      setIsTTSPlaying(false);
      announceStatus('Gagal memutar audio');
    };

    if (text) {
      setLastResponse(text);
    }

    audio.play().catch(console.error);
  }, [ttsEnabled]);

  // Repeat last response
  const repeatLastResponse = useCallback(() => {
    if (lastResponse) {
      announceStatus(`Mengulang: ${lastResponse}`);
      // Would trigger TTS here with lastResponse
    } else {
      announceStatus('Tidak ada respons sebelumnya');
    }
  }, [lastResponse]);

  // Stop all audio
  const stopAllAudio = useCallback(() => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    setIsTTSPlaying(false);
  }, []);

  // Announce help
  const announceHelp = useCallback(() => {
    const helpText = Object.entries(SHORTCUTS)
      .map(([key, action]) => `${key}: ${action}`)
      .join('. ');
    announceStatus(`Keyboard shortcuts: ${helpText}`);
  }, []);

  // Announce status to screen reader
  const announceStatus = useCallback((message: string) => {
    setStatusMessage(message);
    // Update ARIA live region
    const announcer = document.getElementById('status-announcer');
    if (announcer) {
      announcer.textContent = message;
    }
  }, []);

  // Expose playTTS for external use
  useEffect(() => {
    (window as any).playTTS = playTTS;
    return () => {
      delete (window as any).playTTS;
    };
  }, [playTTS]);

  return (
    <div
      role="application"
      aria-label="Voice Interface"
      className="voice-interface p-4 bg-gray-100 dark:bg-gray-800 rounded-lg"
    >
      {/* ARIA Live Regions */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
        id="status-announcer"
      />
      <div
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
        className="sr-only"
        id="alert-announcer"
      />

      {/* Status Message (visible) */}
      {statusMessage && (
        <div
          className="mb-4 p-2 bg-blue-100 dark:bg-blue-900 rounded text-sm"
          role="status"
        >
          {statusMessage}
        </div>
      )}

      {/* Control Buttons */}
      <div className="flex flex-wrap gap-4 justify-center">
        {/* Voice Input Button */}
        <button
          onClick={toggleVoiceInput}
          disabled={!sttEnabled}
          aria-pressed={isListening}
          aria-label={isListening ? "Berhenti mendengarkan (Alt+V)" : "Mulai bicara (Alt+V)"}
          className={`
            flex items-center gap-2 px-6 py-4 rounded-lg font-medium text-lg
            transition-all duration-200 focus:ring-4 focus:ring-blue-500 focus:outline-none
            ${isListening
              ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
              : 'bg-blue-500 hover:bg-blue-600 text-white'
            }
            ${!sttEnabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          {isListening ? <MicOff size={24} /> : <Mic size={24} />}
          <span>{isListening ? 'Mendengarkan...' : 'Tekan untuk Bicara'}</span>
        </button>

        {/* TTS Toggle Button */}
        <button
          onClick={toggleTTS}
          disabled={!ttsEnabled || !currentAudioRef.current}
          aria-pressed={isTTSPlaying}
          aria-label={isTTSPlaying ? "Jeda audio (Alt+S)" : "Putar audio (Alt+S)"}
          className={`
            flex items-center gap-2 px-6 py-4 rounded-lg font-medium text-lg
            transition-all duration-200 focus:ring-4 focus:ring-green-500 focus:outline-none
            ${isTTSPlaying
              ? 'bg-green-500 hover:bg-green-600 text-white'
              : 'bg-gray-500 hover:bg-gray-600 text-white'
            }
            ${!ttsEnabled || !currentAudioRef.current ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          {isTTSPlaying ? <Volume2 size={24} /> : <VolumeX size={24} />}
          <span>{isTTSPlaying ? 'Audio Aktif' : 'Audio Mati'}</span>
        </button>

        {/* Repeat Button */}
        <button
          onClick={repeatLastResponse}
          disabled={!lastResponse}
          aria-label="Ulangi respons terakhir (Alt+R)"
          className={`
            flex items-center gap-2 px-6 py-4 rounded-lg font-medium text-lg
            bg-purple-500 hover:bg-purple-600 text-white
            transition-all duration-200 focus:ring-4 focus:ring-purple-500 focus:outline-none
            ${!lastResponse ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <RotateCcw size={24} />
          <span>Ulangi</span>
        </button>

        {/* Help Button */}
        <button
          onClick={announceHelp}
          aria-label="Bantuan keyboard shortcuts (Alt+H)"
          className="
            flex items-center gap-2 px-6 py-4 rounded-lg font-medium text-lg
            bg-yellow-500 hover:bg-yellow-600 text-black
            transition-all duration-200 focus:ring-4 focus:ring-yellow-500 focus:outline-none
          "
        >
          <HelpCircle size={24} />
          <span>Bantuan</span>
        </button>
      </div>

      {/* Keyboard Shortcuts Help */}
      <div className="mt-6 text-sm text-gray-600 dark:text-gray-400">
        <h3 className="font-semibold mb-2">Keyboard Shortcuts:</h3>
        <ul className="grid grid-cols-2 gap-2">
          {Object.entries(SHORTCUTS).map(([key, action]) => (
            <li key={key}>
              <kbd className="px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded">{key}</kbd>
              {' '}{action}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default VoiceInterface;
