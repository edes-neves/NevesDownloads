"""
Histórico de downloads persistido em JSON (~/.neves_downloads/history.json).

Thread-safety: o acesso é serializado por um único threading.Lock.
Um espelho em memória (`_cache`) evita ler o disco a cada consulta; após
cada nova entrada a gravação é agendada com debounce (~1s) e pode ser
forçada a qualquer momento com flush_history() (registrada em atexit).
A gravação usa atomic_write_json para nunca corromper o arquivo.
"""

import atexit
import json
import logging
import threading
from datetime import datetime
from typing import Any

from app.utils.json_io import atomic_write_json
from app.utils.paths import get_app_data_dir

logger = logging.getLogger("neves_downloads")

HISTORY_FILE = get_app_data_dir() / "history.json"
MAX_HISTORY = 500

_lock = threading.Lock()
_cache: list[dict[str, Any]] | None = None  # espelho em memória (None = não carregado)
_flush_timer: threading.Timer | None = None
_flush_version = 0


def _load() -> list[dict[str, Any]]:
    """Carrega o histórico do disco. Chamar apenas com `_lock` adquirido."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Erro ao carregar histórico: {e}")
        return []


def _flush(items: list[dict[str, Any]]) -> None:
    """Grava `items` no disco. Chamar apenas com `_lock` adquirido."""
    try:
        atomic_write_json(HISTORY_FILE, items)
    except OSError as e:
        logger.error(f"Erro ao salvar histórico: {e}")


def _canceled_flush(timer: threading.Timer | None) -> threading.Timer | None:
    if timer is not None:
        timer.cancel()
    return None


def _schedule_flush() -> None:
    """Agenda gravação do estado atual em disco (debounce ~1s). Lock adquirido."""
    global _flush_timer, _flush_version
    _flush_version += 1
    version = _flush_version
    if _flush_timer is not None:
        _flush_timer.cancel()
    timer = threading.Timer(1.0, _flush_cached, args=(version,))
    timer.daemon = True
    _flush_timer = timer
    timer.start()


def _flush_cached(version: int) -> None:
    """Executado em background: grava o cache atual se ainda for a versão vigente."""
    with _lock:
        if version != _flush_version or _cache is None:
            return
        items = list(_cache)
    _flush(items)


def flush_history() -> None:
    """Força gravação imediata do histórico em disco."""
    global _flush_version, _flush_timer
    with _lock:
        _flush_version += 1
        _flush_timer = _canceled_flush(_flush_timer)
        if _cache is None:
            return
        items = list(_cache)
    _flush(items)


def _save(items: list[dict[str, Any]]) -> None:
    """Persiste imediatamente e sincroniza o cache em memória. Lock adquirido."""
    global _cache
    _cache = list(items)
    _flush(items)


def add_entry(
    url: str,
    title: str,
    filename: str = "",
    status: str = "completed",
    mode: str = "video",
    uploader: str = "",
):
    global _cache
    with _lock:
        if _cache is None:
            _cache = _load()
        entry = {
            "url": url,
            "title": title,
            "filename": filename,
            "status": status,
            "mode": mode,
            "uploader": uploader,
            "timestamp": datetime.now().isoformat(),
        }
        _cache.insert(0, entry)
        if len(_cache) > MAX_HISTORY:
            del _cache[MAX_HISTORY:]
        _schedule_flush()
    logger.info(f"Histórico: entrada adicionada para '{title}'")


def get_history(limit: int = 100) -> list[dict[str, Any]]:
    global _cache
    with _lock:
        if _cache is None:
            _cache = _load()
        return _cache[:limit]


def clear_history():
    global _flush_version, _flush_timer, _cache
    with _lock:
        _flush_version += 1
        _flush_timer = _canceled_flush(_flush_timer)
        _cache = []
        _flush([])
    logger.info("Histórico limpo.")


atexit.register(flush_history)
