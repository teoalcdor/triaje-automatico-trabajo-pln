from __future__ import annotations

from datetime import datetime


def _format_entities(entities):
    """Formatea una lista de entidades detectadas en formato Markdown con NO en negrita delante de las negadas."""
    if not entities:
        return "- _(ninguna detectada)_"
    lines = []
    for e in entities:
        if e.get("is_negated"):
            lines.append(f"- **NO** {e['text']}")
        else:
            lines.append(f"- {e['text']}")
    return "\n".join(lines)


def build_report_markdown(text, symptoms, diseases, diagnoses, urgency, summary):
    """Genera un informe médico preliminar en formato Markdown a partir de las predicciones y el resument."""

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    # diagnostico con mayor probabilidad para el resumen ejecutivo
    top = diagnoses[0] if diagnoses else None

    parts = [
        f"# Informe Médico Preliminar",
        f"_Generado: {timestamp}_",
        "",
        "## Resumen ejecutivo",
        f"- **Nivel de urgencia**: {urgency['label']}",
        f"- **Descripción**: {urgency['description']}",
        f"- **Confianza del modelo de triaje**: {urgency['confidence']*100:.1f}%",
    ]
    if top:
        parts.append(f"- **Diagnóstico más probable**: {top['label']} ({top['probability']*100:.1f}%)")
    parts += [
        "",
        "## Diagnósticos probables",
    ]
    if diagnoses:
        # numerados de mayor a menor probabilidad
        for i, d in enumerate(diagnoses, 1):
            parts.append(f"{i}. **{d['label']}** - {d['probability']*100:.1f}%")
    else:
        parts.append("_(sin diagnósticos disponibles)_")

    parts += [
        "",
        "## Entidades detectadas",
        "",
        "### Síntomas",
        _format_entities(symptoms),
        "",
        "### Enfermedades mencionadas",
        _format_entities(diseases),
        "",
        "## Resumen de la descripción del paciente",
        summary or "_(no disponible)_",
        "",
        "## Transcripción completa",
        "",
        # cada linea se indenta como cita Markdown
        "> " + text.replace("\n", "\n> "),
        "",
        "---",
        "_Este informe ha sido generado automáticamente como apoyo a la decisión clínica._",
        "_Sistema de Alto Riesgo según AI Act - La supervisión humana es obligatoria._",
        "",
    ]
    return "\n".join(parts)


def save_report(content, reports_dir):
    reports_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    # el timestamp en el nombre evita colisiones entre informes
    filename = f"informe_{now.strftime('%Y%m%d_%H%M%S')}.md"
    (reports_dir / filename).write_text(content, encoding="utf-8")
    return filename
