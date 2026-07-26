"""Menús y pantallas de la aplicación (modo línea, portable)."""

import sys

from . import animaciones, engine, estadisticas, layout, ranking, textos
from .renderer import C

BANNER = [
    C["cian"] + C["negrita"] + "╔══════════════════════════════════════════════╗",
    "║       ⌨   MECANOGRAFÍA EN TERMINAL   ⌨       ║",
    "╚══════════════════════════════════════════════╝" + C["reset"],
]

# Sangría del último bloque dibujado. Los `input()` la reutilizan para que el
# texto que escribe el jugador quede alineado con la pantalla, no pegado al
# borde izquierdo de la consola.
_sangria = ""


def limpiar():
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.flush()


def _sangrar(lineas):
    """Fija (y devuelve) la sangría que centra `lineas` como un bloque único."""
    global _sangria
    _sangria = layout.sangria(max((layout.ancho(l) for l in lineas), default=0))
    return _sangria


def _mostrar(lineas):
    """Imprime un bloque de líneas centrado horizontalmente."""
    pre = _sangrar(lineas)
    print("\n".join(pre + l for l in lineas))


def _sangrar_prompt(prompt):
    """Aplica la sangría al prompt, dejando sus saltos de línea iniciales antes
    (si no, la sangría se escribiría en la línea anterior)."""
    cuerpo = prompt.lstrip("\n")
    saltos = len(prompt) - len(cuerpo)
    return "\n" * saltos + _sangria + cuerpo


def _pausa():
    input(_sangrar_prompt("\nPulsa Enter para continuar..."))


def _leer(prompt):
    try:
        return input(_sangrar_prompt(prompt)).strip()
    except (EOFError, KeyboardInterrupt):
        return "salir"


# --------------------------------------------------------------------------- #
#  TOP 5
# --------------------------------------------------------------------------- #
_MEDALLAS = {1: "🥇", 2: "🥈", 3: "🥉"}


def _bloque_top5(resaltar=None):
    """Devuelve las líneas del TOP 5. Si `resaltar` es un puesto (1..5), marca
    esa fila para que el jugador se vea destacado."""
    tabla = ranking.cargar()
    lineas = [C["amarillo"] + C["negrita"] + "🏆  TOP 5 VELOCIDADES" + C["reset"]]
    if not tabla:
        lineas.append(C["dim"] + "Aún no hay marcas. ¡Sé el primero!" + C["reset"])
        return lineas
    for i, e in enumerate(tabla, 1):
        # Las medallas ocupan DOS columnas: se rellena por ancho visible, no por
        # len(), para que las filas con y sin medalla queden alineadas.
        medalla = _MEDALLAS.get(i, f"{i}.")
        medalla += " " * max(1, 3 - layout.ancho(medalla))
        if i == resaltar:
            fila = f"{medalla} {e['ppm']:>5.0f} PPM  {e['nombre'][:18]:<18} ({e['precision']:.0f}%)"
            lineas.append(C["correcto"] + C["negrita"] + fila
                          + "  ◀ ¡AQUÍ ESTÁS!" + C["reset"])
        else:
            lineas.append(
                f"{medalla} {C['amarillo']}{e['ppm']:>5.0f} PPM{C['reset']}  "
                f"{e['nombre'][:18]:<18} {C['dim']}({e['precision']:.0f}%){C['reset']}"
            )
    return lineas


def _quizas_registrar_marca(res):
    """Si el resultado entra al TOP 5, pide el nombre y lo registra."""
    if not ranking.califica(res["ppm"]):
        return
    print()
    print(_sangria + C["amarillo"] + C["negrita"]
          + "⭐  ¡Tu velocidad entra al TOP 5!" + C["reset"])
    nombre = _leer("Escribe tu nombre para el ranking: ")
    if not nombre or nombre.lower() == "salir":
        nombre = "Anónimo"
    nombre = nombre[:20]
    puesto = ranking.agregar(nombre, res)
    if puesto:
        animaciones.celebrar_top(nombre, res["ppm"], puesto)
        # Mostrar la tabla con el jugador resaltado.
        limpiar()
        _mostrar(BANNER + [""] + _bloque_top5(resaltar=puesto))


# --------------------------------------------------------------------------- #
#  Resultado
# --------------------------------------------------------------------------- #
def mostrar_resultado(res):
    limpiar()
    palabras = res["caracteres"] / 5

    # Tally arcade: la velocidad y la precisión suben hasta su valor final.
    tally = [
        lambda t: (f"Velocidad ....... {C['amarillo']}{res['ppm'] * t:.0f} PPM{C['reset']}  "
                   f"({res['cpm'] * t:.0f} caracteres/min)"),
        lambda t: f"Precisión ....... {res['precision'] * t:.1f}%",
    ]

    cabecera = BANNER + [
        "",
        C["negrita"] + "📊  Resultado de la prueba" + C["reset"],
        "─" * 40,
    ]
    cola = [
        f"Errores ......... {res['errores']}",
        f"Tiempo .......... {res['tiempo']:.1f} s",
        f"Longitud ........ {res['caracteres']} caracteres (~{palabras:.0f} palabras)",
    ]
    if res.get("mejor_racha", 0) >= 5:
        cola.append(f"Mejor combo ..... {C['magenta']}{C['negrita']}x{res['mejor_racha']}{C['reset']} 🔥")
    cola.append("─" * 40)
    if res["ppm"] >= 60:
        cola.append(C["correcto"] + "¡Excelente velocidad! 🚀" + C["reset"])
    elif res["ppm"] >= 35:
        cola.append(C["correcto"] + "¡Buen ritmo! Sigue así. 👍" + C["reset"])
    else:
        cola.append(C["dim"] + "La constancia es la clave. 💪" + C["reset"])

    # La sangría se calcula con TODAS las líneas (incluidas las animadas en su
    # valor final) para que el bloque no cambie de sitio a mitad de pantalla.
    pre = _sangrar(cabecera + [f(1.0) for f in tally] + cola)
    print("\n".join(pre + l for l in cabecera))
    animaciones.contador_lineas([lambda t, f=f: pre + f(t) for f in tally])
    print("\n".join(pre + l for l in cola))


