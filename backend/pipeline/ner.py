from __future__ import annotations

from dataclasses import dataclass

import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Span

NEGATION_CUES = {
    "no", "sin", "tampoco", "ningún", "ninguna", "ningun",
    "ausencia", "ausente", "descarta", "descartado", "descartada",
    "niega", "negativo", "negativa", "nunca", "jamás", "exenta", "exento",
}

# Lemmas de palabras funcionales / pronombres que NO deben ser entidades clinicas.
# Se aplica en inferencia: si un match es de un solo token con uno de estos lemas,
# se descarta para evitar falsos positivos.
_BLOCKED_SINGLE_LEMMAS = frozenset({
    # Pronombres personales y su lema canonico en es_core_news_md
    "él", "ella", "ello", "ellos", "ellas",
    "yo", "tú", "nosotros", "vosotros",
    "le", "lo", "la", "los", "las", "les",
    "se", "me", "te", "nos", "os",
    # Artículos / determinantes
    "el", "un", "uno", "una",
    # Preposiciones / conjunciones
    "de", "a", "en", "con", "por", "para", "sin", "sobre",
    "que", "y", "o", "ni", "pero", "aunque", "como",
    # Verbos auxiliares y comunes que no son entidades
    "ser", "estar", "haber", "tener", "poder", "deber", "ir",
    "beber", "comer", "hablar",
    # otros
    "si"
})


@dataclass
class Mention:
    text: str
    lemma: str
    start_char: int
    end_char: int
    is_negated: bool


class GazetteerNER:
    def __init__(self, nlp, label: str, negation_window=4):
        # La pipeline
        self.nlp = nlp

        # Nombre de las entidades
        self.label = label

        # Ventana para la negacion
        self.negation_window = negation_window

        # Herramienta de SpaCy para detectar las entidades tras lematizacion
        self.matcher = PhraseMatcher(nlp.vocab, attr="LEMMA")

        # Numero de entidades en el diccionario
        self._n_patterns = 0


    def fit(self, mentions):
        # Elimina espacios, pasa a minusculas, quita duplicados
        unique = {m.strip().lower() for m in mentions if isinstance(m, str) and m.strip()}

        # Procesa los terminos en batches de 256
        patterns = [p for p in self.nlp.pipe(unique, batch_size=256) if len(p) > 0]

        # Registra entidades
        self.matcher.add(self.label, patterns)

        # Cuenta entidades
        self._n_patterns = len(patterns)

        # Devuelve el Gazetteer con las entidades
        return self


    def _is_negated(self, doc, span_start_token):
        # La ventana debe ser mayor que 0
        if self.negation_window <= 0:
            return False

        # Indice del token para el que empieza la busqueda hacia atras
        win_start = max(0, span_start_token - self.negation_window)

        # Comprueba si hay tokens que precedan dentro de la ventana y esten en nuestra lista de palabras negativas
        return any(tok.lower_ in NEGATION_CUES for tok in doc[win_start:span_start_token])


    def extract(self, text, apply_negation_filter=False):
        # Aplica el pipeline de SpaCy
        doc = self.nlp(text)

        # Ejecuta el PhraseMatcher para encontrar los matches como (match_id, start_token, end_token)
        raw = self.matcher(doc)

        # Resuelve solapamientos
        spans = [Span(doc, s, e, label=self.label) for _, s, e in raw]
        spans = spacy.util.filter_spans(spans)

        # Lista donde guardaremos las entidades extraidas
        out = []
        for sp in spans:

            # Descarta matches de un solo token con lema funcional
            if len(sp) == 1 and sp[0].lemma_.lower() in _BLOCKED_SINGLE_LEMMAS:
                continue

            # Aplica el filtro de negacion
            negated = self._is_negated(doc, sp.start)
            if apply_negation_filter and negated:
                continue

            out.append(Mention(sp.text, sp.lemma_.lower(), sp.start_char, sp.end_char, negated))

        return out


def load_gazetteer(path):
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def build_ners(models_dir):
    nlp = spacy.load("es_core_news_md", disable=["ner", "parser"])

    # senter es util para que la lematización sea estable
    if "senter" not in nlp.pipe_names and "sentencizer" not in nlp.pipe_names:
        nlp.add_pipe("sentencizer")
    sintomas = load_gazetteer(models_dir / "t2_ner" / "gazetteer_sintomas.txt")
    enfermedades = load_gazetteer(models_dir / "t2_ner" / "gazetteer_enfermedades.txt")
    ner_s = GazetteerNER(nlp, "SINTOMA").fit(sintomas)
    ner_e = GazetteerNER(nlp, "ENFERMEDAD").fit(enfermedades)
    return ner_s, ner_e
