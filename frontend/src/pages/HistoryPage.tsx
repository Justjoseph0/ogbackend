import { useEffect, useState } from "react";
import { Clock, ExternalLink, Loader2 } from "lucide-react";

import { getHistory } from "../api/client";
import type { StoredReport } from "../types/report";

export function HistoryPage({ onOpenReport }: { onOpenReport: (report: StoredReport) => void }) {
  const [reports, setReports] = useState<StoredReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getHistory()
      .then(setReports)
      .catch((err) => setError(err instanceof Error ? err.message : "Unable to load history"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="panel grid min-h-80 place-items-center p-6">
        <Loader2 className="animate-spin text-brand" size={32} />
      </div>
    );
  }

  return (
    <section className="panel p-5">
      <div className="mb-5 flex items-center justify-between border-b border-line pb-4">
        <div>
          <span className="label">Persistent memory</span>
          <h1 className="text-2xl font-bold">Stored reports</h1>
        </div>
        <span className="rounded border border-line bg-slate-50 px-3 py-1 text-sm font-bold text-slate-600">{reports.length}</span>
      </div>
      {error && <p className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      {!reports.length && !error && <p className="text-sm text-slate-600">No reports stored yet.</p>}
      <div className="grid gap-3">
        {reports.map((report) => (
          <article key={report.id} className="rounded border border-line bg-white p-4">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <button className="text-left" onClick={() => onOpenReport(report)}>
                <h2 className="break-all text-lg font-bold">{report.query}</h2>
                <p className="mt-1 line-clamp-2 text-sm leading-6 text-slate-600">{report.report.summary}</p>
              </button>
              <div className="flex flex-wrap items-center gap-2">
                <span className="inline-flex items-center gap-1 rounded border border-line bg-slate-50 px-2 py-1 text-xs font-bold text-slate-600">
                  <Clock size={13} />
                  {new Date(report.created_at).toLocaleString()}
                </span>
                <span className="rounded border border-line bg-slate-50 px-2 py-1 text-xs font-bold text-slate-600">{report.storage_status}</span>
                {report.explorer_url && (
                  <a className="secondary-button min-h-0 px-2 py-1 text-xs" href={report.explorer_url} target="_blank" rel="noreferrer">
                    <ExternalLink size={13} />
                    Proof
                  </a>
                )}
              </div>
            </div>
            <p className="mt-3 break-all text-xs text-slate-500">{report.root_hash}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
