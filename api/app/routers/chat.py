import json as _json
import logging
import os
import time
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from app.auth import get_current_user
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db import get_db
from app.services.llm import build_system_prompt, chat_completion, get_model_name
from app.routers.model import preprocess_text, _get_artifact

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["Chat"], dependencies=[Depends(get_current_user)])


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
def list_conversations(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    rows = db.execute(
        text("""
            SELECT id, title, created_at, updated_at
            FROM silver.conversations
            WHERE created_by = :user_id
            ORDER BY updated_at DESC
        """),
        {"user_id": user["id"]},
    ).fetchall()
    return [ConversationSummary(id=r[0], title=r[1], created_at=r[2], updated_at=r[3]) for r in rows]


# --- Create conversation ---

@router.post("/conversations", response_model=ConversationOut, status_code=201)
def create_conversation(
    body: ConversationCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    row = db.execute(
        text("""
            INSERT INTO silver.conversations (title, created_by)
            VALUES (:title, :created_by)
            RETURNING id, title, messages, created_at, updated_at
        """),
        {"title": body.title, "created_by": user["id"]},
    ).fetchone()
    db.commit()
    return ConversationOut(id=row[0], title=row[1], messages=row[2], created_at=row[3], updated_at=row[4])


# --- Get conversation ---

@router.get("/conversations/{conv_id}", response_model=ConversationOut)
def get_conversation(
    conv_id: UUID,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    row = db.execute(
        text("""
            SELECT id, title, messages, created_at, updated_at
            FROM silver.conversations
            WHERE id = :id AND created_by = :user_id
        """),
        {"id": str(conv_id), "user_id": user["id"]},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationOut(id=row[0], title=row[1], messages=row[2], created_at=row[3], updated_at=row[4])


# --- Update conversation ---

@router.patch("/conversations/{conv_id}", response_model=ConversationOut)
def update_conversation(
    conv_id: UUID,
    body: ConversationUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    sets = ["updated_at = now()"]
    params: dict = {"id": str(conv_id), "user_id": user["id"]}

    if body.title is not None:
        sets.append("title = :title")
        params["title"] = body.title
    if body.messages is not None:
        sets.append("messages = CAST(:messages AS jsonb)")
        params["messages"] = _json.dumps(body.messages)

    query = (
        f"UPDATE silver.conversations SET {', '.join(sets)} "
        "WHERE id = :id AND created_by = :user_id "
        "RETURNING id, title, messages, created_at, updated_at"
    )
    row = db.execute(text(query), params).fetchone()
    db.commit()

    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationOut(id=row[0], title=row[1], messages=row[2], created_at=row[3], updated_at=row[4])


# --- Delete conversation ---

@router.delete("/conversations/{conv_id}", status_code=204)
def delete_conversation(
    conv_id: UUID,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    result = db.execute(
        text("DELETE FROM silver.conversations WHERE id = :id AND created_by = :user_id"),
        {"id": str(conv_id), "user_id": user["id"]},
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")


# --- Shared schemas & helpers ---

class DuplicateMatch(BaseModel):
    material_id: str
    short_text: str
    similarity: float


class ModelPrediction(BaseModel):
    categoria: str
    confianza: float
    top_k: list[list]


SHORT_TEXT_MAX = 40


def _clip_short_text(value: str | None) -> str | None:
    if value is None:
        return None
    return value[:SHORT_TEXT_MAX]


def _get_material_types(db: Session) -> list[dict]:
    rows = db.execute(text("SELECT code, description FROM silver.material_types ORDER BY code")).fetchall()
    return [{"code": r[0], "description": r[1]} for r in rows]


def _build_conversation_history(messages: list[dict]) -> list[dict]:
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
            "response_parsed": _json.dumps(response_parsed) if response_parsed else None,
            "action": action,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "elapsed_s": elapsed_s,
            "error": error,
        },
    )


def _update_request_timestamp(db: Session, request_id: int | None, column: str, elapsed_col: str | None = None, elapsed_s: float | None = None):
    """Set a timestamp column (and optional elapsed) on a request."""
    if not request_id:
        return
    sets = [f"{column} = now()"]
    params: dict = {"id": request_id}
    if elapsed_col and elapsed_s is not None:
        sets.append(f"{elapsed_col} = :elapsed")
        params["elapsed"] = elapsed_s
    db.execute(
        text(f"UPDATE silver.requests SET {', '.join(sets)} WHERE id = :id"),
        params,
    )


# --- Step 1: LLM (description & normalization) ---

class LLMRequest(BaseModel):
    conversation_id: str
    message: str
    request_id: int | None = None


class LLMResponse(BaseModel):
    action: str  # "question" | "proposal" | "existing_match"
    message: str | None = None
    short_text: str | None = None
    long_text: str | None = None
    material_type_id: str | None = None
    material_id: str | None = None
    elapsed_s: float = 0


@router.post("/llm", response_model=LLMResponse)
def step_llm(
    body: LLMRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    t0 = time.time()

    row = db.execute(
        text("SELECT messages FROM silver.conversations WHERE id = :id AND created_by = :user_id"),
        {"id": body.conversation_id, "user_id": user["id"]},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Conversation not found")

    existing_messages = row[0] if row[0] else []
    history = _build_conversation_history(existing_messages)

    material_types = _get_material_types(db)
    system_prompt = build_system_prompt(material_types)

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
    elapsed = round(time.time() - t0, 3)

    _log_llm(db, body.conversation_id, result.model, body.message,
             len(history), result.raw, result.parsed, action, elapsed,
             tokens_in=result.tokens_in, tokens_out=result.tokens_out)

    # Record LLM completion on the request if we have one
    _update_request_timestamp(db, body.request_id, "llm_completed_at", "llm_elapsed_s", elapsed)

    db.commit()

    return LLMResponse(
        action=action,
        message=llm_response.get("message"),
        short_text=_clip_short_text(llm_response.get("short_text")),
        long_text=llm_response.get("long_text"),
        material_type_id=llm_response.get("material_type_id"),
        material_id=llm_response.get("material_id"),
        elapsed_s=elapsed,
    )


# --- Step 2: Duplicate search ---

class DuplicatesRequest(BaseModel):
    conversation_id: str
    short_text: str
    request_id: int | None = None
    user_message: str | None = None
    llm_raw: str | None = None


class DuplicatesResponse(BaseModel):
    has_duplicates: bool
    duplicates: list[DuplicateMatch] = []
    message: str | None = None
    elapsed_s: float = 0


def _format_duplicates_for_llm(duplicates: list[DuplicateMatch]) -> str:
    lines = ["[SISTEMA] Se encontraron los siguientes materiales similares en el maestro:"]
    for i, d in enumerate(duplicates, 1):
        lines.append(f"  {i}. ID: {d.material_id} | {d.short_text} (similitud: {d.similarity:.0%})")
    lines.append("")
    lines.append("Presenta estos duplicados al usuario de forma clara y estructurada. "
                 "Preguntale si alguno le sirve o si su material es diferente.")
    return "\n".join(lines)


@router.post("/duplicates", response_model=DuplicatesResponse)
def step_duplicates(
    body: DuplicatesRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    t0 = time.time()

    short_text = _clip_short_text(body.short_text) or ""
    dup_threshold = float(os.environ.get("DUPLICADO_UMBRAL", "0.45"))
    rows = db.execute(
        text("""
            SELECT code, short_text, similarity(short_text, :query) AS sim
            FROM silver.materials
            WHERE similarity(short_text, :query) > :threshold
            ORDER BY sim DESC
            LIMIT 10
        """),
        {"query": short_text, "threshold": dup_threshold},
    ).fetchall()
    duplicates = [DuplicateMatch(material_id=r[0], short_text=r[1], similarity=round(float(r[2]), 3)) for r in rows]

    if not duplicates:
        elapsed = round(time.time() - t0, 3)
        _update_request_timestamp(db, body.request_id, "duplicates_completed_at", "duplicates_elapsed_s", elapsed)
        db.commit()
        return DuplicatesResponse(has_duplicates=False, elapsed_s=elapsed)

    # Duplicates found — call LLM to present them
    dup_context = _format_duplicates_for_llm(duplicates)
    dup_message = None

    # Load conversation for context (only if owned by this user)
    conv_row = db.execute(
        text("SELECT messages FROM silver.conversations WHERE id = :id AND created_by = :user_id"),
        {"id": body.conversation_id, "user_id": user["id"]},
    ).fetchone()
    existing_messages = (conv_row[0] if conv_row and conv_row[0] else [])
    history = _build_conversation_history(existing_messages)

    if body.user_message and body.llm_raw:
        history += [
            {"role": "user", "content": body.user_message},
            {"role": "assistant", "content": body.llm_raw},
        ]

    material_types = _get_material_types(db)
    system_prompt = build_system_prompt(material_types)

    try:
        dup_result = chat_completion(system_prompt, history, dup_context)
        dup_message = dup_result.parsed.get("message", "")
        _log_llm(db, body.conversation_id, dup_result.model, dup_context,
                 len(history), dup_result.raw, dup_result.parsed,
                 "duplicates_review", round(time.time() - t0, 3),
                 tokens_in=dup_result.tokens_in, tokens_out=dup_result.tokens_out)
    except Exception as e:
        logger.error("LLM duplicate call failed: %s", e)

    elapsed = round(time.time() - t0, 3)
    _update_request_timestamp(db, body.request_id, "duplicates_completed_at", "duplicates_elapsed_s", elapsed)
    db.commit()

    return DuplicatesResponse(
        has_duplicates=True,
        duplicates=duplicates,
        message=dup_message,
        elapsed_s=elapsed,
    )


# --- Step 2b: Duplicate decision ---

class DuplicateDecisionRequest(BaseModel):
    conversation_id: str
    request_id: int | None = None
    action: str  # "accepted" | "rejected"
    short_text: str
    selected_material_id: str | None = None
    duplicates: list[dict] = []
    elapsed_s: float | None = None


class DuplicateDecisionResponse(BaseModel):
    ok: bool
    action: str


@router.post("/duplicates/decision", response_model=DuplicateDecisionResponse)
def step_duplicate_decision(body: DuplicateDecisionRequest, db: Session = Depends(get_db)):
    if body.action not in ("accepted", "rejected"):
        raise HTTPException(status_code=400, detail="action must be 'accepted' or 'rejected'")

    db.execute(
        text("""
            INSERT INTO bronze.duplicate_logs
                (conversation_id, request_id, action, short_text, selected_material_id, duplicates, elapsed_s)
            VALUES
                (:conversation_id, :request_id, :action, :short_text, :selected_material_id, CAST(:duplicates AS jsonb), :elapsed_s)
        """),
        {
            "conversation_id": body.conversation_id,
            "request_id": body.request_id,
            "action": body.action,
            "short_text": body.short_text,
            "selected_material_id": body.selected_material_id,
            "duplicates": _json.dumps(body.duplicates),
            "elapsed_s": body.elapsed_s,
        },
    )

    # Record decision timestamp on request
    _update_request_timestamp(db, body.request_id, "duplicates_decided_at")

    if body.action == "accepted" and body.request_id and body.selected_material_id:
        db.execute(
            text("""
                UPDATE silver.requests
                SET status = 'existing_match',
                    specifications = CAST(:specs AS jsonb),
                    duplicates = CAST(:dups AS jsonb)
                WHERE id = :id
            """),
            {
                "id": body.request_id,
                "specs": _json.dumps({"matched_material_id": body.selected_material_id}),
                "dups": _json.dumps(body.duplicates),
            },
        )

    db.commit()
    return DuplicateDecisionResponse(ok=True, action=body.action)


# --- Step 3: ML Model prediction ---

class PredictRequest(BaseModel):
    conversation_id: str | None = None
    request_id: int | None = None
    short_text: str


class PredictResponse(BaseModel):
    prediction: ModelPrediction | None = None
    elapsed_s: float = 0


@router.post("/predict", response_model=PredictResponse)
def step_predict(body: PredictRequest, db: Session = Depends(get_db)):
    t0 = time.time()

    short_text = _clip_short_text(body.short_text) or ""

    try:
        artifact = _get_artifact()
        pipeline = artifact["pipeline"]
        le = artifact["label_encoder"]

        clean = preprocess_text(short_text)
        probas = pipeline.predict_proba([clean])[0]
        top_indices = probas.argsort()[-3:][::-1]

        top_codes = []
        for idx in top_indices:
            class_code = le.inverse_transform([idx])[0]
            conf = round(float(probas[idx]), 4)
            top_codes.append((class_code, conf))

        # Enrich with class names
        codes_list = [c[0] for c in top_codes]
        placeholders = ", ".join(f":c{i}" for i in range(len(codes_list)))
        params = {f"c{i}": code for i, code in enumerate(codes_list)}
        name_rows = db.execute(
            text(f"SELECT code, name FROM silver.classes WHERE code IN ({placeholders})"),
            params,
        ).fetchall()
        code_to_name = {r[0]: r[1] for r in name_rows}

        top_k = []
        for class_code, conf in top_codes:
            name = code_to_name.get(class_code, "")
            top_k.append([class_code, conf, name])

        prediction = ModelPrediction(categoria=top_k[0][0], confianza=top_k[0][1], top_k=top_k)
        elapsed = round(time.time() - t0, 3)

        # Log prediction
        db.execute(
            text("""
                INSERT INTO bronze.prediction_logs (type, input, output, confidence, elapsed_s)
                VALUES ('categorization', CAST(:input AS jsonb), CAST(:output AS jsonb), :confidence, :elapsed_s)
            """),
            {
                "input": _json.dumps({"short_text": body.short_text, "clean": clean, "conversation_id": body.conversation_id}),
                "output": _json.dumps({"categoria": prediction.categoria, "top_k": prediction.top_k}),
                "confidence": prediction.confianza,
                "elapsed_s": elapsed,
            },
        )

        # Record predict completion on the request
        _update_request_timestamp(db, body.request_id, "predict_completed_at", "predict_elapsed_s", elapsed)

        db.commit()
        return PredictResponse(prediction=prediction, elapsed_s=elapsed)

    except Exception as e:
        logger.error("Model prediction failed: %s", e)
        elapsed = round(time.time() - t0, 3)
        return PredictResponse(prediction=None, elapsed_s=elapsed)


# --- Search classes (for manual selection) ---

class ClassOut(BaseModel):
    code: str
    name: str
    article_group: str | None = None
    sector: str | None = None
    material_type_code: str | None = None
    material_type_description: str | None = None
    unspsc_code: str | None = None
    unspsc_description: str | None = None


_CLASS_SELECT = """
    SELECT
        c.code, c.name, c.article_group, c.sector,
        mt.code AS mt_code, mt.description AS mt_desc,
        u.code AS u_code, u.description AS u_desc
    FROM silver.classes c
    LEFT JOIN silver.material_types mt ON mt.id = c.material_type_id
    LEFT JOIN silver.unspsc u ON u.id = c.unspsc_id
"""


def _row_to_class(r) -> ClassOut:
    return ClassOut(
        code=r[0], name=r[1],
        article_group=r[2], sector=r[3],
        material_type_code=r[4], material_type_description=r[5],
        unspsc_code=r[6], unspsc_description=r[7],
    )


@router.get("/classes", response_model=list[ClassOut])
def search_classes(q: str = "", db: Session = Depends(get_db)):
    if not q.strip():
        return []
    rows = db.execute(
        text(_CLASS_SELECT + " WHERE c.code ILIKE :q OR c.name ILIKE :q ORDER BY c.name LIMIT 20"),
        {"q": f"%{q.strip()}%"},
    ).fetchall()
    return [_row_to_class(r) for r in rows]


@router.get("/classes/{code}", response_model=ClassOut)
def get_class(code: str, db: Session = Depends(get_db)):
    row = db.execute(
        text(_CLASS_SELECT + " WHERE c.code = :code"),
        {"code": code},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Class not found")
    return _row_to_class(row)


# --- Request lifecycle ---

class CreateRequestBody(BaseModel):
    conversation_id: str
    short_text: str
    long_text: str | None = None
    material_type_id: str
    llm_elapsed_s: float | None = None


class UpdateRequestBody(BaseModel):
    short_text: str | None = None
    long_text: str | None = None
    material_type_id: str | None = None
    class_code: str | None = None
    class_name: str | None = None
    category: str | None = None
    confidence: float | None = None
    alternatives: list[list] | None = None
    duplicates: list[dict] | None = None
    status: str | None = None
    material_id: str | None = None  # for existing_match


class RequestOut(BaseModel):
    request_id: int
    status: str


def _resolve_material_type(db: Session, code: str) -> int | None:
    row = db.execute(
        text("SELECT id FROM silver.material_types WHERE code = :code"),
        {"code": code},
    ).fetchone()
    return row[0] if row else None


@router.post("/requests", response_model=RequestOut, status_code=201)
def create_request(
    body: CreateRequestBody,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    """Create a new request as pending (called when LLM generates a proposal)."""
    material_type_fk = _resolve_material_type(db, body.material_type_id)
    clipped = _clip_short_text(body.short_text)

    row = db.execute(
        text("""
            INSERT INTO silver.requests
                (conversation_id, created_by, material_type_id, name, short_text, long_text, status,
                 llm_completed_at, llm_elapsed_s)
            VALUES
                (:conversation_id, :created_by, :material_type_id, :name, :short_text, :long_text, 'pending',
                 now(), :llm_elapsed_s)
            RETURNING id, status
        """),
        {
            "conversation_id": body.conversation_id,
            "created_by": user["id"],
            "material_type_id": material_type_fk,
            "name": clipped,
            "short_text": clipped,
            "long_text": body.long_text,
            "llm_elapsed_s": body.llm_elapsed_s,
        },
    ).fetchone()
    db.commit()
    return RequestOut(request_id=row[0], status=row[1])


@router.patch("/requests/{request_id}", response_model=RequestOut)
def update_request(request_id: int, body: UpdateRequestBody, db: Session = Depends(get_db)):
    """Update a request: confirm, discard, mark as existing_match, or edit fields."""
    # Build dynamic SET clause
    sets = []
    params: dict = {"id": request_id}

    if body.short_text is not None:
        sets.append("short_text = :short_text")
        sets.append("name = :short_text")
        params["short_text"] = _clip_short_text(body.short_text)

    if body.long_text is not None:
        sets.append("long_text = :long_text")
        params["long_text"] = body.long_text

    if body.material_type_id is not None:
        mt_fk = _resolve_material_type(db, body.material_type_id)
        sets.append("material_type_id = :material_type_id")
        params["material_type_id"] = mt_fk

    if body.class_code is not None or body.category is not None:
        selected = body.class_code or body.category
        sets.append("category = :category")
        params["category"] = selected
        # Detect correction
        if body.class_code and body.category and body.class_code != body.category:
            sets.append("corrected = true")

    if body.confidence is not None:
        sets.append("confidence = :confidence")
        params["confidence"] = body.confidence

    if body.alternatives is not None:
        sets.append("alternatives = CAST(:alternatives AS jsonb)")
        params["alternatives"] = _json.dumps(body.alternatives)

    if body.duplicates is not None:
        sets.append("duplicates = CAST(:duplicates AS jsonb)")
        params["duplicates"] = _json.dumps(body.duplicates)

    if body.status is not None:
        sets.append("status = :status")
        params["status"] = body.status
        if body.status == "confirmed":
            sets.append("confirmed_at = now()")
            # Compute total machine processing time
            sets.append("""
                processing_time_s = COALESCE(llm_elapsed_s, 0)
                    + COALESCE(duplicates_elapsed_s, 0)
                    + COALESCE(predict_elapsed_s, 0)
            """)
        if body.status == "discarded":
            sets.append("discarded_at = now()")
        if body.status == "existing_match" and body.material_id:
            sets.append("specifications = CAST(:specs AS jsonb)")
            params["specs"] = _json.dumps({"matched_material_id": body.material_id})

    if not sets:
        raise HTTPException(status_code=400, detail="No fields to update")

    query = f"UPDATE silver.requests SET {', '.join(sets)} WHERE id = :id RETURNING id, status"
    row = db.execute(text(query), params).fetchone()
    db.commit()

    if not row:
        raise HTTPException(status_code=404, detail="Request not found")
    return RequestOut(request_id=row[0], status=row[1])
