import Sidebar from "./components/Sidebar";
import WelcomeScreen from "./components/WelcomeScreen";

function App() {
  return (
    <div dir="rtl" className="flex min-h-screen">
      {/* Right sidebar */}
      <div className="hidden w-80 shrink-0 lg:block">
        <div className="sticky top-0 h-screen">
          <Sidebar />
        </div>
      </div>

      {/* Main area */}
      <main className="min-w-0 flex-1">
        <WelcomeScreen />
      </main>
    </div>
  );
}

export default App;