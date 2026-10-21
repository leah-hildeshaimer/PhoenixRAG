import { Bot, ExternalLink, UserRound } from "lucide-react";
import type { Source } from "../types/chat";

export interface Message {
  id: number;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  isError?: boolean;
}

interface ChatMessageProps {
  message: Message;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isAssistant = message.role === "assistant";

  return (
    <article
      dir="rtl"
      className={`flex gap-4 ${
        isAssistant ? "justify-start" : "justify-end"
      }`}
    >
      <div
        className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${
          isAssistant
            ? "bg-[#FFF0E6] text-[#FF6600]"
            : "bg-[#EAF2FF] text-[#0B3B91]"
        }`}
      >
        {isAssistant ? <Bot size={23} /> : <UserRound size={23} />}
      </div>

      <div
        className={`max-w-[85%] rounded-2xl border p-5 shadow-sm ${
          message.isError
            ? "border-red-200 bg-red-50"
            : isAssistant
              ? "border-slate-200 bg-white"
              : "border-blue-100 bg-[#EDF4FF]"
        }`}
      >
        <p className="mb-2 text-sm font-bold text-[#102B56]">
          {isAssistant ? "PhoenixRAG" : "השאלה שלך"}
        </p>

        <div className="whitespace-pre-wrap text-base leading-8 text-slate-700">
          {message.content}
        </div>

        {isAssistant &&
          !message.isError &&
          message.sources &&
          message.sources.length > 0 && (
            <div className="mt-5 border-t border-slate-100 pt-4">
              <p className="mb-3 text-sm font-bold text-[#102B56]">
                מקורות מהאתר
              </p>

              <div className="flex flex-col gap-2">
                {message.sources.map((source) => (
                  <a
                    key={source.url}
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 rounded-xl border border-blue-100 bg-blue-50/50 px-4 py-3 text-sm text-[#0B3B91] transition hover:bg-blue-100"
                  >
                    <ExternalLink size={17} className="shrink-0" />
                    <span className="min-w-0 break-words">
                      {source.title}
                    </span>
                  </a>
                ))}
              </div>
            </div>
          )}
      </div>
    </article>
  );
}