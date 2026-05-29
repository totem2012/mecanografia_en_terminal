"""Estadísticas agregadas de la sesión en curso.

La sesión vive en memoria (una lista de resultados que la UI va acumulando);
este módulo solo calcula el resumen a mostrar. No hay persistencia en disco:
el ranking (ver `ranking.py`) es lo único que se guarda entre ejecuciones.
"""


def resumen(historial):
    """Calcula estadísticas agregadas de la sesión."""
    if not historial:
        return None
    ppms = [r["ppm"] for r in historial]
    precisiones = [r["precision"] for r in historial]
    recientes = historial[-10:]
    return {
        "total": len(historial),
        "mejor_ppm": max(ppms),
        "ppm_promedio": sum(ppms) / len(ppms),
        "mejor_precision": max(precisiones),
        "precision_promedio": sum(precisiones) / len(precisiones),
        "recientes": list(reversed(recientes)),
    }
