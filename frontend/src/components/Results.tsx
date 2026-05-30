import ReactMarkdown from "react-markdown";
import type { ReportResponse, TriageResponse } from "../api";

interface Props {
  data: ReportResponse;
  urgency: TriageResponse;
  onRestart: () => void;
}

export default function Results({ data, urgency, onRestart }: Props) {
  const { diagnoses, report_content, report_filename } = data;

  return (
    <div className="results-card">
      <div className="doctor-banner">
        <span className="doctor-badge">VISTA CLÍNICA</span>
        <div>
          <strong>Esta pantalla está dirigida al personal sanitario.</strong>
          <p>
            El paciente no la ve. Contiene los diagnósticos diferenciales sugeridos
            por el sistema y el informe completo para apoyar la decisión clínica.
          </p>
        </div>
      </div>

      <div
        className="urgency-banner"
        style={{ background: `linear-gradient(135deg, ${urgency.color} 0%, ${urgency.color}cc 100%)` }}
      >
        <div className="urgency-level">{urgency.level}</div>
        <div className="urgency-meta">
          <strong>{urgency.label}</strong>
          <span>{urgency.description}</span>
          <span>Confianza del modelo: {(urgency.confidence * 100).toFixed(1)}%</span>
        </div>
      </div>

      {diagnoses.length > 0 && (
        <>
          <p className="section-title" style={{ marginTop: 20 }}>Diagnósticos probables</p>
          <ul className="diag-list">
            {diagnoses.map((d, i) => (
              <li key={i} className="diag-row">
                <span>
                  <span className="diag-rank">{i + 1}</span>
                  {d.label}
                </span>
                <span className="diag-prob">{(d.probability * 100).toFixed(1)}%</span>
              </li>
            ))}
          </ul>
        </>
      )}

      <div className="report-card">
        <h3>Informe completo · {report_filename}</h3>
        <div className="markdown">
          <ReactMarkdown>{report_content}</ReactMarkdown>
        </div>
      </div>

      <div className="results-actions">
        <button className="btn btn-ghost" onClick={onRestart}>
          ← Nueva consulta
        </button>
        <a
          className="btn btn-primary"
          href={`data:text/markdown;charset=utf-8,${encodeURIComponent(report_content)}`}
          download={report_filename}
        >
          Descargar .md
        </a>
      </div>
    </div>
  );
}
