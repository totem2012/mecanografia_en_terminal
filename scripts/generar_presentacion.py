#!/usr/bin/env python3
"""Genera presentacion.pdf (deck horizontal A4) describiendo el proyecto.

Se dibuja con fpdf2 para tener control total del diseño (tema oscuro arcade),
ya que el entorno no tiene navegador headless ni buena conversión HTML->PDF.

Uso (desde la raíz del repo):
    .pdfvenv/bin/python scripts/generar_presentacion.py
"""

from pathlib import Path
from fpdf import FPDF

BASE = Path(__file__).resolve().parent.parent
FONT = "/usr/share/fonts/truetype/dejavu"

# Paleta (tema oscuro)
BG     = (13, 17, 23)
PANEL  = (18, 27, 38)
BORDER = (33, 48, 63)
INK    = (232, 238, 245)
MUT    = (159, 179, 200)
DIM    = (91, 107, 125)
TEAL   = (45, 212, 191)
CYAN   = (34, 211, 238)
BLUE   = (125, 211, 252)
GOLD   = (251, 191, 36)
GREEN  = (134, 211, 178)

W, H = 297, 210  # A4 horizontal (mm)


class Deck(FPDF):
    def __init__(self):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.set_auto_page_break(False)
        self.add_font("D", "", f"{FONT}/DejaVuSans.ttf")
        self.add_font("D", "B", f"{FONT}/DejaVuSans-Bold.ttf")
        self.add_font("M", "", f"{FONT}/DejaVuSansMono.ttf")
        self.set_text_color(*INK)
        self._page_no = 0

    # ---- helpers --------------------------------------------------------- #
    def bg(self):
        self.set_fill_color(*BG)
        self.rect(0, 0, W, H, "F")

    def accent(self):
        # franja superior degradada (simulada con bandas)
        cols = [(45, 212, 191), (34, 211, 238), (56, 189, 248)]
        bands = 60
        bw = W / bands
        for i in range(bands):
            t = i / (bands - 1)
            if t < 0.5:
                a, b, f = cols[0], cols[1], t / 0.5
            else:
                a, b, f = cols[1], cols[2], (t - 0.5) / 0.5
            c = tuple(int(a[j] + (b[j] - a[j]) * f) for j in range(3))
            self.set_fill_color(*c)
            self.rect(i * bw, 0, bw + 0.3, 6, "F")

    def slide(self, accent=True):
        self.add_page()
        self.bg()
        if accent:
            self.accent()
        self._page_no += 1

    def footer(self):
        self.set_draw_color(*BORDER)
        self.set_line_width(0.2)
        self.line(22, H - 18, W - 22, H - 18)
        self.set_font("D", "", 8)
        self.set_text_color(*DIM)
        self.set_xy(22, H - 16)
        self.cell(0, 5, "Mecanografía en Terminal")
        self.set_xy(W - 60, H - 16)
        self.cell(38, 5, f"{self._page_no} / 11", align="R")

    def kicker(self, txt, x=22, y=22):
        self.set_font("D", "B", 11)
        self.set_text_color(*TEAL)
        self.set_xy(x, y)
        self.cell(0, 6, txt.upper())

    def heading(self, txt, accent_word=None, x=22, y=30, size=26):
        self.set_xy(x, y)
        self.set_font("D", "B", size)
        if accent_word and accent_word in txt:
            pre, post = txt.split(accent_word, 1)
            self.set_text_color(*INK)
            self.cell(self.get_string_width(pre), size * 0.42, pre)
            self.set_text_color(*TEAL)
            self.cell(self.get_string_width(accent_word), size * 0.42, accent_word)
            self.set_text_color(*INK)
            self.cell(0, size * 0.42, post)
        else:
            self.set_text_color(*INK)
            self.cell(0, size * 0.42, txt)

    def rounded(self, x, y, w, h, r=3, fill=PANEL, border=BORDER):
        self.set_fill_color(*fill)
        self.set_draw_color(*border)
        self.set_line_width(0.3)
        self.rect(x, y, w, h, "DF")  # fpdf2 no traza esquinas; rect simple, limpio

    def bullets(self, items, x, y, w, lh=8, gap=4, size=12):
        self.set_x(x)
        cy = y
        for it in items:
            self.set_xy(x, cy)
            self.set_text_color(*TEAL)
            self.set_font("D", "B", size)
            self.cell(6, lh, "▸")
            self.set_xy(x + 7, cy)
            self.set_text_color(*INK)
            self.set_font("D", "", size)
            self.multi_cell(w - 7, lh, it)
            cy = self.get_y() + gap
        return cy

    def card(self, x, y, w, h, head, body):
        self.rounded(x, y, w, h)
        self.set_xy(x + 5, y + 4)
        self.set_font("D", "B", 12)
        self.set_text_color(*TEAL)
        self.cell(0, 6, head)
        self.set_xy(x + 5, y + 12)
        self.set_font("D", "", 10.5)
        self.set_text_color(*MUT)
        self.multi_cell(w - 10, 5, body)

    def codeblock(self, x, y, w, h, lines):
        self.set_fill_color(10, 15, 22)
        self.set_draw_color(*BORDER)
        self.rect(x, y, w, h, "DF")
        self.set_font("M", "", 10)
        cy = y + 6
        for color, txt in lines:
            self.set_xy(x + 5, cy)
            self.set_text_color(*color)
            self.cell(0, 5.5, txt)
            cy += 6


