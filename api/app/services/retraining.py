"""
Reentrenamiento del modelo de clasificacion de categoria.

Mecanica de versionado: el artefacto activo conserva siempre el mismo nombre en
disco, de modo que el cargador del API no cambia nunca. Antes de escribir uno
nuevo, el vigente se archiva con una marca de tiempo. Revertir es copiar el
archivo de vuelta.

Este proceso esta pensado para ejecutarse en contadas ocasiones y bajo
supervision, tipicamente despues de una carga importante al maestro. No se
programa ni se dispara solo.
"""

import json
import logging
import os
import shutil
import time
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    top_k_accuracy_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import LinearSVC
from sqlalchemy import text

from app.services.text import preprocess_text

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model")
ACTIVE_NAME = "model_artifact_v1.joblib"
ACTIVE_PATH = os.path.join(MODEL_DIR, ACTIVE_NAME)
ARCHIVE_DIR = os.path.join(MODEL_DIR, "archive")

# Numero minimo de ejemplos por clase. Por debajo de tres no alcanza para
# entrenar y evaluar la misma categoria.
MIN_EJEMPLOS_POR_CLASE = 3

# Particiones de calibracion deseadas. Se reducen automaticamente si alguna
# clase no tiene suficientes ejemplos en el conjunto de entrenamiento.
CV_PREFERIDO = 3

# Cuantos artefactos archivados se conservan. Cada uno ocupa lo mismo que el
# activo, de modo que el limite es una decision de disco.
MAX_ARCHIVADOS = int(os.environ.get("MODEL_MAX_ARCHIVED", "3"))


def _now_version() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")


def build_dataset(db) -> tuple[pd.DataFrame, dict]:
    """
    Arma el conjunto de entrenamiento.

    Fuente principal: el maestro de materiales, que ya incorpora todo lo cargado
    por el proceso de ingesta. Se le suman las solicitudes que el gestor
    corrigio de forma explicita, porque son senal etiquetada por un experto.

    Se excluyen deliberadamente las solicitudes que el modelo resolvio solo y el
    gestor acepto sin cambios: reentrenar con las propias sugerencias aceptadas
    refuerza los sesgos del modelo en lugar de corregirlos.
    """
    materiales = pd.DataFrame(db.execute(text("""
        SELECT m.short_text, c.code AS class_code
        FROM silver.materials m
        JOIN silver.classes c ON c.id = m.class_id
        WHERE m.short_text IS NOT NULL
          AND m.deletion_flag = false
    """)).fetchall(), columns=["short_text", "class_code"])

    correcciones = pd.DataFrame(db.execute(text("""
        SELECT r.short_text, r.category AS class_code
        FROM silver.requests r
        WHERE r.status = 'confirmed'
          AND r.corrected = true
          AND r.short_text IS NOT NULL
          AND r.category IS NOT NULL
    """)).fetchall(), columns=["short_text", "class_code"])

    origen = {
        "materiales": len(materiales),
        "correcciones": len(correcciones),
    }

    df = pd.concat([materiales, correcciones], ignore_index=True)
    df = df.dropna(subset=["short_text", "class_code"])
    df["clean_text"] = df["short_text"].astype(str).map(preprocess_text)
    df = df[df["clean_text"].str.len() > 0]

    # Se descartan las clases sin representacion suficiente.
    conteo = df["class_code"].value_counts()
    validas = conteo[conteo >= MIN_EJEMPLOS_POR_CLASE].index
    origen["descartados_clase_rara"] = int(len(df) - df["class_code"].isin(validas).sum())
    df = df[df["class_code"].isin(validas)]

    origen["total"] = len(df)
    origen["clases"] = int(df["class_code"].nunique())
    return df, origen


def safe_cv(y, preferido: int = CV_PREFERIDO) -> int:
    """
    Numero de particiones de calibracion que el conjunto admite.

    La calibracion exige al menos tantos ejemplos por clase como particiones. El
    filtro de clases raras se aplica sobre el conjunto completo, pero la
    particion de entrenamiento se queda con cerca del 80 %, de modo que una
    clase con el minimo de tres ejemplos llega al entrenamiento con dos y
    rompe una validacion de tres pliegues.

    Antes que descartar esas clases —lo que dejaria materiales que el modelo no
    podria predecir nunca— se reduce el numero de pliegues a lo que el conjunto
    soporte. El minimo es dos, garantizado por el filtro de clases raras.
    """
    _, counts = np.unique(y, return_counts=True)
    return int(max(2, min(preferido, int(counts.min()))))


