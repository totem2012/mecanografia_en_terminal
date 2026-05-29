"""Menús y pantallas de la aplicación (modo línea, portable)."""

import sys

from . import animaciones, engine, estadisticas, ranking, textos
from .renderer import C

BANNER = (
    C["cian"] + C["negrita"]
    + "╔══════════════════════════════════════════════╗\n"
    + "║        ⌨   MECANOGRAFÍA EN TERMINAL   ⌨        ║\n"
    + "╚══════════════════════════════════════════════╝"
    + C["reset"]
)


def limpiar():
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.flush()


def _pausa():
    input("\n  Pulsa Enter para continuar...")


def _leer(prompt):
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return "salir"


# --------------------------------------------------------------------------- #
#  TOP 5
# --------------------------------------------------------------------------- #
_MEDALLAS = {1: "🥇", 2: "🥈", 3: "🥉"}


def _bloque_top5(resaltar=None):
    """Devuelve el TOP 5 formateado. Si `resaltar` es un puesto (1..5), marca
    esa fila para que el jugador se vea destacado."""
    tabla = ranking.cargar()
    lineas = ["  " + C["amarillo"] + C["negrita"] + "🏆  TOP 5 VELOCIDADES" + C["reset"]]
    if not tabla:
        lineas.append("  " + C["dim"] + "Aún no hay marcas. ¡Sé el primero!" + C["reset"])
        return "\n".join(lineas)
    for i, e in enumerate(tabla, 1):
        medalla = _MEDALLAS.get(i, f"{i}.")
        if i == resaltar:
            fila = f"{medalla:<3} {e['ppm']:>5.0f} PPM  {e['nombre'][:18]:<18} ({e['precision']:.0f}%)"
            lineas.append("  " + C["correcto"] + C["negrita"] + fila
                          + "  ◀ ¡AQUÍ ESTÁS!" + C["reset"])
        else:
            lineas.append(
                f"  {medalla:<3} {C['amarillo']}{e['ppm']:>5.0f} PPM{C['reset']}  "
                f"{e['nombre'][:18]:<18} {C['dim']}({e['precision']:.0f}%){C['reset']}"
            )
    return "\n".join(lineas)


def _quizas_registrar_marca(res):
    """Si el resultado entra al TOP 5, pide el nombre y lo registra."""
    if not ranking.califica(res["ppm"]):
        return
    print()
    print(C["amarillo"] + C["negrita"] + "  ⭐  ¡Tu velocidad entra al TOP 5!" + C["reset"])
    nombre = _leer("  Escribe tu nombre para el ranking: ")
    if not nombre or nombre.lower() == "salir":
        nombre = "Anónimo"
    nombre = nombre[:20]
    puesto = ranking.agregar(nombre, res)
    if puesto:
        animaciones.celebrar_top(nombre, res["ppm"], puesto)
        # Mostrar la tabla con el jugador resaltado.
        limpiar()
        print(BANNER)
        print()
        print(_bloque_top5(resaltar=puesto))


# --------------------------------------------------------------------------- #
#  Resultado
# --------------------------------------------------------------------------- #
def mostrar_resultado(res):
    limpiar()
    print(BANNER)
    palabras = res["caracteres"] / 5
    print()
    print(C["negrita"] + "  📊  Resultado de la prueba" + C["reset"])
    print("  " + "─" * 40)
    print(f"  Velocidad ....... {C['amarillo']}{res['ppm']:.0f} PPM{C['reset']}  "
          f"({res['cpm']:.0f} caracteres/min)")
    print(f"  Precisión ....... {res['precision']:.1f}%")
    print(f"  Errores ......... {res['errores']}")
    print(f"  Tiempo .......... {res['tiempo']:.1f} s")
    print(f"  Longitud ........ {res['caracteres']} caracteres (~{palabras:.0f} palabras)")
    print("  " + "─" * 40)
    if res["ppm"] >= 60:
        print(C["correcto"] + "  ¡Excelente velocidad! 🚀" + C["reset"])
    elif res["ppm"] >= 35:
        print(C["correcto"] + "  ¡Buen ritmo! Sigue así. 👍" + C["reset"])
    else:
        print(C["dim"] + "  La constancia es la clave. 💪" + C["reset"])


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
        resp = _leer("\n  ¿Otra prueba? (s/n): ").lower()
        if resp not in ("s", "si", "sí", ""):
            return


def practicar_citas(sesion):
    citas = textos.cargar_citas()
    _practicar(sesion, citas, fuente="cita", es_citas=True)


def practicar_texto_propio(sesion):
    limpiar()
    print(BANNER)
    print("\n  Carga un archivo de texto (.txt) para practicar con él.")
    ruta = _leer("\n  Ruta del archivo (vacío para cancelar): ")
    if not ruta or ruta.lower() == "salir":
        return
    try:
        fragmentos = textos.cargar_texto_propio(ruta)
    except FileNotFoundError:
        print(C["error_bg"] + "  No se encontró el archivo." + C["reset"])
        _pausa()
        return
    except (ValueError, OSError) as e:
        print(C["error_bg"] + f"  No se pudo leer: {e}" + C["reset"])
        _pausa()
        return
    print(f"\n  Texto dividido en {len(fragmentos)} fragmento(s) para practicar.")
    _pausa()
    _practicar(sesion, fragmentos, fuente="propio", es_citas=False)


def ver_estadisticas(sesion):
    limpiar()
    print(BANNER)
    res = estadisticas.resumen(sesion)
    print("\n" + C["negrita"] + "  📈  Estadísticas de esta sesión" + C["reset"])
    if not res:
        print("\n  Aún no has hecho ninguna prueba en esta sesión.")
        _pausa()
        return
    print("  " + "─" * 46)
    print(f"  Pruebas en la sesión ...... {res['total']}")
    print(f"  Mejor velocidad ........... {C['amarillo']}{res['mejor_ppm']:.0f} PPM{C['reset']}")
    print(f"  Velocidad promedio ........ {res['ppm_promedio']:.0f} PPM")
    print(f"  Mejor precisión ........... {res['mejor_precision']:.1f}%")
    print(f"  Precisión promedio ........ {res['precision_promedio']:.1f}%")
    print("  " + "─" * 46)
    print(C["negrita"] + "  Últimas pruebas:" + C["reset"])
    print(f"  {'Hora':<20}{'PPM':>6}{'Precis.':>10}{'Errores':>9}")
    for r in res["recientes"]:
        hora = r["fecha"].replace("T", " ")
        print(f"  {hora:<20}{r['ppm']:>6.0f}{r['precision']:>9.1f}%{r['errores']:>9}")
    _pausa()


# --------------------------------------------------------------------------- #
#  Menú principal
# --------------------------------------------------------------------------- #
def menu_principal(sesion):
    while True:
        limpiar()
        print(BANNER)
        print()
        print(_bloque_top5())
        print()
        print("  1) Practicar con una cita aleatoria")
        print("  2) Practicar con mi propio texto (.txt)")
        print("  3) Ver estadísticas de la sesión")
        print("  4) Salir")
        opcion = _leer("\n  Elige una opción: ").lower()
        if opcion == "1":
            practicar_citas(sesion)
        elif opcion == "2":
            practicar_texto_propio(sesion)
        elif opcion == "3":
            ver_estadisticas(sesion)
        elif opcion in ("4", "salir", "q"):
            limpiar()
            print("  ¡Hasta la próxima! Sigue practicando. 👋\n")
            return


def ejecutar():
    ranking.seed_inicial()
    animaciones.intro()
    menu_principal(sesion=[])