pdf = Deck()

# ----------------------------------------------------------------------- 1
pdf.slide()
pdf.set_fill_color(21, 54, 74)
pdf.rect(0, 6, W, 70, "F")  # banda superior tenue
pdf.bg() if False else None
pdf.set_xy(24, 40)
pdf.set_font("D", "B", 50)
pdf.set_text_color(*TEAL)
pdf.cell(0, 18, "⌨")
pdf.set_xy(24, 60)
pdf.set_font("D", "B", 46)
pdf.set_text_color(245, 248, 252)
pdf.cell(0, 18, "Mecanografía")
pdf.set_xy(24, 80)
pdf.cell(0, 18, "en Terminal")
pdf.set_xy(24, 108)
pdf.set_font("D", "", 15)
pdf.set_text_color(*MUT)
pdf.cell(0, 8, "Entrenador de mecanografía en español para la consola.")
pdf.set_xy(24, 117)
pdf.cell(0, 8, "Linux y Windows · sin internet · sin dependencias externas.")
pdf.set_fill_color(*TEAL)
pdf.rect(24, 135, 95, 11, "F")
pdf.set_xy(24, 137.5)
pdf.set_font("D", "B", 11)
pdf.set_text_color(*BG)
pdf.cell(95, 6, "Python 3 · solo biblioteca estándar", align="C")

# ----------------------------------------------------------------------- 2
pdf.slide()
pdf.kicker("El proyecto en una frase")
pdf.heading("Practica y mide tu velocidad al teclear", size=24, y=30)
pdf.set_xy(22, 44)
pdf.set_font("D", "", 14)
pdf.set_text_color(*MUT)
pdf.multi_cell(
    250, 7,
    "Una aplicación TUI que cronometra tu escritura, calcula tu velocidad "
    "(PPM) y precisión en tiempo real, y guarda un ranking arcade de las "
    "mejores marcas. Coloreado en vivo, teclado en pantalla y animaciones, "
    "todo con secuencias ANSI puras.")
stats = [("~1.5k", "líneas de Python"), ("9", "módulos"),
         ("5054", "citas para practicar"), ("49", "tests (todos OK)")]
x = 24
for n, l in stats:
    pdf.set_xy(x, 95)
    pdf.set_font("D", "B", 34)
    pdf.set_text_color(*CYAN)
    pdf.cell(60, 16, n, align="C")
    pdf.set_xy(x, 113)
    pdf.set_font("D", "", 10)
    pdf.set_text_color(*MUT)
    pdf.cell(60, 5, l, align="C")
    x += 65
pdf.footer()

