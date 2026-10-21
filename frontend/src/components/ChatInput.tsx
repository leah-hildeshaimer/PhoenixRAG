import { useState } from "react";
import type { FormEvent } from "react";
import { LoaderCircle, Send } from "lucide-react";

interface ChatInputProps {
  onSend: (question: string) => void;
  isLoading: boolean;
}

export default function ChatInput({
  onSend,
  isLoading,
}: ChatInputProps) {
  const [question, setQuestion] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || isLoading) {
      return;
    }

    onSend(trimmedQuestion);
    setQuestion("");
  }

  return (
    <form
      dir="rtl"
      onSubmit={handleSubmit}
      className="flex items-center gap-4 rounded-[26px] border border-blue-200 bg-white px-6 py-5 shadow-[0_10px_40px_rgba(16,43,86,0.09)]"
    >
      <input
        type="text"
        value={question}
        onChange={(event) => setQuestion(event.target.value)}
        placeholder="כתבו את השאלה שלכם כאן..."
        aria-label="השאלה שלכם"
        disabled={isLoading}
        className="min-w-0 flex-1 bg-transparent text-lg text-[#102B56] outline-none placeholder:text-slate-400 disabled:opacity-60"
      />

      <button
        type="submit"
        disabled={!question.trim() || isLoading}
        aria-label="שליחת שאלה"
        className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-[#0B3B91] text-white shadow-md transition hover:bg-[#102B56] disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isLoading ? (
          <LoaderCircle size={22} className="animate-spin" />
        ) : (
          <Send size={22} />
        )}
      </button>
    </form>
  );
}