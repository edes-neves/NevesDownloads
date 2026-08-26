"""
Serviço de suporte dedicado a TikTok.

Normaliza URLs do TikTok, detecta o tipo de conteúdo (vídeo, foto,
story, slide) e configura opções otimizadas de download.

O yt-dlp já suporta TikTok, mas este módulo adiciona:
  - Detecção de tipo de conteúdo (vídeo vs. foto/slide)
  - URLs normalizadas para melhor compatibilidade
  - Qualidades otimizadas para mobile (720p é a máxima do TikTok)
  - Dicas específicas por tipo de conteúdo
"""

import logging
import re

from app.i18n import _

logger = logging.getLogger("neves_downloads")

# Padrões de URLs do TikTok
_TIKTOK_PATTERNS = [
    # Vídeo padrão
    re.compile(
        r"https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/(\d+)",
        re.IGNORECASE,
    ),
    # Vídeo com query params
    re.compile(
        r"https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/(\d+)\?.*",
        re.IGNORECASE,
    ),
    # TikTok shorts (encurtador)
    re.compile(
        r"https?://(?:vm|vt)\.tiktok\.com/[\w]+/?",
        re.IGNORECASE,
    ),
    # TikTok story
    re.compile(
        r"https?://(?:www\.)?tiktok\.com/@[\w.-]+/story/(\d+)",
        re.IGNORECASE,
    ),
    # TikTok photo/carrossel
    re.compile(
        r"https?://(?:www\.)?tiktok\.com/@[\w.-]+/photo/(\d+)",
        re.IGNORECASE,
    ),
]

# Qualidades máximas suportadas pelo TikTok
_TIKTOK_QUALITY_MAP = {
    "Melhor disponivel": "best",
    "Melhor disponível": "best",
    "4K / 2160p": "best",  # TikTok não vai além de 1080p
    "2K / 1440p": "best",
    "Full HD / 1080p": "best[height<=1080]/best",
    "HD / 720p": "best[height<=720]/best",
    "480p": "best[height<=480]/best",
    "360p": "best[height<=360]/best",
}

# Tipos de conteúdo TikTok (chaves internas -> chaves de i18n)
_CONTENT_I18N = {
    "video": "tiktok.video",
    "photo": "tiktok.photo",
    "story": "tiktok.story",
    "unknown": "tiktok.unknown",
}


def is_tiktok_url(url: str) -> bool:
    """Verifica se a URL é do TikTok."""
    if not url:
        return False
    return any(pattern.search(url) for pattern in _TIKTOK_PATTERNS)


def extract_video_id(url: str) -> str | None:
    """Extrai o ID do vídeo TikTok de uma URL."""
    for pattern in _TIKTOK_PATTERNS:
        match = pattern.search(url)
        if match and match.lastindex and match.lastindex >= 1:
            return match.group(1)
    return None


def detect_content_type(url: str) -> str:
    """
    Detecta o tipo de conteúdo TikTok pela URL.

    Retorna: "video", "photo", "story", ou "unknown"
    """
    if not url:
        return "unknown"

    url_lower = url.lower()

    if "/photo/" in url_lower:
        return "photo"
    if "/story/" in url_lower:
        return "story"
    if "/video/" in url_lower:
        return "video"
    if "vm.tiktok.com" in url_lower or "vt.tiktok.com" in url_lower:
        return "video"  # Links curtos geralmente são vídeos

    return "unknown"


def normalize_url(url: str) -> str:
    """
    Normaliza URLs do TikTok para melhor compatibilidade com yt-dlp.

    Remove parâmetros de rastreamento desnecessários e garante
    que a URL esteja em formato aceito.
    """
    if not url:
        return url

    # Remove query params exceto os essenciais
    if "?" in url:
        base = url.split("?")[0]
        # mantém a URL base (o yt-dlp resolve)
        return base.rstrip("/")

    return url.rstrip("/")


def get_quality_for_tiktok(quality: str) -> str:
    """
    Retorna o seletor de qualidade otimizado para TikTok.

    O TikTok tipicamente fornece no máximo 1080p, então
    opções como 4K são redirecionadas para 'best'.
    """
    return _TIKTOK_QUALITY_MAP.get(quality, "best")


def get_content_info(url: str) -> dict[str, str | bool | None]:
    """
    Retorna informações sobre o conteúdo TikTok detectado.

    Retorna:
        {
            "is_tiktok": bool,
            "content_type": str,
            "content_type_label": str,
            "video_id": str | None,
            "quality_tip": str,
            "needs_cookies": bool,
        }
    """
    detected = is_tiktok_url(url)
    content_type = detect_content_type(url) if detected else "unknown"
    video_id = extract_video_id(url) if detected else None

    # Stories podem precisar de cookies
    needs_cookies = content_type == "story"

    tips = {
        "video": _("tiktok.tip.video"),
        "photo": _("tiktok.tip.photo"),
        "story": _("tiktok.tip.story"),
        "unknown": "",
    }

    return {
        "is_tiktok": detected,
        "content_type": content_type,
        "content_type_label": _(_CONTENT_I18N.get(content_type, "tiktok.unknown")),
        "video_id": video_id,
        "quality_tip": tips.get(content_type, ""),
        "needs_cookies": needs_cookies,
    }
