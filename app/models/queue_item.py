"""Modelo de item da fila de downloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class QueueItem:
    url: str
    title: str = ""
    mode: str = "video"  # "video" | "audio" | "playlist_all" | "playlist_select"
    status: str = "pending"  # "pending" | "downloading" | "paused" | "done" | "error"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str | None = None
    attempts: int = 0

    def to_dict(self) -> dict:
        d: dict[str, Any] = {
            "url": self.url,
            "title": self.title,
            "mode": self.mode,
            "status": self.status,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "attempts": self.attempts,
        }
        if self.updated_at is not None:
            d["updated_at"] = self.updated_at
        return d

    @classmethod
    def from_dict(cls, data: dict) -> QueueItem:
        return cls(
            url=data.get("url", ""),
            title=data.get("title", ""),
            mode=data.get("mode", "video"),
            status=data.get("status", "pending"),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at"),
            attempts=int(data.get("attempts", 0)),
        )
