from __future__ import annotations

import logging
import os

import torch
from transformers import AutoTokenizer, EncoderDecoderModel


log = logging.getLogger(__name__)

# El modelo de resumenes
_MODEL_NAME = "mrm8488/bert2bert_shared-spanish-finetuned-summarization"


class Summarizer:
    """Resumen abstractivo en español."""

    def __init__(self, models_dir, model_name=None, max_input_tokens=512, max_output_tokens=128, min_output_tokens=32, num_beams=4):
        
        self.model_name = model_name or os.environ.get("SUMMARIZER_MODEL", _MODEL_NAME)
        self.max_input_tokens = max_input_tokens
        self.max_output_tokens = max_output_tokens
        self.min_output_tokens = min_output_tokens
        self.num_beams = num_beams

        # permite redirigir la cache de HuggingFace mediante variable de entorno
        cache_dir = os.environ.get("HF_HOME") or os.environ.get("TRANSFORMERS_CACHE")
        log.info("Cargando resumidor abstractivo: %s", self.model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, cache_dir=cache_dir)
        self.model = EncoderDecoderModel.from_pretrained(self.model_name, cache_dir=cache_dir)
        self.model.eval()
        self.device = torch.device("cpu")
        self.model.to(self.device)

    @torch.inference_mode()
    def summarize(self, text, max_length=None):
        text = (text or "").strip()
        if not text:
            return ""

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_input_tokens,
            padding=False,
        ).to(self.device)

        max_len = max_length or self.max_output_tokens
        output_ids = self.model.generate(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
            max_length=max_len,
            min_length=self.min_output_tokens,
            num_beams=self.num_beams,
            do_sample=False,
            no_repeat_ngram_size=3,  # evita repeticiones de trigramas
            early_stopping=True,
            length_penalty=1.0,
        )
        # decodifica el primer (y unico) beam
        summary = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        return summary.strip()
