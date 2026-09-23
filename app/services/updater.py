"""
Serviço de atualização do yt-dlp.

Permite verificar e instalar a versão mais recente do yt-dlp
diretamente pela interface do aplicativo.
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

import yt_dlp

from app.i18n import _

logger = logging.getLogger("neves_downloads")

# Consulta rápida de versão no PyPI (sem execução de subprocesso)
PYPI_JSON_URL = "https://pypi.org/pypi/yt-dlp/json"
_HTTP_TIMEOUT = 10

# Binário standalone oficial do yt-dlp (auto-contido, sem Python).
YTDLP_STANDALONE_URL = (
    "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
    if sys.platform.startswith("win")
    else "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"
)


def get_current_version() -> str:
    """Retorna a versão atualmente instalada do yt-dlp."""
    return getattr(yt_dlp.version, "__version__", _("updater.unknown_version"))


def _is_frozen() -> bool:
    """True quando o app roda a partir de um pacote PyInstaller/AppImage."""
    return bool(getattr(sys, "frozen", False))


def get_user_ytdlp_path() -> Path:
    """Caminho de um yt-dlp independente mantido na pasta de dados do usuário.

    O AppImage/binário não pode alterar o yt-dlp embutido (filesystem
    read-only), então a atualização mantém uma cópia standalone oficial na
    pasta de dados do usuário — onde `yt-dlp -U` pode realmente funcionar.
    """
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
        name = "yt-dlp.exe"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
        name = "yt-dlp"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share"))
        name = "yt-dlp"
    return base / "NevesDownloads" / name


def _binary_version(target: Path) -> str | None:
    """Versão de um binário standalone de yt-dlp (None se não executar)."""
    try:
        result = subprocess.run([str(target), "--version"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return (result.stdout or result.stderr).strip() or None


def _download_standalone(target: Path) -> None:
    """Baixa o binário standalone mais recente do yt-dlp para `target`.

    A escrita é atômica (arquivo `.tmp` + rename) e o binário é validado com
    `--version` antes de substituir o destino.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    tmp.unlink(missing_ok=True)
    req = urllib.request.Request(YTDLP_STANDALONE_URL, headers={"User-Agent": "NevesDownloads"})
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp, tmp.open("wb") as fh:
            shutil.copyfileobj(resp, fh)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    if tmp.stat().st_size == 0:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(_("updater.download_failed"))
    if not sys.platform.startswith("win"):
        tmp.chmod(tmp.stat().st_mode | 0o111)
    if _binary_version(tmp) is None:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(_("updater.download_invalid"))
    tmp.replace(target)


def get_manual_update_commands() -> str:
    """Comandos completos (copiar e colar) para o usuário atualizar o yt-dlp.

    Usados quando a atualização automática não é possível: mostrados em uma
    mensagem para o usuário com o comando integral.
    """
    app_release = "https://github.com/edes-neves/NevesDownloads/releases"
    if sys.platform.startswith("win"):
        commands = [
            "pip install --user --upgrade yt-dlp",
            'powershell -Command "Invoke-WebRequest '
            "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe "
            "-OutFile '$env:LOCALAPPDATA\\NevesDownloads\\yt-dlp.exe'; "
            "& '$env:LOCALAPPDATA\\NevesDownloads\\yt-dlp.exe' -U\"",
        ]
    elif sys.platform == "darwin":
        commands = [
            "python3 -m pip install --user --upgrade yt-dlp",
            "mkdir -p ~/bin && curl -fL -o ~/bin/yt-dlp "
            "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp "
            "&& chmod +x ~/bin/yt-dlp && ~/bin/yt-dlp -U",
        ]
    else:
        commands = [
            "python3 -m pip install --user --upgrade yt-dlp",
            "mkdir -p ~/.local/bin && curl -fL -o ~/.local/bin/yt-dlp "
            "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp "
            "&& chmod +x ~/.local/bin/yt-dlp && ~/.local/bin/yt-dlp -U",
            "# Arch/BigLinux: sudo pacman -S --needed yt-dlp",
        ]
    return "\n".join(commands) + f"\n\n{_('updater.manual_commands_app')}:\n{app_release}"