def build_pipeline(cv: int = CV_PREFERIDO) -> Pipeline:
    """
    Misma configuracion que gano la competencia de modelos del laboratorio.

    `ensemble=False` hace que la calibracion conserve un unico estimador base en
    lugar de una copia por particion, lo que reduce varias veces el tamano del
    artefacto sin afectar la calidad de las probabilidades.
    """
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="char_wb", ngram_range=(2, 5),
            max_features=50000, sublinear_tf=True, strip_accents="unicode")),
        ("clf", CalibratedClassifierCV(LinearSVC(C=1.0, max_iter=2000), cv=cv, ensemble=False)),
    ])


def evaluate(pipeline, X_test, y_test) -> dict:
    y_pred = pipeline.predict(X_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1_macro": float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_test, y_pred, average="weighted", zero_division=0)),
    }
    proba = pipeline.predict_proba(X_test)
    k = min(3, proba.shape[1])
    metrics["top3_accuracy"] = float(
        top_k_accuracy_score(y_test, proba, k=k, labels=list(range(proba.shape[1])))
    )
    return metrics


def archive_active(etiqueta_vigente: str) -> str | None:
    """
    Aparta el artefacto vigente y lo nombra con SU PROPIA version.

    El nombre debe corresponder al modelo que se esta guardando, no al que va a
    ocupar su lugar. Nombrarlo con la version entrante desplazaria las
    etiquetas una posicion y haria imposible localizar un modelo para revertir.
    """
    if not os.path.exists(ACTIVE_PATH):
        return None
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    destino = os.path.join(ARCHIVE_DIR, f"model_artifact_{etiqueta_vigente}.joblib")
    shutil.move(ACTIVE_PATH, destino)
    logger.info("Artefacto de la version %s archivado en %s", etiqueta_vigente, destino)
    return destino


def active_version_label(db) -> str:
    """Version registrada como activa; sirve para nombrar su archivo al apartarlo."""
    row = db.execute(text(
        "SELECT version FROM silver.model_versions WHERE is_active LIMIT 1"
    )).fetchone()
    return row[0] if row else f"desconocida_{_now_version()}"


def prune_archive(keep: int = MAX_ARCHIVADOS) -> list[str]:
    """Conserva unicamente los artefactos archivados mas recientes."""
    if not os.path.isdir(ARCHIVE_DIR):
        return []
    archivos = sorted(
        (f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".joblib")),
        reverse=True,
    )
    borrados = []
    for f in archivos[keep:]:
        os.remove(os.path.join(ARCHIVE_DIR, f))
        borrados.append(f)
        logger.info("Artefacto archivado eliminado por limite de retencion: %s", f)
    return borrados


def list_archived() -> list[dict]:
    if not os.path.isdir(ARCHIVE_DIR):
        return []
    out = []
    for f in sorted(os.listdir(ARCHIVE_DIR), reverse=True):
        if not f.endswith(".joblib"):
            continue
        p = os.path.join(ARCHIVE_DIR, f)
        out.append({
            "file_name": f,
            "version": f.removeprefix("model_artifact_").removesuffix(".joblib"),
            "size_bytes": os.path.getsize(p),
        })
    return out


def restore_version(version: str, etiqueta_vigente: str) -> str:
    """
    Devuelve al servicio un artefacto archivado.

    El vigente se archiva primero bajo su propia version, de modo que un
    rollback tampoco pierde nada y puede deshacerse a su vez.
    """
    origen = os.path.join(ARCHIVE_DIR, f"model_artifact_{version}.joblib")
    if not os.path.exists(origen):
        raise FileNotFoundError(f"No existe el artefacto archivado de la version {version}")
    archive_active(etiqueta_vigente)
    shutil.copy2(origen, ACTIVE_PATH)
    logger.info("Restaurada la version %s como artefacto activo", version)
    return ACTIVE_PATH


