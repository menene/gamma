from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["Duplicados"])


class ValidateRequest(BaseModel):
    descripcion: str


class Candidato(BaseModel):
    material: str
    descripcion: str
    score: float


class ValidateResponse(BaseModel):
    candidatos: list[Candidato]


@router.post("/duplicates", response_model=ValidateResponse)
def validate_duplicates(req: ValidateRequest):
    """Stub: validates against silver.materials using pg_trgm similarity.
    Will query the DB once connected."""
    return ValidateResponse(candidatos=[])
