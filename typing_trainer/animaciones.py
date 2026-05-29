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


def _linea_titulo(n_revelado, resaltar, base):
    """Línea central del marco con el título revelado hasta `n_revelado`."""
    partes = ["  " + C["cian"] + C["negrita"] + "║" + C["reset"] + base + C["negrita"]]
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
    sup = "  " + C["cian"] + C["negrita"] + "╔" + "═" * borde + ("╗" if borde >= _ANCHO else "") + C["reset"]
    inf = "  " + C["cian"] + C["negrita"] + "╚" + "═" * borde + ("╝" if borde >= _ANCHO else "") + C["reset"]
    col_subt = C["amarillo"] + C["negrita"] if pulso else C["dim"]
    subt_txt = _centro(_SUBT, len(_MED))[:n_subt]

    out = ["\x1b[H\n\n"]
    out.append(sup + "\x1b[K\n")
    out.append(_linea_titulo(n_titulo, resaltar, base) + "\x1b[K\n")
    out.append(inf + "\x1b[K\n\n")
    out.append("  " + col_subt + "  " + subt_txt + C["reset"] + "\x1b[K\n")
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


_MEDALLAS = {1: "🥇", 2: "🥈", 3: "🥉", 4: "4️⃣", 5: "5️⃣"}


def celebrar_top(nombre, ppm, puesto):
    """Celebración al entrar al TOP 5. El puesto #1 es la más épica."""
    es_record = puesto == 1
    medalla = _MEDALLAS.get(puesto, f"#{puesto}")
    titulo = "🏆  ¡NUEVO RÉCORD!  🏆" if es_record else "🎉  ¡ENTRASTE AL TOP 5!  🎉"

    if not activadas():
        # Sin animación: mensaje simple.
        etiqueta = "¡NUEVO RÉCORD #1!" if es_record else f"¡TOP 5 — Puesto #{puesto}!"
        _w(C["amarillo"] + C["negrita"]
           + f"\n  {medalla} {etiqueta}  {nombre} — {ppm:.0f} PPM\n" + C["reset"])
        return

    colores = [C["amarillo"], C["cian"], C["correcto"], "\x1b[97m"]
    adornos = (["✨  ", "·   ", " ✨ ", "   ✨"] if es_record
               else ["🎊  ", "·   ", " 🎊 ", "   🎊"])
    frames = 10 if es_record else 8
    _w("\x1b[?25l")
    try:
        with io.raw_mode():
            for i in range(frames):
                col = colores[i % len(colores)]
                ado = adornos[i % len(adornos)]
                _w("\x1b[2J\x1b[H")
                _w("\n\n")
                _w(f"        {ado}{col}{C['negrita']}{titulo}{C['reset']}{ado}\n\n")
                _w(f"            {col}{nombre} — {ppm:.0f} PPM{C['reset']}\n\n")
                _w(f"              {C['amarillo']}{medalla}  ¡Puesto #{puesto} del TOP 5!{C['reset']}\n")
                if _esperar(0.13):
                    break
    finally:
        _w("\x1b[?25h")
        io.vaciar_entrada()
