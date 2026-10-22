import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { LoaderCircle, Mic, MicOff, Send, Square } from "lucide-react";

interface ChatInputProps {
  onSend: (question: string) => void;
  isLoading: boolean;
  placeholder?: string;
}

interface SpeechRecognitionResultEvent {
  results: ArrayLike<ArrayLike<{ transcript: string }>>;
}

interface SpeechRecognitionErrorEvent {
  error: string;
}

interface BrowserSpeechRecognition {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((event: SpeechRecognitionResultEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
}

type SpeechWindow = Window & {
  SpeechRecognition?: new () => BrowserSpeechRecognition;
  webkitSpeechRecognition?: new () => BrowserSpeechRecognition;
};

export default function ChatInput({
  onSend,
  isLoading,
  placeholder = "כתבו את השאלה שלכם כאן...",
}: ChatInputProps) {
  const [question, setQuestion] = useState("");
  const [recording, setRecording] = useState(false);
  const [voiceError, setVoiceError] = useState("");
  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null);

  useEffect(() => {
    return () => recognitionRef.current?.abort();
  }, []);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || isLoading || recording) return;
    onSend(trimmed);
    setQuestion("");
    setVoiceError("");
  }

  function toggleMicrophone() {
    setVoiceError("");
    if (recording) {
      recognitionRef.current?.stop();
      return;
    }

    const speechWindow = window as SpeechWindow;
    const Recognition =
      speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;

    if (!Recognition) {
      setVoiceError("הדפדפן הזה אינו תומך בתמלול קולי. אפשר להמשיך בהקלדה.");
      return;
    }

    const recognition = new Recognition();
    recognitionRef.current = recognition;
    recognition.lang = "he-IL";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
      const lastResult = event.results[event.results.length - 1];
      const transcript = Array.from(lastResult)
        .map((alternative) => alternative.transcript)
        .join(" ")
        .trim();
      if (transcript) {
        setQuestion((previous) =>
          [previous.trim(), transcript].filter(Boolean).join(" "),
        );
      }
    };

    recognition.onerror = (event) => {
      const errors: Record<string, string> = {
        "not-allowed": "נדרשת הרשאה למיקרופון. אפשר לאשר בדפדפן ולנסות שוב.",
        "no-speech": "לא זוהה דיבור. נסו שוב או הקלידו את השאלה.",
        network: "שירות זיהוי הדיבור אינו זמין כרגע. אפשר להקליד במקום.",
      };
      setVoiceError(errors[event.error] || "התמלול נכשל. אפשר לנסות שוב.");
    };

    recognition.onend = () => {
      setRecording(false);
      if (recognitionRef.current === recognition) recognitionRef.current = null;
    };

    try {
      recognition.start();
      setRecording(true);
    } catch {
      recognitionRef.current = null;
      setRecording(false);
      setVoiceError("לא ניתן להפעיל את המיקרופון כרגע.");
    }
  }

  return (
    <div dir="rtl" className="w-full">
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-2 rounded-[26px] border border-blue-200 bg-white px-3 py-3 shadow-[0_10px_40px_rgba(16,43,86,0.09)] sm:gap-4 sm:px-6 sm:py-5"
      >
        <input
          type="text"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder={placeholder}
          aria-label="השאלה שלכם"
          disabled={isLoading}
          className="min-w-0 flex-1 bg-transparent text-base text-[#102B56] outline-none placeholder:text-slate-400 disabled:opacity-60 sm:text-lg"
        />

        <button
          type="button"
          onClick={toggleMicrophone}
          disabled={isLoading}
          aria-label={recording ? "עצירת ההקלטה" : "הכתבה קולית בעברית"}
          aria-pressed={recording}
          title={recording ? "עצירת ההקלטה" : "הכתבה קולית בעברית"}
          className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full border transition disabled:opacity-50 ${
            recording
              ? "animate-pulse border-red-200 bg-red-50 text-red-600"
              : "border-blue-100 bg-blue-50 text-[#0B3B91] hover:bg-blue-100"
          }`}
        >
          {recording ? <Square size={19} /> : <Mic size={20} />}
        </button>

        <button
          type="submit"
          disabled={!question.trim() || isLoading || recording}
          aria-label="שליחת שאלה"
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#0B3B91] text-white shadow-md transition hover:bg-[#102B56] disabled:cursor-not-allowed disabled:opacity-50 sm:h-12 sm:w-12"
        >
          {isLoading ? (
            <LoaderCircle size={22} className="animate-spin" />
          ) : (
            <Send size={22} />
          )}
        </button>
      </form>
      {recording && (
        <p role="status" className="mt-2 flex items-center gap-2 text-sm text-red-600">
          <MicOff size={16} /> מקליטים... לחצו שוב לעצירה. בדקו את התמלול לפני השליחה.
        </p>
      )}
      {voiceError && (
        <p role="alert" className="mt-2 text-sm text-red-600">{voiceError}</p>
      )}
    </div>
  );
}
