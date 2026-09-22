"""Constantes de domínio do TikTok."""

# Qualidades máximas suportadas pelo TikTok
TIKTOK_QUALITY_MAP: dict[str, str] = {
    "Melhor disponivel": "best",
    "4K / 2160p": "best",  # TikTok não vai além de 1080p
    "2K / 1440p": "best",
    "Full HD / 1080p": "best[height<=1080]/best",
    "HD / 720p": "best[height<=720]/best",
    "480p": "best[height<=480]/best",
    "360p": "best[height<=360]/best",
}

# Tipos de conteúdo TikTok (chaves internas -> chaves de i18n)
TIKTOK_CONTENT_I18N: dict[str, str] = {
    "video": "tiktok.video",
    "photo": "tiktok.photo",
    "story": "tiktok.story",
    "unknown": "tiktok.unknown",
}
