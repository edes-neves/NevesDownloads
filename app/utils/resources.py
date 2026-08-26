"""
Resolução de caminhos de recursos (assets) para o aplicativo.

Funciona tanto em ambiente de desenvolvimento (rodando via `python main.py`)
quanto em binários empacotados com PyInstaller (modo "frozen").

Quando o app é empacotado, os arquivos de recursos (ex.: ícones) precisam ser
buscados dentro do diretório temporário criado pelo PyInstaller
(`sys._MEIPASS`) ou no diretório onde o binário está (`--onedir`).
"""

import sys
from pathlib import Path

# Diretório raiz do projeto (quando em desenvolvimento).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def is_frozen() -> bool:
    """Retorna True se o aplicativo está em execução a partir de um bundle PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def get_bundle_dir() -> Path:
    """
    Retorna o diretório base dos recursos no bundle empacotado.

    - `--onefile`: uso `sys._MEIPASS` (dir temporário de extração).
    - `--onedir`: uso `sys.executable` (dir do binário).
    """
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(sys.executable).resolve().parent


def get_resource_path(relative: str | Path = "assets") -> Path:
    """
    Retorna o caminho absoluto de um recurso, funcionando em dev e packaged.

    `relative` é relativo à raiz do projeto em dev (ex.: "assets/Icone.png") e
    relativo ao diretório raiz dos recursos no bundle quando empacotado.
    """
    rel = Path(relative)

    if is_frozen():
        return get_bundle_dir() / rel

    return _PROJECT_ROOT / rel


def get_project_root() -> Path:
    """Retorna o diretório raiz do projeto (dev) ou do bundle (packaged)."""
    if is_frozen():
        return get_bundle_dir()
    return _PROJECT_ROOT