# --------------------------------------------------------------------------- #
#  Práctica
# --------------------------------------------------------------------------- #
def _practicar(sesion, fragmentos_o_citas, fuente, es_citas):
    ultimo_texto = None
    indice = 0
    while True:
        if es_citas:
            cita = textos.cita_aleatoria(fragmentos_o_citas, evitar_texto=ultimo_texto)
            texto, autor = cita["texto"], cita.get("autor")
            ultimo_texto = texto
        else:
            if indice >= len(fragmentos_o_citas):
                indice = 0
            texto, autor = fragmentos_o_citas[indice], None
            indice += 1

        res = engine.ejecutar_prueba(texto, fuente=fuente, autor=autor)
        if res is None:
            return  # abortado con ESC
        sesion.append(res)
        mostrar_resultado(res)
        _quizas_registrar_marca(res)
        resp = _leer("\n¿Otra prueba? (s/n): ").lower()
        if resp not in ("s", "si", "sí", ""):
            return


def practicar_citas(sesion):
    citas = textos.cargar_citas()
    _practicar(sesion, citas, fuente="cita", es_citas=True)


def practicar_texto_propio(sesion):
    limpiar()
    _mostrar(BANNER + [
        "",
        "Carga un archivo de texto (.txt) para practicar con él.",
    ])
    ruta = _leer("\nRuta del archivo (vacío para cancelar): ")
    if not ruta or ruta.lower() == "salir":
        return
    try:
        fragmentos = textos.cargar_texto_propio(ruta)
    except FileNotFoundError:
        print(_sangria + C["error_bg"] + "No se encontró el archivo." + C["reset"])
        _pausa()
        return
    except (ValueError, OSError) as e:
        print(_sangria + C["error_bg"] + f"No se pudo leer: {e}" + C["reset"])
        _pausa()
        return
    print("\n" + _sangria + f"Texto dividido en {len(fragmentos)} fragmento(s) para practicar.")
    _pausa()
    _practicar(sesion, fragmentos, fuente="propio", es_citas=False)


def ver_estadisticas(sesion):
    limpiar()
    res = estadisticas.resumen(sesion)
    if not res:
        _mostrar(BANNER + [
            "",
            C["negrita"] + "📈  Estadísticas de esta sesión" + C["reset"],
            "",
            "Aún no has hecho ninguna prueba en esta sesión.",
        ])
        _pausa()
        return
    lineas = BANNER + [
        "",
        C["negrita"] + "📈  Estadísticas de esta sesión" + C["reset"],
        "─" * 46,
        f"Pruebas en la sesión ...... {res['total']}",
        f"Mejor velocidad ........... {C['amarillo']}{res['mejor_ppm']:.0f} PPM{C['reset']}",
        f"Velocidad promedio ........ {res['ppm_promedio']:.0f} PPM",
        f"Mejor precisión ........... {res['mejor_precision']:.1f}%",
        f"Precisión promedio ........ {res['precision_promedio']:.1f}%",
        "─" * 46,
        C["negrita"] + "Últimas pruebas:" + C["reset"],
        f"{'Hora':<20}{'PPM':>6}{'Precis.':>10}{'Errores':>9}",
    ]
    for r in res["recientes"]:
        hora = r["fecha"].replace("T", " ")
        lineas.append(f"{hora:<20}{r['ppm']:>6.0f}{r['precision']:>9.1f}%{r['errores']:>9}")
    _mostrar(lineas)
    _pausa()


# --------------------------------------------------------------------------- #
#  Menú principal
# --------------------------------------------------------------------------- #
def menu_principal(sesion):
    while True:
        limpiar()
        _mostrar(BANNER + [""] + _bloque_top5() + [
            "",
            "1) Practicar con una cita aleatoria",
            "2) Practicar con mi propio texto (.txt)",
            "3) Ver estadísticas de la sesión",
            "4) Salir",
            "",
        ])
        opcion = _leer("Elige una opción: ").lower()
        if opcion == "1":
            practicar_citas(sesion)
        elif opcion == "2":
            practicar_texto_propio(sesion)
        elif opcion == "3":
            ver_estadisticas(sesion)
        elif opcion in ("4", "salir", "q"):
            limpiar()
            _mostrar(["¡Hasta la próxima! Sigue practicando. 👋", ""])
            return


def ejecutar():
    ranking.seed_inicial()
    animaciones.intro()
    menu_principal(sesion=[])
