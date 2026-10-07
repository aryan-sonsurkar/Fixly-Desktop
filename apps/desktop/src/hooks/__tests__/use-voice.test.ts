import { describe, expect, it, vi, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useVoice } from "@/hooks/use-voice";

describe("useVoice graceful degradation", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  function removeSpeechApis() {
    // `"key" in window` checks existence, so delete — don't assign undefined.
    delete (window as unknown as Record<string, unknown>).speechSynthesis;
    delete (window as unknown as Record<string, unknown>).SpeechRecognition;
    delete (window as unknown as Record<string, unknown>).webkitSpeechRecognition;
  }

  it("reports unsupported when neither speech API exists and never throws", () => {
    removeSpeechApis();
    const { result } = renderHook(() => useVoice());
    expect(result.current.ttsSupported).toBe(false);
    expect(result.current.sttSupported).toBe(false);
    expect(() => result.current.speak("hello")).not.toThrow();
    expect(() => result.current.startListening()).not.toThrow();
    expect(() => result.current.stopSpeaking()).not.toThrow();
    expect(() => result.current.stopListening()).not.toThrow();
  });

  it("voice input without recognition shows the text fallback hint", () => {
    removeSpeechApis();
    const { result } = renderHook(() => useVoice());
    act(() => {
      result.current.startListening();
    });
    expect(result.current.listening).toBe(false);
    expect(result.current.sttError).toMatch(/type instead/i);
  });

  it("TTS speaks through the platform synthesizer when available", () => {
    const speak = vi.fn();
    const cancel = vi.fn();
    const utterances: { text: string }[] = [];
    function FakeUtterance(text: string) {
      utterances.push({ text });
      return { text, rate: 1, onstart: null, onend: null, onerror: null };
    }
    vi.stubGlobal("speechSynthesis", { speak, cancel });
    vi.stubGlobal("SpeechSynthesisUtterance", FakeUtterance);
    const { result } = renderHook(() => useVoice());
    expect(result.current.ttsSupported).toBe(true);
    act(() => {
      result.current.speak("**Hello** `code` world");
    });
    expect(speak).toHaveBeenCalledTimes(1);
    expect(utterances[0].text).not.toContain("**");
    expect(utterances[0].text).not.toContain("`");
  });

  it("recognition transcripts are delivered to the callback", () => {
    removeSpeechApis();
    let captured: { onresult?: (e: never) => void } | null = null;
    function FakeRecognition(this: unknown) {
      captured = this as { onresult?: (e: never) => void };
      return captured;
    }
    (
      FakeRecognition.prototype as unknown as Record<string, unknown>
    ).start = vi.fn();
    (
      FakeRecognition.prototype as unknown as Record<string, unknown>
    ).stop = vi.fn();
    vi.stubGlobal("SpeechRecognition", FakeRecognition);
    const onTranscript = vi.fn();
    const { result } = renderHook(() => useVoice({ onTranscript }));
    expect(result.current.sttSupported).toBe(true);
    act(() => {
      result.current.startListening();
    });
    expect(result.current.listening).toBe(true);
    act(() => {
      captured?.onresult?.({
        results: [[{ transcript: "  what should I study  " }]],
      } as never);
    });
    expect(onTranscript).toHaveBeenCalledWith("what should I study");
  });
});
