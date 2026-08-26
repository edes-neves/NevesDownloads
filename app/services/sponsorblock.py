"""
Categorias do SponsorBlock para uso na UI.

A integração real com a API do SponsorBlock é feita pelo yt-dlp via
a opção ``sponsorblock_remove``. Este módulo fornece apenas os rótulos
das categorias para exibição na janela de configurações.
"""

import logging

from app.i18n import _

logger = logging.getLogger("neves_downloads")

# Categorias padrão que são removidas quando o SponsorBlock está ativo
DEFAULT_CATEGORIES = ["sponsor", "selfpromo", "interaction", "intro", "outro", "preview"]

_SPONSOR_LABELS = {
    "sponsor": "sponsor.sponsor",
    "selfpromo": "sponsor.selfpromo",
    "interaction": "sponsor.interaction",
    "intro": "sponsor.intro",
    "outro": "sponsor.outro",
    "preview": "sponsor.preview",
    "music_official": "sponsor.music_official",
    "filler": "sponsor.filler",
}


def get_categories_labels() -> dict[str, str]:
    """Retorna todas as categorias disponíveis com rótulos traduzidos."""
    return {k: _(v) for k, v in _SPONSOR_LABELS.items()}
