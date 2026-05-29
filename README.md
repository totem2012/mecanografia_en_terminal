# ⌨ Mecanografía en Terminal

Aplicación de terminal para practicar mecanografía en español. Funciona en
**Linux y Windows**, **sin conexión a internet** y **sin dependencias externas**
(solo la biblioteca estándar de Python 3.7+).

## Características

- **Texto cronometrado (PPM)**: practica con un banco de **más de 5000 fragmentos**
  reales en español (con `ñ` y acentos) y mide tu velocidad y precisión.
- **Tu propio texto**: carga cualquier archivo `.txt` y se trocea en fragmentos
  con sentido para practicar.
- **TOP 5 de velocidades** (estilo arcade): el ranking de las 5 mejores marcas
  (PPM) se muestra en el menú principal. Si tu velocidad entra al TOP, la app te
  pide tu nombre y te registra; si no, sigues normal.
- **Estadísticas de la sesión**: resumen de las pruebas hechas desde que abriste
  la app (mejor PPM, promedios, precisión).
- Coloreado en vivo: verde = correcto, fondo rojo = error, cursor resaltado.
- **Animaciones**: intro con efecto de máquina de escribir al abrir y celebración
  al conseguir el récord #1. Saltables con cualquier tecla; se pueden desactivar
  con `MECANOGRAFIA_SIN_ANIMACION=1`.

## Uso

```bash
python3 main.py
```

Entras directo al menú, que muestra el TOP 5:

1. Practicar con una cita aleatoria
2. Practicar con mi propio texto (`.txt`)
3. Ver estadísticas de la sesión
4. Salir

### TOP 5 de velocidades

El ranking se guarda en `data/ranking.json`, ordenado por **PPM** (se permiten
nombres repetidos). Al terminar una prueba, si superas la marca más baja del TOP 5
—o si aún hay huecos— la app te pide el nombre y registra la marca. Para reiniciar
el ranking, borra `data/ranking.json`.

Durante una prueba: escribe el texto mostrado. **⌫ Retroceso** corrige; **ESC**
sale sin guardar. La prueba termina al completar el texto.

## Métricas

- **PPM** (palabras por minuto) = caracteres correctos / 5, por minuto.
- **Precisión** = pulsaciones correctas / pulsaciones totales (precisión "cruda":
  un error cuenta aunque luego lo corrijas).

## El banco de citas

`data/citas.json` (~5000 entradas) se compone de:

- **54 citas célebres** curadas a mano (`data/citas_curadas.json`, la semilla).
- **~5000 fragmentos** de 10 obras clásicas de **dominio público** descargadas de
  Project Gutenberg (Cervantes, Pardo Bazán, Blasco Ibáñez, Palacio Valdés,
  Unamuno, Fernán Caballero y una traducción de Dostoyevski).

### Regenerar o ampliar el banco

El script `scripts/importar_gutenberg.py` descarga las obras, elimina las
cabeceras de Gutenberg, trocea por frases y filtra por calidad:

```bash
python3 scripts/importar_gutenberg.py
```

Para añadir más obras, agrega su `(id, autor, obra)` a la lista `OBRAS` del script
(busca el id en https://gutendex.com). Las descargas se cachean en
`data/.descargas/` (puedes borrar esa carpeta; solo se usa para re-ejecutar el
importador sin volver a descargar). **La app en sí no necesita internet.**

### Añadir tus propias citas a mano

Edita `data/citas_curadas.json` (UTF-8) y vuelve a ejecutar el importador, o
edita `data/citas.json` directamente:

```json
[
  {"texto": "Tu cita aquí.", "autor": "Autor"}
]
```

## Estructura

```
main.py                  Punto de entrada
typing_trainer/
  platform_io.py         E/S multiplataforma (teclado + ANSI)
  renderer.py            Renderizado de frames
  engine.py              Lógica de la prueba y métricas
  textos.py              Carga de citas y textos propios
  animaciones.py         Intro y celebración del récord #1
  ranking.py             TOP 5 de velocidades
  estadisticas.py        Cálculo de estadísticas (resumen de sesión)
  ui.py                  Menús y pantallas
data/
  citas.json             Banco de citas (incluido)
  ranking.json           TOP 5 (se genera solo)
```

## Tests

La lógica pura (troceado de texto, ajuste de líneas, ranking, estadísticas) está
cubierta por una batería de tests con la biblioteca estándar (`unittest`), sin
dependencias externas:

```bash
python3 -m unittest discover -s tests
```

## Binario único (opcional)

Si quieres distribuirlo sin requerir Python instalado:

```bash
pip install pyinstaller
pyinstaller --onefile --add-data "data:data" main.py   # Linux/macOS
pyinstaller --onefile --add-data "data;data" main.py   # Windows
```
