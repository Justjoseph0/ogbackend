import { ArrowRight, BrainCircuit, Database, FileSearch, ShieldCheck } from "lucide-react";

export function HomePage({ onStart, onHistory }: { onStart: () => void; onHistory: () => void }) {
  return (
    <div className="grid gap-6">
      <section className="hero-shell overflow-hidden">
        <div className="hero-grid">
          <div className="p-6 sm:p-8 lg:p-10">
            <div className="mb-7 flex w-fit items-center gap-2 rounded border border-white/20 bg-white/10 px-3 py-1 text-xs font-bold uppercase text-teal-50">
              <ShieldCheck size={15} />
              0G APAC Hackathon MVP
            </div>
            <h1 className="max-w-3xl text-4xl font-bold leading-tight text-white sm:text-5xl lg:text-6xl">
              AgentVault AI
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-teal-50 sm:text-lg">
              AI wallet intelligence with persistent reports stored on 0G Storage testnet.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <button className="hero-primary" onClick={onStart}>
                <BrainCircuit size={19} />
                Analyze Wallet
                <ArrowRight size={18} />
              </button>
              <button className="hero-secondary" onClick={onHistory}>
                <Database size={18} />
                Stored Reports
              </button>
            </div>
          </div>

          <div className="hero-proof p-5 sm:p-6">
            <div className="rounded border border-white/15 bg-white/10 p-4">
              <div className="mb-4 flex items-center justify-between">
                <span className="text-xs font-bold uppercase text-teal-100">Live pipeline</span>
                <span className="rounded bg-emerald-400 px-2 py-1 text-xs font-bold text-emerald-950">Ready</span>
              </div>
              <div className="space-y-3">
                {[
                  ["Wallet indexer", "Etherscan V2"],
                  ["AI provider", "OpenAI live"],
                  ["Memory layer", "0G Storage"],
                  ["Proof", "Explorer tx hash"],
                ].map(([label, value]) => (
                  <div key={label} className="flex items-center justify-between gap-4 rounded border border-white/10 bg-slate-950/35 px-3 py-3">
                    <span className="text-sm text-teal-100">{label}</span>
                    <span className="text-right text-sm font-bold text-white">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <Feature icon={<FileSearch size={21} />} title="Indexed Wallet Data" text="Normal, internal, and ERC-20 activity are converted into a compact wallet snapshot." />
        <Feature icon={<BrainCircuit size={21} />} title="AI Risk Report" text="OpenAI turns raw activity into summary, risk level, insights, behaviors, and recommendation." />
        <Feature icon={<Database size={21} />} title="0G Memory" text="Reports are uploaded to 0G Storage and listed later with root hash and transaction proof." />
      </section>
    </div>
  );
}

function Feature({ icon, title, text }: { icon: React.ReactNode; title: string; text: string }) {
  return (
    <article className="panel p-5">
      <div className="mb-4 grid h-10 w-10 place-items-center rounded bg-teal-50 text-brand">{icon}</div>
      <h2 className="text-lg font-bold">{title}</h2>
      <p className="mt-2 text-sm leading-6 text-slate-600">{text}</p>
    </article>
  );
}
