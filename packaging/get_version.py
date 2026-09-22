"""Imprime a versão única do projeto (lida de app/_version.py).

Evita duplicar a lógica de extração de versão nos scripts de build.
"""

import re
from pathlib import Path

_VERSION_FILE = Path("app/_version.py")

match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', _VERSION_FILE.read_text(encoding="utf-8"))
if not match:
    raise SystemExit(f"Versão não encontrada em {_VERSION_FILE}")

print(match.group(1))