def _update_packaged() -> dict[str, str | bool | None]:
    """Atualiza um yt-dlp independente na pasta de dados do usuário.

    Usado em modo empacotado (AppImage/binário), onde o yt-dlp embutido não é
    alterável. Sempre opera no binário standalone do usuário — jamais invoca
    ``sys.executable``/pip (que abriria outra instância do aplicativo).
    """
    target = get_user_ytdlp_path()
    existed = target.is_file()
    old_version = _binary_version(target) or get_current_version()
    try:
        if existed:
            proc = subprocess.run([str(target), "-U"], capture_output=True, text=True, timeout=180)
            if proc.returncode != 0:
                logger.warning(
                    "yt-dlp -U falhou; baixando binário diretamente: %s",
                    (proc.stderr or proc.stdout).strip()[:200],
                )
                _download_standalone(target)
        else:
            _download_standalone(target)
    except Exception as e:
        msg = _("updater.user_update_failed").format(error=e)
        logger.error(msg, exc_info=True)
        return {
            "success": False,
            "old_version": old_version,
            "new_version": None,
            "message": msg,
            "command": get_manual_update_commands(),
        }

    new_version = _binary_version(target) or get_current_version()
    if existed:
        if old_version and new_version and old_version != new_version:
            msg = _("updater.user_updated").format(old=old_version, new=new_version)
        else:
            msg = _("updater.user_uptodate").format(version=new_version)
    else:
        msg = _("updater.user_installed").format(new=new_version)
    note = _("updater.embedded_note")
    location = _("updater.user_location").format(path=target)
    return {
        "success": True,
        "old_version": old_version,
        "new_version": new_version,
        "message": f"{msg}\n{location}\n\n{note}",
    }


def _check_via_pypi() -> str | None:
    """Consulta o PyPI via HTTP e retorna a última versão (ou None em falha)."""
    try:
        with urllib.request.urlopen(PYPI_JSON_URL, timeout=_HTTP_TIMEOUT) as resp:
            data = json.load(resp)
        version = data.get("info", {}).get("version")
        return version if isinstance(version, str) else None
    except (OSError, ValueError) as e:
        logger.debug("PyPI via HTTP indisponível, usando fallback pip: %s", e, exc_info=True)
        return None


def _check_via_pip() -> str | None:
    """Fallback: consulta a versão via `pip index versions` (sem instalar).

    Em pacotes empacotados (AppImage/PyInstaller) ``sys.executable`` é o
    próprio aplicativo, não o Python — executá-lo abriria outra instância.
    Nesse modo o fallback via pip é ignorado.
    """
    if _is_frozen():
        logger.debug("Empacotado: fallback pip ignorado (sys.executable é o app).")
        return None
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
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        logger.error("Erro ao verificar versão do yt-dlp: %s", e, exc_info=True)
    return None


def check_latest_version() -> str | None:
    """
    Verifica a versão mais recente disponível no PyPI (sem instalar).
    Retorna a string da versão ou None em caso de falha.
    """
    version = _check_via_pypi()
    if version:
        return version
    return _check_via_pip()


def update_ytdlp() -> dict[str, str | bool | None]:
    """
    Executa a atualização do yt-dlp.

    Em modo de desenvolvimento atualiza o pacote via pip. Em modo empacotado
    (AppImage/binário) mantém um yt-dlp standalone na pasta do usuário:
    ``sys.executable`` é o próprio app, então nunca é usado como Python.

    Retorna:
        {
            "success": bool,
            "old_version": str,
            "new_version": str | None,
            "message": str,
            "command": str,   # (opcional) comandos manuais quando a atualização
                              # automática não foi possível
        }
    """
    old_version = get_current_version()
    logger.info("Atualizando yt-dlp (versão atual: %s)...", old_version)

    # Em AppImage/binário o yt-dlp é embutido (não alterável) e sys.executable
    # aponta para o próprio app — executá-lo abriria outra instância. Mantemos
    # então um yt-dlp standalone do usuário, onde `-U` funciona de verdade.
    if _is_frozen():
        logger.info("Empacotado: atualizando o yt-dlp standalone do usuário.")
        return _update_packaged()

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
