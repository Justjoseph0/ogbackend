import { AlertTriangle, CheckCircle2, CircleDot } from "lucide-react";

import type { AiReport } from "../types/report";

const riskStyles = {
  low: "bg-emerald-50 text-emerald-800 border-emerald-200",
  medium: "bg-amber-50 text-amber-800 border-amber-200",
  high: "bg-red-50 text-red-800 border-red-200",
};

export function ReportCard({ report }: { report: AiReport }) {
  return (
    <section className="panel p-5">
      <div className="flex flex-col gap-3 border-b border-line pb-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <span className="label">AI intelligence report</span>
          <p className="max-w-3xl text-lg font-semibold leading-7">{report.summary}</p>
        </div>
        <span className={`inline-flex w-fit items-center gap-2 rounded border px-3 py-1 text-sm font-bold ${riskStyles[report.risk_level]}`}>
          {report.risk_level === "high" ? <AlertTriangle size={16} /> : <CheckCircle2 size={16} />}
          {report.risk_level.toUpperCase()} RISK
        </span>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <div>
          <h3 className="mb-3 text-sm font-bold uppercase text-slate-500">Key behaviors</h3>
          <div className="flex flex-wrap gap-2">
            {report.key_behaviors.map((item) => (
              <span key={item} className="rounded border border-line bg-slate-50 px-3 py-1 text-sm font-semibold text-slate-700">
                {item}
              </span>
            ))}
          </div>
        </div>
        <div>
          <h3 className="mb-3 text-sm font-bold uppercase text-slate-500">Recommendation</h3>
          <p className="rounded border border-line bg-[#fbfcf8] p-3 text-sm leading-6 text-slate-700">{report.recommendation}</p>
        </div>
      </div>

      <div className="mt-5">
        <h3 className="mb-3 text-sm font-bold uppercase text-slate-500">Insights</h3>
        <div className="grid gap-3">
          {report.insights.map((item) => (
            <div key={item} className="flex gap-3 rounded border border-line bg-white p-3">
              <CircleDot className="mt-0.5 text-brand" size={17} />
              <p className="text-sm leading-6 text-slate-700">{item}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
