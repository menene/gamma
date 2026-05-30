import random

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="GAMMA API",
    description="Gobierno Automatizado del Maestro de Materiales",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Health ---

@app.get("/api/health", tags=["gamma_api"])
def health():
    return {"status": "ok"}


# --- Duplicates ---

class ValidateRequest(BaseModel):
    descripcion: str


class Candidato(BaseModel):
    material: str
    descripcion: str
    score: float


class ValidateResponse(BaseModel):
    candidatos: list[Candidato]


@app.post("/api/duplicates", response_model=ValidateResponse, tags=["gamma_api"])
def validate_duplicates(req: ValidateRequest):
    """Stub: validates against silver.maestro using pg_trgm similarity.
    Will query the DB once connected."""
    return ValidateResponse(candidatos=[])


# --- Model (categorization) ---

CATEGORIAS = ["RODAMIENTOS", "TRANSMISION", "ELECTRICO", "HIDRAULICO", "NEUMATICO"]


class PredictRequest(BaseModel):
    descripcion: str


class PredictResponse(BaseModel):
    categoria: str
    confianza: float
    top_k: list[list]


@app.post("/api/model/predict", response_model=PredictResponse, tags=["gamma_api"])
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
