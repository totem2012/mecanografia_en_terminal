"""Medida del ancho visible y centrado horizontal de bloques.

Centrar exige saber cuántas COLUMNAS ocupa una línea en pantalla, que no es su
`len()`: las secuencias ANSI de color no ocupan ninguna y los emojis ocupan dos.
Se consulta la propiedad Unicode East_Asian_Width, que es el criterio que siguen
tanto los terminales de Linux como Windows Terminal.

Los bloques (tablas, teclado, menús) se centran como una UNIDAD, usando su línea
más ancha, para que no se pierda su alineación interna.
"""

import os
import re
import shutil
import sys
import unicodedata

_ANSI = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")


def tam_terminal():
    """Tamaño REAL del terminal, consultando el dispositivo.

    Se evita `shutil.get_terminal_size`, que prioriza las variables de entorno
    COLUMNS/LINES; estas pueden quedar obsoletas al redimensionar la ventana y
    provocar que las líneas excedan el ancho real (el terminal las re-parte,
    cortando palabras y desincronizando el redibujado)."""
    for flujo in (sys.__stdout__, sys.stdout, sys.__stderr__):
        try:
            tam = os.get_terminal_size(flujo.fileno())
            if tam.columns > 0:
                return tam.columns, tam.lines
        except (OSError, ValueError, AttributeError):
            continue
    return tuple(shutil.get_terminal_size((80, 24)))


def columnas():
    return tam_terminal()[0]


def ancho(texto):
    """Columnas que ocupa `texto`: sin contar ANSI y con emojis como 2."""
    total = 0
    for ch in _ANSI.sub("", texto):
        if unicodedata.category(ch) in ("Mn", "Me", "Cf"):
            continue  # diacríticos y selectores de variación: no ocupan columna
        total += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return total


def sangria(ancho_bloque, cols=None):
    """Espacios necesarios para centrar un bloque de `ancho_bloque` columnas."""
    if cols is None:
        cols = columnas()
    return " " * max(0, (cols - ancho_bloque) // 2)


def centrar(linea, cols=None):
    """Centra una línea suelta dentro de `cols` columnas."""
    return sangria(ancho(linea), cols) + linea


def centrar_bloque(lineas, cols=None):
    """Centra varias líneas como un bloque (misma sangría para todas)."""
    lineas = list(lineas)
    if not lineas:
        return []
    pre = sangria(max(ancho(l) for l in lineas), cols)
    return [pre + l for l in lineas]
