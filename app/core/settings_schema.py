"""Schema de configurações — valores padrão, tipos e validação."""

from pathlib import Path

SETTINGS_DEFAULTS: dict = {
    "download_path": str(Path.home() / "Downloads"),
    # ── Aparência ──
    "appearance_mode": "system",  # "system" | "light" | "dark"
    "automatic_updates": True,  # verificar atualizações automaticamente no início
    "default_language": "pt-BR",  # idioma da interface
    # ── Padrões de download ──
    "default_type": "video",  # "video" | "audio"
    "default_mode": "video",  # "video" | "playlist_all" | "playlist_select"
    "default_quality": "Melhor disponivel",
    "default_format": "MP4",  # formato de vídeo
    "default_audio_format": "MP3",  # formato de áudio
    "default_subtitles_enabled": False,
    "default_subtitle_langs": "pt,en",
    "default_organize": False,
    "default_cookies_browser": "Nenhum",
    "cookies_file_path": "",  # caminho de cookies.txt (alternativa aos cookies de navegador)
    "playlist_audio_single": False,  # baixar playlists de áudio como um único arquivo
    # ── Rede / Desempenho ──
    "max_concurrent_downloads": 3,  # downloads simultâneos
    "concurrent_fragments": 1,  # fragments paralelos por download (multi-threading)
    "proxy": "",  # ex: socks5://127.0.0.1:1080
    "limit_speed": 0,  # bytes/segundo (0 = ilimitado)
    "retries": 3,
    "transient_retries": 2,  # retries extras em erros transitórios (rede/rate limit/5xx)
    "socket_timeout": 30,
    "notifications_enabled": True,  # notificação de conclusão (toast in-app + sistema)
    # ── SponsorBlock ──
    "sponsorblock_enabled": False,  # ativar remoção de segmentos via SponsorBlock
    "sponsorblock_categories": "sponsor,selfpromo,interaction,intro,outro,preview",
    # ── TikTok ──
    "tiktok_watermark_removal": True,  # remover marca d'água do TikTok (melhor qualidade)
    # ── Nomeação de arquivos ──
    "filename_template": "%(title)s.%(ext)s",
    "embed_thumbnail": False,  # capa/tumbnail embutida em áudio/vídeo
    "write_thumbnail": False,  # salvar thumbnail como arquivo separado
    # ── Comportamento ──
    "confirm_on_exit_with_active_downloads": True,
    "auto_clear_completed": False,
}

# Valores aceitáveis para campos que são seleções
SETTINGS_VALID_VALUES: dict = {
    "appearance_mode": {"system", "light", "dark"},
    "default_language": {"pt-BR", "en-US"},
    "default_type": {"video", "audio"},
    "default_mode": {"video", "playlist_all", "playlist_select"},
    "default_quality": {
        "Melhor disponivel",
        "4K / 2160p",
        "2K / 1440p",
        "Full HD / 1080p",
        "HD / 720p",
        "480p",
        "360p",
    },
    "default_format": {"MP4", "WebM", "Melhor formato disponivel"},
    "default_audio_format": {"MP3", "M4A", "FLAC", "OGG", "WAV"},
    "default_cookies_browser": {
        "Nenhum",
        "chrome",
        "chromium",
        "firefox",
        "opera",
        "vivaldi",
        "edge",
    },
}

SETTINGS_TYPE_BOOL: set = {
    "automatic_updates",
    "default_subtitles_enabled",
    "default_organize",
    "playlist_audio_single",
    "embed_thumbnail",
    "write_thumbnail",
    "confirm_on_exit_with_active_downloads",
    "auto_clear_completed",
    "sponsorblock_enabled",
    "tiktok_watermark_removal",
    "notifications_enabled",
}

SETTINGS_TYPE_INT: set = {
    "max_concurrent_downloads",
    "concurrent_fragments",
    "limit_speed",
    "retries",
    "transient_retries",
    "socket_timeout",
}
