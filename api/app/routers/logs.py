import json
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from app.auth import get_current_user
from app.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/logs", tags=["Logs"], dependencies=[Depends(get_current_user)])


# --- App error logging ---

class AppErrorIn(BaseModel):
    source: str
    message: str
    details: dict | None = None


class AppErrorOut(BaseModel):
    id: int
    source: str
    message: str
    details: dict | None
    logged_at: datetime


@router.post("/errors", status_code=201)
def log_error(body: AppErrorIn, db: Session = Depends(get_db)):
    db.execute(
        text("""
            INSERT INTO bronze.app_errors (source, message, details)
            VALUES (:source, :message, CAST(:details AS jsonb))
        """),
        {
            "source": body.source,
            "message": body.message,
            "details": json.dumps(body.details) if body.details else None,
        },
    )
    db.commit()
    return {"ok": True}


@router.get("/errors", response_model=list[AppErrorOut])
def list_errors(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.execute(
        text("""
            SELECT id, source, message, details, logged_at
            FROM bronze.app_errors
            ORDER BY logged_at DESC
            LIMIT :limit
        """),
        {"limit": limit},
    ).fetchall()
    return [AppErrorOut(id=r[0], source=r[1], message=r[2], details=r[3], logged_at=r[4]) for r in rows]


# --- LLM logs ---

class LLMLogOut(BaseModel):
    id: int
    conversation_id: str | None
    model: str
    user_message: str
    action: str | None
    tokens_in: int | None
    tokens_out: int | None
    elapsed_s: float | None
    error: str | None
    logged_at: datetime


@router.get("/llm", response_model=list[LLMLogOut])
def list_llm_logs(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.execute(
        text("""
            SELECT id, conversation_id, model, user_message, action,
                   tokens_in, tokens_out, elapsed_s, error, logged_at
            FROM bronze.llm_logs
            ORDER BY logged_at DESC
            LIMIT :limit
        """),
        {"limit": limit},
    ).fetchall()
    return [
        LLMLogOut(
            id=r[0], conversation_id=str(r[1]) if r[1] else None, model=r[2],
            user_message=r[3], action=r[4], tokens_in=r[5], tokens_out=r[6],
            elapsed_s=float(r[7]) if r[7] else None, error=r[8], logged_at=r[9],
        )
        for r in rows
    ]


# --- Duplicate decision logs ---

class DuplicateLogOut(BaseModel):
    id: int
    conversation_id: str | None
    request_id: int | None
    action: str
    short_text: str | None
    selected_material_id: str | None
    elapsed_s: float | None
    logged_at: datetime


@router.get("/duplicates", response_model=list[DuplicateLogOut])
def list_duplicate_logs(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.execute(
        text("""
            SELECT id, conversation_id, request_id, action, short_text,
                   selected_material_id, elapsed_s, logged_at
            FROM bronze.duplicate_logs
            ORDER BY logged_at DESC
            LIMIT :limit
        """),
        {"limit": limit},
    ).fetchall()
    return [
        DuplicateLogOut(
            id=r[0], conversation_id=str(r[1]) if r[1] else None,
            request_id=r[2], action=r[3], short_text=r[4],
            selected_material_id=r[5], elapsed_s=float(r[6]) if r[6] else None,
            logged_at=r[7],
        )
        for r in rows
    ]


# --- Prediction logs ---

class PredictionLogOut(BaseModel):
    id: int
    type: str
    input: dict | None
    output: dict | None
    confidence: float | None
    elapsed_s: float | None
    logged_at: datetime


@router.get("/predictions", response_model=list[PredictionLogOut])
def list_prediction_logs(limit: int = 100, db: Session = Depends(get_db)):
    rows = db.execute(
        text("""
            SELECT id, type, input, output, confidence, elapsed_s, logged_at
            FROM bronze.prediction_logs
            ORDER BY logged_at DESC
            LIMIT :limit
        """),
        {"limit": limit},
    ).fetchall()
    return [
        PredictionLogOut(
            id=r[0], type=r[1], input=r[2], output=r[3],
            confidence=float(r[4]) if r[4] else None,
            elapsed_s=float(r[5]) if r[5] else None, logged_at=r[6],
        )
        for r in rows
    ]
