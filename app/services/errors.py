"""
Mapeamento de erros do yt-dlp para mensagens amigáveis ao usuário.

O yt-dlp lança exceções com mensagens técnicas em inglês. Este módulo
normaliza essas mensagens para um texto claro e acionável,
utilizado na interface (cartões, messageboxes, etc).
"""

import logging

from app.core.error_patterns import ERROR_PATTERNS
from app.i18n import _

logger = logging.getLogger("neves_downloads")

# Padrões pré-normalizados (minúsculos) — um único cálculo na importação
_LOOKUP_PATTERNS = [{**padrao, "padroes": [p.lower() for p in padrao["padroes"]]} for padrao in ERROR_PATTERNS]


def friendly_error(error: Exception) -> dict:
    """
    Converte uma exceção do yt-dlp em um dict de erro amigável.

    Retorna:
        {
            "amigavel": str,   # mensagem amigável para o usuário
            "dica": str,       # sugestão de ação
            "icone": str,      # ícone/emoji
            "tecnico": str,   # mensagem técnica original (log)
            "nome": str,      # nome do padrão detectado (ou 'generico')
        }
    """
    msg = str(error)
    lowered = msg.lower()

    for padrao in _LOOKUP_PATTERNS:
        for p in padrao["padroes"]:
            if p in lowered:
                return {
                    "amigavel": _(padrao["msg_key"]),
                    "dica": _(padrao["dica_key"]),
                    "icone": padrao["icone"],
                    "tecnico": msg,
                    "nome": padrao["nome"],
                }

    # Erro genérico
    return {
        "amigavel": _("error.generico"),
        "dica": _("error.generico_dica"),
        "icone": "\u26a0\ufe0f",
        "tecnico": msg,
        "nome": "generico",
    }


def friendly_text(error: Exception) -> str:
    """Retorna apenas o texto amigável (para uso direto na interface)."""
    info = friendly_error(error)
    return f"{info['icone']} {info['amigavel']}"


def log_error(error: Exception, contexto: str = ""):
    """Registra o erro no log com contexto."""
    info = friendly_error(error)
    prefix = f"[{contexto}] " if contexto else ""
    logger.error("%sErro amigável: %s | %s | Técnico: %s", prefix, info["nome"], info["amigavel"], info["tecnico"])
