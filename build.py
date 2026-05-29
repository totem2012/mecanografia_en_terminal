"""Script de construcción del ejecutable.

Uso:
    python3 build.py          # Linux / macOS
    python build.py           # Windows

Genera en dist/ un ejecutable único: mecanografia (Linux) o mecanografia.exe (Windows).
"""

import os
import subprocess
import sys

SEP = ";" if os.name == "nt" else ":"

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onefile",
    "--name", "mecanografia",
    "--add-data", f"data/citas.json{SEP}data",
    "--console",
    "main.py",
]

subprocess.run(cmd, check=True)
