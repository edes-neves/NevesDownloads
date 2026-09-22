"""Categorias do SponsorBlock para uso na UI.

A integração real com a API do SponsorBlock é feita pelo yt-dlp via
a opção ``sponsorblock_remove``. Este módulo fornece apenas os rótulos
das categorias para exibição na janela de configurações.

Fonte da verdade: `app.core.sponsorblock.SPONSOR_CATEGORY_LABELS`
(categorias + chaves de i18n). Rótulos traduzidos ficam em app/i18n.py.
"""

import logging

from app.core.sponsorblock import SPONSOR_CATEGORY_LABELS
from app.i18n import _

logger = logging.getLogger("neves_downloads")


def get_categories_labels() -> dict[str, str]:
    """Retorna todas as categorias disponíveis com rótulos traduzidos."""
    return {k: _(v) for k, v in SPONSOR_CATEGORY_LABELS.items()}
