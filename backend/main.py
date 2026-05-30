from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Carga .env del directorio del backend si existe (no falla si no esta)
load_dotenv(Path(__file__).resolve().parent / ".env")

from pipeline.ner import build_ners
from pipeline.diagnosis import DiagnosisModel
from pipeline.triage import load_triage
from pipeline.summarizer import Summarizer
from pipeline.report import build_report_markdown, save_report


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("triaje")

MODELS_DIR = Path(os.environ.get("MODELS_DIR", "/app/modelos"))
REPORTS_DIR = Path(os.environ.get("REPORTS_DIR", "/app/reports"))
TRIAGE_MODEL = os.environ.get("TRIAGE_MODEL", "roberta").strip().lower()


class State:
    ner_sintomas = None
    ner_enfermedades = None
    diagnosis = None
    triage = None
    summarizer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Cargando modelos desde %s ...", MODELS_DIR)
    log.info("  - T2 NER (spaCy + gazetteers)")
    State.ner_sintomas, State.ner_enfermedades = build_ners(MODELS_DIR)
    log.info("  - T3 Diagnóstico")
    State.diagnosis = DiagnosisModel(MODELS_DIR / "t3_diagnostico")
    log.info("  - T4 Triaje (backend = %s)", TRIAGE_MODEL)
    State.triage = load_triage(MODELS_DIR, backend=TRIAGE_MODEL)
    log.info("  - T5 Resumen")
    State.summarizer = Summarizer(MODELS_DIR)
    # asegura que el directorio de informes existe antes de recibir peticiones
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    log.info("Modelos listos.")
    yield
    log.info("Apagando backend.")


app = FastAPI(title="Triaje médico - PoC", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TextIn(BaseModel):
    text: str = Field(..., min_length=1)


class UrgencyIn(BaseModel):
    """Resultado del triaje previo, devuelto por /api/triage."""
    level: int
    label: str
    description: str
    color: str
    confidence: float
    is_ood: bool
    backend: str = "roberta"


class ReportIn(BaseModel):
    text: str = Field(..., min_length=1)
    urgency: UrgencyIn


def _dedupe_mentions(mentions):
    """Quita menciones repetidas conservando el orden de aparición.

    Una mención se considera duplicada si comparte texto normalizado y estado
    de negación con otra anterior. Eliminamos también el campo lemma del
    payload expuesto al cliente. Es un detalle de implementación.
    """
    out, seen = [], set()
    for m in mentions:
        # la clave combina lema y estado de negacion para detectar duplicados
        key = (m.lemma.lower().strip(), m.is_negated)
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "text": m.text,
            "is_negated": m.is_negated,
            "start_char": m.start_char,
            "end_char": m.end_char,
        })
    return out


@app.get("/api/health")
def health():
    return {"status": "ok", "triage_backend": TRIAGE_MODEL}


@app.post("/api/triage")
def triage(payload: TextIn):
    text = payload.text.strip()
    if not text:
        raise HTTPException(400, "El texto no puede estar vacío.")
    return State.triage.predict(text)


@app.post("/api/analyze")
def analyze(payload: TextIn):
    text = payload.text.strip()
    if not text:
        raise HTTPException(400, "El texto no puede estar vacío.")
    symptoms = _dedupe_mentions(State.ner_sintomas.extract(text))
    diseases = _dedupe_mentions(State.ner_enfermedades.extract(text))
    return {"symptoms": symptoms, "diseases": diseases}


@app.post("/api/report")
def report(payload: ReportIn):
    """Genera el informe .md. La urgencia ya fue calculada en /api/triage."""
    text = payload.text.strip()
    if not text:
        raise HTTPException(400, "El texto no puede estar vacío.")

    # la urgencia viene del cliente para evitar recalcularla
    urgency = payload.urgency.model_dump()
    symptoms = _dedupe_mentions(State.ner_sintomas.extract(text))
    diseases = _dedupe_mentions(State.ner_enfermedades.extract(text))
    diagnoses = State.diagnosis.predict_topk(text, k=3)
    summary = State.summarizer.summarize(text)

    content = build_report_markdown(
        text=text,
        symptoms=symptoms,
        diseases=diseases,
        diagnoses=diagnoses,
        urgency=urgency,
        summary=summary,
    )
    filename = save_report(content, REPORTS_DIR)
    return {
        "diagnoses": diagnoses,
        "symptoms": symptoms,
        "diseases": diseases,
        "summary": summary,
        "report_content": content,
        "report_filename": filename,
    }
