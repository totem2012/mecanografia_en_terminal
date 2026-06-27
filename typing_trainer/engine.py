"""Motor de la prueba de mecanografía y cálculo de métricas.

`ejecutar_prueba` recibe un texto, gestiona el bucle de lectura tecla a tecla,
y devuelve un dict con el resultado (o None si el usuario abortó con ESC).
"""

import time
from datetime import datetime

from . import animaciones
from . import platform_io as io
from . import renderer


def ejecutar_prueba(texto, fuente="cita", autor=None):
    """Ejecuta una prueba interactiva. Devuelve dict-resultado o None."""
    objetivo = list(texto)
    n = len(objetivo)
    escrito = []          # caracteres tecleados (paralelo a objetivo)
    pulsaciones = 0       # total de caracteres pulsados (sin retrocesos)
    errores_pulsacion = 0  # pulsaciones que no coincidían en su momento
    inicio = None
    ultima_tecla = None   # último caracter pulsado (para el teclado en pantalla)
    ultimo_ok = True      # si esa última pulsación fue un acierto
    racha = 0             # aciertos seguidos (COMBO arcade)
    mejor_racha = 0       # mayor racha alcanzada en la prueba

    renderer.entrar_pantalla()
    try:
        animaciones.cuenta_atras()
        with io.raw_mode():
            while True:
                transcurrido = (time.time() - inicio) if inicio else 0.0
                renderer.dibujar_prueba(
                    objetivo, escrito, transcurrido, autor,
                    pulsaciones, errores_pulsacion,
                    ultima_tecla, ultimo_ok, racha,
                )
                if len(escrito) >= n:
                    break  # texto completado

                tipo, ch = io.leer_tecla()
                if tipo in ("ESC", "CTRL_C"):
                    return None
                if tipo == "BACKSPACE":
                    if escrito:
                        escrito.pop()
                    ultima_tecla = None  # al corregir no se ilumina ninguna tecla
                elif tipo == "CHAR":
                    if inicio is None:
                        inicio = time.time()
                    pos = len(escrito)
                    escrito.append(ch)
                    pulsaciones += 1
                    ultima_tecla = ch
                    ultimo_ok = ch == objetivo[pos]
                    if ultimo_ok:
                        racha += 1
                        mejor_racha = max(mejor_racha, racha)
                    else:
                        errores_pulsacion += 1
                        racha = 0
                # ENTER, TAB, SPECIAL y OTHER se ignoran (las citas no
                # contienen saltos de línea ni tabulaciones).
    finally:
        renderer.salir_pantalla()

    fin = time.time()
    tiempo = max(fin - inicio, 0.001) if inicio else 0.001
    correctos = sum(1 for i in range(n) if escrito[i] == objetivo[i])
    errores_finales = n - correctos
    ppm = (correctos / 5) / (tiempo / 60)
    cpm = correctos / (tiempo / 60)
    precision = (pulsaciones - errores_pulsacion) / pulsaciones * 100 if pulsaciones else 0.0

    return {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "fuente": fuente,
        "autor": autor,
        "caracteres": n,
        "tiempo": round(tiempo, 2),
        "ppm": round(ppm, 1),
        "cpm": round(cpm, 1),
        "precision": round(precision, 1),
        "errores": errores_finales,
        "pulsaciones": pulsaciones,
        "mejor_racha": mejor_racha,
    }
