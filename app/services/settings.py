import json
import logging
from pathlib import Path
from typing import Any

from app.utils.paths import get_app_data_dir

logger = logging.getLogger("neves_downloads")

CONFIG_FILE = get_app_data_dir() / "config.json"

_DEFAULTS = {
    "download_path": str(Path.home() / "Downloads"),
    # ── Aparência ──
    "appearance_mode": "system",  # "system" | "light" | "dark"
    "automatic_updates": True,  # avisar/verificar atualizações (placeholder)
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
    # ── Rede / Desempenho ──
    "max_concurrent_downloads": 3,  # downloads simultâneos
    "concurrent_fragments": 1,  # fragments paralelos por download (multi-threading)
    "proxy": "",  # ex: socks5://127.0.0.1:1080
    "limit_speed": 0,  # bytes/segundo (0 = ilimitado)
    "retries": 3,
    "fragment_retries": 3,
    "socket_timeout": 30,
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
    "show_context_menu": True,
}

# Valores aceitáveis para campos que são seleções
_VALID_VALUES = {
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

_TYPE_BOOL = {
    "automatic_updates",
    "default_subtitles_enabled",
    "default_organize",
    "embed_thumbnail",
    "write_thumbnail",
    "confirm_on_exit_with_active_downloads",
    "auto_clear_completed",
    "show_context_menu",
    "sponsorblock_enabled",
    "tiktok_watermark_removal",
}

_TYPE_INT = {
    "max_concurrent_downloads",
    "concurrent_fragments",
    "limit_speed",
    "retries",
    "fragment_retries",
    "socket_timeout",
}


def _sanitize(key: str, value: Any) -> Any:
    """Normaliza o valor conforme o tipo esperado (evita corromper o config)."""
    if key not in _DEFAULTS:
        return value

    # Validação para campos do tipo seleção
    if key in _VALID_VALUES:
        if value not in _VALID_VALUES[key]:
            return _DEFAULTS[key]
        return value

    # Validação para booleanos
    if key in _TYPE_BOOL:
        return bool(value)

    # Validação para inteiros
    if key in _TYPE_INT:
        try:
            return int(value)
        except (TypeError, ValueError):
            return _DEFAULTS[key]

    # Strings gerais
    if value is None:
        return _DEFAULTS[key]
    return value


def load(key: str | None = None) -> Any:
    config = _read()
    if key is None:
        return config
    return config.get(key, _DEFAULTS.get(key))


def save(key: str, value: Any):
    config = _read()
    config[key] = _sanitize(key, value)
    _write(config)


def load_all() -> dict:
    """Retorna o dicionário completo de configurações já sanado."""
    return _read()


def reset_to_defaults():
    """Restaura todas as configurações para os valores padrão."""
    _write(dict(_DEFAULTS))
    logger.info("Configurações restauradas para os padrões.")


def _read() -> dict:
    if not CONFIG_FILE.exists():
        return dict(_DEFAULTS)
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            data = json.load(f)
            # Mescla defaults e sana valores inválidos
            merged = {}
            for k, v in _DEFAULTS.items():
                if k in data:
                    merged[k] = _sanitize(k, data[k])
                else:
                    merged[k] = v
            return merged
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Erro ao ler config: {e}")
        return dict(_DEFAULTS)


def _write(config: dict):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.error(f"Erro ao salvar config: {e}")
