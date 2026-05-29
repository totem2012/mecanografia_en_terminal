"""Dibujo de un teclado genérico que resalta la última tecla pulsada.

Diseño:
  - Genérico: muestra solo el bloque alfabético QWERTY + Ñ + barra espaciadora
    (sin números ni símbolos), de modo que sirve para cualquier distribución
    latina sin depender de la posición de los signos.
  - La última tecla pulsada se ilumina: verde si fue un acierto, rojo si fue un
    fallo. Mientras no haya pulsaciones (o tras un retroceso) no se ilumina nada.
  - Desactivable con la variable de entorno MECANOGRAFIA_SIN_TECLADO.
  - Solo ANSI; portable a Linux y Windows.
"""

import os
import unicodedata

# Filas del bloque alfabético. La sangría (en espacios) imita el escalonado
# físico de un teclado real.
_FILAS = [
    (0, list("QWERTYUIOP")),
    (1, list("ASDFGHJKLÑ")),
    (3, list("ZXCVBNM")),
]

_VERDE = "\x1b[42m\x1b[30m"   # fondo verde, texto negro  -> acierto
_ROJO = "\x1b[41m\x1b[97m"    # fondo rojo, texto blanco   -> fallo
_TENUE = "\x1b[2m"           # gris tenue para el teclado en reposo
_RESET = "\x1b[0m"


def activado():
    """¿Debe mostrarse el teclado? (controlado por variable de entorno)."""
    return os.environ.get("MECANOGRAFIA_SIN_TECLADO", "").strip() == ""


def tecla_fisica(ch):
    """Aproxima la tecla física asociada al caracter `ch`.

    Devuelve una letra A-Z en mayúscula, 'Ñ', ' ' para el espacio, o None si el
    caracter no está representado en el teclado de solo letras (p. ej. una coma
    o un número)."""
    if not ch:
        return None
    if ch == " ":
        return " "
    base = ch.upper()
    if base == "Ñ":
        return "Ñ"
    # Quitar acentos/diacríticos (á -> A, ü -> U), conservando la letra base.
    sin_acento = "".join(
        c for c in unicodedata.normalize("NFD", base)
        if unicodedata.category(c) != "Mn"
    )
    if len(sin_acento) == 1 and "A" <= sin_acento <= "Z":
        return sin_acento
    return None


def lineas(ultima_tecla=None, ultimo_ok=None):
    """Devuelve la lista de líneas (con códigos ANSI) que dibujan el teclado.

    ultima_tecla : caracter pulsado más recientemente (o None).
    ultimo_ok    : True si esa pulsación fue correcta, False si no.
    """
    activa = tecla_fisica(ultima_tecla)
    color = _VERDE if ultimo_ok else _ROJO

    def celda(letra):
        if activa is not None and letra == activa:
            return color + f" {letra} " + _RESET
        return _TENUE + f" {letra} " + _RESET

    filas = []
    for sangria, letras in _FILAS:
        prefijo = "  " + " " * sangria
        filas.append(prefijo + "".join(celda(l) for l in letras))

    # Barra espaciadora.
    etiqueta = "espacio"
    if activa == " ":
        barra = color + f"   {etiqueta}   " + _RESET
    else:
        barra = _TENUE + f"  [{etiqueta}]  " + _RESET
    filas.append("        " + barra)

    return filas
