interface Props {
  onClick: () => void;
}

export default function RecordButton({ onClick }: Props) {
  return (
    <div className="mic-stage">
      <button className="mic-button" onClick={onClick} aria-label="Iniciar consulta">
        <svg className="mic-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <rect x="9" y="3" width="6" height="12" rx="3" />
          <path d="M5 11a7 7 0 0 0 14 0" />
          <line x1="12" y1="18" x2="12" y2="22" />
          <line x1="8" y1="22" x2="16" y2="22" />
        </svg>
      </button>
      <p className="mic-caption">Pulsa para describir tus síntomas</p>
      <p className="mic-hint">Tu descripción será analizada por el sistema y revisada por un profesional.</p>
    </div>
  );
}
