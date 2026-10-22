import { useState } from "react";
import { Compass, MessageCircle } from "lucide-react";
import Sidebar from "./components/Sidebar";
import WelcomeScreen from "./components/WelcomeScreen";
import CompassScreen from "./components/CompassScreen";

type ChatMode = "classic" | "compass";

function App() {
  const [mode, setMode] = useState<ChatMode>("classic");
  const [compassVisited, setCompassVisited] = useState(false);

  function selectMode(nextMode: ChatMode) {
    if (nextMode === "compass") setCompassVisited(true);
    setMode(nextMode);
  }

  return (
    <div dir="rtl" className="flex min-h-screen bg-[#F9FBFF]">
      {/* Keep the existing sidebar intact. */}
      <div className="hidden w-80 shrink-0 lg:block">
        <div className="sticky top-0 h-screen">
          <Sidebar />
        </div>
      </div>

      <main className="flex min-w-0 flex-1 flex-col">
        <div className="sticky top-0 z-30 border-b border-blue-100 bg-white/95 px-4 py-3 backdrop-blur-md sm:px-6">
          <nav
            className="mx-auto flex w-full max-w-xl items-center gap-2 rounded-2xl bg-[#EDF4FF] p-1.5"
            aria-label="בחירת מצב השיחה"
          >
            <button
              type="button"
              aria-pressed={mode === "classic"}
              onClick={() => selectMode("classic")}
              className={`flex min-w-0 flex-1 items-center justify-center gap-2 rounded-xl px-3 py-3 text-sm font-bold transition sm:text-base ${
                mode === "classic"
                  ? "bg-white text-[#0B3B91] shadow-sm"
                  : "text-slate-600 hover:bg-white/60"
              }`}
            >
              <MessageCircle size={19} aria-hidden="true" />
              צ'אט רגיל
            </button>
            <button
              type="button"
              aria-pressed={mode === "compass"}
              onClick={() => selectMode("compass")}
              className={`flex min-w-0 flex-1 items-center justify-center gap-2 rounded-xl px-3 py-3 text-sm font-bold transition sm:text-base ${
                mode === "compass"
                  ? "bg-white text-[#0B3B91] shadow-sm"
                  : "text-slate-600 hover:bg-white/60"
              }`}
            >
              <Compass size={19} aria-hidden="true" />
              ✨ ליווי חכם
            </button>
          </nav>
        </div>

        {/* Keeping both components mounted preserves each conversation while switching. */}
        <div className={mode === "classic" ? "flex-1" : "hidden"}>
          <WelcomeScreen />
        </div>
        {compassVisited && (
          <div className={mode === "compass" ? "flex-1" : "hidden"}>
            <CompassScreen />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
