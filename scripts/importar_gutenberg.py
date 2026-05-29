#!/usr/bin/env python3
"""Importador de textos de dominio público (Project Gutenberg) -> data/citas.json

Descarga varias obras en español, elimina las cabeceras/licencia de Gutenberg,
trocea el texto en fragmentos coherentes (frases con sentido) y los filtra por
calidad para alimentar el entrenador de mecanografía.

Uso:
    python3 scripts/importar_gutenberg.py

Requiere conexión SOLO al ejecutarse (la app sigue funcionando offline después).
Todas las obras incluidas son de dominio público.
"""

import json
import re
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DESTINO = BASE / "data" / "citas.json"
SEMILLA = BASE / "data" / "citas_curadas.json"   # citas célebres curadas a mano
CACHE = BASE / "data" / ".descargas"

# (id Gutenberg, autor, obra) — todas de dominio público
OBRAS = [
    (2000,  "Miguel de Cervantes",     "Don Quijote de la Mancha"),
    (55514, "Emilia Pardo Bazán",      "Cuentos de amor"),
    (52597, "Emilia Pardo Bazán",      "Insolación y Morriña"),
    (25640, "Vicente Blasco Ibáñez",   "Los argonautas"),
    (26983, "Vicente Blasco Ibáñez",   "Sangre y arena"),
    (25777, "Armando Palacio Valdés",  "El idilio de un enfermo"),
    (27738, "Armando Palacio Valdés",  "José"),
    (23600, "Fernán Caballero",        "La gaviota"),
    (78052, "Miguel de Unamuno",       "Andanzas y visiones españolas"),
    (61851, "Fiódor Dostoyevski",      "Crimen y castigo"),
]

MAX_POR_OBRA = 500             # tope de fragmentos por obra
MIN_LEN, MAX_LEN = 100, 250    # longitud de cada fragmento
MIN_PALABRAS = 14

UA = "Mozilla/5.0 (compatible; importador-mecanografia/1.0)"
RE_INICIO = re.compile(r"\*\*\*\s*START OF (THE|THIS)? ?PROJECT GUTENBERG.*?\*\*\*", re.I | re.S)
RE_FIN = re.compile(r"\*\*\*\s*END OF (THE|THIS)? ?PROJECT GUTENBERG.*?\*\*\*", re.I | re.S)
RE_FRASE = re.compile(r"(?<=[.!?…])\s+")
RE_ESPACIOS = re.compile(r"\s+")
RE_NOTAS = re.compile(r"\[[^\]]*\]")   # notas al pie/ilustraciones: [1], [1.4], [Ilustración]
RE_ESPACIO_ANTES = re.compile(r"\s+([,.;:!?…])")  # espacio sobrante antes de puntuación
RE_ENCABEZADO = re.compile(
    r"^(cap[ií]tulo|tomo|parte|libro|secci[oó]n|acto|escena|prólogo|"
    r"ep[ií]logo|introducci[oó]n|[ivxlcdm]+)\b", re.I)


def url_texto(gid):
    """Obtiene la URL de texto plano UTF-8 vía Gutendex."""
    api = f"https://gutendex.com/books/{gid}/"
    req = urllib.request.Request(api, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        meta = json.load(r)
    fmts = meta["formats"]
    # Preferir UTF-8; descartar .zip
    candidatos = [u for k, u in fmts.items()
                  if "text/plain" in k and not u.endswith(".zip")]
    utf8 = [u for u in candidatos if "utf-8" in u or "utf8" in u]
    return (utf8 or candidatos)[0]


def descargar(gid):
    """Descarga (con caché local) el texto plano de una obra."""
    CACHE.mkdir(parents=True, exist_ok=True)
    destino = CACHE / f"{gid}.txt"
    if destino.is_file() and destino.stat().st_size > 1000:
        return destino.read_text(encoding="utf-8", errors="replace")
    url = url_texto(gid)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        datos = r.read().decode("utf-8", errors="replace")
    destino.write_text(datos, encoding="utf-8")
    time.sleep(1.0)  # cortesía con el servidor
    return datos


def quitar_envoltorio(texto):
    """Elimina cabecera y pie de licencia de Project Gutenberg."""
    m = RE_INICIO.search(texto)
    if m:
        texto = texto[m.end():]
    m = RE_FIN.search(texto)
    if m:
        texto = texto[:m.start()]
    return texto


def es_fragmento_valido(frag):
    if not (MIN_LEN <= len(frag) <= MAX_LEN):
        return False
    if not frag[0].isupper() and frag[0] not in "«¿¡—":
        return False
    if frag[-1] not in ".!?…»":
        return False
    palabras = frag.split()
    if len(palabras) < MIN_PALABRAS:
        return False
    letras = [c for c in frag if c.isalpha()]
    if not letras:
        return False
    # Descartar encabezados/cosas en mayúsculas
    if sum(c.isupper() for c in letras) / len(letras) > 0.30:
        return False
    # Debe tener proporción alta de letras (no tablas/números)
    if len(letras) / len(frag) < 0.65:
        return False
    bajo = frag.lower()
    if any(t in bajo for t in ("gutenberg", "http", "www.", "ebook", "©")):
        return False
    return True


def trocear(texto):
    """Convierte el cuerpo de una obra en fragmentos limpios y coherentes."""
    fragmentos = []
    for parrafo in re.split(r"\n\s*\n", texto):
        p = parrafo.replace("_", "")           # marcas de cursiva de Gutenberg
        p = RE_NOTAS.sub("", p)                # notas al pie / ilustraciones
        p = RE_ESPACIOS.sub(" ", p).strip()
        p = RE_ESPACIO_ANTES.sub(r"\1", p)     # limpiar espacio antes de puntuación
        if len(p) < 60 or RE_ENCABEZADO.match(p):
            continue
        frases = RE_FRASE.split(p)
        actual = ""
        for frase in frases:
            if not actual:
                actual = frase
            elif len(actual) + 1 + len(frase) <= MAX_LEN:
                actual += " " + frase
            else:
                if es_fragmento_valido(actual):
                    fragmentos.append(actual)
                actual = frase
        if actual and es_fragmento_valido(actual):
            fragmentos.append(actual)
    return fragmentos


def muestrear(lista, cantidad):
    """Toma `cantidad` elementos repartidos uniformemente (variedad de la obra)."""
    if len(lista) <= cantidad:
        return lista
    paso = len(lista) / cantidad
    return [lista[int(i * paso)] for i in range(cantidad)]


def main():
    cap = MAX_POR_OBRA
    citas = []
    vistos = set()

    # Incluir primero las citas célebres curadas a mano.
    if SEMILLA.is_file():
        for c in json.loads(SEMILLA.read_text(encoding="utf-8")):
            if c["texto"] not in vistos:
                vistos.add(c["texto"])
                citas.append(c)
        print(f"  Semilla curada: {len(citas)} citas")

    for gid, autor, obra in OBRAS:
        try:
            crudo = descargar(gid)
        except Exception as e:
            print(f"  [!] {obra}: error al descargar ({e})")
            continue
        cuerpo = quitar_envoltorio(crudo)
        frags = [f for f in trocear(cuerpo) if f not in vistos]
        elegidos = muestrear(frags, cap)
        for f in elegidos:
            if f in vistos:
                continue
            vistos.add(f)
            citas.append({"texto": f, "autor": f"{autor} · {obra}"})
        print(f"  {obra[:38]:<38} {len(frags):>5} válidos -> {len(elegidos):>4} usados")

    DESTINO.write_text(
        json.dumps(citas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  TOTAL: {len(citas)} citas escritas en {DESTINO}")


if __name__ == "__main__":
    main()
