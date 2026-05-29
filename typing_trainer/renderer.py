"""Renderizado del frame de la prueba mediante secuencias ANSI.

Estrategia anti-parpadeo: se reposiciona el cursor en el origen (\x1b[H),
se reescribe el contenido y cada línea se limpia con \x1b[K, y al final se
borra lo que sobre con \x1b[J. Así no hay un borrado total de pantalla por
pulsación.
"""

import os
import shutil
import sys

from . import teclado


def _tam_terminal():
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

C = {
    "reset": "\x1b[0m",
    "correcto": "\x1b[32m",          # verde
    "error_bg": "\x1b[41m\x1b[97m",  # fondo rojo, texto blanco
    "pendiente": "\x1b[90m",         # gris
    "actual": "\x1b[7m",             # vídeo inverso (cursor)
    "dim": "\x1b[2m",
    "cian": "\x1b[36m",
    "amarillo": "\x1b[33m",
    "negrita": "\x1b[1m",
}


def _w(texto):
    sys.stdout.write(texto)


def entrar_pantalla():
    """Activa el buffer alternativo y oculta el cursor del sistema."""
    _w("\x1b[?1049h")
    _w("\x1b[?25l")
    _w("\x1b[H")
    sys.stdout.flush()


def salir_pantalla():
    """Restaura cursor y buffer principal."""
    _w("\x1b[?25h")
    _w("\x1b[?1049l")
    sys.stdout.flush()


# Estilo (código ANSI) por cada estado de caracter. Agrupar caracteres del
# mismo estilo en un único span reduce el I/O por frame.
_ESTILOS = {
    "correcto": C["correcto"],
    "error": C["error_bg"],
    "actual": C["actual"],
    "pendiente": C["pendiente"],
}

# Caché del ajuste de líneas: el texto y el ancho no cambian durante la prueba,
# así que evitamos recalcularlo en cada pulsación.
_cache_ajuste = {"clave": None, "lineas": None}


def _ajustar_lineas(texto, ancho):
    """Divide `texto` en rangos (inicio, fin) que caben en `ancho` columnas,
    cortando preferentemente en los espacios. Resultado cacheado por (texto, ancho)."""
    clave = (texto, ancho)
    if _cache_ajuste["clave"] == clave:
        return _cache_ajuste["lineas"]

    lineas = []
    i = 0
    n = len(texto)
    while i < n:
        fin = min(i + ancho, n)
        if fin < n:
            corte = texto.rfind(" ", i, fin + 1)
            if corte > i:
                fin = corte + 1
        lineas.append((i, fin))
        i = fin
    if not lineas:
        lineas.append((0, 0))

    _cache_ajuste["clave"] = clave
    _cache_ajuste["lineas"] = lineas
    return lineas


def _estilo_de(i, pos, objetivo, escrito):
    """Devuelve (estilo, caracter_visible) para la posición i."""
    ch = objetivo[i]
    if i < pos:
        if escrito[i] == ch:
            return "correcto", ch
        return "error", (ch if ch != " " else "_")
    if i == pos:
        return "actual", ch
    return "pendiente", ch


def _barra(porcentaje, ancho=22):
    lleno = int(porcentaje / 100 * ancho)
    return "[" + "█" * lleno + "·" * (ancho - lleno) + f"] {porcentaje:3.0f}%"


def dibujar_prueba(objetivo, escrito, transcurrido, autor, pulsaciones, errores,
                   ultima_tecla=None, ultimo_ok=True):
    """Pinta un frame completo de la prueba en curso.

    objetivo     : lista de caracteres objetivo
    escrito      : lista de caracteres ya tecleados (paralela a objetivo)
    ultima_tecla : último caracter pulsado, para iluminarlo en el teclado
    ultimo_ok    : True si esa última pulsación fue correcta
    """
    cols, filas = _tam_terminal()
    ancho = max(20, cols - 4)
    pos = len(escrito)
    texto = "".join(objetivo)
    lineas = _ajustar_lineas(texto, ancho)

    out = ["\x1b[H"]
    out.append(C["negrita"] + C["cian"] + "  ⌨  Práctica de Mecanografía" + C["reset"] + "\x1b[K\n")
    out.append("\x1b[K\n")

    reset = C["reset"]
    for (a, b) in lineas:
        pintada = ["  "]
        estilo_actual = None
        buffer = []
        for i in range(a, b):
            estilo, ch = _estilo_de(i, pos, objetivo, escrito)
            if estilo != estilo_actual:
                if buffer:
                    pintada.append(_ESTILOS[estilo_actual] + "".join(buffer) + reset)
                buffer = [ch]
                estilo_actual = estilo
            else:
                buffer.append(ch)
        if buffer:
            pintada.append(_ESTILOS[estilo_actual] + "".join(buffer) + reset)
        pintada.append("\x1b[K")
        out.append("".join(pintada) + "\n")

    out.append("\x1b[K\n")

    correctos = sum(1 for i in range(pos) if escrito[i] == objetivo[i])
    minutos = transcurrido / 60 if transcurrido > 0 else 0
    ppm = (correctos / 5) / minutos if minutos > 0 else 0
    precision = (pulsaciones - errores) / pulsaciones * 100 if pulsaciones else 100.0
    progreso = pos / len(objetivo) * 100 if objetivo else 0

    if pulsaciones == 0:
        # El cronómetro aún no arranca: arrancará con la primera tecla.
        out.append(
            "  " + C["dim"] + "⏱  El tiempo arranca al pulsar la primera tecla…"
            + C["reset"] + "\x1b[K\n"
        )
    else:
        out.append(
            "  "
            + C["amarillo"] + f"{ppm:5.0f} PPM" + C["reset"]
            + f"   Precisión: {precision:5.1f}%"
            + f"   Tiempo: {transcurrido:5.1f}s"
            + "\x1b[K\n"
        )
    out.append("  " + C["dim"] + _barra(progreso) + C["reset"] + "\x1b[K\n")
    if autor:
        out.append("  " + C["dim"] + f"— {autor}" + C["reset"] + "\x1b[K\n")
    out.append("\x1b[K\n")

    # Teclado: solo si está activado y la terminal tiene altura suficiente,
    # para no provocar scroll que rompa el redibujado anti-parpadeo.
    filas_teclado = teclado.lineas(ultima_tecla, ultimo_ok)
    usadas = 2 + len(lineas) + 4 + (1 if autor else 0)  # cabecera, texto, métricas, autor
    if teclado.activado() and filas >= usadas + len(filas_teclado) + 2:
        for fila in filas_teclado:
            out.append(fila + "\x1b[K\n")
        out.append("\x1b[K\n")

    out.append("  " + C["dim"] + "ESC: salir   ·   ⌫ Retroceso: corregir" + C["reset"] + "\x1b[K")
    out.append("\x1b[J")

    sys.stdout.write("".join(out))
    sys.stdout.flush()
