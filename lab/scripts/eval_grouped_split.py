"""
Evaluacion de los modelos candidatos bajo particion agrupada por descripcion.

El catalogo contiene descripciones repetidas. Una particion aleatoria reparte
registros con el mismo texto entre entrenamiento y prueba, de modo que el
modelo se evalua sobre descripciones que ya vio. Este script reproduce la
competencia del notebook 02 bajo dos protocolos:

  random   - particion aleatoria estratificada (el protocolo original)
  grouped  - particion agrupada por clean_text, ningun texto cruza la frontera

Escribe resultados incrementalmente a lab/results/grouped_split.json para que
las configuraciones rapidas esten disponibles antes de que terminen las lentas.
El archivo se lee al arrancar y se fusiona, de modo que el script puede correrse
una configuracion a la vez sin perder lo ya medido:

    python eval_grouped_split.py --config LinearSVC
    python eval_grouped_split.py --config RandomForest --protocol grouped
"""

import os
import re
import sys
import glob
import json
import time
import argparse
import tempfile
import warnings
import unicodedata

import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split, StratifiedGroupKFold
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    top_k_accuracy_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings('ignore')

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
DATA_DIR = os.path.join(LAB, 'data', 'xlsx')
OUT_DIR = os.path.join(LAB, 'results')
OUT_JSON = os.path.join(OUT_DIR, 'grouped_split.json')
os.makedirs(OUT_DIR, exist_ok=True)

STATE = {'protocols': {}, 'meta': {}}


def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)


def load_state():
    """Recupera lo ya medido para que una corrida parcial no borre las anteriores."""
    if not os.path.exists(OUT_JSON):
        return
    try:
        with open(OUT_JSON) as fh:
            prev = json.load(fh)
    except (json.JSONDecodeError, OSError) as e:
        log(f'no se pudo leer {OUT_JSON} ({e}); se empieza de cero')
        return
    STATE['meta'] = prev.get('meta', {})
    STATE['protocols'] = prev.get('protocols', {})
    ya = sum(len(v) for v in STATE['protocols'].values())
    if ya:
        log(f'resultados previos recuperados: {ya} configuracion(es)')


def flush():
    with open(OUT_JSON, 'w') as fh:
        json.dump(STATE, fh, indent=2, default=str)


# --------------------------------------------------------------------------
# Carga de datos (identica al notebook 02)
# --------------------------------------------------------------------------

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
    return s.split(' - ')[0].strip() if ' - ' in s else s


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


