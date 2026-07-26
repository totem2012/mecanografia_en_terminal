"""Renderizado del frame de la prueba mediante secuencias ANSI.

Estrategia anti-parpadeo: se reposiciona el cursor en el origen (\x1b[H),
se reescribe el contenido y cada línea se limpia con \x1b[K, y al final se
borra lo que sobre con \x1b[J. Así no hay un borrado total de pantalla por
pulsación.
"""

import sys

from . import layout, teclado

# Ancho máximo del bloque de juego. En pantallas anchas el texto no se estira de
# borde a borde (cansa la vista y descoloca la mirada al saltar de línea): se
# limita a una columna legible que luego se centra.
ANCHO_MAX = 92

C = {
    "reset": "\x1b[0m",
    "correcto": "\x1b[32m",          # verde
    "error_bg": "\x1b[41m\x1b[97m",  # fondo rojo, texto blanco
    "pendiente": "\x1b[90m",         # gris
    "actual": "\x1b[7m",             # vídeo inverso (cursor)
    "dim": "\x1b[2m",
    "cian": "\x1b[36m",
    "amarillo": "\x1b[33m",
    "magenta": "\x1b[95m",
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


# Ancho de la línea de métricas SIN el COMBO: los campos tienen ancho fijo, así
# que es constante durante toda la prueba. Sirve de ancho mínimo del bloque para
# que este no se mueva cuando aparece o desaparece el COMBO.
_ANCHO_METRICAS = 46


def _barra(porcentaje, ancho=22):
    lleno = int(porcentaje / 100 * ancho)
    return "[" + "█" * lleno + "·" * (ancho - lleno) + f"] {porcentaje:3.0f}%"


def _combo(racha):
    """Indicador arcade de aciertos seguidos. Vacío por debajo del umbral."""
    if racha < 5:
        return ""
    if racha >= 20:
        col, fuego = C["magenta"], " 🔥🔥"
    elif racha >= 10:
        col, fuego = C["amarillo"], " 🔥"
    else:
        col, fuego = C["cian"], ""
    return "   " + col + C["negrita"] + f"COMBO x{racha}{fuego}" + C["reset"]


def dibujar_prueba(objetivo, escrito, transcurrido, autor, pulsaciones, errores,
                   ultima_tecla=None, ultimo_ok=True, racha=0):
    """Pinta un frame completo de la prueba en curso.

    objetivo     : lista de caracteres objetivo
    escrito      : lista de caracteres ya tecleados (paralela a objetivo)
    ultima_tecla : último caracter pulsado, para iluminarlo en el teclado
    ultimo_ok    : True si esa última pulsación fue correcta
    racha        : aciertos seguidos, para el indicador de COMBO
    """
    cols, filas = layout.tam_terminal()
    ancho = max(20, min(cols - 4, ANCHO_MAX))
    pos = len(escrito)
    texto = "".join(objetivo)
    lineas = _ajustar_lineas(texto, ancho)

    # `bloque` son las líneas del frame SIN la sangría de centrado: se compone
    # entero para conocer su alto y poder centrarlo también en vertical.
    bloque = [C["negrita"] + C["cian"] + "⌨  Práctica de Mecanografía" + C["reset"], ""]

    reset = C["reset"]
    for (a, b) in lineas:
        pintada = []
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
        bloque.append("".join(pintada))

    bloque.append("")

    correctos = sum(1 for i in range(pos) if escrito[i] == objetivo[i])
    minutos = transcurrido / 60 if transcurrido > 0 else 0
    ppm = (correctos / 5) / minutos if minutos > 0 else 0
    precision = (pulsaciones - errores) / pulsaciones * 100 if pulsaciones else 100.0
    progreso = pos / len(objetivo) * 100 if objetivo else 0

    # Las métricas van alineadas al borde izquierdo del bloque (no centradas una
    # a una): su ancho cambia con cada pulsación —dígitos, COMBO— y centrarlas
    # las haría bailar de lado a lado en cada frame.
    if pulsaciones == 0:
        # El cronómetro aún no arranca: arrancará con la primera tecla.
        bloque.append(
            C["dim"] + "⏱  El tiempo arranca al pulsar la primera tecla…" + C["reset"]
        )
    else:
        bloque.append(
            C["amarillo"] + f"{ppm:5.0f} PPM" + C["reset"]
            + f"   Precisión: {precision:5.1f}%"
            + f"   Tiempo: {transcurrido:5.1f}s"
            + _combo(racha)
        )
    bloque.append(C["dim"] + _barra(progreso) + C["reset"])
    if autor:
        bloque.append(C["dim"] + f"— {autor}" + C["reset"])
    bloque.append("")

    ayuda = C["dim"] + "ESC: salir   ·   ⌫ Retroceso: corregir" + C["reset"]

    # Ancho real del bloque: con textos cortos se encoge al contenido para que
    # quede bien centrado. Se mide con elementos de ancho ESTABLE (el texto, las
    # métricas sin COMBO, la ayuda): si dependiera del COMBO o de los dígitos de
    # las cifras, el bloque entero se movería de lado en cada pulsación.
    ancho_bloque = min(ancho, max(
        [layout.ancho(texto[a:b].rstrip()) for (a, b) in lineas]
        + [_ANCHO_METRICAS, layout.ancho(ayuda)]
        + ([layout.ancho(f"— {autor}")] if autor else [])
    ))

    # Teclado: solo si está activado y la terminal tiene altura suficiente,
    # para no provocar scroll que rompa el redibujado anti-parpadeo.
    filas_teclado = teclado.lineas(ultima_tecla, ultimo_ok)
    alto_util = filas - 1
    if (teclado.activado()
            and len(bloque) + len(filas_teclado) + 2 <= alto_util):
        ancho_bloque = max(ancho_bloque, max(layout.ancho(f) for f in filas_teclado))
        # Ancho fijo, así que centrarlo dentro del bloque no produce baile.
        bloque.extend(layout.centrar_bloque(filas_teclado, ancho_bloque))
        bloque.append("")
    bloque.append(layout.centrar(ayuda, ancho_bloque))

    # Centrado: sangría común a la izquierda y relleno de líneas arriba.
    izq = layout.sangria(ancho_bloque, cols)
    arriba = max(0, (alto_util - len(bloque)) // 2)

    out = ["\x1b[H"]
    out.extend(["\x1b[K\n"] * arriba)
    for linea in bloque[:-1]:
        out.append(izq + linea + "\x1b[K\n")
    out.append(izq + bloque[-1] + "\x1b[K")
    out.append("\x1b[J")

    sys.stdout.write("".join(out))
    sys.stdout.flush()
