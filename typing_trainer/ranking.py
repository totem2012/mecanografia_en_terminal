"""TOP 5 de velocidades (ranking arcade global).

El ranking se ordena por PPM (velocidad). Se permiten nombres repetidos.
Se guarda en data/ranking.json y se conservan solo las TOPE mejores marcas.
"""

import json
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE = Path(sys.executable).parent
else:
    BASE = Path(__file__).resolve().parent.parent
RUTA = BASE / "data" / "ranking.json"
TOPE = 5


def cargar():
    """Devuelve el ranking (lista de dicts) ordenado de mayor a menor PPM."""
    if not RUTA.is_file():
        return []
    try:
        datos = json.loads(RUTA.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(datos, list):
        return []
    datos.sort(key=lambda e: -e.get("ppm", 0))
    return datos[:TOPE]


def _guardar(ranking):
    RUTA.parent.mkdir(parents=True, exist_ok=True)
    tmp = RUTA.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ranking, f, ensure_ascii=False, indent=2)
    tmp.replace(RUTA)


def califica(ppm, ranking=None):
    """¿Esta marca entra al TOP 5?"""
    ranking = cargar() if ranking is None else ranking
    if len(ranking) < TOPE:
        return True
    return ppm > ranking[-1]["ppm"]


def agregar(nombre, resultado):
    """Inserta una marca en el ranking. Devuelve el puesto (1..TOPE) o None."""
    ranking = cargar()
    entrada = {
        "nombre": nombre,
        "ppm": resultado["ppm"],
        "precision": resultado["precision"],
        "fecha": resultado["fecha"],
    }
    ranking.append(entrada)
    ranking.sort(key=lambda e: -e.get("ppm", 0))     # orden estable: empates conservan orden
    puesto = next(i for i, e in enumerate(ranking) if e is entrada)
    ranking = ranking[:TOPE]
    if puesto < TOPE:
        _guardar(ranking)
        return puesto + 1
    return None


def _sembrar_desde(candidatos):
    if not candidatos:
        return
    candidatos.sort(key=lambda e: -e["ppm"])
    _guardar(candidatos[:TOPE])


def seed_inicial():
    """Si no hay ranking aún, lo siembra con datos heredados (perfiles o
    historial antiguo) para que el TOP 5 no aparezca vacío la primera vez."""
    if RUTA.exists():
        return

    candidatos = []
    dir_perfiles = BASE / "data" / "perfiles"
    if dir_perfiles.is_dir():
        for f in dir_perfiles.glob("*.json"):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            nombre = d.get("nombre", f.stem)
            for r in d.get("historial", []):
                if "ppm" in r:
                    candidatos.append({"nombre": nombre, "ppm": r["ppm"],
                                       "precision": r.get("precision", 0),
                                       "fecha": r.get("fecha", "")})

    if not candidatos:  # respaldos antiguos sin nombre de jugador
        for legado in ("historial.json", "historial.json.bak"):
            p = BASE / "data" / legado
            if p.is_file():
                try:
                    arr = json.loads(p.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue
                for r in (arr if isinstance(arr, list) else []):
                    if "ppm" in r:
                        candidatos.append({"nombre": "Anónimo", "ppm": r["ppm"],
                                           "precision": r.get("precision", 0),
                                           "fecha": r.get("fecha", "")})

    _sembrar_desde(candidatos)
