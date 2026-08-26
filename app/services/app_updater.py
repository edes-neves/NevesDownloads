"""
Auto-update do aplicativo via GitHub Releases.

Verifica o repositório GitHub na busca de versões mais recentes,
baixa o AppImage e substitui o executável atual.
"""

import json
import logging
import shutil
import stat
import sys
from pathlib import Path
from urllib.request import Request, urlopen

from app.core.constants import APP_NAME, APP_VERSION
from app.i18n import _

logger = logging.getLogger("neves_downloads")

# Configuração do repositório GitHub
_GITHUB_REPO = "edes-neves/NevesDownloads"
_GITHUB_API_URL = f"https://api.github.com/repos/{_GITHUB_REPO}/releases/latest"
_GITHUB_RELEASES_URL = f"https://github.com/{_GITHUB_REPO}/releases/latest"
_USER_AGENT = f"{APP_NAME}/{APP_VERSION}"


def _get_executable_path() -> Path | None:
    """Retorna o caminho do executável atual (AppImage ou script Python)."""
    import os

    # AppImage define APPIMAGE ao extrair para /tmp
    appimage = os.environ.get("APPIMAGE")
    if appimage:
        return Path(appimage).resolve()

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    # Modo desenvolvimento — sem auto-update
    return None


def _get_app_dir() -> Path:
    """Retorna o diretório do executável."""
    exe = _get_executable_path()
    if exe:
        return exe.parent
    return Path(__file__).resolve().parent.parent.parent


def check_latest_release() -> dict | None:
    """
    Consulta a API do GitHub para a release mais recente.

    Retorna:
        {
            "version": str,         # tag_name sem prefixo 'v'
            "tag": str,             # tag_name original (ex: "v1.2.0")
            "name": str,            # nome da release
            "body": str,            # descrição/changelog
            "published_at": str,    # data de publicação
            "assets": [             # binários anexados
                {
                    "name": str,
                    "browser_download_url": str,
                    "size": int,
                }
            ]
        }
    ou None em caso de falha.
    """
    try:
        req = Request(
            _GITHUB_API_URL,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": _USER_AGENT,
            },
        )
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        tag = data.get("tag_name", "")
        version = tag.lstrip("v") if tag else ""

        assets = []
        for a in data.get("assets", []):
            name = a.get("name", "")
            # Filtra apenas AppImages e binários relevantes
            if name.endswith((".AppImage", ".exe", ".zip")):
                assets.append(
                    {
                        "name": name,
                        "browser_download_url": a.get("browser_download_url", ""),
                        "size": a.get("size", 0),
                    }
                )

        return {
            "version": version,
            "tag": tag,
            "name": data.get("name", ""),
            "body": data.get("body", ""),
            "published_at": data.get("published_at", ""),
            "assets": assets,
        }

    except Exception as e:
        logger.error("Erro ao verificar release no GitHub: %s", e)
        return None


def check_for_update() -> dict | None:
    """
    Verifica se há uma versão mais recente disponível.

    Retorna:
        {
            "available": bool,
            "current": str,
            "latest": str,
            "release": dict | None,
        }
    """
    current = APP_VERSION
    release = check_latest_release()

    if not release or not release["version"]:
        return {
            "available": False,
            "current": current,
            "latest": "unknown",
            "release": None,
        }

    latest = release["version"]

    # Compara versões simples (x.y.z)
    try:
        current_parts = tuple(int(x) for x in current.split("."))
        latest_parts = tuple(int(x) for x in latest.split("."))
        available = latest_parts > current_parts
    except (ValueError, AttributeError):
        available = current != latest

    return {
        "available": available,
        "current": current,
        "latest": latest,
        "release": release,
    }


def download_release_asset(url: str, dest: Path, progress_callback=None) -> bool:
    """
    Baixa um asset de release do GitHub.

    Args:
        url: URL de download do asset.
        dest: Caminho de destino.
        progress_callback: Callable(bytes_downloaded, total_size).

    Retorna True se o download foi concluído com sucesso.
    """
    try:
        req = Request(
            url,
            headers={
                "User-Agent": _USER_AGENT,
                "Accept": "application/octet-stream",
            },
        )
        with urlopen(req, timeout=300) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 64 * 1024  # 64 KB

            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total)

        logger.info("Download concluído: %s (%d bytes)", dest.name, dest.stat().st_size)
        return True

    except Exception as e:
        logger.error("Erro ao baixar asset: %s", e)
        return False


def install_update(asset_path: Path) -> dict:
    """
    Instala uma atualização substituindo o executável atual.

    Retorna:
        {"success": bool, "message": str, "requires_restart": bool}
    """
    exe = _get_executable_path()
    if not exe:
        return {
            "success": False,
            "message": "Auto-update indisponível no modo de desenvolvimento.",
            "requires_restart": False,
        }

    try:
        # Verifica se o asset é AppImage
        if asset_path.suffix == ".AppImage" or "AppImage" in asset_path.name:
            # Torna executável
            asset_path.chmod(asset_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

            # Backup do executável atual
            backup = exe.with_suffix(".AppImage.bak")
            if backup.exists():
                backup.unlink()
            shutil.move(str(exe), str(backup))

            # Substitui pelo novo
            shutil.move(str(asset_path), str(exe))
            exe.chmod(exe.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

            msg = _("updater.app_updated").format(version=APP_VERSION)
            logger.info(msg)

            return {
                "success": True,
                "message": msg,
                "requires_restart": True,
            }

        return {
            "success": False,
            "message": "Formato de asset não suportado: " + asset_path.name,
            "requires_restart": False,
        }

    except Exception as e:
        msg = _("updater.install_failed").format(error=str(e))
        logger.error(msg)
        return {
            "success": False,
            "message": msg,
            "requires_restart": False,
        }


def _cleanup_backups():
    """Remove backups de atualizações anteriores."""
    exe = _get_executable_path()
    if not exe:
        return
    for bak in exe.parent.glob("*.AppImage.bak"):
        try:
            bak.unlink()
            logger.info("Backup removido: %s", bak.name)
        except OSError:
            pass
