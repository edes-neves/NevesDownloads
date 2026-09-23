"""
Auto-update do aplicativo via GitHub Releases.

Verifica o repositório GitHub na busca de versões mais recentes,
baixa o AppImage e substitui o executável atual.
"""

import contextlib
import hashlib
import json
import logging
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

from app.core.constants import APP_NAME, APP_VERSION
from app.i18n import _
from app.utils.json_io import atomic_write_json
from app.utils.paths import get_app_data_dir

logger = logging.getLogger("neves_downloads")

# Configuração do repositório GitHub
_GITHUB_REPO = "edes-neves/NevesDownloads"
_GITHUB_API_URL = f"https://api.github.com/repos/{_GITHUB_REPO}/releases/latest"
# URL de releases para consulta manual.
_GITHUB_RELEASES_URL = f"https://github.com/{_GITHUB_REPO}/releases/latest"
# Cache em disco da última release conferida (TTL de 1h).
_UPDATE_CACHE_FILE = get_app_data_dir() / "update_check.json"
_UPDATE_CACHE_TTL = 3600  # segundos (1h)
_VER_SEG = re.compile(r"\d+")
_USER_AGENT = f"{APP_NAME}/{APP_VERSION}"
# Plataforma-alvo do instalador (constante para permitir testes direcionados).
_IS_WINDOWS = os.name == "nt"


def _get_executable_path() -> Path | None:
    """Retorna o caminho do executável atual (AppImage ou script Python)."""
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


def _parse_version(v: str) -> tuple:
    """Extrai apenas os segmentos numéricos de uma versão ("1.2.0-rc1" -> (1, 2, 0, 1))."""
    return tuple(int(x) for x in _VER_SEG.findall(str(v)))


