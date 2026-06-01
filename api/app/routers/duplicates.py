from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth import get_current_user

router = APIRouter(prefix="/api", tags=["Duplicados"], dependencies=[Depends(get_current_user)])


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
