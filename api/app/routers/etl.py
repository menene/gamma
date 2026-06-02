import io
import time

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.auth import get_current_user
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

import pandas as pd

from app.db import get_db

router = APIRouter(prefix="/api/etl", tags=["ETL"], dependencies=[Depends(get_current_user)])


class IngestionResult(BaseModel):
    file_name: str
    target: str
    row_count: int
    status: str
    error_message: str | None = None
    elapsed_s: float


class IngestionLog(BaseModel):
    id: int
    file_name: str
    file_path: str | None
    row_count: int
    status: str
    error_message: str | None
    ingested_at: str


# ── Column mappings ──────────────────────────────────────────

MATERIAL_COLS = {
    "Material": "id",
    "Tipo material": "material_type_id",
    "Grupo de artículos": "article_group",
    "Unidad medida base": "unit_of_measure",
    "Info fabr./insp.": "manufacturer_info",
    "Denom.estándar": "class_id",
    "Texto breve de material": "short_text",
}

CLASS_COLS = {
    "Código": "code",
    "Denominación": "name",
    "Grupo de Artículos": "article_group",
    "Sector": "sector",
    "Tipo de Material": "material_type_id",
    "UNSPSC": "unspsc_id",
}

UNSPSC_COLS = {
    "Código Producto": "id",
    "Nombre Producto": "description",
}


