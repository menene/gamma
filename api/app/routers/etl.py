import io
import time

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.auth import get_current_user
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

import pandas as pd

from app.db import get_db
from app.services.text import preprocess_text

router = APIRouter(prefix="/api/etl", tags=["ETL"], dependencies=[Depends(get_current_user)])


class IngestionResult(BaseModel):
    file_name: str
    target: str
    row_count: int
    status: str
    error_message: str | None = None
    elapsed_s: float
    # Materials created by GAMMA that got their SAP code assigned by this upload
    # instead of being inserted as a new row (see _reconcile_pending_materials).
    reconciled_count: int = 0


class IngestionLog(BaseModel):
    id: int
    file_name: str
    file_path: str | None
    row_count: int
    status: str
    error_message: str | None
    elapsed_s: float | None
    ingested_at: str


# ── Column mappings ──────────────────────────────────────────

MATERIAL_COLS = {
    "Material": "code",
    "Unidad medida base": "_uom_code",
    "Denom.estándar": "_class_code",
    "Texto breve de material": "short_text",
}

CLASS_COLS = {
    "Código": "code",
    "Denominación": "name",
    "Grupo de Artículos": "article_group",
    "Sector": "sector",
    "Tipo de Material": "_material_type_code",
    "UNSPSC": "_unspsc_code",
}

UNSPSC_COLS = {
    "Código Producto": "code",
    "Nombre Producto": "description",
}


