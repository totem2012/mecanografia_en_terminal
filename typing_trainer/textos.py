"""Carga de las citas internas y de textos propios del usuario."""

import json
import random
import re
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE = Path(sys._MEIPASS)
else:
    BASE = Path(__file__).resolve().parent.parent
RUTA_CITAS = BASE / "data" / "citas.json"


def cargar_citas():
    """Devuelve la lista de citas internas [{texto, autor}, ...]."""
    with open(RUTA_CITAS, encoding="utf-8") as f:
        return json.load(f)


def cita_aleatoria(citas, evitar_texto=None):
    """Elige una cita al azar, evitando repetir la última si es posible."""
    if len(citas) > 1 and evitar_texto is not None:
        opciones = [c for c in citas if c["texto"] != evitar_texto]
        return random.choice(opciones or citas)
    return random.choice(citas)


def _normalizar(texto):
    """Colapsa espacios/saltos de línea en espacios simples."""
    return re.sub(r"\s+", " ", texto).strip()


def trocear_texto(texto, maximo=240):
    """Divide un texto largo en fragmentos legibles (~maximo caracteres),
    cortando por frases para que cada práctica tenga sentido."""
    texto = _normalizar(texto)
    if not texto:
        return []
    frases = re.split(r"(?<=[.!?…])\s+", texto)
    fragmentos = []
    actual = ""
    for frase in frases:
        if not actual:
            actual = frase
        elif len(actual) + 1 + len(frase) <= maximo:
            actual += " " + frase
        else:
            fragmentos.append(actual)
            actual = frase
        # Si una sola frase ya excede el máximo, se parte por palabras.
        while len(actual) > maximo:
            corte = actual.rfind(" ", 0, maximo)
            corte = corte if corte > 0 else maximo
            fragmentos.append(actual[:corte].strip())
            actual = actual[corte:].strip()
    if actual:
        fragmentos.append(actual)
    return fragmentos


def cargar_texto_propio(ruta):
    """Lee un archivo .txt del usuario y lo devuelve troceado.

    Lanza FileNotFoundError o ValueError (si está vacío)."""
    p = Path(ruta).expanduser()
    if not p.is_file():
        raise FileNotFoundError(ruta)
    contenido = p.read_text(encoding="utf-8", errors="replace")
    fragmentos = trocear_texto(contenido)
    if not fragmentos:
        raise ValueError("El archivo no contiene texto utilizable.")
    return fragmentos
