#!/usr/bin/env python3
"""Escribe guion.md de vuelta dentro de presentation.html.

Es la direccion inversa de build_guion.py. Los dos scripts mantienen
sincronizados el deck y el guion; se usa el que corresponda segun donde se
haya editado:

    python3 build_guion.py     deck  -> guion.md   (el deck manda)
    python3 apply_guion.py     guion -> deck       (el guion manda)

Empareja por posicion: el bloque «### 07» del guion es la septima lamina del
deck. Solo toca el texto de los <aside class="notes">; no altera ninguna
lamina, ni la pista de tiempos, ni el resto del HTML.
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

DECK = Path(__file__).with_name("presentation.html")
SRC = Path(__file__).with_name("guion.md")

SLIDE_RE = re.compile(r"(?ms)^<section\b.*?^</section>")
NOTES_RE = re.compile(r'(<aside class="notes">\s*)(.*?)(\s*</aside>)', re.S)
CUE_RE = re.compile(r'<b class="cue">.*?</b>', re.S)
HEAD_RE = re.compile(r"^###\s*(\d+)\s*$", re.M)


def bloques_del_guion(texto: str) -> list[str]:
    """Devuelve el texto hablado de cada lamina, en orden."""
    marcas = list(HEAD_RE.finditer(texto))
    out = []
    for i, mk in enumerate(marcas):
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
        cuerpo = texto[mk.end(): fin]
        # Corta en el encabezado del siguiente bloque (--- / # TITULO)
        cuerpo = re.split(r"(?m)^---\s*$", cuerpo)[0]
        lineas = [l.rstrip() for l in cuerpo.strip().split("\n")]
        out.append([l for l in lineas if l and l != "_(sin nota)_"])
    return out


def main() -> None:
    deck = DECK.read_text(encoding="utf-8")
    bloques = bloques_del_guion(SRC.read_text(encoding="utf-8"))
    laminas = SLIDE_RE.findall(deck)

    if len(bloques) != len(laminas):
        print(f"ABORTADO: {SRC.name} tiene {len(bloques)} bloques y el deck "
              f"{len(laminas)} laminas. Deben coincidir.")
        print("Si agregaste o quitaste laminas, corre build_guion.py --force primero.")
        raise SystemExit(1)

    cambiadas = 0
    nuevo = deck
    for lamina, lineas in zip(laminas, bloques):
        m = NOTES_RE.search(lamina)
        if not m:
            continue
        cue = CUE_RE.search(m.group(2))
        cuerpo = "\n".join("    " + html.escape(l, quote=False) for l in lineas)
        if cue:
            cuerpo = "    " + cue.group(0) + ("\n" + cuerpo if cuerpo else "")
        actualizada = lamina.replace(m.group(0), m.group(1) + cuerpo.strip() + m.group(3), 1)
        if actualizada != lamina:
            nuevo = nuevo.replace(lamina, actualizada, 1)
            cambiadas += 1

    if not cambiadas:
        print("Sin cambios: el deck ya coincide con el guion.")
        return
    if "--dry-run" in sys.argv:
        print(f"{cambiadas} laminas cambiarian. No se escribio nada (--dry-run).")
        return
    DECK.write_text(nuevo, encoding="utf-8")
    print(f"{DECK.name}: {cambiadas} laminas actualizadas desde {SRC.name}")


if __name__ == "__main__":
    main()
