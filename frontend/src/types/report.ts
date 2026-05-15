export type RiskLevel = "low" | "medium" | "high";

export type AiReport = {
  summary: string;
  risk_level: RiskLevel;
  key_behaviors: string[];
  insights: string[];
  recommendation: string;
  _ai?: AiMetadata;
};

export type AiMetadata = {
  ai_provider: string;
  ai_model: string;
  ai_status: "live" | "fallback" | string;
  ai_error?: string;
};

export type AnalysisPayload = {
  query: string;
  input_type: "wallet" | "project" | "website";
  raw_data: Record<string, unknown>;
  report: AiReport;
  ai?: AiMetadata;
};

export type StoredReport = AnalysisPayload & {
  id: number;
  root_hash: string;
  tx_hash: string;
  explorer_url: string;
  storage_status: string;
  created_at: string;
};