def _to_str(val) -> str | None:
    """Convert a value to a clean string (no trailing .0 from pandas float coercion)."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, float) and val == int(val):
        return str(int(val))
    return str(val).strip()


def _extract_code(val: str | None) -> str | None:
    """Extract code before ' - ' separator (e.g. 'ZCON - Materiales' → 'ZCON')."""
    if val is None or pd.isna(val):
        return None
    s = str(val).strip()
    if " - " in s:
        return s.split(" - ")[0].strip()
    return s


def _extract_code_and_desc(val) -> tuple[str | None, str | None]:
    """Extract code and description from composite value (e.g. 'ZCON - Materiales' → ('ZCON', 'Materiales'))."""
    if val is None or pd.isna(val):
        return None, None
    s = str(val).strip()
    if " - " in s:
        parts = s.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()
    return _to_str(val), None


def _build_lookup(db: Session, table: str) -> dict[str, int]:
    """Build a code → id lookup dict for a reference table."""
    rows = db.execute(text(f"SELECT code, id FROM {table}")).fetchall()
    return {str(r[0]): r[1] for r in rows}


def _nan_to_none(val):
    """pandas leaves NaN where a lookup missed; the DB wants NULL."""
    if isinstance(val, float) and pd.isna(val):
        return None
    return val


def _reconcile_pending_materials(db: Session, rows: list[dict]) -> tuple[list[dict], int]:
    """Close the loop between export and import.

    A material exported to SAP is written to silver.materials with code NULL
    (pending) and a source_request_id. Once SAP assigns it a code, the material
    comes back in the next maestro upload. Without this step it would be
    inserted as a brand-new row, leaving the pending one behind as a duplicate
    of itself.

    Instead we match incoming rows against pending materials by normalized
    short_text and stamp the SAP code onto the existing row. Returns the rows
    that still need a plain insert, plus how many were reconciled.
    """
    pending = db.execute(
        text("SELECT id, short_text FROM silver.materials "
             "WHERE code IS NULL AND short_text IS NOT NULL ORDER BY id")
    ).fetchall()
    if not pending:
        return rows, 0

    # Several pending materials can normalize to the same text; keep them in a
    # queue per key so each incoming row consumes exactly one.
    by_text: dict[str, list[int]] = {}
    for mat_id, short_text in pending:
        by_text.setdefault(preprocess_text(short_text), []).append(mat_id)

    # A code already present in the maestro must not be moved onto a pending
    # row — that row would then collide with the existing one. Those fall
    # through to the regular upsert.
    taken_codes = {
        str(r[0])
        for r in db.execute(text("SELECT code FROM silver.materials WHERE code IS NOT NULL")).fetchall()
    }

    remaining: list[dict] = []
    updates: list[dict] = []

    for row in rows:
        code = row.get("code")
        short_text = row.get("short_text")
        key = preprocess_text(str(short_text)) if short_text else None
        candidates = by_text.get(key) if key else None

        if not code or code in taken_codes or not candidates:
            remaining.append(row)
            continue

        updates.append({
            "id": candidates.pop(0),
            "code": code,
            # The uploaded file may not carry these columns at all; keep whatever
            # GAMMA assigned at export time rather than blanking it out.
            "class_id": _nan_to_none(row.get("class_id")),
            "unit_of_measure_id": _nan_to_none(row.get("unit_of_measure_id")),
            "short_text": short_text,
            "deletion_flag": row.get("deletion_flag", False),
        })
        taken_codes.add(code)

    if updates:
        db.execute(
            text("""
                UPDATE silver.materials SET
                    code               = :code,
                    class_id           = COALESCE(CAST(:class_id AS BIGINT), class_id),
                    unit_of_measure_id = COALESCE(CAST(:unit_of_measure_id AS BIGINT), unit_of_measure_id),
                    short_text         = :short_text,
                    deletion_flag      = :deletion_flag,
                    updated_at         = now()
                WHERE id = :id
            """),
            updates,
        )

    return remaining, len(updates)


# ── Upload endpoints ─────────────────────────────────────────

@router.post("/upload/materials", response_model=IngestionResult)
def upload_materials(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(400, "Solo se aceptan archivos .xlsx")

    t0 = time.time()
    try:
        content = file.file.read()
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl", dtype=str)

        # Handle duplicate column names (two "Texto breve de material")
        cols = list(df.columns)
        seen: dict[str, int] = {}
        for i, c in enumerate(cols):
            if c in seen:
                cols[i] = f"{c}_{seen[c]}"
            seen[c] = seen.get(c, 0) + 1
        df.columns = cols

        rename = {}
        for col in df.columns:
            for src, dst in MATERIAL_COLS.items():
                if col == src or col.startswith(src):
                    rename[col] = dst
                    break
        df = df.rename(columns=rename)

        required = ["code", "short_text"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise HTTPException(400, f"Columnas faltantes: {missing}")

        keep = [c for c in ["code", "_class_code", "_uom_code", "short_text"] if c in df.columns]
        df = df[keep].copy()

        # Clean string columns
        df["code"] = df["code"].apply(_to_str)
        for col in ["_class_code", "_uom_code"]:
            if col in df.columns:
                df[col] = df[col].apply(_to_str)

        df = df.dropna(subset=["code", "short_text"])

        # Auto-populate units_of_measure table from data
        if "_uom_code" in df.columns:
            uom_codes = df["_uom_code"].dropna().unique().tolist()
            if uom_codes:
                db.execute(
                    text("INSERT INTO silver.units_of_measure (code) VALUES (:code) "
                         "ON CONFLICT (code) DO NOTHING"),
                    [{"code": c} for c in uom_codes],
                )

        # Resolve codes → synthetic IDs
        cls_lookup = _build_lookup(db, "silver.classes")
        uom_lookup = _build_lookup(db, "silver.units_of_measure")

        if "_class_code" in df.columns:
            df["class_id"] = df["_class_code"].map(cls_lookup)
            df.drop(columns=["_class_code"], inplace=True)

        if "_uom_code" in df.columns:
            df["unit_of_measure_id"] = df["_uom_code"].map(uom_lookup)
            df.drop(columns=["_uom_code"], inplace=True)

        df["deletion_flag"] = False

        rows = df.to_dict("records")
        # Replace NaN with None for DB insert
        for row in rows:
            for k, v in row.items():
                if pd.isna(v) if isinstance(v, float) else False:
                    row[k] = None

        total_rows = len(rows)

        # Materials GAMMA already created (code pending) get their SAP code
        # stamped onto the existing row instead of being inserted again.
        rows, reconciled = _reconcile_pending_materials(db, rows)

        if rows:
            cols_str = ", ".join(rows[0].keys())
            vals_str = ", ".join(f":{k}" for k in rows[0].keys())
            db.execute(
                text(f"INSERT INTO silver.materials ({cols_str}) VALUES ({vals_str}) "
                     "ON CONFLICT (code) DO UPDATE SET "
                     "class_id = EXCLUDED.class_id, "
                     "unit_of_measure_id = EXCLUDED.unit_of_measure_id, "
                     "short_text = EXCLUDED.short_text, "
                     "deletion_flag = EXCLUDED.deletion_flag, "
                     "updated_at = now()"),
                rows,
            )

        elapsed = round(time.time() - t0, 3)
        _log_ingestion(db, file.filename, "silver.materials", total_rows, "success", elapsed_s=elapsed)
        db.commit()

        return IngestionResult(
            file_name=file.filename, target="silver.materials",
            row_count=total_rows, status="success", elapsed_s=elapsed,
            reconciled_count=reconciled,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        elapsed = round(time.time() - t0, 3)
        _log_ingestion(db, file.filename or "unknown", "silver.materials", 0, "failed", str(e), elapsed_s=elapsed)
        db.commit()
        raise HTTPException(500, f"Error procesando archivo: {e}")


@router.post("/upload/classes", response_model=IngestionResult)
def upload_classes(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(400, "Solo se aceptan archivos .xlsx")

    t0 = time.time()
    try:
        content = file.file.read()
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl", dtype=str)

        rename = {}
        for col in df.columns:
            for src, dst in CLASS_COLS.items():
                if col == src or col.startswith(src):
                    rename[col] = dst
                    break
        df = df.rename(columns=rename)

        required = ["code", "name"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise HTTPException(400, f"Columnas faltantes: {missing}")

        keep = [c for c in ["code", "name", "article_group", "sector",
                            "_material_type_code", "_unspsc_code"]
                if c in df.columns]
        df = df[keep].copy()
        df["code"] = df["code"].apply(_to_str)

        if "article_group" in df.columns:
            df["article_group"] = df["article_group"].apply(_extract_code)
        if "sector" in df.columns:
            df["sector"] = df["sector"].apply(_extract_code)

        # Auto-create missing material_types from composite values
        if "_material_type_code" in df.columns:
            mt_pairs = df["_material_type_code"].dropna().apply(_extract_code_and_desc).tolist()
            mt_to_insert = {code: desc for code, desc in mt_pairs if code is not None}
            if mt_to_insert:
                db.execute(
                    text("INSERT INTO silver.material_types (code, description) VALUES (:code, :description) "
                         "ON CONFLICT (code) DO NOTHING"),
                    [{"code": c, "description": d} for c, d in mt_to_insert.items()],
                )
            df["_material_type_code"] = df["_material_type_code"].apply(_extract_code)

        # Auto-create missing unspsc from composite values
        if "_unspsc_code" in df.columns:
            unspsc_pairs = df["_unspsc_code"].dropna().apply(_extract_code_and_desc).tolist()
            unspsc_to_insert = {code: (desc or code) for code, desc in unspsc_pairs if code is not None}
            if unspsc_to_insert:
                db.execute(
                    text("INSERT INTO silver.unspsc (code, description) VALUES (:code, :description) "
                         "ON CONFLICT (code) DO NOTHING"),
                    [{"code": c, "description": d} for c, d in unspsc_to_insert.items()],
                )
            df["_unspsc_code"] = df["_unspsc_code"].apply(_extract_code)

        df = df.dropna(subset=["code", "name"])

        # Resolve codes → synthetic IDs
        mt_lookup = _build_lookup(db, "silver.material_types")
        unspsc_lookup = _build_lookup(db, "silver.unspsc")

        if "_material_type_code" in df.columns:
            df["material_type_id"] = df["_material_type_code"].map(mt_lookup)
            df.drop(columns=["_material_type_code"], inplace=True)

        if "_unspsc_code" in df.columns:
            df["unspsc_id"] = df["_unspsc_code"].map(unspsc_lookup)
            df.drop(columns=["_unspsc_code"], inplace=True)

        rows = df.to_dict("records")
        for row in rows:
            for k, v in row.items():
                if pd.isna(v) if isinstance(v, float) else False:
                    row[k] = None

        if rows:
            cols_str = ", ".join(rows[0].keys())
            vals_str = ", ".join(f":{k}" for k in rows[0].keys())
            db.execute(
                text(f"INSERT INTO silver.classes ({cols_str}) VALUES ({vals_str}) "
                     "ON CONFLICT (code) DO UPDATE SET "
                     "name = EXCLUDED.name, "
                     "material_type_id = EXCLUDED.material_type_id, "
                     "unspsc_id = EXCLUDED.unspsc_id, "
                     "article_group = EXCLUDED.article_group, "
                     "sector = EXCLUDED.sector"),
                rows,
            )

        elapsed = round(time.time() - t0, 3)
        _log_ingestion(db, file.filename, "silver.classes", len(rows), "success", elapsed_s=elapsed)
        db.commit()

        return IngestionResult(
            file_name=file.filename, target="silver.classes",
            row_count=len(rows), status="success", elapsed_s=elapsed,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        elapsed = round(time.time() - t0, 3)
        _log_ingestion(db, file.filename or "unknown", "silver.classes", 0, "failed", str(e), elapsed_s=elapsed)
        db.commit()
        raise HTTPException(500, f"Error procesando archivo: {e}")


@router.post("/upload/unspsc", response_model=IngestionResult)
def upload_unspsc(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(400, "Solo se aceptan archivos .xlsx")

    t0 = time.time()
    try:
        content = file.file.read()
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl", skiprows=5, dtype=str)

        rename = {}
        for col in df.columns:
            for src, dst in UNSPSC_COLS.items():
                if col == src or col.startswith(src):
                    rename[col] = dst
                    break
        df = df.rename(columns=rename)

        required = ["code", "description"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise HTTPException(400, f"Columnas faltantes: {missing}")

        df = df[["code", "description"]].copy()
        df["code"] = df["code"].apply(_to_str)
        df = df.dropna(subset=["code", "description"])
        df = df.drop_duplicates(subset=["code"])

        rows = df.to_dict("records")
        if rows:
            db.execute(
                text("INSERT INTO silver.unspsc (code, description) VALUES (:code, :description) "
                     "ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description"),
                rows,
            )

        elapsed = round(time.time() - t0, 3)
        _log_ingestion(db, file.filename, "silver.unspsc", len(rows), "success", elapsed_s=elapsed)
        db.commit()

        return IngestionResult(
            file_name=file.filename, target="silver.unspsc",
            row_count=len(rows), status="success", elapsed_s=elapsed,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        elapsed = round(time.time() - t0, 3)
        _log_ingestion(db, file.filename or "unknown", "silver.unspsc", 0, "failed", str(e), elapsed_s=elapsed)
        db.commit()
        raise HTTPException(500, f"Error procesando archivo: {e}")


# ── Ingestion history ────────────────────────────────────────

@router.get("/logs", response_model=list[IngestionLog])
def get_ingestion_logs(db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT id, file_name, file_path, row_count, status, error_message, elapsed_s, ingested_at "
             "FROM bronze.ingestion_logs ORDER BY ingested_at DESC LIMIT 50")
    ).fetchall()
    return [
        IngestionLog(
            id=r[0], file_name=r[1], file_path=r[2], row_count=r[3],
            status=r[4], error_message=r[5], elapsed_s=float(r[6]) if r[6] else None,
            ingested_at=str(r[7]),
        )
        for r in rows
    ]


# ── Table counts ─────────────────────────────────────────────

@router.get("/counts")
def get_table_counts(db: Session = Depends(get_db)):
    counts = {}
    for table in ["silver.materials", "silver.classes", "silver.unspsc", "silver.units_of_measure"]:
        row = db.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
        counts[table] = row[0] if row else 0
    return counts


# ── Helper ───────────────────────────────────────────────────

def _log_ingestion(db: Session, file_name: str, target: str, row_count: int,
                   status: str, error_message: str | None = None, elapsed_s: float | None = None):
    db.execute(
        text("""
            INSERT INTO bronze.ingestion_logs (file_name, file_path, row_count, status, error_message, elapsed_s)
            VALUES (:file_name, :file_path, :row_count, :status, :error_message, :elapsed_s)
        """),
        {
            "file_name": file_name,
            "file_path": target,
            "row_count": row_count,
            "status": status,
            "error_message": error_message,
            "elapsed_s": elapsed_s,
        },
    )