def run_retraining(db, job_id: int, user_id: int | None = None) -> None:
    """
    Ejecuta el reentrenamiento completo y deja constancia en la base.

    Se invoca en segundo plano: no debe propagar excepciones, sino registrarlas
    en el trabajo para que el administrador pueda consultarlas.
    """
    t0 = time.time()

    def step(nombre: str):
        db.execute(
            text("UPDATE silver.retrain_jobs SET step = :s, status = 'running' WHERE id = :id"),
            {"s": nombre, "id": job_id},
        )
        db.commit()

    try:
        step("construyendo el conjunto de datos")
        df, origen = build_dataset(db)
        if origen["clases"] < 2:
            raise ValueError("El conjunto no tiene suficientes clases para entrenar")

        le = LabelEncoder()
        y = le.fit_transform(df["class_code"].values)
        X = df["clean_text"].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        cv = safe_cv(y_train)
        if cv < CV_PREFERIDO:
            logger.warning(
                "Se reduce la calibracion a %d particiones: la clase mas pequena "
                "aporta %d ejemplos al entrenamiento", cv, cv)

        step(f"entrenando (calibracion de {cv} particiones)")
        pipeline = build_pipeline(cv)
        t_train = time.time()
        pipeline.fit(X_train, y_train)
        train_seconds = round(time.time() - t_train, 3)

        step("evaluando")
        metrics = evaluate(pipeline, X_test, y_test)

        # Se conserva el mismo numero de particiones que en la evaluacion, para
        # que el artefacto desplegado corresponda a la configuracion medida.
        step("reentrenando sobre el conjunto completo")
        pipeline = build_pipeline(cv)
        pipeline.fit(X, y)

        version = _now_version()
        step("archivando el artefacto vigente")
        archive_active(active_version_label(db))

        step("publicando el nuevo artefacto")
        label_to_class = (
            df.assign(label=y).drop_duplicates("label").set_index("label")["class_code"].to_dict()
        )
        artifact = {
            "pipeline": pipeline,
            "label_encoder": le,
            "model_name": "LinearSVC + CharTFIDF",
            "n_classes": int(len(le.classes_)),
            "n_samples": int(len(X)),
            "metrics": {**metrics, "cv": cv},
            "label_to_class_code": {int(k): str(v) for k, v in label_to_class.items()},
            "version": version,
        }
        os.makedirs(MODEL_DIR, exist_ok=True)
        joblib.dump(artifact, ACTIVE_PATH, compress=3)
        size_bytes = os.path.getsize(ACTIVE_PATH)

        prune_archive()

        # Se registra la version nueva y se traslada la marca de activo.
        db.execute(text("UPDATE silver.model_versions SET is_active = false WHERE is_active"))
        row = db.execute(text("""
            INSERT INTO silver.model_versions
                (version, file_name, is_active, model_name, n_classes, n_samples,
                 accuracy, f1_macro, f1_weighted, top3_accuracy, train_seconds, size_bytes,
                 source_materials, source_requests, created_by)
            VALUES
                (:version, :file_name, true, :model_name, :n_classes, :n_samples,
                 :accuracy, :f1_macro, :f1_weighted, :top3_accuracy, :train_seconds, :size_bytes,
                 :source_materials, :source_requests, :created_by)
            RETURNING id
        """), {
            "version": version,
            "file_name": ACTIVE_NAME,
            "model_name": artifact["model_name"],
            "n_classes": artifact["n_classes"],
            "n_samples": artifact["n_samples"],
            "accuracy": metrics["accuracy"],
            "f1_macro": metrics["f1_macro"],
            "f1_weighted": metrics["f1_weighted"],
            "top3_accuracy": metrics["top3_accuracy"],
            "train_seconds": train_seconds,
            "size_bytes": size_bytes,
            "source_materials": origen["materiales"],
            "source_requests": origen["correcciones"],
            "created_by": user_id,
        }).fetchone()

        elapsed = round(time.time() - t0, 3)
        db.execute(text("""
            UPDATE silver.retrain_jobs
               SET status = 'completed', step = 'finalizado', finished_at = now(),
                   elapsed_s = :elapsed, version_id = :vid,
                   n_train = :ntr, n_test = :nte, n_classes = :ncl,
                   metrics = CAST(:metrics AS jsonb)
             WHERE id = :id
        """), {
            "elapsed": elapsed, "vid": row[0], "id": job_id,
            "ntr": len(X_train), "nte": len(X_test), "ncl": artifact["n_classes"],
            "metrics": json.dumps({**metrics, "cv": cv}),
        })
        db.commit()

        # El API recarga el artefacto en la siguiente prediccion.
        from app.routers import model as model_router
        model_router.invalidate_artifact()

        logger.info("Reentrenamiento %s completado en %.1fs", job_id, elapsed)

    except Exception as e:  # noqa: BLE001 - el trabajo debe registrar cualquier fallo
        logger.exception("Reentrenamiento %s fallido", job_id)
        db.rollback()
        db.execute(text("""
            UPDATE silver.retrain_jobs
               SET status = 'failed', finished_at = now(),
                   elapsed_s = :elapsed, error_message = :err
             WHERE id = :id
        """), {"elapsed": round(time.time() - t0, 3), "err": str(e)[:2000], "id": job_id})
        db.commit()
