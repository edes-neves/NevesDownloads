APP_NAME = "Neves Downloads"
APP_VERSION = "1.0.0"
# Identificador usado na propriedade WM_CLASS do X11 (sem espaços, em minúsculas)
# para que o usuário possa agrupar/personalizar a janela no gerenciador de janelas.
APP_WM_CLASS = "nevesdownloads"
Developer = "José Edes Neves"
Contato = "edes.neves7@gmail.com"

# ── Opções de UI (fonte única para main_window e settings_window) ──
# NOTA: Estes são os valores internos usados para armazenamento nas configurações.
# As labels de exibição traduzidas ficam em i18n.py (chaves "quality.*", "format.*", etc.).

QUALITY_OPTIONS = [
    "Melhor disponivel",
    "4K / 2160p",
    "2K / 1440p",
    "Full HD / 1080p",
    "HD / 720p",
    "480p",
    "360p",
]

FORMAT_OPTIONS = ["MP4", "WebM", "Melhor formato disponivel"]

AUDIO_FORMAT_OPTIONS = ["MP3", "M4A", "FLAC", "OGG", "WAV"]

COOKIES_OPTIONS = ["Nenhum", "chrome", "chromium", "firefox", "opera", "vivaldi", "edge"]

LANGUAGE_OPTIONS = ["pt-BR", "en-US"]

APPEARANCE_OPTIONS = ["system", "light", "dark"]
