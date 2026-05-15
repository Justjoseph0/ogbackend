import { useState } from "react";
import { BrainCircuit, Database, History, Home, ShieldCheck } from "lucide-react";

import { DashboardPage } from "./pages/DashboardPage";
import { HistoryPage } from "./pages/HistoryPage";
import { HomePage } from "./pages/HomePage";
import { InputPage } from "./pages/InputPage";
import type { AnalysisPayload, StoredReport } from "./types/report";

type View = "home" | "input" | "dashboard" | "history";

export default function App() {
  const [view, setView] = useState<View>("home");
  const [analysis, setAnalysis] = useState<AnalysisPayload | null>(null);
  const [storedReport, setStoredReport] = useState<StoredReport | null>(null);

  const handleAnalyzed = (payload: AnalysisPayload) => {
    setAnalysis(payload);
    setStoredReport(null);
    setView("dashboard");
  };

  return (
    <div className="min-h-screen bg-app text-ink">
      <header className="sticky top-0 z-20 border-b border-line/80 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <button className="flex items-center gap-3" onClick={() => setView("home")}>
            <span className="grid h-10 w-10 place-items-center rounded bg-brand text-white">
              <ShieldCheck size={22} />
            </span>
            <span>
              <span className="block text-left text-lg font-semibold">AgentVault AI</span>
              <span className="block text-left text-xs text-slate-500">0G persistent intelligence</span>
            </span>
          </button>
          <nav className="flex items-center gap-2">
            <button className="nav-button" onClick={() => setView("home")} title="Home">
              <Home size={18} />
              <span>Home</span>
            </button>
            <button className="nav-button" onClick={() => setView("input")} title="Analyze">
              <BrainCircuit size={18} />
              <span>Analyze</span>
            </button>
            <button className="nav-button" onClick={() => setView("dashboard")} disabled={!analysis} title="Dashboard">
              <Database size={18} />
              <span>Dashboard</span>
            </button>
            <button className="nav-button" onClick={() => setView("history")} title="History">
              <History size={18} />
              <span>History</span>
            </button>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        {view === "home" && <HomePage onStart={() => setView("input")} onHistory={() => setView("history")} />}
        {view === "input" && <InputPage onAnalyzed={handleAnalyzed} />}
        {view === "dashboard" && analysis && (
          <DashboardPage analysis={analysis} storedReport={storedReport} onStored={setStoredReport} />
        )}
        {view === "dashboard" && !analysis && <InputPage onAnalyzed={handleAnalyzed} />}
        {view === "history" && <HistoryPage onOpenReport={(report) => {
          setAnalysis(report);
          setStoredReport(report);
          setView("dashboard");
        }} />}
      </main>
    </div>
  );
}
