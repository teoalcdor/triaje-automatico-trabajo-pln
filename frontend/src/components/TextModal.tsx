import { useState } from "react";

interface Props {
  onSubmit: (text: string) => void;
  onClose: () => void;
  loading?: boolean;
  error?: string | null;
}

export default function TextModal({ onSubmit, onClose, loading, error }: Props) {
  const [value, setValue] = useState("");
  const canSend = value.trim().length > 10 && !loading;

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal">
        <h2>Describe lo que te ocurre</h2>
        <p className="modal-hint">
          En un sistema real, hablarías al micrófono. Para esta prueba de concepto,
          escribe a continuación lo que dirías al describir tus síntomas.
        </p>
        <textarea
          autoFocus
          placeholder="Por ejemplo: 'Llevo dos días con dolor de cabeza muy fuerte, fiebre alta de unos 39 ºC y náuseas. No tengo tos pero sí mucho cansancio…'"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={loading}
        />
        {error && (
          <div className="error-box" style={{ marginTop: 12 }}>
            {error}
          </div>
        )}
        <div className="modal-actions">
          <button className="btn btn-ghost" onClick={onClose} disabled={loading}>
            Cancelar
          </button>
          <button className="btn btn-primary" disabled={!canSend} onClick={() => onSubmit(value.trim())}>
            {loading ? "Evaluando urgencia…" : "Enviar"}
          </button>
        </div>
      </div>
    </div>
  );
}
