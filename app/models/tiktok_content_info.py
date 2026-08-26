"""Modelo de informação de conteúdo TikTok."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TikTokContentInfo:
    is_tiktok: bool
    content_type: str  # "video" | "photo" | "story" | "unknown"
    content_type_label: str  # label traduzido
    video_id: str | None = None
    quality_tip: str = ""
    needs_cookies: bool = False

    def to_dict(self) -> dict:
        return {
            "is_tiktok": self.is_tiktok,
            "content_type": self.content_type,
            "content_type_label": self.content_type_label,
            "video_id": self.video_id,
            "quality_tip": self.quality_tip,
            "needs_cookies": self.needs_cookies,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TikTokContentInfo:
        return cls(
            is_tiktok=data.get("is_tiktok", False),
            content_type=data.get("content_type", "unknown"),
            content_type_label=data.get("content_type_label", ""),
            video_id=data.get("video_id"),
            quality_tip=data.get("quality_tip", ""),
            needs_cookies=data.get("needs_cookies", False),
        )
