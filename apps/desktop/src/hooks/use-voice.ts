import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Experimental voice layer for Focus Companion (no new dependencies).
 *
 * - Text-to-speech uses the built-in Web Speech synthesis API, which speaks
 *   through OS voices and generally works offline. Always available when the
 *   API exists; otherwise a silent no-op.
 * - Speech-to-text uses the built-in Web Speech recognition API where the
 *   runtime provides it (Chromium/WebView2 may, others usually don't; it also
 *   needs network). Absence is normal: typed input always remains.
 * - Linux note (WebKitGTK WebView): SpeechRecognition is not provided, so STT
 *   reports unsupported and the type-to-chat fallback stays. speechSynthesis
 *   exists but WebKitGTK ships no voices by default, so TTS may be silent;
 *   both cases are graceful no-ops, never errors.
 * - Nothing here ever throws for missing APIs. Text interaction is never
 *   gated behind voice. Voice is never mandatory.
 */

export type TtsState = "idle" | "speaking" | "paused";

function sanitizeForSpeech(text: string): string {
  return text
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/[#*_>`|]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 1200);
}

type RecognitionInstance = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((event: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: ((event: { error?: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort?: () => void;
};

function getRecognitionConstructor(): (new () => RecognitionInstance) | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as Record<string, unknown>;
  const ctor = w.SpeechRecognition ?? w.webkitSpeechRecognition;
  return (typeof ctor === "function" ? ctor : null) as (new () => RecognitionInstance) | null;
}

export function useVoice(options?: { onTranscript?: (text: string) => void; rate?: number }) {
  const [ttsSupported] = useState(
    () => typeof window !== "undefined" && "speechSynthesis" in window,
  );
  const [sttSupported] = useState(() => getRecognitionConstructor() !== null);
  const [ttsState, setTtsState] = useState<TtsState>("idle");
  const [listening, setListening] = useState(false);
  const [sttError, setSttError] = useState<string | null>(null);
  const recognitionRef = useRef<RecognitionInstance | null>(null);
  const onTranscriptRef = useRef(options?.onTranscript);
  onTranscriptRef.current = options?.onTranscript;

  const stopSpeaking = useCallback(() => {
    try {
      window.speechSynthesis?.cancel();
    } catch {
      // Speaking is best-effort; never break the chat.
    }
    setTtsState("idle");
  }, []);

  useEffect(() => stopSpeaking, [stopSpeaking]);

  const speak = useCallback(
    (text: string) => {
      if (!ttsSupported) return;
      try {
        const synth = window.speechSynthesis;
        synth.cancel();
        const clean = sanitizeForSpeech(text);
        if (!clean) return;
        const utterance = new SpeechSynthesisUtterance(clean);
        utterance.rate = options?.rate ?? 1;
        utterance.onstart = () => setTtsState("speaking");
        utterance.onend = () => setTtsState("idle");
        utterance.onerror = () => setTtsState("idle");
        synth.speak(utterance);
      } catch {
        setTtsState("idle");
      }
    },
    [ttsSupported, options?.rate],
  );

  const pauseSpeaking = useCallback(() => {
    try {
      window.speechSynthesis?.pause();
      setTtsState("paused");
    } catch {
      // ignore
    }
  }, []);

  const resumeSpeaking = useCallback(() => {
    try {
      window.speechSynthesis?.resume();
      setTtsState("speaking");
    } catch {
      // ignore
    }
  }, []);

  const stopListening = useCallback(() => {
    try {
      recognitionRef.current?.stop();
    } catch {
      // ignore
    }
    setListening(false);
  }, []);

  const startListening = useCallback(() => {
    const Ctor = getRecognitionConstructor();
    if (!Ctor) {
      setSttError("Voice input isn't available here — type instead.");
      return;
    }
    try {
      stopListening();
      const rec = new Ctor();
      rec.lang = "en-US";
      rec.interimResults = false;
      rec.continuous = false;
      rec.onresult = (event) => {
        const last = event.results[event.results.length - 1];
        const text = last?.[0]?.transcript?.trim();
        if (text) onTranscriptRef.current?.(text);
      };
      rec.onerror = (event) => {
        setSttError("Didn't catch that — type instead, or try again.");
      };
      rec.onend = () => setListening(false);
      recognitionRef.current = rec;
      setSttError(null);
      rec.start();
      setListening(true);
    } catch {
      setSttError("Voice input isn't available here — type instead.");
      setListening(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stopListening]);

  useEffect(() => stopListening, [stopListening]);

  return {
    ttsSupported,
    sttSupported,
    ttsState,
    speak,
    pauseSpeaking,
    resumeSpeaking,
    stopSpeaking,
    listening,
    sttError,
    startListening,
    stopListening,
  };
}
