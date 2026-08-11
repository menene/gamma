"""
Normalizacion de texto para el modelo de clasificacion.

Vive en un modulo propio porque debe ser identica en entrenamiento y en
inferencia. Si ambas rutas divergen, el modelo recibe en produccion un texto
distinto al que vio al entrenarse y su desempeno se degrada sin producir ningun
error visible.
"""

import re
import unicodedata


def preprocess_text(text: str) -> str:
    text = text.upper()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[;:,/\\|]+", " ", text)
    text = re.sub(r"[^A-Z0-9.\-\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
