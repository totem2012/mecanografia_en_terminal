"""Animaciones de terminal (intro y récord del TOP 1).

Diseño:
  - Saltables con cualquier tecla.
  - Cortas (~1.5 s).
  - Desactivables con la variable de entorno MECANOGRAFIA_SIN_ANIMACION.
  - Solo ANSI + sleep; portables a Linux y Windows.
"""

import os
import sys
import time

from . import layout
from . import platform_io as io
from .renderer import C

_TOP = "  ╔══════════════════════════════════════════════╗"
_MED = "        ⌨   MECANOGRAFÍA EN TERMINAL   ⌨        "
_BOT = "  ╚══════════════════════════════════════════════╝"


def activadas():
    return os.environ.get("MECANOGRAFIA_SIN_ANIMACION", "").strip() == ""


def _w(texto):
    sys.stdout.write(texto)
    sys.stdout.flush()


def _esperar(segundos, paso=0.02):
    """Duerme en pasos pequeños; devuelve True si se pulsó una tecla (saltar)."""
    fin = time.time() + segundos
    while time.time() < fin:
        if io.hay_tecla():
            return True
        time.sleep(paso)
    return False


_SUBT = "Practica · Mejora · Domina el teclado"
# Paleta para el tecleo arcoíris y la ola de color.
_PALETA = ["\x1b[96m", "\x1b[36m", "\x1b[93m", "\x1b[92m", "\x1b[95m"]
_ANCHO = len(_TOP) - 2  # ancho interior del marco (sin los 2 espacios del margen)


def _centro(texto, ancho):
    sobra = max(0, ancho - len(texto))
    izq = sobra // 2
    return " " * izq + texto + " " * (sobra - izq)


def _sangria_marco():
    """Sangría fija del marco de la intro (constante en todos los frames, para
    que el marco no se desplace mientras se dibuja de izquierda a derecha)."""
    return layout.sangria(_ANCHO + 2)


def _linea_titulo(n_revelado, resaltar, base):
    """Línea central del marco con el título revelado hasta `n_revelado`."""
    partes = [_sangria_marco() + C["cian"] + C["negrita"] + "║" + C["reset"] + base + C["negrita"]]
    for i, ch in enumerate(_MED):
        if i >= n_revelado:
            partes.append(" ")
        elif i == resaltar:
            partes.append(C["reset"] + "\x1b[97m" + C["negrita"] + ch + C["reset"] + base + C["negrita"])
        else:
            partes.append(ch)
    partes.append(C["reset"] + C["cian"] + C["negrita"] + "║" + C["reset"])
    return "".join(partes)


