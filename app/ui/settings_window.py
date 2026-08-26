import logging
from tkinter import messagebox

import customtkinter as ctk

from app.constants import (
    APPEARANCE_OPTIONS,
    AUDIO_FORMAT_OPTIONS,
    COOKIES_OPTIONS,
    FORMAT_OPTIONS,
    LANGUAGE_OPTIONS,
    QUALITY_OPTIONS,
)
from app.i18n import _, set_language
from app.services import settings
from app.services.sponsorblock import get_categories_labels

logger = logging.getLogger("neves_downloads")


class SettingsWindow(ctk.CTkToplevel):
    """
    Janela de configurações avançadas persistentes.
    Todas as alterações são salvas imediatamente via settings.save().
    """

    def __init__(self, master, on_saved=None):
        super().__init__(master)
        self.title(_("settings.title"))
        self.geometry("760x640")
        self.minsize(600, 480)
        self.transient(master)
        self.after(100, self.grab_set)

        # Callback chamado após salvar para que a main_window aplique o tema etc.
        self.on_saved = on_saved

        self._cfg = settings.load_all()

        # ── Variáveis de controle ──
        self.appearance_var = ctk.StringVar(value=self._cfg.get("appearance_mode", "system"))
        self.language_var = ctk.StringVar(value=self._cfg.get("default_language", "pt-BR"))
        self.automatic_updates_var = ctk.BooleanVar(value=self._cfg.get("automatic_updates", True))

        self.default_type_var = ctk.StringVar(value=self._cfg.get("default_type", "video"))
        self.default_mode_var = ctk.StringVar(value=self._cfg.get("default_mode", "video"))
        self.quality_var = ctk.StringVar(value=self._cfg.get("default_quality"))
        self.format_var = ctk.StringVar(value=self._cfg.get("default_format"))
        self.audio_format_var = ctk.StringVar(value=self._cfg.get("default_audio_format"))
        self.cookies_var = ctk.StringVar(value=self._cfg.get("default_cookies_browser"))
        self.organize_var = ctk.BooleanVar(value=self._cfg.get("default_organize", False))
        self.subtitles_var = ctk.BooleanVar(value=self._cfg.get("default_subtitles_enabled", False))
        self.subtitle_langs_var = ctk.StringVar(value=self._cfg.get("default_subtitle_langs", "pt,en"))

        self.max_concurrent_var = ctk.StringVar(value=str(self._cfg.get("max_concurrent_downloads", 3)))
        self.proxy_var = ctk.StringVar(value=self._cfg.get("proxy", ""))
        self.limit_speed_var = ctk.StringVar(value=str(self._cfg.get("limit_speed", 0)))
        self.retries_var = ctk.StringVar(value=str(self._cfg.get("retries", 3)))
        self.socket_timeout_var = ctk.StringVar(value=str(self._cfg.get("socket_timeout", 30)))

        self.filename_template_var = ctk.StringVar(value=self._cfg.get("filename_template", "%(title)s.%(ext)s"))
        self.embed_thumb_var = ctk.BooleanVar(value=self._cfg.get("embed_thumbnail", False))
        self.write_thumb_var = ctk.BooleanVar(value=self._cfg.get("write_thumbnail", False))

        self.confirm_exit_var = ctk.BooleanVar(value=self._cfg.get("confirm_on_exit_with_active_downloads", True))
        self.auto_clear_var = ctk.BooleanVar(value=self._cfg.get("auto_clear_completed", False))

        # ── Novas configurações (SponsorBlock, TikTok, Multi-threading) ──
        self.sponsorblock_var = ctk.BooleanVar(value=self._cfg.get("sponsorblock_enabled", False))
        self.sponsorblock_cats_var = ctk.StringVar(
            value=self._cfg.get("sponsorblock_categories", "sponsor,selfpromo,interaction,intro,outro,preview")
        )
        self.concurrent_fragments_var = ctk.StringVar(value=str(self._cfg.get("concurrent_fragments", 1)))
        self.tiktok_watermark_var = ctk.BooleanVar(value=self._cfg.get("tiktok_watermark_removal", True))

        self._build_ui()

    # ── Construção da UI ─────────────────────────────────────────

    def _build_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # Area rolável principal
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=15, pady=(15, 5))
        scroll.grid_columnconfigure(0, weight=1)

        row = 0

        # ── Aparência e Idioma ──
        row = self._section(scroll, row, _("settings.section.appearance"))

        self._label(scroll, row, _("settings.appearance_theme"))
        self._option_menu(scroll, row, self.appearance_var, APPEARANCE_OPTIONS, callback=self._apply_appearance)
        row += 1

        self._label(scroll, row, _("settings.language"))
        self._option_menu(scroll, row, self.language_var, LANGUAGE_OPTIONS)
        row += 2

        # ── Padrões de download ──
        row = self._section(scroll, row, _("settings.section.download"))

        self._label(scroll, row, _("settings.default_type"))
        self._radio_group(
            scroll,
            row,
            self.default_type_var,
            {"video": _("settings.type.video"), "audio": _("settings.type.audio")},
        )
        row += 1

        self._label(scroll, row, _("settings.default_mode"))
        self._radio_group(
            scroll,
            row,
            self.default_mode_var,
            {
                "video": _("settings.mode.video"),
                "playlist_all": _("settings.mode.playlist_all"),
                "playlist_select": _("settings.mode.playlist_select"),
            },
        )
        row += 2

        self._label(scroll, row, _("settings.default_quality"))
        self._option_menu(scroll, row, self.quality_var, QUALITY_OPTIONS)
        row += 1

        self._label(scroll, row, _("settings.default_format"))
        self._option_menu(scroll, row, self.format_var, FORMAT_OPTIONS)
        row += 1

        self._label(scroll, row, _("settings.default_audio_format"))
        self._option_menu(scroll, row, self.audio_format_var, AUDIO_FORMAT_OPTIONS)
        row += 1

        self._label(scroll, row, _("settings.cookies"))
        self._option_menu(scroll, row, self.cookies_var, COOKIES_OPTIONS)
        row += 1

        # Checkboxes organizar / legendas
        ctk.CTkCheckBox(scroll, text=_("settings.organize"), variable=self.organize_var).grid(
            row=row, column=0, sticky="w", padx=10, pady=2
        )
        row += 1

        ctk.CTkCheckBox(scroll, text=_("settings.download_subtitles"), variable=self.subtitles_var).grid(
            row=row, column=0, sticky="w", padx=10, pady=2
        )
        row += 1

        self._label(scroll, row, _("settings.subtitle_langs"))
        ctk.CTkEntry(scroll, textvariable=self.subtitle_langs_var, height=30, width=320).grid(
            row=row, column=1, sticky="w", padx=(0, 10), pady=3
        )
        row += 2

        # ── Rede e Desempenho ──
        row = self._section(scroll, row, _("settings.section.network"))

        self._label(scroll, row, _("settings.concurrent_downloads"))
        ctk.CTkEntry(scroll, textvariable=self.max_concurrent_var, height=30, width=80, placeholder_text="3").grid(
            row=row, column=1, sticky="w", padx=(0, 10), pady=3
        )
        row += 1

        self._label(scroll, row, _("settings.proxy"))
        ctk.CTkEntry(
            scroll,
            textvariable=self.proxy_var,
            height=30,
            width=400,
            placeholder_text=_("settings.proxy_placeholder"),
        ).grid(row=row, column=1, sticky="w", padx=(0, 10), pady=3)
        row += 1

        self._label(scroll, row, _("settings.speed_limit"))
        ctk.CTkEntry(scroll, textvariable=self.limit_speed_var, height=30, width=120, placeholder_text="0").grid(
            row=row, column=1, sticky="w", padx=(0, 10), pady=3
        )
        row += 1

        self._label(scroll, row, _("settings.retries"))
        ctk.CTkEntry(scroll, textvariable=self.retries_var, height=30, width=80, placeholder_text="3").grid(
            row=row, column=1, sticky="w", padx=(0, 10), pady=3
        )
        row += 1

        self._label(scroll, row, _("settings.timeout"))
        ctk.CTkEntry(scroll, textvariable=self.socket_timeout_var, height=30, width=80, placeholder_text="30").grid(
            row=row, column=1, sticky="w", padx=(0, 10), pady=3
        )
        row += 1

        self._label(scroll, row, _("settings.concurrent_fragments"))
        ctk.CTkEntry(
            scroll, textvariable=self.concurrent_fragments_var, height=30, width=80, placeholder_text="1"
        ).grid(row=row, column=1, sticky="w", padx=(0, 10), pady=3)
        row += 1

        ctk.CTkLabel(
            scroll,
            text=_("settings.fragments_hint"),
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).grid(row=row, column=1, columnspan=2, sticky="w", padx=(0, 10), pady=(0, 5))
        row += 2

        # ── SponsorBlock ──
        row = self._section(scroll, row, _("settings.section.sponsorblock"))

        ctk.CTkCheckBox(
            scroll,
            text=_("settings.sponsorblock_enable"),
            variable=self.sponsorblock_var,
        ).grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        row += 1

        self._label(scroll, row, _("settings.sponsorblock_categories"))
        ctk.CTkEntry(
            scroll,
            textvariable=self.sponsorblock_cats_var,
            height=30,
            width=450,
        ).grid(row=row, column=1, sticky="w", padx=(0, 10), pady=3)
        row += 1

        cats_labels = get_categories_labels()
        cats_text = _("settings.sponsorblock_available").format(
            categories=", ".join(f"{k} ({v})" for k, v in cats_labels.items())
        )
        ctk.CTkLabel(scroll, text=cats_text, font=ctk.CTkFont(size=10), text_color="gray").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 5)
        )
        row += 2

        # ── TikTok ──
        row = self._section(scroll, row, _("settings.section.tiktok"))

        ctk.CTkCheckBox(
            scroll,
            text=_("settings.tiktok_optimize"),
            variable=self.tiktok_watermark_var,
        ).grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=2)
        row += 2

        # ── Nomeação de Arquivos e Thumbnails ──
        row = self._section(scroll, row, _("settings.section.filenames"))

        self._label(scroll, row, _("settings.filename_template"))
        ctk.CTkEntry(scroll, textvariable=self.filename_template_var, height=30, width=400).grid(
            row=row, column=1, sticky="w", padx=(0, 10), pady=3
        )
        row += 1

        ctk.CTkLabel(
            scroll,
            text=_("settings.filename_vars"),
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).grid(row=row, column=1, columnspan=2, sticky="w", padx=(0, 10), pady=(0, 5))
        row += 1

        ctk.CTkCheckBox(scroll, text=_("settings.embed_thumbnail"), variable=self.embed_thumb_var).grid(
            row=row, column=0, sticky="w", padx=10, pady=2
        )
        row += 1

        ctk.CTkCheckBox(scroll, text=_("settings.save_thumbnail"), variable=self.write_thumb_var).grid(
            row=row, column=0, sticky="w", padx=10, pady=2
        )
        row += 2

        # ── Comportamento ──
        row = self._section(scroll, row, _("settings.section.behavior"))

        ctk.CTkCheckBox(scroll, text=_("settings.confirm_exit"), variable=self.confirm_exit_var).grid(
            row=row, column=0, sticky="w", padx=10, pady=2
        )
        row += 1

        ctk.CTkCheckBox(scroll, text=_("settings.auto_clear"), variable=self.auto_clear_var).grid(
            row=row, column=0, sticky="w", padx=10, pady=2
        )
        row += 1

        # ── Botões ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=(5, 15))

        ctk.CTkButton(
            btn_frame,
            text=_("btn.restore_defaults"),
            width=150,
            fg_color="#b02b2b",
            hover_color="#7a1f1f",
            command=self._reset_defaults,
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text=_("btn.save"), width=120, fg_color="#2b8c3e", hover_color="#1e6b30", command=self._save
        ).pack(side="right", padx=(5, 0))

        ctk.CTkButton(btn_frame, text=_("btn.cancel"), width=100, command=self.destroy).pack(side="right")

    # ── Helpers de UI ────────────────────────────────────────────

    def _section(self, parent, row, title):
        """Cria um cabeçalho de seção e retorna a linha atual+1."""
        ctk.CTkLabel(parent, text=title, font=ctk.CTkFont(size=15, weight="bold"), text_color="#2b8c3e").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(12, 6)
        )
        return row + 1

    def _label(self, parent, row, text):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=13), anchor="w", justify="left").grid(
            row=row, column=0, sticky="w", padx=10, pady=3
        )

    def _option_menu(self, parent, row, var, values, callback=None):
        ctk.CTkOptionMenu(
            parent, variable=var, values=values, width=220, font=ctk.CTkFont(size=12), command=callback
        ).grid(row=row, column=1, sticky="w", padx=(0, 10), pady=3)

    def _radio_group(self, parent, row, var, options: dict):
        """options = {valor: texto} dispostos horizontalmente."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=1, sticky="w", padx=(0, 10), pady=3)
        for value, text in options.items():
            ctk.CTkRadioButton(frame, text=text, variable=var, value=value, font=ctk.CTkFont(size=12)).pack(
                side="left", padx=(0, 10)
            )

    # ── Ações ────────────────────────────────────────────────────

    def _apply_appearance(self, mode):
        """Aplica o tema em tempo real (pré-visualização)."""
        ctk.set_appearance_mode(mode)

    def _reset_defaults(self):
        if messagebox.askyesno(
            _("dialog.settings.restore_title"),
            _("dialog.settings.restore_body"),
            icon="warning",
        ):
            settings.reset_to_defaults()
            messagebox.showinfo(_("settings.title"), _("dialog.settings.restored"))
            # Recarrega valores
            self._cfg = settings.load_all()
            # Atualiza as variáveis existentes com os novos padrões
            self._sync_vars_from_cfg()

    def _sync_vars_from_cfg(self):
        """Atualiza variáveis de controle após resetar padrões."""
        self.appearance_var.set(self._cfg.get("appearance_mode", "system"))
        self.language_var.set(self._cfg.get("default_language", "pt-BR"))
        self.automatic_updates_var.set(self._cfg.get("automatic_updates", True))
        self.default_type_var.set(self._cfg.get("default_type", "video"))
        self.default_mode_var.set(self._cfg.get("default_mode", "video"))
        self.quality_var.set(self._cfg.get("default_quality"))
        self.format_var.set(self._cfg.get("default_format"))
        self.audio_format_var.set(self._cfg.get("default_audio_format"))
        self.cookies_var.set(self._cfg.get("default_cookies_browser"))
        self.organize_var.set(self._cfg.get("default_organize", False))
        self.subtitles_var.set(self._cfg.get("default_subtitles_enabled", False))
        self.subtitle_langs_var.set(self._cfg.get("default_subtitle_langs", "pt,en"))
        self.max_concurrent_var.set(str(self._cfg.get("max_concurrent_downloads", 3)))
        self.proxy_var.set(self._cfg.get("proxy", ""))
        self.limit_speed_var.set(str(self._cfg.get("limit_speed", 0)))
        self.retries_var.set(str(self._cfg.get("retries", 3)))
        self.socket_timeout_var.set(str(self._cfg.get("socket_timeout", 30)))
        self.filename_template_var.set(self._cfg.get("filename_template", "%(title)s.%(ext)s"))
        self.embed_thumb_var.set(self._cfg.get("embed_thumbnail", False))
        self.write_thumb_var.set(self._cfg.get("write_thumbnail", False))
        self.confirm_exit_var.set(self._cfg.get("confirm_on_exit_with_active_downloads", True))
        self.auto_clear_var.set(self._cfg.get("auto_clear_completed", False))
        self.sponsorblock_var.set(self._cfg.get("sponsorblock_enabled", False))
        self.sponsorblock_cats_var.set(
            self._cfg.get("sponsorblock_categories", "sponsor,selfpromo,interaction,intro,outro,preview")
        )
        self.concurrent_fragments_var.set(str(self._cfg.get("concurrent_fragments", 1)))
        self.tiktok_watermark_var.set(self._cfg.get("tiktok_watermark_removal", True))

    def _save(self):
        """Valida e salva todas as configurações."""

        # Validação de inteiros
        def _valid_int(var, name, default):
            try:
                val = int(var.get().strip())
            except (ValueError, AttributeError):
                val = default
            if val < 0:
                val = default
            return val

        def _valid_positive_int(var, name, default):
            try:
                val = int(var.get().strip())
            except (ValueError, AttributeError):
                val = default
            if val < 1:
                val = default
            return val

        # Proxy: validar formato básico se informado
        proxy = self.proxy_var.get().strip()
        if proxy and not (
            proxy.startswith("http://")
            or proxy.startswith("https://")
            or proxy.startswith("socks4://")
            or proxy.startswith("socks5://")
        ):
            messagebox.showwarning(_("dialog.proxy.title"), _("dialog.proxy.body"))
            proxy = ""

        settings.save("appearance_mode", self.appearance_var.get())
        settings.save("default_language", self.language_var.get())
        settings.save("automatic_updates", self.automatic_updates_var.get())

        settings.save("default_type", self.default_type_var.get())
        settings.save("default_mode", self.default_mode_var.get())
        settings.save("default_quality", self.quality_var.get())
        settings.save("default_format", self.format_var.get())
        settings.save("default_audio_format", self.audio_format_var.get())
        settings.save("default_cookies_browser", self.cookies_var.get())
        settings.save("default_organize", self.organize_var.get())
        settings.save("default_subtitles_enabled", self.subtitles_var.get())
        settings.save("default_subtitle_langs", self.subtitle_langs_var.get())

        settings.save(
            "max_concurrent_downloads", _valid_positive_int(self.max_concurrent_var, "Downloads simultâneos", 3)
        )
        settings.save("proxy", proxy)
        settings.save("limit_speed", _valid_int(self.limit_speed_var, "Limite de velocidade", 0))
        settings.save("retries", _valid_positive_int(self.retries_var, "Tentativas", 3))
        settings.save("socket_timeout", _valid_positive_int(self.socket_timeout_var, "Timeout", 30))

        settings.save("filename_template", self.filename_template_var.get().strip() or "%(title)s.%(ext)s")
        settings.save("embed_thumbnail", self.embed_thumb_var.get())
        settings.save("write_thumbnail", self.write_thumb_var.get())

        settings.save("confirm_on_exit_with_active_downloads", self.confirm_exit_var.get())
        settings.save("auto_clear_completed", self.auto_clear_var.get())

        # Novas configurações
        settings.save("sponsorblock_enabled", self.sponsorblock_var.get())
        settings.save("sponsorblock_categories", self.sponsorblock_cats_var.get().strip())
        settings.save(
            "concurrent_fragments", _valid_positive_int(self.concurrent_fragments_var, "Fragments paralelos", 1)
        )
        settings.save("tiktok_watermark_removal", self.tiktok_watermark_var.get())

        # Aplica tema imediatamente
        ctk.set_appearance_mode(self.appearance_var.get())

        # Atualiza idioma ativo
        set_language(self.language_var.get())

        # Notifica a janela principal para aplicar as novas configurações
        if self.on_saved:
            try:
                self.on_saved()
            except Exception as e:
                logger.error("Erro ao aplicar configurações: %s", e)

        messagebox.showinfo(_("settings.title"), _("dialog.settings.saved"), parent=self)
        self.destroy()
