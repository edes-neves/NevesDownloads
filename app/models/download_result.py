"""Modelo de resultado de download."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DownloadResult:
    status: str  # "completed" | "error" | "cancelled"
    filename: str = ""
    title: str = ""
    uploader: str = ""
    filesize: int = 0
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "filename": self.filename,
            "title": self.title,
            "uploader": self.uploader,
            "filesize": self.filesize,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict) -> DownloadResult:
        return cls(
            status=data.get("status", "error"),
            filename=data.get("filename", ""),
            title=data.get("title", ""),
            uploader=data.get("uploader", ""),
            filesize=data.get("filesize", 0),
            error=data.get("error"),
        )