def _frame(borde, n_titulo, resaltar, base, n_subt, pulso=False):
    """Compone un frame completo de la intro.

    borde     : nº de caracteres del marco superior/inferior ya dibujados
    n_titulo  : caracteres del título revelados
    resaltar  : posición a resaltar en el título (ola), o None
    base      : color base del título
    n_subt    : caracteres del subtítulo revelados
    pulso     : si el subtítulo va resaltado (pulso final)
    """
    pre = _sangria_marco()
    sup = pre + C["cian"] + C["negrita"] + "╔" + "═" * borde + ("╗" if borde >= _ANCHO else "") + C["reset"]
    inf = pre + C["cian"] + C["negrita"] + "╚" + "═" * borde + ("╝" if borde >= _ANCHO else "") + C["reset"]
    col_subt = C["amarillo"] + C["negrita"] if pulso else C["dim"]
    subt_txt = _centro(_SUBT, len(_MED))[:n_subt]

    filas = layout.tam_terminal()[1]
    arriba = max(1, (filas - 5) // 2)   # el bloque ocupa 5 líneas

    out = ["\x1b[H"]
    out.extend(["\x1b[K\n"] * arriba)
    out.append(sup + "\x1b[K\n")
    out.append(_linea_titulo(n_titulo, resaltar, base) + "\x1b[K\n")
    out.append(inf + "\x1b[K\n\n")
    out.append(pre + col_subt + " " + subt_txt + C["reset"] + "\x1b[K\n")
    out.append("\x1b[J")
    return "".join(out)


def intro():
    """Pantalla de bienvenida multi-fase (marco, tecleo, ola de color, pulso)."""
    if not activadas():
        return
    nt = len(_MED)
    ns = len(_centro(_SUBT, nt))   # ancho del subtítulo ya centrado
    _w("\x1b[2J\x1b[H\x1b[?25l")
    saltar = False
    try:
        with io.raw_mode():
            # Fase 1 — el marco se dibuja de izquierda a derecha
            for b in range(_ANCHO + 1):
                _w(_frame(b, 0, None, _PALETA[0], 0))
                if _esperar(0.006):
                    saltar = True
                    break

            # Fase 2 — el título se teclea con color cambiante (arcoíris)
            if not saltar:
                for k in range(nt + 1):
                    base = _PALETA[k % len(_PALETA)]
                    _w(_frame(_ANCHO, k, None, base, 0))
                    if _esperar(0.016):
                        saltar = True
                        break

            # Fase 3 — ola de luz que barre el título
            if not saltar:
                for _ in range(2):
                    for pos in range(nt):
                        _w(_frame(_ANCHO, nt, pos, _PALETA[0], 0))
                        if _esperar(0.010):
                            saltar = True
                            break
                    if saltar:
                        break

            # Fase 4 — aparece el subtítulo
            if not saltar:
                for k in range(ns + 1):
                    _w(_frame(_ANCHO, nt, None, _PALETA[0], k))
                    if _esperar(0.014):
                        saltar = True
                        break

            # Fase 5 — pulso final del subtítulo
            if not saltar:
                for i in range(6):
                    _w(_frame(_ANCHO, nt, None, _PALETA[0], ns, pulso=(i % 2 == 0)))
                    if _esperar(0.13):
                        break

            # Frame final estable
            _w(_frame(_ANCHO, nt, None, C["cian"], ns))
    finally:
        _w("\x1b[?25h")
        io.vaciar_entrada()


# --------------------------------------------------------------------------- #
#  Cuenta atrás arcade (antes de cada prueba)
# --------------------------------------------------------------------------- #
def _caja_centrada(texto, color, ancho_int=13):
    """Caja de doble marco con `texto` centrado, estilo marcador arcade."""
    medio = _centro(texto, ancho_int)
    pad = layout.sangria(ancho_int + 2)   # caja centrada en la consola
    cab = color + C["negrita"]
    top = pad + cab + "╔" + "═" * ancho_int + "╗" + C["reset"]
    vac = pad + cab + "║" + " " * ancho_int + "║" + C["reset"]
    mid = pad + cab + "║" + C["reset"] + cab + medio + C["reset"] + cab + "║" + C["reset"]
    bot = pad + cab + "╚" + "═" * ancho_int + "╝" + C["reset"]
    return "\n".join([top, vac, mid, vac, bot])


def cuenta_atras():
    """Cuenta atrás 3 · 2 · 1 · ¡YA! antes de arrancar una prueba.

    Se dibuja sobre el buffer de pantalla activo (el que ya preparó el
    renderer), de modo que enlaza directo con el primer frame de la prueba.
    """
    if not activadas():
        return
    pasos = [
        ("3", C["amarillo"], 0.55),
        ("2", C["amarillo"], 0.55),
        ("1", "\x1b[91m", 0.55),       # rojo intenso
        ("¡YA!", C["correcto"], 0.45),
    ]
    _w("\x1b[2J\x1b[H\x1b[?25l")
    arriba = max(1, (layout.tam_terminal()[1] - 5) // 2)   # la caja ocupa 5 líneas
    try:
        with io.raw_mode():
            for txt, col, dur in pasos:
                _w("\x1b[H" + "\n" * arriba)
                _w(_caja_centrada(txt, col) + "\n")
                _w("\x1b[J")
                if _esperar(dur):
                    break
    finally:
        _w("\x1b[?25h")
        io.vaciar_entrada()


# --------------------------------------------------------------------------- #
#  Contador de puntuación (tally arcade del resultado)
# --------------------------------------------------------------------------- #
def contador_lineas(formatos, pasos=16, paso=0.03):
    """Anima varias líneas-contador subiendo de 0 a su valor final a la vez.

    `formatos` es una lista de funciones `f(t) -> str`, donde `t` va de 0 a 1;
    cada una compone la línea completa con el valor escalado por `t`. Útil para
    el tally de PPM/precisión del resultado (efecto de marcador que sube).
    Saltable con cualquier tecla; respeta MECANOGRAFIA_SIN_ANIMACION.
    """
    n = len(formatos)
    if not n:
        return
    if not activadas():
        for f in formatos:
            _w(f(1.0) + "\n")
        return
    for _ in range(n):       # reservar las n líneas
        _w("\n")
    try:
        with io.raw_mode():
            saltar = False
            for k in range(1, pasos):     # frames intermedios (no el final)
                t = k / pasos
                _w(f"\x1b[{n}A")          # subir al inicio del bloque
                for f in formatos:
                    _w("\r" + f(t) + "\x1b[K\n")
                if _esperar(paso):
                    saltar = True
                    break
    finally:
        _w(f"\x1b[{n}A")                  # frame final exacto
        for f in formatos:
            _w("\r" + f(1.0) + "\x1b[K\n")
        io.vaciar_entrada()


# --------------------------------------------------------------------------- #
#  PRESS START parpadeante (menú principal)
# --------------------------------------------------------------------------- #
def press_start(parpadeos=3, paso=0.18):
    """Parpadea un '► PRESS START ◄' estilo 'insert coin' y lo deja encendido.

    Se dibuja en la línea actual (la deja ocupada y baja con \\n al terminar).
    """
    linea = layout.centrar("► PRESS START ◄")
    encendido = C["amarillo"] + C["negrita"]
    if not activadas():
        _w(encendido + linea + C["reset"] + "\n")
        return
    try:
        with io.raw_mode():
            for i in range(parpadeos * 2 - 1):
                col = encendido if i % 2 == 0 else C["dim"]
                _w("\r" + col + linea + C["reset"] + "\x1b[K")
                if _esperar(paso):
                    break
    finally:
        _w("\r" + encendido + linea + C["reset"] + "\x1b[K\n")
        io.vaciar_entrada()


_MEDALLAS = {1: "🥇", 2: "🥈", 3: "🥉", 4: "4️⃣", 5: "5️⃣"}


def celebrar_top(nombre, ppm, puesto):
    """Celebración al entrar al TOP 5. El puesto #1 es la más épica."""
    es_record = puesto == 1
    medalla = _MEDALLAS.get(puesto, f"#{puesto}")
    titulo = "🏆  ¡NUEVO RÉCORD!  🏆" if es_record else "🎉  ¡ENTRASTE AL TOP 5!  🎉"

    if not activadas():
        # Sin animación: mensaje simple.
        etiqueta = "¡NUEVO RÉCORD #1!" if es_record else f"¡TOP 5 — Puesto #{puesto}!"
        _w("\n" + layout.centrar(C["amarillo"] + C["negrita"]
                                 + f"{medalla} {etiqueta}  {nombre} — {ppm:.0f} PPM")
           + C["reset"] + "\n")
        return

    colores = [C["amarillo"], C["cian"], C["correcto"], "\x1b[97m"]
    adornos = (["✨  ", "·   ", " ✨ ", "   ✨"] if es_record
               else ["🎊  ", "·   ", " 🎊 ", "   🎊"])
    frames = 10 if es_record else 8
    _w("\x1b[?25l")
    cols, filas = layout.tam_terminal()
    arriba = max(1, (filas - 5) // 2)   # el bloque ocupa 5 líneas
    try:
        with io.raw_mode():
            for i in range(frames):
                col = colores[i % len(colores)]
                ado = adornos[i % len(adornos)]
                # Los adornos tienen todos el mismo ancho, así que el centrado
                # no cambia entre frames y el texto no se mueve al parpadear.
                lineas = [
                    f"{ado}{col}{C['negrita']}{titulo}{C['reset']}{ado}",
                    "",
                    f"{col}{nombre} — {ppm:.0f} PPM{C['reset']}",
                    "",
                    f"{C['amarillo']}{medalla}  ¡Puesto #{puesto} del TOP 5!{C['reset']}",
                ]
                _w("\x1b[2J\x1b[H" + "\n" * arriba)
                _w("\n".join(layout.centrar(l, cols) for l in lineas) + "\n")
                if _esperar(0.13):
                    break
    finally:
        _w("\x1b[?25h")
        io.vaciar_entrada()