# ----------------------------------------------------------------------- 3
pdf.slide()
pdf.kicker("Qué ofrece")
pdf.heading("Características principales", "principales", y=30, size=24)
cards = [
    ("Texto cronometrado", "Banco de +5000 fragmentos reales en español (con ñ y acentos) que mide velocidad y precisión."),
    ("Tu propio texto", "Carga cualquier .txt y se trocea en fragmentos con sentido, cortando por frases."),
    ("TOP 5 arcade", "Ranking de las 5 mejores marcas (PPM). Si entras, la app te pide el nombre y te registra."),
    ("Estadísticas de sesión", "Resumen de las pruebas hechas: mejor PPM, promedios y precisión."),
    ("Coloreado en vivo", "Verde = correcto, fondo rojo = error, cursor resaltado y teclado en pantalla."),
    ("Animaciones", "Intro tipo máquina de escribir y celebración al lograr el récord #1. Saltables."),
]
cw, ch = 124, 32
x0, y0, gx, gy = 22, 48, 9, 8
for i, (hd, bd) in enumerate(cards):
    cx = x0 + (i % 2) * (cw + gx)
    cy = y0 + (i // 2) * (ch + gy)
    pdf.card(cx, cy, cw, ch, hd, bd)
pdf.footer()

# ----------------------------------------------------------------------- 4
pdf.slide()
pdf.kicker("Cómo está construido")
pdf.heading("Arquitectura por módulos", "por módulos", y=30, size=24)
mods = [
    ("main.py", "Punto de entrada: configura y restaura el terminal."),
    ("platform_io.py", "Única capa que conoce el SO: teclado raw y ANSI."),
    ("engine.py", "Bucle de la prueba y cálculo de métricas."),
    ("renderer.py", "Dibujo del frame anti-parpadeo y ajuste de líneas."),
    ("textos.py", "Carga de citas y troceado de textos propios."),
    ("teclado.py", "Teclado QWERTY en pantalla; resalta la última tecla."),
    ("ranking.py", "TOP 5 persistente con escritura atómica."),
    ("estadisticas.py", "Resumen agregado de la sesión."),
    ("ui · animaciones", "Menús, pantallas e intro/celebración."),
]
y = 50
for mod, desc in mods:
    pdf.set_xy(22, y)
    pdf.set_font("M", "", 10.5)
    pdf.set_text_color(*GOLD)
    pdf.cell(46, 6, mod)
    pdf.set_font("D", "", 10.5)
    pdf.set_text_color(*MUT)
    pdf.cell(110, 6, desc)
    pdf.set_draw_color(*BORDER)
    pdf.line(22, y + 7.5, 178, y + 7.5)
    y += 8.6
pdf.card(186, 50, 88, 78, "Principio de diseño",
         "Separación estricta: la lógica pura (troceado, ajuste de líneas, "
         "ranking, estadísticas) no toca el terminal, así es testeable sin "
         "dependencias.\n\nToda la diferencia entre sistemas operativos vive "
         "aislada en platform_io.py; el resto del código es portable.")
pdf.footer()

# ----------------------------------------------------------------------- 5
pdf.slide()
pdf.kicker("Experiencia de usuario")
pdf.heading("Flujo de uso", "de uso", y=30, size=24)
pdf.bullets([
    "Arranca con una intro animada tipo máquina de escribir.",
    "El menú muestra siempre el TOP 5 actual.",
    "Eliges una cita aleatoria o tu propio archivo .txt.",
    "Tecleas: feedback de color por carácter y métricas en vivo.",
    "Al terminar ves el resultado; si entras al TOP, te registra.",
], x=22, y=50, w=120, lh=7, gap=5, size=12.5)
pdf.codeblock(150, 50, 124, 80, [
    (DIM,   "# Menú principal"),
    (GOLD,  " TOP 5 VELOCIDADES"),
    (INK,   "  67 PPM  pepino   (96%)"),
    (INK,   "  61 PPM  nahuel   (96%)"),
    (DIM,   "  ..."),
    (CYAN,  "1) Practicar con una cita aleatoria"),
    (CYAN,  "2) Practicar con mi propio texto"),
    (CYAN,  "3) Ver estadísticas de la sesión"),
    (CYAN,  "4) Salir"),
])
pdf.footer()

# ----------------------------------------------------------------------- 6
pdf.slide()
pdf.kicker("El corazón del entrenador")
pdf.heading("Motor y métricas", "métricas", y=30, size=24)
pdf.bullets([
    "El cronómetro arranca con la primera tecla, no antes.",
    "⌫ Retroceso corrige; ESC aborta sin guardar.",
    "Soporta UTF-8 multibyte: ñ y acentos = un carácter.",
    "Precisión 'cruda': un error cuenta aunque luego lo corrijas.",
], x=22, y=50, w=125, lh=7, gap=5, size=12.5)
pdf.card(158, 50, 116, 78, "Fórmulas",
         "PPM = (caracteres correctos ÷ 5) por minuto\n\n"
         "Precisión = pulsaciones correctas ÷ pulsaciones totales\n\n"
         "Cada prueba devuelve PPM, CPM, precisión, errores, tiempo y "
         "longitud del fragmento.")
pdf.footer()

# ----------------------------------------------------------------------- 7
pdf.slide()
pdf.kicker("El contenido")
pdf.heading("El banco de citas", "citas", y=30, size=24)
pdf.set_xy(22, 44)
pdf.set_font("D", "", 13)
pdf.set_text_color(*MUT)
pdf.multi_cell(250, 6.5, "~5000 fragmentos listos para practicar, generados "
               "sin depender de internet en tiempo de ejecución.")
cards7 = [
    ("54 citas curadas", "Frases célebres seleccionadas a mano en citas_curadas.json, la semilla del banco."),
    ("~5000 de obras clásicas", "Fragmentos de 10 obras de dominio público (Cervantes, Pardo Bazán, Unamuno…)."),
    ("Importador Gutenberg", "El script descarga, limpia cabeceras, trocea por frases y filtra por calidad."),
    ("Ampliable", "Añade obras por su id de Gutendex o tus citas a mano. La app nunca necesita red."),
]
for i, (hd, bd) in enumerate(cards7):
    cx = 22 + (i % 2) * 133
    cy = 64 + (i // 2) * 38
    pdf.card(cx, cy, 124, 32, hd, bd)
pdf.footer()

# ----------------------------------------------------------------------- 8
pdf.slide()
pdf.kicker("El gancho arcade")
pdf.heading("TOP 5 de velocidades", "de velocidades", y=30, size=24)
pdf.bullets([
    "Se ordena por PPM; se permiten nombres repetidos.",
    "Persiste en ranking.json con escritura atómica (tmp + replace).",
    "Al entrar al TOP, una celebración resalta tu fila (#1 es la más épica).",
    "Siembra inicial desde historiales o perfiles antiguos si está vacío.",
], x=22, y=50, w=125, lh=7, gap=5, size=12.5)
pdf.codeblock(158, 50, 116, 60, [
    (GOLD,  "1.  67 PPM  pepino   (96%)  <- AQUI"),
    (GOLD,  "2.  61 PPM  nahuel   (96%)"),
    (GOLD,  "3.  61 PPM  nahuel   (98%)"),
    (INK,   "4.  61 PPM  nahuel   (95%)"),
    (INK,   "5.  60 PPM  nahuel   (94%)"),
])
pdf.footer()

# ----------------------------------------------------------------------- 9
pdf.slide()
pdf.kicker("Robustez")
pdf.heading("Calidad y portabilidad", "portabilidad", y=30, size=24)
cards9 = [
    ("49 tests, todos verdes", "Lógica pura cubierta con unittest de la stdlib, sin dependencias externas."),
    ("Multiplataforma", "Linux (termios/tty) y Windows (msvcrt) tras una única interfaz común."),
    ("Cero dependencias", "Solo Python 3.7+ estándar. Nada de pip en tiempo de ejecución."),
    ("⚙ Configurable por entorno", "Desactiva animaciones o teclado con variables MECANOGRAFIA_SIN_*."),
]
for i, (hd, bd) in enumerate(cards9):
    cx = 22 + (i % 2) * 133
    cy = 50 + (i // 2) * 38
    pdf.card(cx, cy, 124, 32, hd, bd)
pdf.footer()

# ----------------------------------------------------------------------- 10
pdf.slide()
pdf.kicker("Manos a la obra")
pdf.heading("Cómo ejecutarlo", "ejecutarlo", y=30, size=24)
pdf.codeblock(22, 48, 252, 82, [
    (DIM,  "# Lanzar la aplicación"),
    (CYAN, "python3 main.py"),
    (INK,  ""),
    (DIM,  "# Ejecutar la batería de tests"),
    (CYAN, "python3 -m unittest discover -s tests"),
    (INK,  ""),
    (DIM,  "# Regenerar o ampliar el banco de citas"),
    (CYAN, "python3 scripts/importar_gutenberg.py"),
    (INK,  ""),
    (DIM,  "# (Opcional) binario único, sin requerir Python"),
    (CYAN, 'pyinstaller --onefile --add-data "data:data" main.py'),
])
pdf.footer()

# ----------------------------------------------------------------------- 11
pdf.slide()
pdf.set_xy(24, 55)
pdf.set_font("D", "B", 44)
pdf.set_text_color(*TEAL)
pdf.cell(0, 16, "⌨")
pdf.set_xy(24, 72)
pdf.set_font("D", "B", 40)
pdf.set_text_color(245, 248, 252)
pdf.cell(0, 16, "Practica · Mejora")
pdf.set_xy(24, 90)
pdf.cell(0, 16, "Domina el teclado")
pdf.set_xy(24, 118)
pdf.set_font("D", "", 14)
pdf.set_text_color(*MUT)
pdf.multi_cell(250, 7, "Un proyecto pequeño, limpio y portable: lógica "
               "testeable, E/S aislada y una experiencia arcade en el terminal.")
pdf.set_fill_color(*TEAL)
pdf.rect(24, 145, 45, 11, "F")
pdf.set_xy(24, 147.5)
pdf.set_font("D", "B", 11)
pdf.set_text_color(*BG)
pdf.cell(45, 6, "¡Gracias!", align="C")

out = BASE / "presentacion.pdf"
pdf.output(str(out))
print("OK ->", out)