def _to_str(val) -> str | None:
    """Convert a value to a clean string id (no trailing .0 from pandas float coercion)."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, float) and val == int(val):
        return str(int(val))
    return str(val).strip()


def _to_raw_str(val) -> str | None:
    """Convert to string preserving leading zeros (no int coercion)."""
    if val is None or pd.isna(val):
        return None
    return str(val).strip()


def _extract_code(val: str | None) -> str | None:
    """Extract code before ' - ' separator (e.g. 'ZCON - Materiales' → 'ZCON')."""
    if val is None or pd.isna(val):
        return None
    s = str(val).strip()
    if " - " in s:
        return s.split(" - ")[0].strip()
    return s


# ── Upload endpoints ─────────────────────────────────────────

@router.post("/upload/materials", response_model=IngestionResult)
def upload_materials(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(400, "Solo se aceptan archivos .xlsx")

    t0 = time.time()
    try:
        content = file.file.read()
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl")

        # Handle duplicate column names (two "Texto breve de material")
        cols = list(df.columns)
        seen: dict[str, int] = {}
        for i, c in enumerate(cols):
            if c in seen:
                cols[i] = f"{c}_{seen[c]}"
            seen[c] = seen.get(c, 0) + 1
        df.columns = cols

        rename = {}
        for src, dst in MATERIAL_COLS.items():
            if src in df.columns:
                rename[src] = dst
        df = df.rename(columns=rename)

        required = ["id", "material_type_id", "short_text"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise HTTPException(400, f"Columnas faltantes: {missing}")

        keep = [c for c in ["id", "material_type_id", "article_group", "unit_of_measure",
                            "manufacturer_info", "class_id", "short_text"] if c in df.columns]
        df = df[keep].copy()
        df["id"] = df["id"].apply(_to_str)
        if "manufacturer_info" in df.columns:
            df["manufacturer_info"] = df["manufacturer_info"].apply(_to_raw_str)
        if "class_id" in df.columns:
            df["class_id"] = df["class_id"].apply(_to_raw_str)
        df["deletion_flag"] = False
        df = df.dropna(subset=["id", "short_text"])

        rows = df.to_dict("records")
        if rows:
            cols_str = ", ".join(rows[0].keys())
            vals_str = ", ".join(f":{k}" for k in rows[0].keys())
            db.execute(
                text(f"INSERT INTO silver.materials ({cols_str}) VALUES ({vals_str}) "
                     "ON CONFLICT (id) DO UPDATE SET "
                     "material_type_id = EXCLUDED.material_type_id, "
                     "article_group = EXCLUDED.article_group, "
                     "unit_of_measure = EXCLUDED.unit_of_measure, "
                     "manufacturer_info = EXCLUDED.manufacturer_info, "
                     "class_id = EXCLUDED.class_id, "
                     "short_text = EXCLUDED.short_text, "
                     "deletion_flag = EXCLUDED.deletion_flag, "
                     "updated_at = now()"),
                rows,
            )

        _log_ingestion(db, file.filename, "silver.materials", len(rows), "success")
        db.commit()

        return IngestionResult(
            file_name=file.filename, target="silver.materials",
            row_count=len(rows), status="success", elapsed_s=round(time.time() - t0, 2),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        _log_ingestion(db, file.filename or "unknown", "silver.materials", 0, "failed", str(e))
        db.commit()
        raise HTTPException(500, f"Error procesando archivo: {e}")


@router.post("/upload/classes", response_model=IngestionResult)
def upload_classes(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(400, "Solo se aceptan archivos .xlsx")

    t0 = time.time()
    try:
        content = file.file.read()
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl")

        rename = {}
        for src, dst in CLASS_COLS.items():
            if src in df.columns:
                rename[src] = dst
        df = df.rename(columns=rename)

        required = ["code", "name"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise HTTPException(400, f"Columnas faltantes: {missing}")

        keep = [c for c in ["code", "name", "article_group", "sector", "material_type_id", "unspsc_id"]
                if c in df.columns]
        df = df[keep].copy()
        df["code"] = df["code"].apply(_to_raw_str)

        for col in ["article_group", "sector", "material_type_id", "unspsc_id"]:
            if col in df.columns:
                df[col] = df[col].apply(_extract_code)

        df = df.dropna(subset=["code", "name"])

        rows = df.to_dict("records")
        if rows:
            cols_str = ", ".join(rows[0].keys())
            vals_str = ", ".join(f":{k}" for k in rows[0].keys())
            db.execute(
                text(f"INSERT INTO silver.classes ({cols_str}) VALUES ({vals_str}) "
                     "ON CONFLICT (code) DO UPDATE SET "
                     "name = EXCLUDED.name, "
                     "article_group = EXCLUDED.article_group, "
                     "sector = EXCLUDED.sector, "
                     "material_type_id = EXCLUDED.material_type_id, "
                     "unspsc_id = EXCLUDED.unspsc_id"),
                rows,
            )

        _log_ingestion(db, file.filename, "silver.classes", len(rows), "success")
        db.commit()

        return IngestionResult(
            file_name=file.filename, target="silver.classes",
            row_count=len(rows), status="success", elapsed_s=round(time.time() - t0, 2),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        _log_ingestion(db, file.filename or "unknown", "silver.classes", 0, "failed", str(e))
        db.commit()
        raise HTTPException(500, f"Error procesando archivo: {e}")


@router.post("/upload/unspsc", response_model=IngestionResult)
def upload_unspsc(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(400, "Solo se aceptan archivos .xlsx")

    t0 = time.time()
    try:
        content = file.file.read()
        df = pd.read_excel(io.BytesIO(content), engine="openpyxl", skiprows=5)

        rename = {}
        for src, dst in UNSPSC_COLS.items():
            if src in df.columns:
                rename[src] = dst
        df = df.rename(columns=rename)

        required = ["id", "description"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise HTTPException(400, f"Columnas faltantes: {missing}")

        df = df[["id", "description"]].copy()
        df["id"] = df["id"].apply(_to_str)
        df = df.dropna(subset=["id", "description"])
        df = df.drop_duplicates(subset=["id"])

        rows = df.to_dict("records")
        if rows:
            db.execute(
                text("INSERT INTO silver.unspsc (id, description) VALUES (:id, :description) "
                     "ON CONFLICT (id) DO UPDATE SET description = EXCLUDED.description"),
                rows,
            )

        _log_ingestion(db, file.filename, "silver.unspsc", len(rows), "success")
        db.commit()

        return IngestionResult(
            file_name=file.filename, target="silver.unspsc",
            row_count=len(rows), status="success", elapsed_s=round(time.time() - t0, 2),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        _log_ingestion(db, file.filename or "unknown", "silver.unspsc", 0, "failed", str(e))
        db.commit()
        raise HTTPException(500, f"Error procesando archivo: {e}")


# ── Ingestion history ────────────────────────────────────────

@router.get("/logs", response_model=list[IngestionLog])
def get_ingestion_logs(db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT id, file_name, file_path, row_count, status, error_message, ingested_at "
             "FROM bronze.ingestion_logs ORDER BY ingested_at DESC LIMIT 50")
    ).fetchall()
    return [
        IngestionLog(
            id=r[0], file_name=r[1], file_path=r[2], row_count=r[3],
            status=r[4], error_message=r[5], ingested_at=str(r[6]),
        )
        for r in rows
    ]


# ── Table counts ─────────────────────────────────────────────

@router.get("/counts")
def get_table_counts(db: Session = Depends(get_db)):
    counts = {}
    for table in ["silver.materials", "silver.classes", "silver.unspsc"]:
        row = db.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
        counts[table] = row[0] if row else 0
    return counts


# ── Helper ───────────────────────────────────────────────────

def _log_ingestion(db: Session, file_name: str, target: str, row_count: int,
                   status: str, error_message: str | None = None):
    db.execute(
        text("""
            INSERT INTO bronze.ingestion_logs (file_name, file_path, row_count, status, error_message)
            VALUES (:file_name, :file_path, :row_count, :status, :error_message)
        """),
        {
            "file_name": file_name,
            "file_path": target,
            "row_count": row_count,
            "status": status,
            "error_message": error_message,
        },
    )
