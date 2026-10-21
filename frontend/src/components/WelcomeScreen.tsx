import { useEffect, useRef, useState } from "react";
import {
  House,
  FileText,
  Headset,
  ChartNoAxesColumnIncreasing,
  ChevronLeft,
  LoaderCircle,
} from "lucide-react";

import PhoenixBackground from "./PhoenixBackground";
import ChatInput from "./ChatInput";
import ChatMessage from "./ChatMessage";
import type { Message } from "./ChatMessage";
import { sendChatMessage } from "../services/chatApi";

const suggestions = [
  {
    title: "ביטוח דירה",
    description: "מה כולל ביטוח דירה ומה הוא מכסה?",
    icon: House,
  },
  {
    title: "הגשת תביעה",
    description: "איך מגישים תביעה ומה התהליך?",
    icon: FileText,
  },
  {
    title: "שירות לקוחות",
    description: "איך יוצרים קשר ואילו שירותים זמינים?",
    icon: Headset,
  },
  {
    title: "חיסכון ופנסיה",
    description: "מידע על מוצרים, הטבות וכלים",
    icon: ChartNoAxesColumnIncreasing,
  },
];

export default function WelcomeScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const nextId = useRef(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const hasMessages = messages.length > 0;

  useEffect(() => {
    if (hasMessages) {
      messagesEndRef.current?.scrollIntoView({
        behavior: "smooth",
      });
    }
  }, [messages, isLoading, hasMessages]);

  async function handleSend(question: string) {
    if (!question.trim() || isLoading) {
      return;
    }

    const userMessage: Message = {
      id: ++nextId.current,
      role: "user",
      content: question,
    };

    setMessages((previous) => [...previous, userMessage]);
    setIsLoading(true);

    try {
      const response = await sendChatMessage(question);

      const assistantMessage: Message = {
        id: ++nextId.current,
        role: "assistant",
        content: response.answer,
        sources: response.sources,
      };

      setMessages((previous) => [
        ...previous,
        assistantMessage,
      ]);
    } catch (error) {
      console.error("Chat request failed:", error);

      const errorMessage: Message = {
        id: ++nextId.current,
        role: "assistant",
        content:
          "לא הצלחנו לקבל תשובה כרגע. בדקי שהשרת פועל ונסי שוב.",
        isError: true,
      };

      setMessages((previous) => [...previous, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div
      dir="rtl"
      className="relative isolate flex min-h-screen flex-col overflow-hidden bg-[#F9FBFF]"
    >
      <PhoenixBackground />

      <div className="relative z-10 mx-auto flex w-full max-w-6xl flex-1 flex-col px-6 py-10 md:px-12">
        {!hasMessages ? (
          <>
            {/* Welcome heading */}
            <div className="mb-12 mt-12 text-center md:mt-16">
              <p className="mb-4 text-xl font-bold text-[#FF6600]">
                PhoenixRAG
              </p>

              <h1 className="text-4xl font-extrabold tracking-tight text-[#102B56] md:text-6xl">
                איך אפשר לעזור לך היום?
              </h1>

              <p className="mt-6 text-xl leading-relaxed text-[#64748B] md:text-2xl">
                שאלו שאלה וקבלו תשובה המבוססת על המידע באתר הפניקס
              </p>
            </div>

            {/* Suggestion cards */}
            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              {suggestions.map((item) => {
                const Icon = item.icon;

                return (
                  <button
                    key={item.title}
                    type="button"
                    onClick={() => void handleSend(item.description)}
                    disabled={isLoading}
                    className="group flex min-h-[125px] items-center gap-5 rounded-2xl border border-slate-200/80 bg-white/90 p-7 text-right shadow-[0_5px_25px_rgba(16,43,86,0.05)] backdrop-blur-sm transition-all duration-300 hover:-translate-y-1 hover:border-blue-200 hover:shadow-[0_12px_35px_rgba(16,43,86,0.12)] disabled:opacity-60"
                  >
                    <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-[#FFF0E6] text-[#FF6600]">
                      <Icon size={30} strokeWidth={1.8} />
                    </div>

                    <div className="min-w-0 flex-1">
                      <h3 className="text-xl font-bold text-[#102B56] md:text-[22px]">
                        {item.title}
                      </h3>

                      <p className="mt-2 text-base leading-relaxed text-slate-500">
                        {item.description}
                      </p>
                    </div>

                    <ChevronLeft
                      size={23}
                      className="shrink-0 text-slate-400 transition-transform group-hover:-translate-x-1 group-hover:text-[#FF6600]"
                    />
                  </button>
                );
              })}
            </div>
          </>
        ) : (
          <section
            aria-label="שיחת PhoenixRAG"
            className="flex flex-1 flex-col gap-6 pb-10"
          >
            <div className="border-b border-slate-200 pb-5">
              <p className="text-sm font-semibold text-[#FF6600]">
                PhoenixRAG
              </p>
              <h2 className="mt-2 text-3xl font-bold text-[#102B56]">
                השיחה שלך
              </h2>
            </div>

            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
              />
            ))}

            {isLoading && (
              <div
                role="status"
                className="flex items-center gap-3 text-[#0B3B91]"
              >
                <LoaderCircle
                  size={22}
                  className="animate-spin"
                />
                <span>מחפשים מידע ומכינים תשובה...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </section>
        )}

        {/* Input stays at the bottom */}
        <div className="mt-auto pt-12">
          <ChatInput
            onSend={(question) => void handleSend(question)}
            isLoading={isLoading}
          />

          <p className="mt-6 text-center text-sm leading-relaxed text-slate-500">
            התשובות מבוססות על תוכן שנאסף מאתר הפניקס.
            במקרה שהמידע אינו קיים באתר, נעדכן זאת.
          </p>
        </div>
      </div>
    </div>
  );
}