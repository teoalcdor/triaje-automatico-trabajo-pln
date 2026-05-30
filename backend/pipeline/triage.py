from __future__ import annotations

from typing import Protocol

import joblib
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


# nivel 0 indica consulta fuera del dominio medico (OOD)
URGENCY_INFO = {
    0: {"label": "Fuera de dominio", "description": "La consulta no se ha reconocido como una urgencia médica.", "color": "#9CA3AF"},
    1: {"label": "Nivel 1", "description": "Atención inmediata. Riesgo vital.", "color": "#DC2626"},
    2: {"label": "Nivel 2", "description": "Muy urgente.", "color": "#EA580C"},
    3: {"label": "Nivel 3", "description": "Urgente", "color": "#D97706"},
    4: {"label": "Nivel 4", "description": "No muy urgente", "color": "#65A30D"},
    5: {"label": "Nivel 5", "description": "Atención no prioritaria.", "color": "#16A34A"},
}


def _format(level, confidence, backend):
    info = URGENCY_INFO[level]
    # construye el dict de respuesta unificado para ambos backends
    return {
        "level": level,
        "label": info["label"],
        "description": info["description"],
        "color": info["color"],
        "confidence": float(confidence),
        "is_ood": level == 0,
        "backend": backend,
    }


class TriagePredictor(Protocol):
    backend: str
    def predict(self, text): ...


class RobertaTriageModel:
    backend = "roberta"

    def __init__(self, model_dir, max_length=256, device="cpu"):
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
        self.model = AutoModelForSequenceClassification.from_pretrained(str(model_dir))
        self.model.eval()
        self.device = device
        self.model.to(device)
        self.max_length = max_length

    @torch.no_grad()
    def predict(self, text):
        inputs = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding=True,
            return_tensors="pt",
        ).to(self.device)
        logits = self.model(**inputs).logits[0]
        probs = torch.softmax(logits, dim=-1)
        # la clase con mayor probabilidad determina el nivel de urgencia
        level = int(probs.argmax().item())
        return _format(level, probs[level].item(), self.backend)


class BaselineTriageModel:
    """TF-IDF + Regresión logística."""

    backend = "baseline"

    def __init__(self, joblib_path):
        # carga el pipeline serializado con joblib
        self.pipeline = joblib.load(joblib_path)

    def predict(self, text):
        probs = self.pipeline.predict_proba([text])[0]
        classes = list(self.pipeline.classes_)
        idx = int(np.argmax(probs))
        # las clases del pipeline son los niveles de urgencia (int)
        level = int(classes[idx])
        return _format(level, float(probs[idx]), self.backend)


def load_triage(models_dir, backend="roberta"):
    # normaliza el nombre del backend para evitar errores de mayusculas/espacios
    backend = (backend or "roberta").strip().lower()
    if backend == "baseline":
        return BaselineTriageModel(models_dir / "t4_triaje" / "baseline_tfidf_logreg.joblib")
    if backend == "roberta":
        return RobertaTriageModel(models_dir / "t4_triaje" / "roberta_bio_ft")
    raise ValueError(f"TRIAGE_MODEL desconocido: {backend!r}. Usa 'roberta' o 'baseline'.")
