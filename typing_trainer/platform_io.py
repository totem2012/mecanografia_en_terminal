"""Capa de entrada/salida multiplataforma.

Es el ÚNICO módulo que conoce diferencias entre sistemas operativos.
Expone:
  - configurar_terminal() / restaurar_terminal()
  - raw_mode  (context manager para lectura tecla a tecla)
  - leer_tecla() -> (tipo, caracter)

Tipos devueltos por leer_tecla():
  'CHAR'      -> caracter imprimible (incluye ñ, acentos); 2.º valor = el caracter
  'ENTER', 'BACKSPACE', 'ESC', 'TAB', 'CTRL_C', 'SPECIAL', 'OTHER'
"""

import os
import sys

IS_WINDOWS = os.name == "nt"


def configurar_terminal():
    """Prepara la consola: UTF-8 en salida y secuencias ANSI en Windows."""
    if IS_WINDOWS:
        # En Windows 10+ esto habilita el procesamiento de secuencias VT.
        os.system("")
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            modo = ctypes.c_uint32()
            kernel32.GetConsoleMode(handle, ctypes.byref(modo))
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            kernel32.SetConsoleMode(handle, modo.value | 0x0004)
        except Exception:
            pass
    # Forzar UTF-8 en la salida para que ñ y acentos se vean bien.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def restaurar_terminal():
    """Restaura el cursor por si quedó oculto."""
    try:
        sys.stdout.write("\x1b[?25h")
        sys.stdout.flush()
    except Exception:
        pass


# --------------------------------------------------------------------------- #
#  Implementación específica por sistema operativo
# --------------------------------------------------------------------------- #
if IS_WINDOWS:
    import msvcrt

    class raw_mode:
        """En Windows msvcrt ya lee tecla a tecla; no hay que cambiar modos."""

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def leer_tecla():
        ch = msvcrt.getwch()
        # Teclas especiales (flechas, F1..F12) llegan en dos lecturas.
        if ch in ("\x00", "\xe0"):
            msvcrt.getwch()  # descartar el segundo código
            return ("SPECIAL", None)
        if ch in ("\r", "\n"):
            return ("ENTER", None)
        if ch == "\x08":
            return ("BACKSPACE", None)
        if ch == "\x1b":
            return ("ESC", None)
        if ch == "\x03":
            return ("CTRL_C", None)
        if ch == "\t":
            return ("TAB", None)
        if ord(ch) < 32:
            return ("OTHER", None)
        return ("CHAR", ch)

    def hay_tecla():
        """¿Hay una tecla pendiente? (no bloqueante)"""
        return msvcrt.kbhit()

    def vaciar_entrada():
        while msvcrt.kbhit():
            msvcrt.getwch()

else:
    import select
    import termios
    import tty

    class raw_mode:
        """Pone stdin en modo crudo (raw) mientras dure el bloque `with`."""

        def __enter__(self):
            self.fd = sys.stdin.fileno()
            self.anterior = termios.tcgetattr(self.fd)
            tty.setraw(self.fd)
            # `setraw` también desactiva el post-procesado de SALIDA (OPOST), y
            # como stdin y stdout son el mismo terminal eso afecta al dibujado:
            # sin OPOST/ONLCR, "\n" es un avance de línea puro (LF) que NO
            # devuelve el cursor a la columna 0, así que cada línea del frame se
            # pinta corrida a la derecha de donde acabó la anterior (en Windows
            # no pasa porque msvcrt no toca el modo de salida). Restauramos los
            # flags de salida originales; el modo crudo de ENTRADA se conserva.
            modo = termios.tcgetattr(self.fd)
            modo[1] = self.anterior[1]
            termios.tcsetattr(self.fd, termios.TCSADRAIN, modo)
            return self

        def __exit__(self, *exc):
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.anterior)
            return False

    def _leer_utf8(primer_byte):
        """Lee los bytes de continuación de un caracter UTF-8 multibyte."""
        if primer_byte < 0x80:
            n = 1
        elif primer_byte >> 5 == 0b110:
            n = 2
        elif primer_byte >> 4 == 0b1110:
            n = 3
        elif primer_byte >> 3 == 0b11110:
            n = 4
        else:
            n = 1
        buf = bytes([primer_byte])
        for _ in range(n - 1):
            buf += os.read(0, 1)
        try:
            return buf.decode("utf-8")
        except UnicodeDecodeError:
            return ""

    def leer_tecla():
        b = os.read(0, 1)
        if not b:
            return ("OTHER", None)
        o = b[0]
        if o in (13, 10):
            return ("ENTER", None)
        if o in (127, 8):
            return ("BACKSPACE", None)
        if o == 9:
            return ("TAB", None)
        if o == 3:
            return ("CTRL_C", None)
        if o == 27:
            # ¿Inicio de secuencia de escape (flechas, etc.)? Drenarla.
            listo, _, _ = select.select([0], [], [], 0.001)
            if listo:
                os.read(0, 5)  # descartar el resto de la secuencia
                return ("SPECIAL", None)
            return ("ESC", None)
        if o < 32:
            return ("OTHER", None)
        ch = _leer_utf8(o)
        if not ch:
            return ("OTHER", None)
        return ("CHAR", ch)

    def hay_tecla():
        """¿Hay una tecla pendiente? (no bloqueante)"""
        listo, _, _ = select.select([0], [], [], 0)
        return bool(listo)

    def vaciar_entrada():
        try:
            termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
        except Exception:
            pass
