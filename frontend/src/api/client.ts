import type { AnalysisPayload, StoredReport } from "../types/report";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) },
    ...options,
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }
  return response.json();
}

export function analyze(query: string, chainId?: number) {
  return request<AnalysisPayload>("/analyze/", {
    method: "POST",
    body: JSON.stringify({ query, chain_id: chainId }),
  });
}

export function storeReport(payload: AnalysisPayload) {
  return request<StoredReport>("/store/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getHistory() {
  return request<StoredReport[]>("/history/");
}

export function getReport(id: number) {
  return request<StoredReport>(`/report/${id}/`);
}
