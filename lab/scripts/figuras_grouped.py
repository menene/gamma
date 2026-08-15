"""
Regenera las tres figuras del capitulo de modelos bajo la particion agrupada.

Reemplaza las versiones producidas por el notebook 02, que se midieron sobre la
particion aleatoria. Conserva el estilo, los titulos y la composicion de las
originales para que el documento no cambie de aspecto.

    nb02_cell29.png  comparacion de metricas de la primera ronda
    nb02_cell33.png  matriz de confusion del modelo seleccionado (top 20)
    nb02_cell36.png  distribucion de confianza y compromiso exactitud/cobertura

Uso
---
    .venv/bin/python lab/scripts/figuras_grouped.py
"""

import os
import sys
import json

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score, confusion_matrix,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval_grouped_split as egs

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, 'docs', 'informe', 'figuras', 'modelos')

sns.set_theme(style='whitegrid')

# Mismo orden y color que la figura original del notebook 02.
PALETA = {
    'LogReg + WordTFIDF': '#66c2a5',
    'LinearSVC + CharTFIDF': '#fc8d62',
    'RandomForest + WordTFIDF': '#8da0cb',
    'LogReg + CharTFIDF': '#e78ac3',
}
METRICAS = [
    ('Accuracy', 'accuracy'),
    ('F1 Macro', 'f1_macro'),
    ('F1 Weighted', 'f1_weighted'),
    ('Precision', 'precision_weighted'),
    ('Recall', 'recall_weighted'),
]


def figura_comparacion(resultados):
    fig, ax = plt.subplots(figsize=(12, 6))
    modelos = list(PALETA)
    n = len(modelos)
    x = np.arange(len(METRICAS))
    ancho = 0.8 / n

    for i, nombre in enumerate(modelos):
        vals = [resultados[nombre][clave] for _, clave in METRICAS]
        ax.bar(x + i * ancho - 0.4 + ancho / 2, vals, ancho,
               label=nombre, color=PALETA[nombre])

    ax.axhline(0.80, color='gray', linestyle='--', linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels([etiqueta for etiqueta, _ in METRICAS])
    ax.set_ylabel('Score')
    ax.set_title('Comparacion de Modelos')
    ax.set_ylim(0, 1.05)
    ax.legend(loc='lower right')
    fig.tight_layout()
    ruta = os.path.join(OUT_DIR, 'nb02_cell29.png')
    fig.savefig(ruta, dpi=110)
    plt.close(fig)
    print(f'  {ruta}')


def figura_confusion(y_true, y_pred, nombres):
    conteo = pd.Series(y_true).value_counts().head(20)
    top = list(conteo.index)
    etiquetas = [nombres.get(int(c), str(c)) for c in top]

    mask = np.isin(y_true, top)
    cm = confusion_matrix(y_true[mask], y_pred[mask], labels=top)

    fig, ax = plt.subplots(figsize=(14, 12))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', square=True,
                xticklabels=etiquetas, yticklabels=etiquetas,
                linewidths=0.5, linecolor='#f0f0f0', ax=ax)
    ax.set_xlabel('Prediccion')
    ax.set_ylabel('Real')
    ax.set_title('Matriz de Confusion - Top 20 Clases (LinearSVC + CharTFIDF)')
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    plt.setp(ax.get_yticklabels(), rotation=0)
    fig.tight_layout()
    ruta = os.path.join(OUT_DIR, 'nb02_cell33.png')
    fig.savefig(ruta, dpi=110)
    plt.close(fig)
    print(f'  {ruta}')


def figura_confianza(y_true, y_pred, conf):
    fig, (izq, der) = plt.subplots(1, 2, figsize=(14, 5))

    ok = y_pred == y_true
    bins = np.linspace(conf.min(), conf.max(), 45)
    izq.hist([conf[ok], conf[~ok]], bins=bins, stacked=True,
             color=['#2ca02c', '#d62728'], label=['Correctas', 'Incorrectas'])
    izq.set_xlabel('Confianza')
    izq.set_ylabel('Frecuencia')
    izq.set_title('Distribucion de Confianza')
    izq.legend(loc='upper left')

    umbrales = np.arange(0.10, conf.max(), 0.05)
    exact, cobertura = [], []
    for t in umbrales:
        m = conf >= t
        exact.append(accuracy_score(y_true[m], y_pred[m]) if m.sum() else np.nan)
        cobertura.append(m.mean())

    der.plot(umbrales, exact, marker='o', color='#1f77b4', label='Accuracy')
    der.set_xlabel('Umbral de Confianza')
    der.set_ylabel('Accuracy', color='#1f77b4')
    der.tick_params(axis='y', labelcolor='#1f77b4')
    der.set_title('Accuracy vs Cobertura por Umbral')
    der.legend(loc='lower left')

    gemelo = der.twinx()
    gemelo.plot(umbrales, cobertura, marker='s', linestyle='--',
                color='#d62728', label='Cobertura')
    gemelo.set_ylabel('Cobertura', color='#d62728')
    gemelo.tick_params(axis='y', labelcolor='#d62728')
    gemelo.grid(False)
    gemelo.legend(loc='lower right')

    fig.tight_layout()
    ruta = os.path.join(OUT_DIR, 'nb02_cell36.png')
    fig.savefig(ruta, dpi=110)
    plt.close(fig)
    print(f'  {ruta}')


GANADOR = 'LinearSVC + CharTFIDF'


def main():
    # La comparacion de metricas se dibuja con los valores ya medidos en
    # grouped_split.json: no hace falta reentrenar para redibujar un resumen.
    with open(egs.OUT_JSON) as fh:
        resultados = json.load(fh)['protocols']['grouped']
    faltan = [m for m in PALETA if m not in resultados]
    if faltan:
        raise SystemExit(f'faltan resultados en {egs.OUT_JSON}: {faltan}')
    egs.log('generando comparacion desde resultados guardados...')
    figura_comparacion(resultados)

    # Las otras dos necesitan la prediccion y la probabilidad de cada fila de
    # prueba, que el resumen no contiene. Un solo entrenamiento sirve para ambas.
    #
    # `load_state` es obligatorio antes de `make_splits`: esta ultima hace flush
    # del STATE del modulo, de modo que sin recuperar primero lo ya medido el
    # archivo de resultados se sobrescribe con un STATE vacio.
    egs.load_state()
    df = egs.load_dataset()
    X, y, le, splits = egs.make_splits(df)
    tr, te = splits['grouped']

    code_to_name = (df.drop_duplicates('class_code')
                      .set_index('class_code')['class_name'].to_dict())
    nombres = {i: code_to_name.get(c, c) for i, c in enumerate(le.classes_)}

    nombre, calibra, factory = next(
        c for c in egs.build_configs() if c[0] == GANADOR)
    tr_i, _ = egs.recorta_para_calibracion(tr, y) if calibra else (tr, None)
    egs.log(f'entrenando {nombre} (unica vez) ...')
    pipe = factory().fit(X[tr_i], y[tr_i])
    pred = pipe.predict(X[te])
    conf = pipe.predict_proba(X[te]).max(axis=1)

    egs.log('generando figuras del modelo seleccionado...')
    figura_confusion(y[te], pred, nombres)
    figura_confianza(y[te], pred, conf)
    egs.log('LISTO')


if __name__ == '__main__':
    main()
