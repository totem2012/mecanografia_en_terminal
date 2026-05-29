#!/usr/bin/env python3
"""Entrenador de mecanografía para terminal.

Funciona en Linux y Windows, sin conexión a internet y sin dependencias
externas (solo la biblioteca estándar de Python 3).

Uso:
    python3 main.py
"""

from typing_trainer import platform_io, ui


def main():
    platform_io.configurar_terminal()
    try:
        ui.ejecutar()
    except KeyboardInterrupt:
        pass
    finally:
        platform_io.restaurar_terminal()


if __name__ == "__main__":
    main()
