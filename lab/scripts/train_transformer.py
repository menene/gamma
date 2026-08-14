"""
Fine-tuning del transformer multilingue para clasificacion de categoria.

Evalua `microsoft/Multilingual-MiniLM-L12-H384` como candidato de la competencia
de modelos. Replica exactamente la carga de datos, el preprocesamiento y la
particion de `03_modelos_candidatos_v2.ipynb` (misma semilla) para que el
resultado sea comparable con el resto de las configuraciones.

Notas de configuracion
----------------------
1. Tasas de aprendizaje diferenciadas: backbone 5e-5, cabeza 1e-3. La cabeza de
   clasificacion es una capa de 384 x 1234 inicializada desde cero (el reporte
   de carga la marca como MISSING), de modo que necesita avanzar mucho mas
   rapido que un backbone que solo debe ajustarse. Una tasa unica calibrada
   para el backbone deja la cabeza practicamente inmovil.
2. Tokenizacion una sola vez al inicio, no en cada __getitem__ de cada epoca:
   el tokenizador de este modelo no es "fast", y hacerlo por lote lo convierte
   en el cuello de botella del entrenamiento.
3. Longitud de secuencia derivada de los datos en lugar de un valor fijo. Las
   descripciones tienen 40 caracteres como maximo, de modo que el resto serian
   posiciones de relleno.

Uso
---
    .venv/bin/python lab/scripts/train_transformer.py
    .venv/bin/python lab/scripts/train_transformer.py --epochs 20 --head-lr 2e-3
"""

import argparse
import glob
import json
import os
import re
import time
import unicodedata
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    top_k_accuracy_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import DataLoader, TensorDataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(ROOT, "lab", "data", "xlsx")
RESULTS_DIR = os.path.join(ROOT, "lab", "results")

MODEL_NAME = "microsoft/Multilingual-MiniLM-L12-H384"
SEED = 42
MIN_SAMPLES = 3


# ── Carga de datos: identica al notebook 03 ───────────────────────────────────

def _to_str(val):
    if val is None or pd.isna(val):
        return None
    if isinstance(val, float) and val == int(val):
        return str(int(val))
    return str(val).strip()


def _extract_code(val):
    if val is None or pd.isna(val):
        return None
    s = str(val).strip()
    if " - " in s:
        return s.split(" - ")[0].strip()
    return s


def _prefix_rename(df, col_map):
    rename, used = {}, set()
    for col in df.columns:
        for src, dst in col_map.items():
            if dst in used:
                continue
            if col == src or col.startswith(src):
                rename[col] = dst
                used.add(dst)
                break
    return df.rename(columns=rename)


