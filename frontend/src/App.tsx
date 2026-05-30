import { useState } from "react";
import RecordButton from "./components/RecordButton";
import TextModal from "./components/TextModal";
import NERPreview from "./components/NERPreview";
import Results from "./components/Results";
import { api, type AnalyzeResponse, type TriageResponse, type ReportResponse } from "./api";

/**
 * Flujo (igual que la arquitectura del .tex):
 *   idle → input → triaging → ood (si nivel 0)
 *                           → preview → confirming → results
 */
type Stage = "idle" | "input" | "triaging" | "ood" | "preview" | "confirming" | "results";

export default function App() {
  const [stage, setStage] = useState<Stage>("idle");
  const [text, setText] = useState("");
  const [urgency, setUrgency] = useState<TriageResponse | null>(null);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [reportData, setReportData] = useState<ReportResponse | null>(null);
  const [inputError, setInputError] = useState<string | null>(null); // error dentro del modal
  const [pageError, setPageError] = useState<string | null>(null);   // error en pantalla preview/confirming

  // ── Paso 1: triaje + NER ──────────────────────────────────────────────────
  const handleSubmitText = async (value: string) => {
    setInputError(null);
    setText(value);
    setStage("triaging");
    try {
      // T4: triaje primero — si OOD, rechazamos sin más
      const triageRes = await api.triage(value);
      setUrgency(triageRes);
      if (triageRes.is_ood) {
        setStage("ood");
        return;
      }
      // T2: NER — mostrar al usuario para que confirme
      const analyzeRes = await api.analyze(value);
      setAnalysis(analyzeRes);
      setStage("preview");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Error de comunicación con el servidor.";
      setInputError(msg);
      setStage("input"); // vuelve al modal con el error visible dentro
    }
  };

  // ── Paso 2: el usuario confirma las entidades ─────────────────────────────
  const handleConfirm = async () => {
    setPageError(null);
    setStage("confirming");
    try {
      const res = await api.report(text, urgency!);
      setReportData(res);
      setStage("results");
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Error al generar el informe.";
      setPageError(msg);
      setStage("preview"); // vuelve al preview con error
    }
  };

  const reset = () => {
    setStage("idle");
    setText("");
    setUrgency(null);
    setAnalysis(null);
    setReportData(null);
    setInputError(null);
    setPageError(null);
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <div className="app-title">Triaje<span> ·</span> PoC</div>
          <div className="app-subtitle">Sistema de apoyo al triaje médico en español</div>
        </div>
        {stage !== "idle" && (
          <button className="btn btn-ghost" onClick={reset}>
            Inicio
          </button>
        )}
      </header>

      {/* Pantalla 0: botón micrófono */}
      {stage === "idle" && <RecordButton onClick={() => setStage("input")} />}

      {/* Pantalla 1: modal de entrada de texto */}
      {(stage === "input" || stage === "triaging") && (
        <TextModal
          onSubmit={handleSubmitText}
          onClose={reset}
          loading={stage === "triaging"}
          error={inputError}
        />
      )}

      {/* Pantalla 2: consulta fuera de dominio */}
      {stage === "ood" && urgency && (
        <div className="preview-card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: "3.5rem", marginBottom: 12 }}>⚠️</div>
          <h2 style={{ marginTop: 0 }}>Consulta no reconocida</h2>
          <p style={{ color: "var(--fg-1)", maxWidth: 520, margin: "0 auto 24px" }}>
            No hemos podido identificar esto como una consulta de urgencia médica.
            Por favor, describe un problema de salud concreto.
          </p>
          <p style={{ color: "var(--fg-2)", fontSize: "0.85rem", marginBottom: 24 }}>
            Confianza del modelo: {(urgency.confidence * 100).toFixed(1)}%
          </p>
          <button className="btn btn-primary" onClick={reset}>
            Intentar de nuevo
          </button>
        </div>
      )}

      {/* Spinner: triaje en curso (antes de transición al modal en triaging) */}
      {stage === "triaging" && (
        <div className="loading">
          <div className="spinner" />
          <p style={{ color: "var(--fg-2)" }}>Evaluando la urgencia de la consulta…</p>
        </div>
      )}

      {/* Pantalla 3: preview de entidades NER */}
      {(stage === "preview" || stage === "confirming") && analysis && (
        <>
          <NERPreview
            symptoms={analysis.symptoms}
            diseases={analysis.diseases}
            text={text}
            onConfirm={handleConfirm}
            onCancel={reset}
            loading={stage === "confirming"}
          />
          {pageError && <div className="error-box" style={{ marginTop: 12 }}>{pageError}</div>}
        </>
      )}

      {/* Spinner: generando informe */}
      {stage === "confirming" && (
        <div className="loading" style={{ paddingTop: 24 }}>
          <div className="spinner" />
          <p style={{ color: "var(--fg-2)" }}>Generando diagnóstico, resumen e informe…</p>
        </div>
      )}

      {/* Pantalla 4: resultados */}
      {stage === "results" && reportData && urgency && (
        <Results data={reportData} urgency={urgency} onRestart={reset} />
      )}

      <footer className="footer">
        Sistema de Alto Riesgo bajo AI Act · supervisión humana obligatoria.
      </footer>
    </div>
  );
}
