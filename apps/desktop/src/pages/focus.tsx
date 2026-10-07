import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import { Button } from "@fixly/ui";
import { MarkdownRenderer } from "@/components/ai/markdown-renderer";
import {
  continueCompanionSession,
  getNextAction,
  sendCompanionChatStream,
} from "@/lib/companion-service";
import { useVoice } from "@/hooks/use-voice";
import { focusReducer, initialFocusState } from "@/lib/focus-machine";
import type { Message } from "@/lib/ai-service";

const SESSION_KEY = "fixly:focus-companion";
const TIME_PRESETS = [5, 10, 15];

interface SavedSession {
  conversationId: string | null;
  actionKey: string | null;
}

function loadSavedSession(): SavedSession | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as SavedSession;
    if (!parsed.conversationId && !parsed.actionKey) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function FocusPage() {
  const [state, dispatch] = useReducer(focusReducer, initialFocusState);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingAction, setLoadingAction] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [minutes, setMinutes] = useState<number | null>(null);
  const [resumeOffer, setResumeOffer] = useState<SavedSession | null>(null);
  const [autoSpeak, setAutoSpeak] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const voice = useVoice({
    onTranscript: (text) => {
      setInput(text);
    },
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Interruption recovery: offer to continue a saved session.
  useEffect(() => {
    const saved = loadSavedSession();
    if (saved) setResumeOffer(saved);
  }, []);

  const persistSession = useCallback((convId: string | null, actionKey: string | null) => {
    try {
      localStorage.setItem(SESSION_KEY, JSON.stringify({ conversationId: convId, actionKey }));
    } catch {
      // Session resume is best-effort; chat still works without it.
    }
  }, []);

  const sendCompanionMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || loading) return null;
      setLoading(true);
      setError(null);
      try {
        const res = await sendCompanionChatStream(
          { message: trimmed, conversation_id: conversationId ?? undefined },
          () => undefined,
        );
        setMessages((prev) => [...prev, res.message]);
        setConversationId(res.conversation.id);
        persistSession(res.conversation.id, state.action?.key ?? null);
        if (autoSpeak) voice.speak(res.message.content);
        return res;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Fixly couldn't reply just now. Your text is safe — try again.");
        return null;
      } finally {
        setLoading(false);
      }
    },
    [loading, autoSpeak, voice, conversationId, persistSession, state.action],
  );

  const suggestOne = useCallback(
    async (mins: number | null, exclude: string[] = []) => {
      setLoadingAction(true);
      setError(null);
      try {
        const res = await getNextAction({ available_minutes: mins ?? undefined, exclude_keys: exclude });
        if (res.action) {
          dispatch({ type: "SUGGEST", action: res.action, minutes: mins });
          persistSession(conversationId, res.action.key);
        } else {
          dispatch({ type: "RESET" });
          setError(res.empty_reason ?? "Nothing pending was found.");
        }
        return res;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Couldn't look at your workload. Try again.");
        return null;
      } finally {
        setLoadingAction(false);
      }
    },
    [persistSession, conversationId],
  );

  const handleDismiss = useCallback(async () => {
    if (!state.action) {
      dispatch({ type: "DISMISS" });
      return;
    }
    const dismissed = [...state.dismissedKeys, state.action.key];
    dispatch({ type: "DISMISS" });
    await suggestOne(minutes, dismissed);
  }, [state.action, state.dismissedKeys, minutes, suggestOne]);

  const handleResume = useCallback(async () => {
    if (!resumeOffer) return;
    setResumeOffer(null);
    setLoadingAction(true);
    try {
      const res = await continueCompanionSession({
        current_key: resumeOffer.actionKey,
        available_minutes: minutes ?? undefined,
      });
      if (res.action) {
        dispatch({
          type: "RESTORE",
          action: res.action,
          conversationId: resumeOffer.conversationId,
        });
        setConversationId(resumeOffer.conversationId);
        persistSession(resumeOffer.conversationId, res.action.key);
      } else {
        await suggestOne(minutes);
      }
    } catch {
      await suggestOne(minutes);
    } finally {
      setLoadingAction(false);
    }
  }, [resumeOffer, minutes, persistSession, suggestOne]);

  const handleSend = useCallback(async () => {
    const text = input;
    const res = await sendCompanionMessage(text);
    if (res) {
      setInput("");
      persistSession(res.conversation.id, state.action?.key ?? null);
    }
  }, [input, state.action, sendCompanionMessage, persistSession]);

  const handleStop = useCallback(() => {
    voice.stopSpeaking();
    voice.stopListening();
    dispatch({ type: "RESET" });
    setMessages([]);
    setInput("");
    try {
      localStorage.removeItem(SESSION_KEY);
    } catch {
      // ignore
    }
  }, [voice]);

  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");

  return (
    <div className="mx-auto flex h-full w-full max-w-[720px] flex-col">
      <div className="flex shrink-0 items-center gap-2 border-b bg-card/80 px-4 py-2.5 backdrop-blur">
        <div>
          <h1 className="text-sm font-semibold tracking-tight">Focus Companion</h1>
          <p className="text-xs text-muted-foreground">One thing at a time.</p>
        </div>
        <span className="ml-auto rounded-full border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-amber-600 dark:text-amber-400">
          Experimental
        </span>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
        {resumeOffer && (
          <div className="rounded-xl border bg-card p-4">
            <p className="text-sm font-medium">Welcome back. Want to continue where you stopped?</p>
            <div className="mt-3 flex gap-2">
              <Button size="sm" onClick={() => void handleResume()}>Continue</Button>
              <Button size="sm" variant="outline" onClick={() => setResumeOffer(null)}>Start fresh</Button>
            </div>
          </div>
        )}

        {state.step === "idle" && !resumeOffer && (
          <div className="flex flex-col items-center gap-4 py-10 text-center">
            <p className="text-lg font-medium">What should I do right now?</p>
            <div className="flex flex-wrap justify-center gap-2">
              {TIME_PRESETS.map((m) => (
                <Button
                  key={m}
                  size="sm"
                  variant={minutes === m ? "default" : "outline"}
                  onClick={() => setMinutes(minutes === m ? null : m)}
                >
                  {m} min
                </Button>
              ))}
            </div>
            <Button
              disabled={loadingAction}
              onClick={() => void suggestOne(minutes, state.dismissedKeys)}
            >
              {loadingAction ? "Looking…" : "Suggest one thing"}
            </Button>
            {error && <p className="text-sm text-muted-foreground">{error}</p>}
          </div>
        )}

        {state.action && state.step !== "idle" && (
          <div className="rounded-xl border bg-card p-4">
            <p className="text-xs uppercase tracking-wider text-muted-foreground">
              {state.action.overdue ? "Overdue — start here" : "Up next"}
              {minutes ? ` · ~${Math.min(state.action.suggested_minutes, minutes)} min` : ""}
            </p>
            <p className="mt-1 text-base font-semibold">{state.action.title}</p>
            {state.action.subject && (
              <p className="text-sm text-muted-foreground">{state.action.subject}</p>
            )}
            {state.action.reason && (
              <p className="mt-2 text-sm text-muted-foreground">{state.action.reason}</p>
            )}
            <div className="mt-3 flex flex-wrap gap-2">
              {state.step === "suggested" && (
                <Button size="sm" onClick={() => dispatch({ type: "START" })}>Start</Button>
              )}
              <Button size="sm" variant="outline" onClick={() => void handleDismiss()}>
                Not now
              </Button>
              {voice.ttsSupported && lastAssistant && (
                <Button size="sm" variant="outline" onClick={() => voice.speak(lastAssistant.content)}>
                  Read aloud
                </Button>
              )}
            </div>
          </div>
        )}

        {state.step === "done" && (
          <div className="rounded-xl border bg-card p-4 text-center">
            <p className="text-sm font-medium">Nice — that&apos;s done. Want to keep going?</p>
            <div className="mt-3 flex justify-center gap-2">
              <Button size="sm" onClick={() => void suggestOne(minutes, state.dismissedKeys)}>
                What&apos;s next?
              </Button>
              <Button size="sm" variant="outline" onClick={handleStop}>Stop</Button>
            </div>
          </div>
        )}

        {messages.map((msg) =>
          msg.role === "user" ? (
            <div key={msg.id} className="flex justify-end">
              <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-primary px-4 py-2.5 text-sm text-primary-foreground">
                {msg.content}
              </div>
            </div>
          ) : (
            <div key={msg.id} className="flex justify-start">
              <div className="w-full max-w-3xl">
                <MarkdownRenderer content={msg.content} />
                <div className="mt-1 flex gap-2">
                  {voice.ttsSupported && (
                    <button
                      type="button"
                      onClick={() => voice.speak(msg.content)}
                      className="text-xs text-muted-foreground hover:text-foreground"
                    >
                      Listen
                    </button>
                  )}
                </div>
              </div>
            </div>
          ),
        )}

        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center gap-2 rounded-2xl bg-muted px-4 py-3 text-xs text-muted-foreground">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
              Fixly AI is generating…
            </div>
          </div>
        )}

        {error && state.step !== "idle" && (
          <p className="text-sm text-destructive">{error}</p>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="border-t bg-card px-4 py-3">
        {voice.sttError && (
          <p className="mb-2 text-xs text-muted-foreground">{voice.sttError}</p>
        )}
        <div className="relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void handleSend();
              }
            }}
            placeholder={voice.sttSupported ? "Type or talk to Fixly…" : "Type to Fixly…"}
            rows={2}
            className="max-h-[160px] w-full resize-none rounded-xl border bg-background px-4 py-3 pr-24 text-sm outline-none focus:ring-2 focus:ring-primary"
          />
          <div className="absolute bottom-2.5 right-2.5 flex gap-1.5">
            {voice.sttSupported && (
              <Button
                size="sm"
                variant={voice.listening ? "destructive" : "outline"}
                onClick={() => (voice.listening ? voice.stopListening() : voice.startListening())}
                title={voice.listening ? "Stop listening" : "Talk to Fixly"}
              >
                {voice.listening ? "Stop" : "Talk"}
              </Button>
            )}
            <Button size="sm" onClick={() => void handleSend()} disabled={!input.trim() || loading}>
              Send
            </Button>
          </div>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          {voice.ttsSupported && (
            <>
              <button
                type="button"
                onClick={() => {
                  if (voice.ttsState === "speaking") voice.pauseSpeaking();
                  else if (voice.ttsState === "paused") voice.resumeSpeaking();
                  else if (lastAssistant) voice.speak(lastAssistant.content);
                }}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                {voice.ttsState === "speaking" ? "Pause voice" : voice.ttsState === "paused" ? "Resume voice" : "Voice on"}
              </button>
              <button
                type="button"
                onClick={voice.stopSpeaking}
                className="text-xs text-muted-foreground hover:text-foreground"
              >
                Stop voice
              </button>
              <label className="flex items-center gap-1 text-xs text-muted-foreground">
                <input
                  type="checkbox"
                  checked={autoSpeak}
                  onChange={(e) => setAutoSpeak(e.target.checked)}
                  className="h-3 w-3"
                />
                Read replies aloud
              </label>
            </>
          )}
          {state.step !== "idle" && (
            <button
              type="button"
              onClick={handleStop}
              className="ml-auto text-xs text-muted-foreground hover:text-foreground"
            >
              End session
            </button>
          )}
          <p className="w-full text-center text-[10px] text-muted-foreground">
            Experimental. Say stop anytime — text always works.
          </p>
        </div>
      </div>
    </div>
  );
}