def preprocess_text(text: str) -> str:
    """Identica a api/app/services/text.py. Debe permanecer sincronizada."""
    text = text.upper()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[;:,/\\|]+", " ", text)
    text = re.sub(r"[^A-Z0-9.\-\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_dataset() -> pd.DataFrame:
    CLASS_COLS = {
        "Código": "class_code", "Denominación": "class_name",
        "Grupo de Artículos": "article_group", "Sector": "sector",
        "Tipo de Material": "material_type", "UNSPSC": "unspsc",
    }
    MATERIAL_COLS = {
        "Material": "material_code", "Unidad medida base": "uom",
        "Denom.estándar": "class_code", "Texto breve de material": "short_text",
    }

    all_files = glob.glob(os.path.join(DATA_DIR, "*.xlsx"))
    classes_files = [f for f in all_files if "clase" in os.path.basename(f).lower()]
    material_files = [
        f for f in all_files
        if "clase" not in os.path.basename(f).lower()
        and "unspsc" not in os.path.basename(f).lower()
        and "naciones" not in os.path.basename(f).lower()
    ]

    dfs = []
    for f in classes_files:
        dfs.append(_prefix_rename(pd.read_excel(f, dtype=str, engine="openpyxl"), CLASS_COLS))
    df_classes = pd.concat(dfs, ignore_index=True)
    df_classes["class_code"] = df_classes["class_code"].apply(_to_str)
    if "material_type" in df_classes.columns:
        df_classes["material_type"] = df_classes["material_type"].apply(_extract_code)
    df_classes = (df_classes
                  .dropna(subset=["class_code", "class_name"])
                  .drop_duplicates(subset=["class_code"]))

    dfs = []
    for f in material_files:
        df_m = _prefix_rename(pd.read_excel(f, dtype=str, engine="openpyxl"), MATERIAL_COLS)
        keep = [c for c in ["material_code", "class_code", "short_text"] if c in df_m.columns]
        dfs.append(df_m[keep].copy())
    df_materials = pd.concat(dfs, ignore_index=True)
    df_materials["material_code"] = df_materials["material_code"].apply(_to_str)
    df_materials["class_code"] = df_materials["class_code"].apply(_to_str)
    df_materials = df_materials.dropna(subset=["material_code", "short_text"])

    df = df_materials.merge(
        df_classes[["class_code", "class_name", "material_type"]],
        on="class_code", how="inner",
    )
    df = df.loc[:, ~df.columns.duplicated()]
    df["clean_text"] = df["short_text"].apply(preprocess_text)
    df = df[df["clean_text"].str.len() > 0]

    counts = df["class_code"].value_counts()
    valid = counts[counts >= MIN_SAMPLES].index
    return df[df["class_code"].isin(valid)].copy()


# ── Entrenamiento ─────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--backbone-lr", type=float, default=5e-5)
    ap.add_argument("--head-lr", type=float, default=1e-3)
    ap.add_argument("--warmup-frac", type=float, default=0.1)
    ap.add_argument("--weight-decay", type=float, default=0.01)
    ap.add_argument("--tag", type=str, default="minilm_fixed")
    args = ap.parse_args()

    torch.manual_seed(SEED)
    np.random.seed(SEED)

    device = (
        "mps" if torch.backends.mps.is_available()
        else "cuda" if torch.cuda.is_available()
        else "cpu"
    )
    print(f"Device: {device}", flush=True)

    print("Cargando datos...", flush=True)
    df = load_dataset()
    le = LabelEncoder()
    y = le.fit_transform(df["class_code"].values)
    X = df["clean_text"].values
    n_classes = len(le.classes_)
    print(f"Dataset: {len(df):,} materiales, {n_classes} clases", flush=True)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y
    )
    print(f"Train: {len(X_train):,} | Test: {len(X_test):,}", flush=True)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    print(f"Tokenizer: {type(tokenizer).__name__}", flush=True)

    # Longitud real de las secuencias: las descripciones tienen 40 caracteres
    # como maximo, de modo que 64 posiciones eran casi todo relleno.
    probe = tokenizer(list(X_train[:2000]), add_special_tokens=True)["input_ids"]
    max_len = int(min(64, max(len(t) for t in probe) + 4))
    print(f"max_len derivado de los datos: {max_len}", flush=True)

    def encode(texts):
        enc = tokenizer(
            list(texts), truncation=True, padding="max_length",
            max_length=max_len, return_tensors="pt",
        )
        return enc["input_ids"], enc["attention_mask"]

    print("Tokenizando (una sola vez)...", flush=True)
    tr_ids, tr_mask = encode(X_train)
    te_ids, te_mask = encode(X_test)

    train_loader = DataLoader(
        TensorDataset(tr_ids, tr_mask, torch.tensor(y_train, dtype=torch.long)),
        batch_size=args.batch_size, shuffle=True,
    )
    test_loader = DataLoader(
        TensorDataset(te_ids, te_mask, torch.tensor(y_test, dtype=torch.long)),
        batch_size=args.batch_size * 2, shuffle=False,
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=n_classes
    ).to(device)

    # Tasas diferenciadas: la cabeza parte de ruido y necesita avanzar mucho mas
    # rapido que el backbone, que solo debe ajustarse.
    head_params, backbone_params = [], []
    for name, p in model.named_parameters():
        (head_params if name.startswith("classifier") else backbone_params).append(p)
    print(f"Parametros: backbone={sum(p.numel() for p in backbone_params):,} "
          f"cabeza={sum(p.numel() for p in head_params):,}", flush=True)

    optimizer = torch.optim.AdamW(
        [
            {"params": backbone_params, "lr": args.backbone_lr},
            {"params": head_params, "lr": args.head_lr},
        ],
        weight_decay=args.weight_decay,
    )
    total_steps = len(train_loader) * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, int(args.warmup_frac * total_steps), total_steps
    )

    chance_loss = float(np.log(n_classes))
    print(f"\nPerdida de un clasificador aleatorio: ln({n_classes}) = {chance_loss:.4f}")
    print(f"Entrenando {args.epochs} epocas "
          f"(backbone_lr={args.backbone_lr}, head_lr={args.head_lr})...\n", flush=True)

    @torch.no_grad()
    def evaluate():
        model.eval()
        preds, probs = [], []
        for ids, mask, _ in test_loader:
            out = model(input_ids=ids.to(device), attention_mask=mask.to(device))
            p = torch.softmax(out.logits.float(), dim=-1)
            probs.append(p.cpu().numpy())
            preds.append(p.argmax(dim=-1).cpu().numpy())
        model.train()
        return np.concatenate(preds), np.concatenate(probs)

    history = []
    t0 = time.time()
    model.train()
    for epoch in range(args.epochs):
        ep_loss, correct, total = 0.0, 0, 0
        for ids, mask, labels in train_loader:
            ids, mask, labels = ids.to(device), mask.to(device), labels.to(device)
            out = model(input_ids=ids, attention_mask=mask, labels=labels)
            loss = out.loss

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()

            ep_loss += loss.item() * labels.size(0)
            correct += (out.logits.argmax(dim=-1) == labels).sum().item()
            total += labels.size(0)

        avg_loss = ep_loss / total
        train_acc = correct / total
        y_pred, _ = evaluate()
        test_acc = accuracy_score(y_test, y_pred)
        history.append({
            "epoch": epoch + 1, "loss": round(avg_loss, 4),
            "train_acc": round(train_acc, 4), "test_acc": round(test_acc, 4),
            "elapsed_s": round(time.time() - t0, 1),
        })
        print(f"  Epoca {epoch+1:2d}/{args.epochs}: loss={avg_loss:.4f} "
              f"train_acc={train_acc:.4f} test_acc={test_acc:.4f} "
              f"({time.time()-t0:.0f}s)", flush=True)

    train_seconds = time.time() - t0
    print(f"\nEntrenamiento completo: {train_seconds:.1f}s", flush=True)

    # ── Evaluacion final ──────────────────────────────────────────────────────
    y_pred, y_proba = evaluate()
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1_macro": float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_test, y_pred, average="weighted", zero_division=0)),
        "precision_weighted": float(precision_score(y_test, y_pred, average="weighted", zero_division=0)),
        "recall_weighted": float(recall_score(y_test, y_pred, average="weighted", zero_division=0)),
        "top3_accuracy": float(top_k_accuracy_score(
            y_test, y_proba, k=3, labels=list(range(n_classes)))),
        "train_seconds": round(train_seconds, 1),
    }

    print("\n" + "=" * 62)
    print("TRANSFORMER (multilingual-MiniLM)")
    print("=" * 62)
    for k, v in metrics.items():
        print(f"  {k:22s} {v:.4f}" if isinstance(v, float) else f"  {k:22s} {v}")

    # Prediccion selectiva, para comparar con el modelo desplegado.
    conf = y_proba.max(axis=1)
    ok = y_pred == y_test
    print("\n  Analisis de umbral de confianza:")
    umbrales = {}
    for t in (0.5, 0.6, 0.7, 0.8, 0.9):
        m = conf >= t
        if m.sum():
            a, c = float(ok[m].mean()), float(m.mean())
            umbrales[str(t)] = {"accuracy": round(a, 4), "cobertura": round(c, 4),
                                "n": int(m.sum())}
            print(f"    Umbral {t}: accuracy={a:.4f} cobertura={c*100:.2f}% ({m.sum():,})")

    print("\n  Comparacion con el modelo desplegado (LinearSVC + CharTFIDF):")
    print(f"    LinearSVC   accuracy=0.8491 f1_macro=0.7523 top3=0.9404 tiempo=62.9s")
    print(f"    Transformer accuracy={metrics['accuracy']:.4f} "
          f"f1_macro={metrics['f1_macro']:.4f} top3={metrics['top3_accuracy']:.4f} "
          f"tiempo={train_seconds:.1f}s")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out_path = os.path.join(RESULTS_DIR, f"transformer_{args.tag}_{stamp}.json")
    with open(out_path, "w") as f:
        json.dump({
            "model_name": MODEL_NAME,
            "config": vars(args) | {"max_len": max_len, "seed": SEED, "device": device},
            "dataset": {"n_samples": len(df), "n_classes": n_classes,
                        "n_train": len(X_train), "n_test": len(X_test)},
            "chance_loss": round(chance_loss, 4),
            "history": history,
            "metrics": metrics,
            "umbrales": umbrales,
        }, f, indent=2)
    print(f"\nResultados guardados en {out_path}")


if __name__ == "__main__":
    main()
