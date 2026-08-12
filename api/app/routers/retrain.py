"""
Reentrenamiento del modelo de clasificacion.

Todas las rutas exigen privilegios de administrador. La comprobacion vive aqui,
en el servidor: ocultar la pantalla en el frontend es una comodidad, no una
medida de seguridad.
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.db import SessionLocal, get_db
from app.services import retraining

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/model",
    tags=["Reentrenamiento"],
    dependencies=[Depends(require_admin)],
)


# ── Esquemas ──────────────────────────────────────────────────

class RetrainStarted(BaseModel):
    job_id: int
    status: str
    message: str


class MetricComparison(BaseModel):
    metric: str
    anterior: float | None = None
    nueva: float | None = None
    delta: float | None = None


class JobStatus(BaseModel):
    job_id: int
    status: str
    step: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    elapsed_s: float | None = None
    n_train: int | None = None
    n_test: int | None = None
    n_classes: int | None = None
    metrics: dict | None = None
    comparison: list[MetricComparison] = Field(default_factory=list)
    error_message: str | None = None


class ModelVersion(BaseModel):
    id: int | None = None
    version: str
    file_name: str
    is_active: bool = False
    model_name: str | None = None
    n_classes: int | None = None
    n_samples: int | None = None
    accuracy: float | None = None
    f1_macro: float | None = None
    f1_weighted: float | None = None
    top3_accuracy: float | None = None
    size_bytes: int | None = None
    created_at: str | None = None
    notes: str | None = None


class RollbackRequest(BaseModel):
    version: str


class RollbackResult(BaseModel):
    ok: bool
    version: str
    message: str


# ── Ejecucion en segundo plano ────────────────────────────────

def _run_job(job_id: int, user_id: int) -> None:
    """
    El trabajo abre su propia sesion: la del request muere al responder, y este
    proceso sigue corriendo despues.
    """
    db = SessionLocal()
    try:
        retraining.run_retraining(db, job_id, user_id)
    finally:
        db.close()


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/retrain", response_model=RetrainStarted, status_code=status.HTTP_202_ACCEPTED)
def start_retraining(
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: dict = Depends(require_admin),
):
    """
    Dispara un reentrenamiento y responde de inmediato.

    El proceso puede tardar varios minutos y mantiene en memoria el modelo
    vigente y el nuevo a la vez, por lo que se ejecuta en segundo plano. Solo se
    admite una ejecucion simultanea.
    """
    activo = db.execute(text(
        "SELECT id FROM silver.retrain_jobs WHERE status IN ('pending', 'running') LIMIT 1"
    )).fetchone()
    if activo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya hay un reentrenamiento en curso (trabajo {activo[0]})",
        )

    previa = db.execute(text(
        "SELECT id FROM silver.model_versions WHERE is_active LIMIT 1"
    )).fetchone()

    row = db.execute(text("""
        INSERT INTO silver.retrain_jobs (status, step, triggered_by, previous_version_id)
        VALUES ('pending', 'en cola', :uid, :prev)
        RETURNING id
    """), {"uid": user["id"], "prev": previa[0] if previa else None}).fetchone()
    db.commit()

    job_id = row[0]
    background.add_task(_run_job, job_id, user["id"])
    logger.info("Reentrenamiento %s encolado por el usuario %s", job_id, user["id"])

    return RetrainStarted(
        job_id=job_id,
        status="pending",
        message="Reentrenamiento iniciado. Consulte el estado con el identificador del trabajo.",
    )


@router.get("/retrain/{job_id}", response_model=JobStatus)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Estado de una ejecucion, con la comparacion contra el modelo anterior."""
    row = db.execute(text("""
        SELECT j.id, j.status, j.step, j.started_at, j.finished_at, j.elapsed_s,
               j.n_train, j.n_test, j.n_classes, j.metrics, j.error_message,
               p.accuracy AS p_acc, p.f1_macro AS p_f1m, p.f1_weighted AS p_f1w,
               p.top3_accuracy AS p_top3
          FROM silver.retrain_jobs j
          LEFT JOIN silver.model_versions p ON p.id = j.previous_version_id
         WHERE j.id = :id
    """), {"id": job_id}).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")

    metrics = row.metrics or {}
    anteriores = {
        "accuracy": row.p_acc, "f1_macro": row.p_f1m,
        "f1_weighted": row.p_f1w, "top3_accuracy": row.p_top3,
    }

    comparison: list[MetricComparison] = []
    for m in ("accuracy", "f1_macro", "f1_weighted", "top3_accuracy"):
        nueva = metrics.get(m)
        anterior = float(anteriores[m]) if anteriores[m] is not None else None
        delta = round(nueva - anterior, 4) if (nueva is not None and anterior is not None) else None
        comparison.append(MetricComparison(
            metric=m,
            anterior=anterior,
            nueva=round(nueva, 4) if nueva is not None else None,
            delta=delta,
        ))

    return JobStatus(
        job_id=row.id,
        status=row.status,
        step=row.step,
        started_at=row.started_at.isoformat() if row.started_at else None,
        finished_at=row.finished_at.isoformat() if row.finished_at else None,
        elapsed_s=float(row.elapsed_s) if row.elapsed_s is not None else None,
        n_train=row.n_train,
        n_test=row.n_test,
        n_classes=row.n_classes,
        metrics=metrics or None,
        comparison=comparison,
        error_message=row.error_message,
    )


