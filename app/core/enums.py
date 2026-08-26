"""Enums de domínio para valores de status e tipo."""

from enum import StrEnum


class DownloadStatus(StrEnum):
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class QueueItemStatus(StrEnum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    DONE = "done"
    ERROR = "error"


class DownloadType(StrEnum):
    VIDEO = "video"
    AUDIO = "audio"


class DownloadMode(StrEnum):
    VIDEO = "video"
    PLAYLIST_ALL = "playlist_all"
    PLAYLIST_SELECT = "playlist_select"


class ThemeMode(StrEnum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


class TikTokContentType(StrEnum):
    VIDEO = "video"
    PHOTO = "photo"
    STORY = "story"
    UNKNOWN = "unknown"
