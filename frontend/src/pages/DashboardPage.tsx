import { useState } from "react";
import { Activity, CheckCircle2, Copy, Database, ExternalLink, Loader2, Network, ShieldCheck, Wallet } from "lucide-react";

import { storeReport } from "../api/client";
import { ReportCard } from "../components/ReportCard";
import type { AnalysisPayload, StoredReport } from "../types/report";

export function DashboardPage({
  analysis,
  storedReport,
  onStored,
}: {
  analysis: AnalysisPayload;
  storedReport: StoredReport | null;
  onStored: (report: StoredReport) => void;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const raw = analysis.raw_data;
  const ai = analysis.ai ?? analysis.report._ai;
  const recentTransactions = Array.isArray(raw.recent_transactions) ? raw.recent_transactions.slice(0, 6) : [];

  const save = async () => {
    setError("");
    setLoading(true);
    try {
      onStored(await storeReport(analysis));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to store report");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid gap-6">
      <section className="dashboard-hero">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <span className="label text-teal-100">Current report</span>
            <h2 className="break-all text-2xl font-bold text-white sm:text-3xl">{analysis.query}</h2>
            <div className="mt-3 flex flex-wrap gap-2">
              <Badge icon={<Wallet size={14} />} text={`${analysis.input_type} analysis`} />
              <Badge icon={<Network size={14} />} text={`chain ${formatValue(raw.chain_id)}`} />
              <Badge icon={<Activity size={14} />} text={String(raw.data_source ?? "project snapshot")} />
              <Badge icon={<ShieldCheck size={14} />} text={`${ai?.ai_provider ?? "unknown"} / ${ai?.ai_status ?? "unknown"}`} />
            </div>
            {ai?.ai_error && (
              <p className="mt-3 max-w-3xl rounded border border-amber-200 bg-amber-50 p-2 text-xs leading-5 text-amber-800">
                {ai.ai_error}
              </p>
            )}
          </div>
          <div className="flex flex-col gap-3 sm:flex-row lg:flex-col">
            <button className="hero-primary min-w-44" disabled={loading || !!storedReport} onClick={save}>
              {loading ? <Loader2 className="animate-spin" size={18} /> : storedReport ? <CheckCircle2 size={18} /> : <Database size={18} />}
              {storedReport ? "Stored on 0G" : "Store on 0G"}
            </button>
            <p className="text-xs leading-5 text-teal-50 lg:max-w-52">
              Store the full JSON report and proof metadata on 0G Storage testnet.
            </p>
          </div>
        </div>
        {error && <p className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      </section>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="Transactions" value={formatValue(raw.transaction_count)} />
        <Metric label="ERC-20 Transfers" value={formatValue(raw.erc20_transfer_count)} />
        <Metric label="Counterparties" value={formatValue(raw.counterparty_count)} />
        <Metric label="Volume" value={formatValue(raw.estimated_volume_eth)} />
      </section>

      <ReportCard report={analysis.report} />

      <section className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
        <div className="panel p-5">
          <div className="mb-4 flex items-center justify-between">
            <span className="label mb-0">Recent wallet activity</span>
            <span className="rounded border border-line bg-slate-50 px-2 py-1 text-xs font-bold text-slate-500">{recentTransactions.length}</span>
          </div>
          {recentTransactions.length ? (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[680px] text-left text-sm">
                <thead className="border-b border-line text-xs uppercase text-slate-500">
                  <tr>
                    <th className="py-2 pr-3">Type</th>
                    <th className="py-2 pr-3">Direction</th>
                    <th className="py-2 pr-3">Asset</th>
                    <th className="py-2 pr-3">Value</th>
                    <th className="py-2 pr-3">Hash</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {recentTransactions.map((tx, index) => (
                    <tr key={`${String(tx.hash)}-${index}`} className="text-slate-700">
                      <td className="py-3 pr-3 font-semibold">{formatValue(tx.transfer_type)}</td>
                      <td className="py-3 pr-3">{formatValue(tx.direction)}</td>
                      <td className="py-3 pr-3">{formatValue(tx.asset)}</td>
                      <td className="py-3 pr-3">{formatValue(tx.token_amount ?? tx.value_native)}</td>
                      <td className="max-w-52 truncate py-3 pr-3 font-mono text-xs">{formatValue(tx.hash)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm leading-6 text-slate-600">No recent indexed transactions were returned for this chain and wallet.</p>
          )}
        </div>

        <div className="panel p-5">
          <span className="label">0G storage proof</span>
          {storedReport ? (
            <div className="space-y-3 text-sm">
              <ProofRow label="Status" value={storedReport.storage_status} />
              <ProofRow label="Root hash" value={storedReport.root_hash} />
              <ProofRow label="Transaction" value={storedReport.tx_hash || "No transaction in local demo mode"} />
              {storedReport.explorer_url && (
                <a className="secondary-button w-fit" href={storedReport.explorer_url} target="_blank" rel="noreferrer">
                  <ExternalLink size={16} />
                  Explorer
                </a>
              )}
            </div>
          ) : (
            <p className="text-sm leading-6 text-slate-600">Store this report to create a 0G root hash and blockchain proof.</p>
          )}
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <div className="panel p-5">
          <span className="label">Data source details</span>
          <div className="grid gap-3 text-sm">
            <InfoRow label="Source" value={formatValue(raw.data_source)} />
            <InfoRow label="Chain ID" value={formatValue(raw.chain_id)} />
            <InfoRow label="Normal txs" value={formatValue(raw.normal_transaction_count)} />
            <InfoRow label="Internal txs" value={formatValue(raw.internal_transaction_count)} />
            <InfoRow label="Tokens" value={Array.isArray(raw.token_symbols_seen) ? raw.token_symbols_seen.join(", ") || "None" : "None"} />
          </div>
        </div>
        <div className="panel p-5">
          <span className="label">Raw activity snapshot</span>
          <pre className="max-h-72 overflow-auto rounded border border-line bg-slate-950 p-4 text-xs leading-5 text-slate-100">
            {JSON.stringify(analysis.raw_data, null, 2)}
          </pre>
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="panel p-4">
      <span className="block text-xs font-bold uppercase text-slate-500">{label}</span>
      <span className="mt-2 block break-words text-2xl font-bold text-ink">{value}</span>
    </div>
  );
}

function Badge({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded border border-white/20 bg-white/10 px-2.5 py-1 text-xs font-bold uppercase text-teal-50">
      {icon}
      {text}
    </span>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-line pb-2 last:border-b-0">
      <span className="font-semibold text-slate-500">{label}</span>
      <span className="text-right font-bold text-slate-800">{value}</span>
    </div>
  );
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : String(Number(value.toFixed(6)));
  }
  return String(value);
}

function ProofRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="mb-1 block text-xs font-bold uppercase text-slate-500">{label}</span>
      <button
        className="flex w-full items-start gap-2 break-all rounded border border-line bg-slate-50 p-3 text-left text-slate-700"
        onClick={() => navigator.clipboard.writeText(value)}
        title="Copy"
      >
        <Copy className="mt-0.5 shrink-0" size={15} />
        {value}
      </button>
    </div>
  );
}