@router.get("/retrain", response_model=list[JobStatus])
def list_jobs(limit: int = 20, db: Session = Depends(get_db)):
    """Historial de ejecuciones, de la mas reciente a la mas antigua."""
    rows = db.execute(text("""
        SELECT id, status, step, started_at, finished_at, elapsed_s,
               n_train, n_test, n_classes, metrics, error_message
          FROM silver.retrain_jobs
         ORDER BY started_at DESC
         LIMIT :limit
    """), {"limit": limit}).fetchall()

    return [
        JobStatus(
            job_id=r.id, status=r.status, step=r.step,
            started_at=r.started_at.isoformat() if r.started_at else None,
            finished_at=r.finished_at.isoformat() if r.finished_at else None,
            elapsed_s=float(r.elapsed_s) if r.elapsed_s is not None else None,
            n_train=r.n_train, n_test=r.n_test, n_classes=r.n_classes,
            metrics=r.metrics or None, error_message=r.error_message,
        )
        for r in rows
    ]


@router.get("/versions", response_model=list[ModelVersion])
def list_versions(db: Session = Depends(get_db)):
    """
    Versiones registradas del modelo.

    Se cruza el registro de la base con los artefactos presentes en disco: una
    version sin archivo ya no se puede restaurar, y conviene que se note.
    """
    rows = db.execute(text("""
        SELECT id, version, file_name, is_active, model_name, n_classes, n_samples,
               accuracy, f1_macro, f1_weighted, top3_accuracy, size_bytes, created_at, notes
          FROM silver.model_versions
         ORDER BY created_at DESC
    """)).fetchall()

    en_disco = {a["version"]: a for a in retraining.list_archived()}

    versiones = []
    for r in rows:
        archivo = en_disco.get(r.version)
        versiones.append(ModelVersion(
            id=r.id, version=r.version, file_name=r.file_name, is_active=r.is_active,
            model_name=r.model_name, n_classes=r.n_classes, n_samples=r.n_samples,
            accuracy=float(r.accuracy) if r.accuracy is not None else None,
            f1_macro=float(r.f1_macro) if r.f1_macro is not None else None,
            f1_weighted=float(r.f1_weighted) if r.f1_weighted is not None else None,
            top3_accuracy=float(r.top3_accuracy) if r.top3_accuracy is not None else None,
            size_bytes=r.size_bytes or (archivo["size_bytes"] if archivo else None),
            created_at=r.created_at.isoformat() if r.created_at else None,
            notes=r.notes,
        ))

    # Artefactos en disco sin registro en la base (por ejemplo, los respaldos
    # que deja un rollback). Se listan para que el administrador los vea.
    registradas = {r.version for r in rows}
    for a in retraining.list_archived():
        if a["version"] not in registradas:
            versiones.append(ModelVersion(
                version=a["version"], file_name=a["file_name"],
                size_bytes=a["size_bytes"], notes="Artefacto en disco sin registro en la base",
            ))

    return versiones


@router.post("/rollback", response_model=RollbackResult)
def rollback(body: RollbackRequest, db: Session = Depends(get_db)):
    """
    Restaura un artefacto archivado como modelo activo.

    El vigente se archiva antes de ser reemplazado, de modo que el rollback
    tambien se puede deshacer.
    """
    en_curso = db.execute(text(
        "SELECT id FROM silver.retrain_jobs WHERE status IN ('pending', 'running') LIMIT 1"
    )).fetchone()
    if en_curso:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede revertir mientras hay un reentrenamiento en curso",
        )

    try:
        retraining.restore_version(body.version, retraining.active_version_label(db))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    db.execute(text("UPDATE silver.model_versions SET is_active = false WHERE is_active"))
    db.execute(text("UPDATE silver.model_versions SET is_active = true WHERE version = :v"),
               {"v": body.version})
    db.commit()

    from app.routers import model as model_router
    model_router.invalidate_artifact()

    return RollbackResult(
        ok=True,
        version=body.version,
        message=f"Version {body.version} restaurada. Se aplicara en la proxima prediccion.",
    )