def preprocess_text(text):
    text = text.upper()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[;:,/\\|]+', ' ', text)
    text = re.sub(r'[^A-Z0-9.\-\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def load_dataset():
    all_files = glob.glob(os.path.join(DATA_DIR, '*.xlsx'))
    classes_files, material_files = [], []
    for f in all_files:
        name = os.path.basename(f).lower()
        if 'clase' in name:
            classes_files.append(f)
        elif 'unspsc' in name or 'naciones' in name:
            pass
        else:
            material_files.append(f)

    CLASS_COLS = {
        'Código': 'class_code', 'Denominación': 'class_name',
        'Grupo de Artículos': 'article_group', 'Sector': 'sector',
        'Tipo de Material': 'material_type', 'UNSPSC': 'unspsc',
    }
    dfs = []
    for f in classes_files:
        dfs.append(_prefix_rename(pd.read_excel(f, dtype=str, engine='openpyxl'), CLASS_COLS))
    df_classes = pd.concat(dfs, ignore_index=True)
    df_classes['class_code'] = df_classes['class_code'].apply(_to_str)
    if 'material_type' in df_classes.columns:
        df_classes['material_type'] = df_classes['material_type'].apply(_extract_code)
    df_classes = (df_classes.dropna(subset=['class_code', 'class_name'])
                            .drop_duplicates(subset=['class_code']))

    MATERIAL_COLS = {
        'Material': 'material_code', 'Unidad medida base': 'uom',
        'Denom.estándar': 'class_code', 'Texto breve de material': 'short_text',
    }
    dfs = []
    for f in material_files:
        d = _prefix_rename(pd.read_excel(f, dtype=str, engine='openpyxl'), MATERIAL_COLS)
        keep = [c for c in ['material_code', 'class_code', 'short_text'] if c in d.columns]
        d = d[keep].copy()
        d['source_file'] = os.path.basename(f)
        dfs.append(d)
    df_materials = pd.concat(dfs, ignore_index=True)
    df_materials['material_code'] = df_materials['material_code'].apply(_to_str)
    df_materials['class_code'] = df_materials['class_code'].apply(_to_str)
    df_materials = df_materials.dropna(subset=['material_code', 'short_text'])

    df = df_materials.merge(
        df_classes[['class_code', 'class_name', 'material_type']],
        on='class_code', how='inner')
    df = df.loc[:, ~df.columns.duplicated()]
    df['clean_text'] = df['short_text'].apply(preprocess_text)

    counts = df['class_code'].value_counts()
    valid = counts[counts >= 3].index
    df_model = df[df['class_code'].isin(valid)].copy()

    log(f'maestro cargado: {len(df_materials):,} | con clase: {len(df):,} '
        f'| conjunto de modelado: {len(df_model):,} ({df_model["class_code"].nunique()} clases)')
    return df_model


# --------------------------------------------------------------------------
# Particiones
# --------------------------------------------------------------------------

def make_splits(df_model):
    le = LabelEncoder()
    y = le.fit_transform(df_model['class_code'].values)
    X = df_model['clean_text'].values
    groups = df_model['clean_text'].values

    idx = np.arange(len(X))
    tr_r, te_r = train_test_split(idx, test_size=0.2, random_state=42, stratify=y)

    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    tr_g, te_g = next(sgkf.split(X, y, groups=groups))

    overlap = len(set(X[te_r]) & set(X[tr_r]))
    leak_rows = np.isin(X[te_r], np.unique(X[tr_r])).mean()
    leak_rows_g = np.isin(X[te_g], np.unique(X[tr_g])).mean()

    STATE['meta'] = {
        'n_total': int(len(X)),
        'n_classes': int(len(le.classes_)),
        'random': {'n_train': int(len(tr_r)), 'n_test': int(len(te_r)),
                   'classes_in_test': int(len(np.unique(y[te_r]))),
                   'test_rows_seen_in_train_pct': round(float(leak_rows) * 100, 2)},
        'grouped': {'n_train': int(len(tr_g)), 'n_test': int(len(te_g)),
                    'classes_in_test': int(len(np.unique(y[te_g]))),
                    'test_rows_seen_in_train_pct': round(float(leak_rows_g) * 100, 2)},
    }
    log(f'random  : train {len(tr_r):,} test {len(te_r):,} | fuga {leak_rows*100:.2f}%')
    log(f'grouped : train {len(tr_g):,} test {len(te_g):,} | fuga {leak_rows_g*100:.2f}%')
    flush()
    return X, y, le, {'random': (tr_r, te_r), 'grouped': (tr_g, te_g)}


# --------------------------------------------------------------------------
# fastText con interfaz sklearn
# --------------------------------------------------------------------------

def _parchar_fasttext():
    """
    `FastText.predict` llama `np.array(probs, copy=False)` (FastText.py:232), que
    numpy 2 rechaza. Se sustituye `np.array` en el espacio de nombres del modulo
    por `np.asarray`, que es la migracion que la propia excepcion recomienda.

    Envolver `predict` desde fuera no sirve: la llamada ofensora esta dentro. Es
    el mismo parche de la celda 15 del notebook 03, no el de la celda 14.
    """
    import fasttext.FastText as _ft
    if getattr(_ft, '_gamma_patched', False):
        return
    _ft.np.array = lambda obj, *a, **kw: np.asarray(obj)
    _ft._gamma_patched = True


class FastTextClassifier:
    """
    Envoltura de `fasttext.train_supervised` con la interfaz que espera
    `evaluate()`: `fit`, `predict`, `predict_proba` y `classes_`.

    Los hiperparametros son los de la celda 13 del notebook 03. Las etiquetas se
    escriben como el entero codificado en lugar del `class_code` original: para
    fastText la etiqueta es un token opaco, de modo que el resultado es
    identico, y asi ningun codigo con espacios puede romper el formato del
    archivo.
    """

    def __init__(self, epoch=50, lr=0.5, word_ngrams=2, minn=2, maxn=5,
                 dim=100, loss='softmax', bucket=2000000):
        self.epoch, self.lr, self.word_ngrams = epoch, lr, word_ngrams
        self.minn, self.maxn, self.dim = minn, maxn, dim
        self.loss, self.bucket = loss, bucket

    def fit(self, X, y):
        import fasttext
        _parchar_fasttext()
        self.classes_ = np.unique(y)
        self._pos = {int(c): j for j, c in enumerate(self.classes_)}

        fd, path = tempfile.mkstemp(suffix='.txt', prefix='ft_train_')
        try:
            with os.fdopen(fd, 'w') as fh:
                for texto, etiqueta in zip(X, y):
                    fh.write(f'__label__{int(etiqueta)} {texto}\n')
            self._model = fasttext.train_supervised(
                input=path, epoch=self.epoch, lr=self.lr,
                wordNgrams=self.word_ngrams, minn=self.minn, maxn=self.maxn,
                dim=self.dim, loss=self.loss, bucket=self.bucket,
                thread=os.cpu_count(), verbose=0)
        finally:
            os.unlink(path)
        return self

    def predict_proba(self, X):
        k = len(self.classes_)
        out = np.zeros((len(X), k))
        for i, texto in enumerate(X):
            etiquetas, probs = self._model.predict(texto, k=k)
            for etiqueta, p in zip(etiquetas, np.asarray(probs)):
                j = self._pos.get(int(etiqueta.replace('__label__', '')))
                if j is not None:
                    out[i, j] = p
        return out

    def predict(self, X):
        return self.classes_[self.predict_proba(X).argmax(axis=1)]


# --------------------------------------------------------------------------
# Calibracion bajo particion agrupada
# --------------------------------------------------------------------------

CV_CALIBRACION = 2


def recorta_para_calibracion(tr, y, cv=CV_CALIBRACION):
    """
    Excluye del entrenamiento las clases que no alcanzan `cv` ejemplos.

    `CalibratedClassifierCV` estratifica internamente y exige al menos tantos
    ejemplos por clase como pliegues. El filtro de clases raras del conjunto de
    modelado (>=3 ejemplos) garantiza ese minimo cuando la particion es
    estratificada, pero no cuando es agrupada: al no poder separar registros que
    comparten descripcion, una clase puede llegar al entrenamiento con un solo
    ejemplo. `safe_cv` de la API no resuelve el caso porque su piso es 2.

    El recorte se aplica igual en ambos protocolos —en el aleatorio no excluye
    nada— para que la comparacion no dependa del tratamiento. La clase excluida
    desaparece del espacio de salida y sus registros de prueba cuentan como
    error, que es el costo honesto del protocolo y queda registrado en el JSON.
    """
    vals, counts = np.unique(y[tr], return_counts=True)
    insuficientes = vals[counts < cv]
    if not len(insuficientes):
        return tr, {'clases_excluidas': 0, 'filas_excluidas': 0}
    mask = ~np.isin(y[tr], insuficientes)
    return tr[mask], {
        'clases_excluidas': int(len(insuficientes)),
        'filas_excluidas': int((~mask).sum()),
        'cv_calibracion': int(cv),
    }


# --------------------------------------------------------------------------
# Configuraciones
# --------------------------------------------------------------------------

def build_configs():
    """(nombre, factory, calibra) — `calibra` marca las que llevan CV interno."""
    return [
        ('LinearSVC + CharTFIDF', True, lambda: Pipeline([
            ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 5),
                                      max_features=50000, sublinear_tf=True,
                                      strip_accents='unicode')),
            ('clf', CalibratedClassifierCV(LinearSVC(max_iter=2000, C=1.0),
                                           cv=CV_CALIBRACION)),
        ])),
        ('RandomForest + WordTFIDF', False, lambda: Pipeline([
            ('tfidf', TfidfVectorizer(analyzer='word', ngram_range=(1, 2),
                                      max_features=30000, sublinear_tf=True,
                                      strip_accents='unicode')),
            ('clf', RandomForestClassifier(n_estimators=300, max_depth=None,
                                           n_jobs=-1, random_state=42)),
        ])),
        ('LogReg + WordTFIDF', False, lambda: Pipeline([
            ('tfidf', TfidfVectorizer(analyzer='word', ngram_range=(1, 2),
                                      max_features=30000, sublinear_tf=True,
                                      strip_accents='unicode')),
            ('clf', LogisticRegression(max_iter=1000, C=5.0, solver='saga', n_jobs=-1)),
        ])),
        # fastText no usa TF-IDF: aprende sus propios embeddings de subpalabras
        # sobre el texto crudo, de modo que entra sin Pipeline.
        ('fastText', False, lambda: FastTextClassifier()),
        ('LogReg + CharTFIDF', False, lambda: Pipeline([
            ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 5),
                                      max_features=50000, sublinear_tf=True,
                                      strip_accents='unicode')),
            ('clf', LogisticRegression(max_iter=1000, C=5.0, solver='saga', n_jobs=-1)),
        ])),
    ]


