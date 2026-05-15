import { FormEvent, useState } from "react";
import { BrainCircuit, Loader2, Search } from "lucide-react";

import { analyze } from "../api/client";
import type { AnalysisPayload } from "../types/report";

const CHAINS = [
  { id: 1, name: "Ethereum" },
  { id: 56, name: "BNB Chain" },
  { id: 8453, name: "Base" },
  { id: 137, name: "Polygon" },
  { id: 42161, name: "Arbitrum" },
  { id: 10, name: "Optimism" },
];

export function InputPage({ onAnalyzed }: { onAnalyzed: (payload: AnalysisPayload) => void }) {
  const [query, setQuery] = useState("");
  const [chainId, setChainId] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = await analyze(query, chainId);
      onAnalyzed(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to generate report");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
      <section className="panel p-6 sm:p-8">
        <div className="mb-8 flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded bg-brand text-white">
            <BrainCircuit size={24} />
          </span>
          <div>
            <h1 className="text-2xl font-bold sm:text-3xl">AgentVault AI</h1>
            <p className="mt-1 text-sm text-slate-600">Generate Web3 intelligence and persist it to 0G Storage.</p>
          </div>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="label" htmlFor="query">Wallet address or project name</label>
            <div className="grid gap-3 lg:grid-cols-[1fr_12rem_auto]">
              <input
                id="query"
                className="min-h-12 flex-1 rounded border border-line bg-white px-4 text-base outline-none ring-brand/20 transition focus:ring-4"
                placeholder="0x742d... or https://project.xyz"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                required
              />
              <select
                className="min-h-12 rounded border border-line bg-white px-3 text-sm font-semibold outline-none ring-brand/20 transition focus:ring-4"
                value={chainId}
                onChange={(event) => setChainId(Number(event.target.value))}
                title="Wallet chain"
              >
                {CHAINS.map((chain) => (
                  <option key={chain.id} value={chain.id}>
                    {chain.name}
                  </option>
                ))}
              </select>
              <button className="primary-button" disabled={loading || !query.trim()}>
                {loading ? <Loader2 className="animate-spin" size={18} /> : <Search size={18} />}
                Generate Report
              </button>
            </div>
          </div>
          {error && <p className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
        </form>
      </section>

      <aside className="grid content-start gap-4">
        {["AI converts raw Web3 activity into structured JSON.", "Reports can be uploaded to 0G Storage testnet.", "History acts as persistent decentralized memory."].map((item) => (
          <div key={item} className="panel p-5">
            <p className="text-sm font-semibold leading-6 text-slate-700">{item}</p>
          </div>
        ))}
      </aside>
    </div>
  );
}
