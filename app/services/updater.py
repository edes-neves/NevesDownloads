"""
Serviço de atualização do yt-dlp.

Permite verificar e instalar a versão mais recente do yt-dlp
diretamente pela interface do aplicativo.
"""

import logging
import subprocess
import sys

import yt_dlp

from app.i18n import _

logger = logging.getLogger("neves_downloads")


def get_current_version() -> str:
    """Retorna a versão atualmente instalada do yt-dlp."""
    return getattr(yt_dlp.version, "__version__", _("updater.unknown_version"))


def check_latest_version() -> str | None:
    """
    Verifica a versão mais recente disponível no PyPI (sem instalar).
    Retorna a string da versão ou None em caso de falha.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "index", "versions", "yt-dlp"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Saída típica: "yt-dlp (2024.12.23)"
        output = result.stdout.strip()
        if output:
            # Extrai versão entre parênteses
            start = output.find("(")
            end = output.find(")")
            if start != -1 and end != -1:
                return output[start + 1 : end]
            # Fallback: pega a primeira linha após ": "
            parts = output.split()
            if len(parts) >= 2:
                return parts[1]
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.error("Erro ao verificar versão do yt-dlp: %s", e)
    return None


def update_ytdlp() -> dict[str, str | bool | None]:
    """
    Executa a atualização do yt-dlp via pip.

    Retorna:
        {
            "success": bool,
            "old_version": str,
            "new_version": str | None,
            "message": str,
        }
    """
    old_version = get_current_version()
    logger.info("Atualizando yt-dlp (versão atual: %s)...", old_version)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp[default]"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        new_version = get_current_version()

        if result.returncode == 0:
            if new_version != old_version:
                msg = _("updater.updated").format(old=old_version, new=new_version)
                logger.info(msg)
            else:
                msg = _("updater.up_to_date").format(version=new_version)
                logger.info(msg)
            return {
                "success": True,
                "old_version": old_version,
                "new_version": new_version,
                "message": msg,
            }
        else:
            error_msg = result.stderr.strip() or result.stdout.strip()
            msg = _("updater.failed").format(error=error_msg[:300])
            logger.error(msg)
            return {
                "success": False,
                "old_version": old_version,
                "new_version": None,
                "message": msg,
            }

    except subprocess.TimeoutExpired:
        msg = _("updater.timeout")
        logger.error(msg)
        return {
            "success": False,
            "old_version": old_version,
            "new_version": None,
            "message": msg,
        }
    except Exception as e:
        msg = _("updater.unexpected_error").format(error=e)
        logger.error(msg)
        return {
            "success": False,
            "old_version": old_version,
            "new_version": None,
            "message": msg,
        }
