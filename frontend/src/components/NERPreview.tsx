import type { Mention } from "../api";

interface Props {
  symptoms: Mention[];
  diseases: Mention[];
  text: string;
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
}

function Chip({ m, kind }: { m: Mention; kind: "symptom" | "disease" }) {
  // Todas las entidades usan el mismo color clínico.
  // La negación se indica únicamente con la insignia "NO".
  const cls = `chip ${m.is_negated ? "chip-absent" : "chip-present"} ${kind === "disease" ? "chip-disease" : ""}`;
  return (
    <span className={cls}>
      {m.is_negated && <span className="chip-no">NO</span>}
      {m.text}
    </span>
  );
}

export default function NERPreview({ symptoms, diseases, text, onConfirm, onCancel, loading }: Props) {
  return (
    <div className="preview-card">
      <div className="preview-header">
        <h2>Esto es lo que hemos entendido</h2>
        <p>
          Revisa los síntomas y enfermedades detectados antes de generar el informe.
          La etiqueta <strong>NO</strong> indica que el paciente los ha descartado.
        </p>
      </div>

      <div className="entity-grid">
        <div>
          <p className="section-title">Síntomas</p>
          {symptoms.length === 0 ? (
            <p className="empty">No se han detectado síntomas.</p>
          ) : (
            <div className="entity-list">
              {symptoms.map((m, i) => (
                <Chip key={i} m={m} kind="symptom" />
              ))}
            </div>
          )}
        </div>
        <div>
          <p className="section-title">Enfermedades mencionadas</p>
          {diseases.length === 0 ? (
            <p className="empty">No se han detectado enfermedades.</p>
          ) : (
            <div className="entity-list">
              {diseases.map((m, i) => (
                <Chip key={i} m={m} kind="disease" />
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="transcript-box">{text}</div>

      <div className="preview-actions">
        <button className="btn btn-ghost" onClick={onCancel} disabled={loading}>
          ← Cancelar
        </button>
        <button className="btn btn-success" onClick={onConfirm} disabled={loading}>
          {loading ? "Generando informe…" : "Confirmar y generar informe"}
        </button>
      </div>
    </div>
  );
}

