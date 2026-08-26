import json
import logging
from datetime import datetime
from typing import Any

from app.utils.paths import get_app_data_dir

logger = logging.getLogger("neves_downloads")

HISTORY_FILE = get_app_data_dir() / "history.json"
MAX_HISTORY = 500


def _load() -> list[dict[str, Any]]:
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Erro ao carregar histórico: {e}")
        return []


def _save(items: list[dict[str, Any]]):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.error(f"Erro ao salvar histórico: {e}")


def add_entry(
    url: str,
    title: str,
    filename: str = "",
    status: str = "completed",
    mode: str = "video",
    uploader: str = "",
):
    items = _load()
    entry = {
        "url": url,
        "title": title,
        "filename": filename,
        "status": status,
        "mode": mode,
        "uploader": uploader,
        "timestamp": datetime.now().isoformat(),
    }
    items.insert(0, entry)
    if len(items) > MAX_HISTORY:
        items = items[:MAX_HISTORY]
    _save(items)
    logger.info(f"Histórico: entrada adicionada para '{title}'")


def get_history(limit: int = 100) -> list[dict[str, Any]]:
    return _load()[:limit]


def clear_history():
    _save([])
    logger.info("Histórico limpo.")