def _load_update_cache() -> dict | None:
    """Retorna a release em cache se ainda dentro do TTL; senão, None."""
    try:
        if not _UPDATE_CACHE_FILE.exists():
            return None
        with open(_UPDATE_CACHE_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if time.time() - (data.get("timestamp", 0) or 0) > _UPDATE_CACHE_TTL:
            return None
        release = data.get("release")
        return release if isinstance(release, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _save_update_cache(release: dict):
    if not isinstance(release, dict):
        return
    # cache é apenas otimização
    with contextlib.suppress(OSError):
        atomic_write_json(
            _UPDATE_CACHE_FILE,
            {"timestamp": time.time(), "release": release},
        )


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
    # Cache em disco com TTL de 1h evita bater na API a cada abertura.
    cached = _load_update_cache()
    if cached is not None:
        return cached

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

        result = {
            "version": version,
            "tag": tag,
            "name": data.get("name", ""),
            "body": data.get("body", ""),
            "published_at": data.get("published_at", ""),
            "assets": assets,
        }
        _save_update_cache(result)
        return result

    except Exception as e:
        logger.error("Erro ao verificar release no GitHub: %s", e)
        return None


# Códigos de erro da verificação (distinguem "falha" de "está atualizado").
ERR_DEV_MODE = "dev"
ERR_NETWORK = "network"


def check_for_update() -> dict:
    """
    Verifica se há uma versão mais recente disponível.

    Retorna:
        {
            "available": bool,
            "current": str,
            "latest": str,
            "release": dict | None,
            "error": str | None,  # None = verificação OK; senão um dos ERR_*
        }

    ``error`` é preenchido quando a API do GitHub não pôde ser consultada ou
    quando a instalação não suporta auto-update. A UI deve diferenciar isso de
    "está na versão mais recente".
    """
    # Modo desenvolvimento/instalação manual (sem AppImage/frozen) não permite
    # auto-update — reporta como erro, não como "atualizado".
    if _get_executable_path() is None:
        return {
            "available": False,
            "current": APP_VERSION,
            "latest": "unknown",
            "release": None,
            "error": ERR_DEV_MODE,
        }

    current = APP_VERSION
    release = check_latest_release()

    if not release or not release["version"]:
        return {
            "available": False,
            "current": current,
            "latest": "unknown",
            "release": None,
            "error": ERR_NETWORK,
        }

    latest = release["version"]

    # Compara versões usando apenas os segmentos numéricos (suporta sufixos ex: 1.2.0-rc1)
    try:
        current_parts = _parse_version(current)
        latest_parts = _parse_version(latest)
        if current_parts and latest_parts:
            available = latest_parts > current_parts
        else:
            available = current != latest
    except (ValueError, AttributeError):
        available = current != latest

    return {
        "available": available,
        "current": current,
        "latest": latest,
        "release": release,
        "error": None,
    }


def download_release_asset(
    url: str,
    dest: Path,
    progress_callback=None,
    expected_sha256: str = "",
) -> bool:
    """
    Baixa um asset de release do GitHub.

    Args:
        url: URL de download do asset.
        dest: Caminho de destino.
        progress_callback: Callable(bytes_downloaded, total_size).
        expected_sha256: Hash sha256 esperado. Vazio = sem validação.

    Retorna True se o download foi concluído com sucesso.

    Nota: o fluxo automático (check_for_update -> install_update) não a usa;
    fica disponível para integrações/UI.
    """
    if not expected_sha256:
        logger.warning("Download sem sha256; integridade não verificada")
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

        if expected_sha256:
            sha = hashlib.sha256(dest.read_bytes()).hexdigest()
            if sha.lower() != expected_sha256.lower():
                logger.error(
                    "Hash sha256 divergente para %s (esperado %s, obtido %s). Arquivo removido.",
                    dest.name,
                    expected_sha256,
                    sha,
                )
                with contextlib.suppress(OSError):
                    dest.unlink()
                return False

        return True

    except Exception as e:
        logger.error("Erro ao baixar asset: %s", e)
        return False


def install_update(asset_path: Path) -> dict:
    """
    Instala uma atualização.

    Em vez de substituir o executável enquanto está em execução (impossível
    com AppImage/FUSE no Linux e com processos .exe no Windows), copia o
    novo binário para <exe>.pending e cria um helper script que, após o app
    fechar, faz a troca e relança o app. No Linux o helper é um script bash
    (depende de bash e flock); no Windows é um .bat via cmd.

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

    if not os.access(exe.parent, os.W_OK):
        return {
            "success": False,
            "message": "Diretório do executável não é gravável.",
            "requires_restart": False,
        }

    is_windows = _IS_WINDOWS

    try:
        if is_windows:
            if asset_path.suffix.lower() != ".exe":
                return {
                    "success": False,
                    "message": "Formato de asset não suportado: " + asset_path.name,
                    "requires_restart": False,
                }
            # Valida que o novo binário é um PE (MZ) íntegro
            if not _is_valid_pe(asset_path):
                return {
                    "success": False,
                    "message": "Binário baixado não é um executável Windows válido: " + asset_path.name,
                    "requires_restart": False,
                }
            pending = exe.with_suffix(".exe.pending")
        else:
            if not (asset_path.suffix == ".AppImage" or "AppImage" in asset_path.name):
                return {
                    "success": False,
                    "message": "Formato de asset não suportado: " + asset_path.name,
                    "requires_restart": False,
                }
            # Valida que o novo binário é um ELF íntegro antes de qualquer substituição
            if not _is_valid_elf(asset_path):
                return {
                    "success": False,
                    "message": "Binário baixado não é um ELF válido: " + asset_path.name,
                    "requires_restart": False,
                }
            # Torna executável (Linux)
            asset_path.chmod(asset_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
            pending = exe.with_suffix(".AppImage.pending")

        # Copia o novo binário para <exe>.pending (ao lado do atual)
        if pending.exists():
            pending.unlink()
        shutil.copy2(str(asset_path), str(pending))

        # Remove o download temporário
        with contextlib.suppress(OSError):
            asset_path.unlink()

        if is_windows:
            # Helper .bat: espera o app fechar (PID) e troca exe -> .bak,
            # pending -> exe; renomear um .exe em execução é permitido no
            # Windows (não é possível sobrescrever/remover).
            helper = exe.parent / ".update_helper.bat"
            helper.write_text(
                (
                    "@echo off\r\n"
                    "REM Auto-update helper - espera o app fechar e troca o executavel\r\n"
                    'set "EXE=%~1"\r\n'
                    'set "PENDING=%~2"\r\n'
                    'set "BAK=%~3"\r\n'
                    'set "APP_PID=%~4"\r\n'
                    "set /a n=0\r\n"
                    ":wait\r\n"
                    'tasklist /fi "PID eq %APP_PID%" 2>nul | findstr /c:"%APP_PID%" >nul\r\n'
                    "if errorlevel 1 goto replace\r\n"
                    "set /a n+=1\r\n"
                    "if %n% geq 30 goto replace\r\n"
                    "timeout /t 1 /nobreak >nul\r\n"
                    "goto wait\r\n"
                    ":replace\r\n"
                    'if exist "%PENDING%" (\r\n'
                    '    if exist "%BAK%" del /f /q "%BAK%" 2>nul\r\n'
                    '    move /y "%EXE%" "%BAK%" >nul 2>nul\r\n'
                    '    move /y "%PENDING%" "%EXE%" >nul 2>nul\r\n'
                    ")\r\n"
                    'del /f /q "%~f0" 2>nul\r\n'
                    'start "" "%EXE%"\r\n'
                ),
                encoding="ascii",
            )
            flags = (
                getattr(subprocess, "DETACHED_PROCESS", 0x8)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x200)
                | getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            )
            subprocess.Popen(
                ["cmd", "/c", str(helper), str(exe), str(pending), str(exe) + ".bak", str(os.getpid())],
                creationflags=flags,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            msg = _("updater.app_updated").format(version=APP_VERSION)
            logger.info(msg)
            return {
                "success": True,
                "message": msg,
                "requires_restart": True,
            }

        # Cria helper script que faz a troca após o app fechar.
        # Valores passados por argumentos posicionais ($1..$5) — sem interpolar
        # caminhos no corpo do script, evitando escape/execução de comandos.
        helper = exe.parent / ".update_helper.sh"
        helper.write_text(
            """#!/bin/bash
# Auto-update helper — espera o app fechar e substitui o AppImage
EXE=$1
PENDING=$2
BAK=$3
APP_PID=$4
LOCK=$5

# Exclusão mútua: impede que duas trocas rodem ao mesmo tempo
exec 9>"$LOCK"
flock 9

# Espera o app fechar (max 30s) verificando o PID informado pelo app
for i in $(seq 1 30); do
    if ! kill -0 "$APP_PID" 2>/dev/null; then
        break
    fi
    sleep 1
done

# Pequena pausa extra para garantir flush de sistema de arquivos
sleep 2

# Troca os ficheiros (já protegido pelo flock)
if [ -f "$PENDING" ]; then
    [ -f "$BAK" ] && rm -f "$BAK"
    mv "$EXE" "$BAK" 2>/dev/null
    mv "$PENDING" "$EXE"
    chmod +x "$EXE"
fi
rm -f "$0"
""",
            encoding="utf-8",
        )
        helper.chmod(0o755)

        lock_file = exe.parent / ".update.lock"
        # Lança o helper em background (detached) e fecha o app
        subprocess.Popen(
            [
                "/bin/bash",
                str(helper),
                str(exe),
                str(pending),
                str(exe) + ".bak",
                str(os.getpid()),
                str(lock_file),
            ],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        msg = _("updater.app_updated").format(version=APP_VERSION)
        logger.info(msg)

        return {
            "success": True,
            "message": msg,
            "requires_restart": True,
        }

    except Exception as e:
        msg = _("updater.install_failed").format(error=str(e))
        logger.error(msg)
        return {
            "success": False,
            "message": msg,
            "requires_restart": False,
        }


def _is_valid_elf(path: Path) -> bool:
    """Verifica se o arquivo começa com o magic number de ELF (\\x7fELF)."""
    try:
        with open(path, "rb") as f:
            return f.read(4) == b"\x7fELF"
    except OSError as e:
        logger.error("Falha ao validar ELF de %s: %s", path, e)
        return False


def _is_valid_pe(path: Path) -> bool:
    """Verifica se o arquivo começa com o magic number de PE/Windows (MZ)."""
    try:
        with open(path, "rb") as f:
            return f.read(2) == b"MZ"
    except OSError as e:
        logger.error("Falha ao validar PE de %s: %s", path, e)
        return False
