import random

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/model", tags=["Modelo"])

CATEGORIAS = ["RODAMIENTOS", "TRANSMISION", "ELECTRICO", "HIDRAULICO", "NEUMATICO"]


class PredictRequest(BaseModel):
    descripcion: str


class PredictResponse(BaseModel):
    categoria: str
    confianza: float
    top_k: list[list]


@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    """Stub: returns a random category. Will be replaced with actual model."""
    confianza = round(random.uniform(0.75, 0.99), 4)
    categoria = random.choice(CATEGORIAS)
    top_k = [[categoria, confianza]]
    for c in CATEGORIAS:
        if c != categoria:
            score = round(random.uniform(0.01, 0.10), 4)
            top_k.append([c, score])
    top_k.sort(key=lambda x: x[1], reverse=True)
    return PredictResponse(categoria=categoria, confianza=confianza, top_k=top_k[:3])
