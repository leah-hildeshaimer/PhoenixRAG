import { useEffect, useRef, useState } from "react";
import {
  Compass,
  FileSearch,
  House,
  CarFront,
  Headset,
  ShieldCheck,
  ChevronLeft,
  LoaderCircle,
  RefreshCcw,
  Sparkles,
} from "lucide-react";

import PhoenixBackground from "./PhoenixBackground";
import ChatInput from "./ChatInput";
import ChatMessage from "./ChatMessage";
import type { Message } from "./ChatMessage";
import { sendChatMessage } from "../services/chatApi";

const startingChoices = [
  { label: "קרה לי משהו ואני צריכה עזרה", question: "נגרם לי נזק. איזה מידע כדאי למסור כדי לברר מה עושים?", icon: ShieldCheck },
  { label: "ביטוח רכב", question: "מה חשוב לבדוק כשבוחרים ביטוח רכב בפניקס?", icon: CarFront },
  { label: "ביטוח דירה", question: "מה חשוב לבדוק בכיסויים של ביטוח דירה בפניקס?", icon: House },
  { label: "תביעה או שירות", question: "איך אפשר לקבל מידע על תביעות ושירות לקוחות באתר הפניקס?", icon: Headset },
];

const nextChoices = [
  { label: "מה כדאי לבדוק עכשיו?", question: "לפי המידע באתר הפניקס, מה כדאי לבדוק כדי להתקדם?" },
  { label: "מה התהליך הרלוונטי?", question: "האם באתר הפניקס יש מידע על התהליך הרלוונטי ומה השלבים שלו?" },
  { label: "איפה אפשר לקרוא עוד?", question: "איפה באתר הפניקס אפשר לקרוא מידע נוסף בנושא?" },
];

export default function CompassScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [busy, setBusy] = useState(false);
  const [lastQuestion, setLastQuestion] = useState("");
  const nextId = useRef(0);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messages.length > 0) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  async function ask(question: string) {
    const text = question.trim();
    if (!text || busy) return;
    setLastQuestion(text);
    setMessages((old) => [...old, { id: ++nextId.current, role: "user", content: text }]);
    setBusy(true);
    try {
      // Safe initial integration: reuse the existing verified endpoint.
      const response = await sendChatMessage(text);
      setMessages((old) => [
        ...old,
        { id: ++nextId.current, role: "assistant", content: response.answer, sources: response.sources },
      ]);
    } catch (error) {
      console.error("Compass chat failed:", error);
      setMessages((old) => [
        ...old,
        {
          id: ++nextId.current,
          role: "assistant",
          content: "לא הצלחנו לקבל תשובה כרגע. נסו שוב בעוד רגע.",
          isError: true,
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    if (busy) return;
    setMessages([]);
    setLastQuestion("");
    nextId.current = 0;
  }

  return (
    <div dir="rtl" className="relative isolate flex min-h-screen flex-col overflow-hidden bg-[#F9FBFF]">
      <PhoenixBackground />
      <div className="relative z-10 mx-auto flex w-full max-w-6xl flex-1 flex-col px-5 py-9 md:px-12">
        {messages.length === 0 ? (
          <>
            <div className="mx-auto mb-10 mt-10 max-w-3xl text-center md:mt-14">
              <span className="mb-4 inline-flex items-center gap-2 rounded-full border border-orange-100 bg-orange-50 px-4 py-2 text-sm font-bold text-[#DF6018]">
                <Sparkles size={17} /> Phoenix Compass
              </span>
              <h1 className="text-4xl font-extrabold tracking-tight text-[#102B56] md:text-6xl">בואי נמצא את הדרך שלך</h1>
              <p className="mt-5 text-lg leading-8 text-slate-600 md:text-xl">
                לא חייבים לדעת איך לנסח שאלה. בחרי נושא, הקלידי או דברי — ונעזור למצוא מידע מאומת באתר הפניקס.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {startingChoices.map(({ label, question, icon: Icon }) => (
                <button
                  key={label}
                  type="button"
                  onClick={() => void ask(question)}
                  disabled={busy}
                  className="group flex min-h-[110px] items-center gap-4 rounded-2xl border border-blue-100 bg-white/95 p-6 text-right shadow-[0_8px_30px_rgba(16,43,86,0.06)] transition hover:-translate-y-1 hover:border-orange-200 hover:shadow-lg disabled:opacity-50"
                >
                  <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-orange-50 text-[#FF6600]"><Icon size={28} /></span>
                  <span className="min-w-0 flex-1 text-lg font-bold text-[#102B56]">{label}</span>
                  <ChevronLeft className="shrink-0 text-slate-400 transition group-hover:-translate-x-1" />
                </button>
              ))}
            </div>
          </>
        ) : (
          <section aria-label="שיחת Phoenix Compass" className="flex flex-1 flex-col gap-5 pb-8">
            <div className="flex items-center justify-between gap-3 border-b border-slate-200 pb-4">
              <div>
                <p className="flex items-center gap-2 text-sm font-bold text-[#FF6600]"><Compass size={17} /> Phoenix Compass</p>
                <h2 className="mt-1 text-2xl font-bold text-[#102B56]">הליווי שלך</h2>
              </div>
              <button type="button" onClick={reset} disabled={busy} className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm text-[#102B56] hover:bg-slate-50 disabled:opacity-50">
                <RefreshCcw size={16} /> התחלה מחדש
              </button>
            </div>
            {messages.map((message) => <ChatMessage key={message.id} message={message} />)}
            {busy && <p role="status" className="flex items-center gap-2 text-sm text-[#0B3B91]"><LoaderCircle className="animate-spin" size={19} /> מחפשים ומאמתים מידע באתר הפניקס...</p>}
            {!busy && messages.at(-1)?.role === "assistant" && !messages.at(-1)?.isError && (
              <div className="rounded-2xl border border-blue-100 bg-white/90 p-5">
                <p className="mb-3 flex items-center gap-2 font-bold text-[#102B56]"><FileSearch size={19} /> מה תרצי לבדוק בהמשך?</p>
                <div className="flex flex-wrap gap-2">
                  {nextChoices.map((item) => (
                    <button key={item.label} type="button" className="rounded-full border border-blue-200 bg-blue-50 px-4 py-2 text-sm font-semibold text-[#0B3B91] hover:bg-blue-100" onClick={() => void ask(`בהמשך לשאלה: ${lastQuestion}\n${item.question}`)}>
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </section>
        )}
        <div className="mt-auto pt-9">
          <ChatInput onSend={(question) => void ask(question)} isLoading={busy} placeholder="ספרי לי מה קרה, או השתמשי במיקרופון..." />
          <p className="mt-4 text-center text-sm text-slate-500">
            שלב ראשון: בחירת נושא ושיחה דרך מנוע ה־RAG המאומת. שאלות AI דינמיות, מסלולי פעולה וראיות ברמת הטענה יתווספו בשלבים הבאים.
          </p>
        </div>
      </div>
    </div>
  );
}