def evaluate(name, pipe, X, y, tr, te, n_classes, class_names, extras, calibra=False):
    recorte = {'clases_excluidas': 0, 'filas_excluidas': 0}
    if calibra:
        tr, recorte = recorta_para_calibracion(tr, y)
        if recorte['clases_excluidas']:
            log(f'  recorte de calibracion: -{recorte["clases_excluidas"]} clase(s), '
                f'-{recorte["filas_excluidas"]} fila(s) del entrenamiento')

    t0 = time.time()
    pipe.fit(X[tr], y[tr])
    train_time = time.time() - t0

    y_pred = pipe.predict(X[te])
    y_true = y[te]

    out = {
        'accuracy': float(accuracy_score(y_true, y_pred)),
        'f1_macro': float(f1_score(y_true, y_pred, average='macro', zero_division=0)),
        'f1_weighted': float(f1_score(y_true, y_pred, average='weighted', zero_division=0)),
        'precision_weighted': float(precision_score(y_true, y_pred, average='weighted', zero_division=0)),
        'recall_weighted': float(recall_score(y_true, y_pred, average='weighted', zero_division=0)),
        'train_time': round(train_time, 1),
        'n_errors': int((y_pred != y_true).sum()),
        'n_test': int(len(y_true)),
        'n_train': int(len(tr)),
        'clases_en_train': int(len(np.unique(y[tr]))),
        'recorte_calibracion': recorte,
    }

    if hasattr(pipe, 'predict_proba'):
        proba = pipe.predict_proba(X[te])
        # El modelo puede no cubrir las 1,234 clases (recorte de calibracion, o
        # clases ausentes del train). Se expande a ancho completo con probabilidad
        # cero en las faltantes para que top-3 se mida sobre el espacio completo.
        if proba.shape[1] != n_classes:
            full = np.zeros((proba.shape[0], n_classes), dtype=proba.dtype)
            full[:, pipe.classes_] = proba
            proba = full
        out['top3_accuracy'] = float(top_k_accuracy_score(
            y_true, proba, k=3, labels=list(range(n_classes))))
        if extras:
            conf = proba.max(axis=1)
            thr = {}
            for t in (0.5, 0.6, 0.7, 0.8, 0.9):
                m = conf >= t
                thr[str(t)] = {
                    'accuracy': float(accuracy_score(y_true[m], y_pred[m])) if m.sum() else None,
                    'coverage': round(float(m.mean()) * 100, 2),
                    'n': int(m.sum()),
                }
            out['thresholds'] = thr
            err = y_pred != y_true
            pairs = pd.DataFrame({'real': y_true[err], 'pred': y_pred[err]})
            top = pairs.groupby(['real', 'pred']).size().sort_values(ascending=False).head(10)
            out['top_confusions'] = [
                {'real': class_names.get(int(r), str(r)),
                 'pred': class_names.get(int(p), str(p)), 'n': int(c)}
                for (r, p), c in top.items()
            ]
    else:
        out['top3_accuracy'] = None

    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config', default=None,
                    help='corre solo las configuraciones cuyo nombre contenga este texto')
    ap.add_argument('--protocol', default=None, choices=['grouped', 'random'],
                    help='corre solo este protocolo (por defecto, ambos)')
    args = ap.parse_args()

    load_state()

    df_model = load_dataset()
    X, y, le, splits = make_splits(df_model)
    n_classes = len(le.classes_)

    code_to_name = (df_model.drop_duplicates('class_code')
                            .set_index('class_code')['class_name'].to_dict())
    class_names = {i: code_to_name.get(code, code) for i, code in enumerate(le.classes_)}

    configs = build_configs()
    if args.config:
        configs = [c for c in configs if args.config.lower() in c[0].lower()]
        if not configs:
            log(f'ninguna configuracion coincide con "{args.config}"')
            return
    protocols = (args.protocol,) if args.protocol else ('grouped', 'random')
    log(f'a correr: {len(configs) * len(protocols)} celda(s) '
        f'-> {[c[0] for c in configs]} x {list(protocols)}')

    for protocol in protocols:
        tr, te = splits[protocol]
        STATE['protocols'].setdefault(protocol, {})
        for name, calibra, factory in configs:
            log(f'{protocol:8s} | {name} ...')
            try:
                res = evaluate(name, factory(), X, y, tr, te, n_classes,
                               class_names, extras=name.startswith('LinearSVC'),
                               calibra=calibra)
                STATE['protocols'][protocol][name] = res
                log(f'{protocol:8s} | {name}: acc={res["accuracy"]:.4f} '
                    f'f1m={res["f1_macro"]:.4f} f1w={res["f1_weighted"]:.4f} '
                    f'top3={res.get("top3_accuracy")} t={res["train_time"]}s')
            except Exception as e:
                log(f'FALLO {protocol}/{name}: {type(e).__name__}: {e}')
                STATE['protocols'][protocol][name] = {'error': f'{type(e).__name__}: {e}'}
            flush()

    log('LISTO')
    flush()


if __name__ == '__main__':
    main()
