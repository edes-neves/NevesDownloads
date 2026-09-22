"""
Fila persistente de downloads.

Permite enfileirar URLs e, se o aplicativo for fechado com itens pendentes,
retomá-los no próximo início. Cada item da fila guarda a URL e as opções
de download naquele momento, números de tentativas, etc.

Formato persistido (JSON ~/.neves_downloads/queue.json):
[
    {
        "url": "...",
        "title": "...",
        "mode": "video",
        "status": "pending",   # pending | downloading | paused | done | error
        "created_at": "ISO",
        "attempts": 0,
    },
    ...
]

Thread-safety: todas as mutações são feitas sob um único threading.Lock.
A gravação em disco é agendada após cada mutação (debounce de ~1s) e pode
ser forçada a qualquer momento com save()/flush(). Métodos que retornam
itens (ex.: next_pending) retornam CÓPIAS, para não expor a lista interna.
"""

import json
import logging
import threading
from datetime import datetime
from typing import Any

from app.utils.json_io import atomic_write_json
from app.utils.paths import get_app_data_dir

logger = logging.getLogger("neves_downloads")

QUEUE_FILE = get_app_data_dir() / "queue.json"
MAX_QUEUE = 5000


class DownloadQueue:
    """Fila de downloads com persistência opcional."""

    def __init__(self, persist: bool = True):
        self._items: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._persist = persist
        self._save_version = 0
        self._save_timer: threading.Timer | None = None
        self._load()

    # ── Persistência ───────────────────────────────────────────

    def _load(self):
        if not self._persist:
            return
        if not QUEUE_FILE.exists():
            return
        try:
            with open(QUEUE_FILE, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self._items = data
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Erro ao carregar fila: {e}")

    def _save(self):
        """Agenda gravação em disco (debounce de ~1s). Chamado com o lock adquirido."""
        if not self._persist:
            return
        snapshot = list(self._items)
        self._save_version += 1
        version = self._save_version
        timer = getattr(self, "_save_timer", None)
        if timer is not None:
            timer.cancel()
        timer = threading.Timer(1.0, self._write_snapshot, args=(snapshot, version))
        timer.daemon = True
        self._save_timer = timer
        timer.start()

    def _write_snapshot(self, snapshot: list[dict[str, Any]], version: int):
        """Grava um snapshot em disco (executado em thread de background)."""
        if not self._persist or version != self._save_version:
            return  # versão obsoleta; houve gravação mais recente
        try:
            atomic_write_json(QUEUE_FILE, snapshot)
        except OSError as e:
            logger.error(f"Erro ao salvar fila: {e}")

    def flush(self):
        """Força gravação imediata do estado atual em disco."""
        if not self._persist:
            return
        self._save_version += 1
        timer = getattr(self, "_save_timer", None)
        if timer is not None:
            timer.cancel()
            self._save_timer = None
        with self._lock:
            snapshot = list(self._items)
        self._write_snapshot(snapshot, self._save_version)

    # ── Gerenciamento de itens ─────────────────────────────────

    def add(
        self, url: str, title: str = "", mode: str = "video", metadata: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Adiciona um item ao final da fila. Retorna o item criado (ou None se duplicado)."""
        with self._lock:
            # Evita duplicatas de URL idêntica pendente
            if any(i.get("url") == url and i.get("status") == "pending" for i in self._items):
                logger.info(f"URL já está na fila: {url}")
                return None
            item = {
                "url": url,
                "title": title,
                "mode": mode,
                "status": "pending",
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "attempts": 0,
            }
            self._items.append(item)
            if len(self._items) > MAX_QUEUE:
                self._items = self._items[-MAX_QUEUE:]
            self._save()
            logger.info(f"Fila: adicionado '{title or url}'")
            return item

    def set_status(self, url: str, status: str):
        """Atualiza o status de um item (pelo url)."""
        with self._lock:
            for item in self._items:
                if item.get("url") == url:
                    item["status"] = status
                    item["updated_at"] = datetime.now().isoformat()
                    break
            self._save()

    def remove(self, url: str) -> bool:
        """Remove um item da fila (pelo url). Retorna True se removeu."""
        with self._lock:
            before = len(self._items)
            self._items = [i for i in self._items if i.get("url") != url]
            removed = len(self._items) != before
            if removed:
                self._save()
            return removed

    def increment_attempts(self, url: str) -> int:
        """Incrementa o contador de tentativas de um item. Retorna novo valor."""
        with self._lock:
            for item in self._items:
                if item.get("url") == url:
                    item["attempts"] = int(item.get("attempts", 0)) + 1
                    self._save()
                    return int(item["attempts"])
            return 0

    def pending(self) -> list[dict[str, Any]]:
        """Retorna os itens ainda não finalizados (pending/downloading/paused)."""
        with self._lock:
            return [i for i in self._items if i.get("status") in ("pending", "downloading", "paused")]

    def all(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._items)

    def next_pending(self) -> dict[str, Any] | None:
        """Retorna uma cópia do próximo item 'pending', sem removê-lo da fila."""
        with self._lock:
            for item in self._items:
                if item.get("status") == "pending":
                    return dict(item)
            return None

    def pop_next_pending(self) -> dict[str, Any] | None:
        """Remove e retorna o próximo item 'pending' (operação atômica)."""
        with self._lock:
            for i, item in enumerate(self._items):
                if item.get("status") == "pending":
                    self._items.pop(i)
                    self._save()
                    return dict(item)
            return None

    def mark_downloading(self, url: str):
        self.set_status(url, "downloading")

    def mark_paused(self, url: str):
        self.set_status(url, "paused")

    def mark_done(self, url: str):
        self.set_status(url, "done")

    def mark_error(self, url: str):
        self.set_status(url, "error")

    def prune_finished(self):
        """Remove itens 'done'/'error' da fila para mantê-la enxuta."""
        with self._lock:
            before = len(self._items)
            self._items = [i for i in self._items if i.get("status") not in ("done", "error")]
            if len(self._items) != before:
                self._save()

    def save(self):
        """Força gravação em disco (ex.: ao fechar o app)."""
        self.flush()
