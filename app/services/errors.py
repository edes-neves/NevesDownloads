"""
Mapeamento de erros do yt-dlp para mensagens amigáveis ao usuário.

O yt-dlp lança exceções com mensagens técnicas em inglês. Este módulo
normaliza essas mensagens para um texto claro e acionável,
utilizado na interface (cartões, messageboxes, etc).
"""

import logging

from app.i18n import _

logger = logging.getLogger("neves_downloads")

# Registry de padrões -> mensagem amigável
# Cada padrão é uma lista de substrings (case-insensitive) e a mensagem de erro.
_ERROR_PATTERNS = [
    {
        "nome": "video_privado",
        "padroes": [
            "video is private",
            "private video",
            "this video is private",
            "este vídeo é privado",
            "precisa de login",
        ],
        "icone": "\U0001f512",
        "msg_key": "error.video_privado",
        "dica_key": "error.video_privado_dica",
    },
    {
        "nome": "video_indisponivel",
        "padroes": [
            "video unavailable",
            "video is unavailable",
            "unavailable",
            "this video has been removed",
            "removed by the user",
            "vídeo indisponível",
            "vídeo removido",
        ],
        "icone": "\U0001f6ab",
        "msg_key": "error.video_indisponivel",
        "dica_key": "error.video_indisponivel_dica",
    },
    {
        "nome": "regiao_bloqueada",
        "padroes": [
            "not available in your country",
            "copyright",
            "geo-restriction",
            "region",
            "não disponível no seu país",
            "bloqueado",
        ],
        "icone": "\U0001f30d",
        "msg_key": "error.regiao_bloqueada",
        "dica_key": "error.regiao_bloqueada_dica",
    },
    {
        "nome": "idade_restrita",
        "padroes": ["age-restricted", "age restricted", "sign in to confirm", "restrição de idade", "confirm your age"],
        "icone": "\U0001f51e",
        "msg_key": "error.idade_restrita",
        "dica_key": "error.idade_restrita_dica",
    },
    {
        "nome": "login_necessario",
        "padroes": [
            "sign in",
            "log in",
            "login required",
            "requires authentication",
            "precisa estar logado",
            "autenticação",
        ],
        "icone": "\U0001f464",
        "msg_key": "error.login_necessario",
        "dica_key": "error.login_necessario_dica",
    },
    {
        "nome": "ffmpeg_faltando",
        "padroes": ["ffmpeg is not installed", "ffmpeg not found", "postprocessing", "ffmpeg não", "no ffmpeg"],
        "icone": "\u25b6\ufe0f",
        "msg_key": "error.ffmpeg_faltando",
        "dica_key": "error.ffmpeg_faltando_dica",
    },
    {
        "nome": "url_invalida",
        "padroes": ["unsupported url", "no matching extractor", "invalid url", "não suportada", "extractor", "url não"],
        "icone": "\U0001f517",
        "msg_key": "error.url_invalida",
        "dica_key": "error.url_invalida_dica",
    },
    {
        "nome": "timeout",
        "padroes": ["timed out", "timeout", "connection timeout", "tempo esgotado", "nao foi possivel conectar"],
        "icone": "\u23f1\ufe0f",
        "msg_key": "error.timeout",
        "dica_key": "error.timeout_dica",
    },
    {
        "nome": "rate_limit",
        "padroes": ["rate limit", "too many requests", "429", "muitas requisições"],
        "icone": "\U0001f422",
        "msg_key": "error.rate_limit",
        "dica_key": "error.rate_limit_dica",
    },
    {
        "nome": "erro_rede",
        "padroes": [
            "connection error",
            "network",
            "connection refused",
            "erro de rede",
            "name resolution",
            "socket error",
            "failed to establish",
        ],
        "icone": "\U0001f4e1",
        "msg_key": "error.erro_rede",
        "dica_key": "error.erro_rede_dica",
    },
]


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

    for padrao in _ERROR_PATTERNS:
        for p in padrao["padroes"]:
            if p.lower() in lowered:
                return {
                    "amigavel": _(str(padrao["msg_key"])),
                    "dica": _(str(padrao["dica_key"])),
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
