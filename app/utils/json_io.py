"""
Utilitários de leitura/escrita de JSON com consistência em disco.

Em vez de abrir e sobrescrever o arquivo no lugar, a gravação atômica
escreve primeiro em um arquivo temporário no mesmo diretório e depois
usa os.replace (atômico no mesmo filesystem). Assim, uma falha no meio
da escrita nunca corrompe o arquivo original.
"""

import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def read_json(path: Path, default: Any = None) -> Any:
    """Lê um JSON do disco; retorna `default` em caso de erro."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def atomic_write_json(path: Path, data: Any) -> None:
    """Escreve `data` como JSON de forma atômica (arquivo temporário + os.replace).

    Lança OSError em caso de falha, deixando o arquivo original intacto.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except OSError:
        with contextlib.suppress(OSError):
            os.unlink(tmp_path)
        raise
