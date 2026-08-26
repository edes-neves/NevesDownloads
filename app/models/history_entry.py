"""Modelo de entrada do histórico de downloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class HistoryEntry:
    url: str
    title: str
    filename: str = ""
    status: str = "completed"  # "completed" | "error"
    mode: str = "video"  # "video" | "audio"
    uploader: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "title": self.title,
            "filename": self.filename,
            "status": self.status,
            "mode": self.mode,
            "uploader": self.uploader,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> HistoryEntry:
        return cls(
            url=data.get("url", ""),
            title=data.get("title", ""),
            filename=data.get("filename", ""),
            status=data.get("status", "completed"),
            mode=data.get("mode", "video"),
            uploader=data.get("uploader", ""),
            timestamp=data.get("timestamp", ""),
        )
