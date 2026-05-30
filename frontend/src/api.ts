export interface Mention {
  text: string;
  start_char: number;
  end_char: number;
  is_negated: boolean;
}

export interface Diagnosis {
  label: string;
  label_en: string;
  probability: number;
}

export interface TriageResponse {
  level: number;
  label: string;
  description: string;
  color: string;
  confidence: number;
  is_ood: boolean;
  backend: string;
}

export interface AnalyzeResponse {
  symptoms: Mention[];
  diseases: Mention[];
}

export interface ReportResponse {
  diagnoses: Diagnosis[];
  symptoms: Mention[];
  diseases: Mention[];
  summary: string;
  report_content: string;
  report_filename: string;
}

const API_BASE = "/api";

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = "";
    try {
      const json = await res.json();
      detail = json?.detail ?? JSON.stringify(json);
    } catch {
      detail = await res.text();
    }
    throw new Error(`HTTP ${res.status}: ${detail}`);
  }
  return res.json();
}

export const api = {
  triage: (text: string) =>
    postJSON<TriageResponse>("/triage", { text }),
  analyze: (text: string) =>
    postJSON<AnalyzeResponse>("/analyze", { text }),
  report: (text: string, urgency: TriageResponse) =>
    postJSON<ReportResponse>("/report", { text, urgency }),
};
