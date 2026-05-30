from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


# Traduccion de ingles a español de las 24 etiquetas del modelo
DIAGNOSIS_ES = {
    "Acne": "Acné",
    "Arthritis": "Artritis",
    "Bronchial Asthma": "Asma bronquial",
    "Cervical spondylosis": "Espondilosis cervical",
    "Chicken pox": "Varicela",
    "Common Cold": "Resfriado común",
    "Dengue": "Dengue",
    "Dimorphic Hemorrhoids": "Hemorroides",
    "Fungal infection": "Infección fúngica",
    "Hypertension": "Hipertensión",
    "Impetigo": "Impétigo",
    "Jaundice": "Ictericia",
    "Malaria": "Malaria",
    "Migraine": "Migraña",
    "Pneumonia": "Neumonía",
    "Psoriasis": "Psoriasis",
    "Typhoid": "Fiebre tifoidea",
    "Varicose Veins": "Varices",
    "allergy": "Alergia",
    "diabetes": "Diabetes",
    "drug reaction": "Reacción a fármacos",
    "gastroesophageal reflux disease": "Reflujo gastroesofágico",
    "peptic ulcer disease": "Úlcera péptica",
    "urinary tract infection": "Infección urinaria",
}


class DiagnosisModel:
    def __init__(self, model_dir, max_length=192, device="cpu"):
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
        self.model = AutoModelForSequenceClassification.from_pretrained(str(model_dir))
        self.model.eval()
        self.device = device
        self.model.to(device)
        self.max_length = max_length
        with open(model_dir / "label_map.json", encoding="utf-8") as f:
            lm = json.load(f)
        # id2label puede tener claves str
        self.id2label = {int(k): v for k, v in lm["id2label"].items()}

    @torch.no_grad()
    def predict_topk(self, text, k=3):
        inputs = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding=True,
            return_tensors="pt",
        ).to(self.device)
        logits = self.model(**inputs).logits[0]
        # convierte logits a probabilidades
        probs = torch.softmax(logits, dim=-1)
        # selecciona las k clases con mayor probabilidad
        top_p, top_i = torch.topk(probs, k=min(k, probs.shape[0]))
        results = []
        for p, i in zip(top_p.tolist(), top_i.tolist()):
            label_en = self.id2label[i]
            results.append({
                "label_en": label_en,
                "label": DIAGNOSIS_ES.get(label_en, label_en),  # usa la original si no hay traduccion
                "probability": float(p),
            })
        return results
