import logging
import os
import re
import unicodedata

import joblib
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/model", tags=["Modelo"], dependencies=[Depends(get_current_user)])

# ── Load model artifact at startup ────────────────────────────

ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "..", "model", "model_artifact_v1.joblib")

_artifact = None


def _get_artifact():
    global _artifact
    if _artifact is None:
        logger.info("Loading model artifact from %s", ARTIFACT_PATH)
        _artifact = joblib.load(ARTIFACT_PATH)
        logger.info("Model loaded: %s (%d classes, accuracy=%.2f%%)",
                     _artifact["model_name"], _artifact["n_classes"],
                     _artifact["metrics"]["accuracy"] * 100)
    return _artifact


# ── Preprocessing (matches training pipeline) ────────────────

def preprocess_text(text: str) -> str:
    text = text.upper()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[;:,/\\|]+", " ", text)
    text = re.sub(r"[^A-Z0-9.\-\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ── Schemas ───────────────────────────────────────────────────

class PredictRequest(BaseModel):
    descripcion: str


class PredictResponse(BaseModel):
    categoria: str
    confianza: float
    top_k: list[list]


# ── Endpoint ──────────────────────────────────────────────────

@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    artifact = _get_artifact()
    pipeline = artifact["pipeline"]
    le = artifact["label_encoder"]

    clean = preprocess_text(req.descripcion)
    probas = pipeline.predict_proba([clean])[0]
    top_indices = probas.argsort()[-5:][::-1]

    top_k = []
    for idx in top_indices:
        class_code = le.inverse_transform([idx])[0]
        confidence = round(float(probas[idx]), 4)
        top_k.append([class_code, confidence])

    return PredictResponse(
        categoria=top_k[0][0],
        confianza=top_k[0][1],
        top_k=top_k[:3],
    )
