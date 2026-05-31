import logging
import os
import time
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db import get_db
from app.services.llm import build_system_prompt, chat_completion, get_model_name

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"])


class ConversationCreate(BaseModel):
    title: str = "Nueva conversacion"


class ConversationUpdate(BaseModel):
    title: str | None = None
    messages: list[dict] | None = None


class ConversationOut(BaseModel):
    id: UUID
    title: str
    messages: list[dict]
    created_at: datetime
    updated_at: datetime


class ConversationSummary(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


# --- List conversations ---

@router.get("/conversations", response_model=list[ConversationSummary])
def list_conversations(db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT id, title, created_at, updated_at FROM silver.conversations ORDER BY updated_at DESC")
    ).fetchall()
    return [ConversationSummary(id=r[0], title=r[1], created_at=r[2], updated_at=r[3]) for r in rows]


# --- Create conversation ---

@router.post("/conversations", response_model=ConversationOut, status_code=201)
def create_conversation(body: ConversationCreate, db: Session = Depends(get_db)):
    row = db.execute(
        text("""
            INSERT INTO silver.conversations (title)
            VALUES (:title)
            RETURNING id, title, messages, created_at, updated_at
        """),
        {"title": body.title},
    ).fetchone()
    db.commit()
    return ConversationOut(id=row[0], title=row[1], messages=row[2], created_at=row[3], updated_at=row[4])


# --- Get conversation ---

@router.get("/conversations/{conv_id}", response_model=ConversationOut)
def get_conversation(conv_id: UUID, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT id, title, messages, created_at, updated_at FROM silver.conversations WHERE id = :id"),
        {"id": str(conv_id)},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationOut(id=row[0], title=row[1], messages=row[2], created_at=row[3], updated_at=row[4])


# --- Update conversation ---

@router.patch("/conversations/{conv_id}", response_model=ConversationOut)
def update_conversation(conv_id: UUID, body: ConversationUpdate, db: Session = Depends(get_db)):
    sets = ["updated_at = now()"]
    params: dict = {"id": str(conv_id)}

    if body.title is not None:
        sets.append("title = :title")
        params["title"] = body.title
    if body.messages is not None:
        sets.append("messages = CAST(:messages AS jsonb)")
        import json
        params["messages"] = json.dumps(body.messages)

    query = f"UPDATE silver.conversations SET {', '.join(sets)} WHERE id = :id RETURNING id, title, messages, created_at, updated_at"
    row = db.execute(text(query), params).fetchone()
    db.commit()

    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationOut(id=row[0], title=row[1], messages=row[2], created_at=row[3], updated_at=row[4])


# --- Delete conversation ---

@router.delete("/conversations/{conv_id}", status_code=204)
def delete_conversation(conv_id: UUID, db: Session = Depends(get_db)):
    result = db.execute(
        text("DELETE FROM silver.conversations WHERE id = :id"),
        {"id": str(conv_id)},
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")


# --- Process message (LLM + duplicates) ---

class ProcessRequest(BaseModel):
    conversation_id: str
    message: str


class DuplicateMatch(BaseModel):
    material_id: str
    short_text: str
    similarity: float


class ProcessResponse(BaseModel):
    action: str  # "question" | "proposal" | "existing_match"
    message: str | None = None
    short_text: str | None = None
    material_type_id: str | None = None
    material_id: str | None = None
    confidence: float | None = None
    duplicates: list[DuplicateMatch] = []
    elapsed_s: float = 0


def _get_material_types(db: Session) -> list[dict]:
    rows = db.execute(text("SELECT id, description FROM silver.material_types ORDER BY id")).fetchall()
    return [{"id": r[0], "description": r[1]} for r in rows]


def _search_duplicates(db: Session, short_text: str, threshold: float, limit: int = 10) -> list[DuplicateMatch]:
    rows = db.execute(
        text("""
            SELECT id, short_text, similarity(short_text, :query) AS sim
            FROM silver.materials
            WHERE similarity(short_text, :query) > :threshold
            ORDER BY sim DESC
            LIMIT :limit
        """),
        {"query": short_text, "threshold": threshold, "limit": limit},
    ).fetchall()
    return [DuplicateMatch(material_id=r[0], short_text=r[1], similarity=round(float(r[2]), 3)) for r in rows]


def _build_conversation_history(messages: list[dict]) -> list[dict]:
    """Extract text messages for LLM context (skip processing/proposal/confirmed UI types)."""
    history = []
    for m in messages:
        if m.get("role") in ("user", "assistant") and m.get("content"):
            history.append({"role": m["role"], "content": m["content"]})
        elif m.get("role") == "assistant" and m.get("llm_content"):
            history.append({"role": "assistant", "content": m["llm_content"]})
    return history


def _log_llm(db: Session, conv_id: str, model: str, user_message: str,
             history_len: int, response_raw: str | None, response_parsed: dict | None,
             action: str | None, elapsed_s: float, error: str | None = None,
             tokens_in: int | None = None, tokens_out: int | None = None):
    import json
    db.execute(
        text("""
            INSERT INTO bronze.llm_logs
                (conversation_id, model, user_message, history_len,
                 response_raw, response_parsed, action,
                 tokens_in, tokens_out, elapsed_s, error)
            VALUES
                (:conversation_id, :model, :user_message, :history_len,
                 :response_raw, CAST(:response_parsed AS jsonb), :action,
                 :tokens_in, :tokens_out, :elapsed_s, :error)
        """),
        {
            "conversation_id": conv_id,
            "model": model,
            "user_message": user_message,
            "history_len": history_len,
            "response_raw": response_raw,
            "response_parsed": json.dumps(response_parsed) if response_parsed else None,
            "action": action,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "elapsed_s": elapsed_s,
            "error": error,
        },
    )


def _format_duplicates_for_llm(duplicates: list[DuplicateMatch]) -> str:
    """Format duplicate matches as a system message for the LLM."""
    lines = ["[SISTEMA] Se encontraron los siguientes materiales similares en el maestro:"]
    for i, d in enumerate(duplicates, 1):
        lines.append(f"  {i}. ID: {d.material_id} | {d.short_text} (similitud: {d.similarity:.0%})")
    lines.append("")
    lines.append("Presenta estos duplicados al usuario de forma conversacional. "
                 "Preguntale si alguno le sirve o si su material es diferente.")
    return "\n".join(lines)


@router.post("/process", response_model=ProcessResponse)
def process_message(body: ProcessRequest, db: Session = Depends(get_db)):
    t0 = time.time()

    # Load conversation messages for history
    row = db.execute(
        text("SELECT messages FROM silver.conversations WHERE id = :id"),
        {"id": body.conversation_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")

    existing_messages = row[0] if row[0] else []
    history = _build_conversation_history(existing_messages)

    # Build system prompt with material types from DB
    material_types = _get_material_types(db)
    system_prompt = build_system_prompt(material_types)

    # Call LLM (first pass)
    try:
        result = chat_completion(system_prompt, history, body.message)
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        elapsed = round(time.time() - t0, 3)
        _log_llm(db, body.conversation_id, get_model_name(), body.message,
                 len(history), None, None, None, elapsed, error=str(e))
        db.commit()
        raise HTTPException(status_code=502, detail=f"Error al comunicarse con el modelo: {e}")

    llm_response = result.parsed
    action = llm_response.get("action", "question")

    # Log first LLM call
    _log_llm(db, body.conversation_id, result.model, body.message,
             len(history), result.raw, result.parsed, action,
             round(time.time() - t0, 3),
             tokens_in=result.tokens_in, tokens_out=result.tokens_out)

    # Handle existing_match (user confirmed a duplicate works)
    if action == "existing_match":
        elapsed = round(time.time() - t0, 3)
        db.commit()
        return ProcessResponse(
            action="existing_match",
            material_id=llm_response.get("material_id"),
            message=llm_response.get("message", "Material existente confirmado."),
            elapsed_s=elapsed,
        )

    # Handle proposal — check for duplicates first
    if action == "proposal":
        short_text = llm_response.get("short_text", "")
        material_type_id = llm_response.get("material_type_id")
        confidence = llm_response.get("confidence", 0)

        dup_threshold = float(os.environ.get("DUPLICADO_UMBRAL", "0.45"))
        duplicates = _search_duplicates(db, short_text, dup_threshold)

        if duplicates:
            # Duplicates found — ask LLM to present them conversationally
            dup_context = _format_duplicates_for_llm(duplicates)

            # Add the proposal as model response, then the duplicate context as user input
            extended_history = history + [
                {"role": "user", "content": body.message},
                {"role": "assistant", "content": result.raw},
            ]

            try:
                dup_result = chat_completion(system_prompt, extended_history, dup_context)
            except Exception as e:
                logger.error("LLM duplicate call failed: %s", e)
                # Fall through to return proposal with duplicates anyway
                elapsed = round(time.time() - t0, 3)
                db.commit()
                return ProcessResponse(
                    action="proposal", short_text=short_text,
                    material_type_id=material_type_id, confidence=confidence,
                    duplicates=duplicates, elapsed_s=elapsed,
                )

            # Log second LLM call
            _log_llm(db, body.conversation_id, dup_result.model, dup_context,
                     len(extended_history), dup_result.raw, dup_result.parsed,
                     "duplicates_review", round(time.time() - t0, 3),
                     tokens_in=dup_result.tokens_in, tokens_out=dup_result.tokens_out)

            dup_message = dup_result.parsed.get("message", "")
            elapsed = round(time.time() - t0, 3)
            db.commit()

            return ProcessResponse(
                action="duplicates_review",
                message=dup_message,
                short_text=short_text,
                material_type_id=material_type_id,
                confidence=confidence,
                duplicates=duplicates,
                elapsed_s=elapsed,
            )

        # No duplicates — return proposal directly
        elapsed = round(time.time() - t0, 3)
        db.commit()
        return ProcessResponse(
            action="proposal", short_text=short_text,
            material_type_id=material_type_id, confidence=confidence,
            duplicates=[], elapsed_s=elapsed,
        )

    # Default: question
    elapsed = round(time.time() - t0, 3)
    db.commit()
    return ProcessResponse(
        action="question",
        message=llm_response.get("message", ""),
        elapsed_s=elapsed,
    )
