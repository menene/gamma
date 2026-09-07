#!/usr/bin/env python3
"""Genera guion.md a partir de presentation.html.

Formato pensado para practicar: se corre el deck y se lee este archivo en
paralelo. Solo lleva lo que hay que decir en voz alta — ni tiempos, ni el
texto que ya se ve proyectado.

El deck es la unica fuente de verdad. Correr despues de cada edicion:

    python3 build_guion.py
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

DECK = Path(__file__).with_name("presentation.html")
OUT = Path(__file__).with_name("guion.md")

SECTION_RE = re.compile(r"<!--\s*═+\s*(.*?)\s*═+\s*-->")
SLIDE_RE = re.compile(r"(?ms)^<section\b.*?^</section>")
NOTES_RE = re.compile(r'<aside class="notes">(.*?)</aside>', re.S)
CUE_RE = re.compile(r'<b class="cue">(.*?)</b>', re.S)


def lines_of(fragment: str) -> list[str]:
    """Aplana HTML a parrafos de texto, uno por linea."""
    f = re.sub(r"<br\s*/?>", " ", fragment)
    f = re.sub(r"</(p|li|h1|h2|div)>", "\n", f)
    f = re.sub(r"<[^>]+>", "", f)
    out: list[str] = []
    for raw in f.split("\n"):
        line = re.sub(r"\s+", " ", html.unescape(raw)).strip()
        if line:
            out.append(line)
    return out


def main() -> None:
    src = DECK.read_text(encoding="utf-8")
    body = src.split('<div class="slides">', 1)[1].rsplit("</div>", 2)[0]

    marks = list(SECTION_RE.finditer(body))
    blocks = [
        (mk.group(1).strip(),
         body[mk.end(): marks[i + 1].start() if i + 1 < len(marks) else len(body)])
        for i, mk in enumerate(marks)
    ]

    out = [
        "# GAMMA — guion de la defensa",
        "",
        "> Este archivo y `presentation.html` estan sincronizados. Se puede editar cualquiera",
        "> de los dos; despues hay que correr el script de la direccion correspondiente:",
        ">",
        "> - editaste el **deck** -> `python3 build_guion.py`",
        "> - editaste el **guion** -> `python3 apply_guion.py`",
        "",
        "Solo lo que se dice en voz alta. Los numeros corresponden a las laminas del deck.",
        "El reparto (quien dice cada lamina) todavia no esta asignado.",
        
        "",
    ]

    n = 0
    for title, block in blocks:
        out += ["---", "", f"# {title}", ""]
        for chunk in SLIDE_RE.findall(block):
            n += 1
            m = NOTES_RE.search(chunk)
            notes = lines_of(m.group(1)) if m else []
            if notes and CUE_RE.search(chunk):
                notes = notes[1:]          # la pista de orador/tiempo no se dice en voz alta
            out += [f"### {n:02d}", ""]
            out += notes if notes else ["_(sin nota)_"]
            out += [""]

    nuevo = "\n".join(out)
    if OUT.exists() and OUT.read_text(encoding="utf-8") != nuevo:
        # Protege contra el caso real de perder ediciones: si alguien edito
        # guion.md despues de tocar el deck, esos cambios se irian en silencio.
        if OUT.stat().st_mtime > DECK.stat().st_mtime and "--force" not in sys.argv:
            print(f"ABORTADO: {OUT.name} se edito despues que el deck y se perderia.")
            print("Pasa esos cambios a los <aside class=\"notes\"> de presentation.html,")
            print("o vuelve a correr con --force para descartarlos.")
            raise SystemExit(1)
    OUT.write_text(nuevo, encoding="utf-8")
    print(f"{OUT.name}: {n} laminas, {len(blocks)} bloques")


if __name__ == "__main__":
    main()
