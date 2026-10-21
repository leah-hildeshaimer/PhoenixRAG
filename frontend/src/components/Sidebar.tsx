import {
  MessageCircle,
  MessageSquare,
  Plus,
  Info,
  Link2,
  HelpCircle,
  Sparkles,
} from "lucide-react";

const recentChats = [
  "מה מכסה ביטוח דירה?",
  "איך מגישים תביעה?",
  "מה שעות פעילות השירות?",
];

export default function Sidebar() {
  return (
    <aside
      dir="rtl"
      className="flex h-full w-full flex-col border-l border-slate-200 bg-white"
    >
      {/* Official logo area */}
      <div className="flex min-h-[92px] items-center justify-center border-b border-slate-100 bg-white px-5 py-4">
        <img
          src="/FnxLogo.svg"
          alt="לוגו הפניקס"
          className="max-h-14 max-w-full object-contain"
        />
      </div>

      {/* PhoenixRAG brand */}
      <div className="bg-gradient-to-bl from-[#102B56] to-[#183B70] px-6 py-6 text-white">
        <div className="flex items-center gap-3">
          <div className="flex h-13 w-13 shrink-0 items-center justify-center rounded-xl bg-[#FF6600] p-3 shadow-lg shadow-orange-950/20">
            <Sparkles size={25} />
          </div>

          <div className="min-w-0">
            <h1 className="text-[25px] font-bold tracking-tight">
              PhoenixRAG
            </h1>
            <p className="mt-1 text-xs text-blue-100">
              עוזר מידע המבוסס על אתר הפניקס
            </p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="space-y-2 px-4 py-6">
        <button
          type="button"
          className="flex w-full items-center gap-3 rounded-xl bg-[#EDF4FF] px-4 py-4 text-right text-base font-semibold text-[#0B3B91] transition hover:bg-blue-100"
        >
          <Plus size={22} />
          שיחה חדשה
        </button>

        <div className="flex items-center gap-3 rounded-xl px-4 py-3.5 text-base text-[#102B56]">
          <HelpCircle size={21} />
          שאלות נפוצות
        </div>

        <div className="flex items-center gap-3 rounded-xl px-4 py-3.5 text-base text-[#102B56]">
          <Info size={21} />
          מידע על המערכת
        </div>

        <div className="flex items-center gap-3 rounded-xl px-4 py-3.5 text-base text-[#102B56]">
          <Link2 size={21} />
          המקורות שלנו
        </div>
      </nav>

      <div className="mx-5 border-t border-slate-200" />

      {/* Recent chats: visual examples */}
      <section className="min-h-0 flex-1 overflow-y-auto px-4 py-6">
        <h2 className="mb-4 px-3 text-base font-semibold text-slate-500">
          שיחות אחרונות
        </h2>

        <div className="space-y-1">
          {recentChats.map((chat) => (
            <div
              key={chat}
              className="flex items-center gap-3 rounded-lg px-3 py-3.5 text-base text-slate-600"
            >
              <MessageSquare size={19} className="shrink-0" />
              <span className="truncate">{chat}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <div className="border-t border-slate-200 px-5 py-5">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <MessageCircle size={18} />
          <span>מבוסס על מידע מאתר הפניקס</span>
        </div>
      </div>
    </aside>
  );
}