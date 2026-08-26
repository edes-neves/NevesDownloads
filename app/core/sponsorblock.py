"""Constantes de domínio do SponsorBlock."""

# Categorias padrão que são removidas quando o SponsorBlock está ativo
DEFAULT_CATEGORIES = ["sponsor", "selfpromo", "interaction", "intro", "outro", "preview"]

# Chaves de i18n para cada categoria
SPONSOR_CATEGORY_LABELS: dict[str, str] = {
    "sponsor": "sponsor.sponsor",
    "selfpromo": "sponsor.selfpromo",
    "interaction": "sponsor.interaction",
    "intro": "sponsor.intro",
    "outro": "sponsor.outro",
    "preview": "sponsor.preview",
    "music_official": "sponsor.music_official",
    "filler": "sponsor.filler",
}
