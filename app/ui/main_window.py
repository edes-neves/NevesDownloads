import threading
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from app.constants import APP_NAME, APP_VERSION, APP_WM_CLASS, AUDIO_FORMAT_OPTIONS, QUALITY_OPTIONS
from app.i18n import _, init_language, set_language
from app.services import settings
from app.services.clipboard_monitor import ClipboardMonitor
from app.services.queue import DownloadQueue
from app.services.tray_manager import SystemTray
from app.services.ytdlp_service import YtDlpService
from app.ui.clipboard_handler import ClipboardHandler
from app.ui.download_handler import DownloadHandler
from app.ui.folder_browser import FolderBrowser
from app.ui.settings_window import SettingsWindow
from app.ui.tray_handler import TrayHandler
from app.utils.logger import setup_logger
from app.utils.paths import ensure_directories

# Inicializa idioma a partir das configurações salvas
init_language()

# Configuração inicial do CustomTkinter
ctk.set_appearance_mode(settings.load("appearance_mode"))
ctk.set_default_color_theme("dark-blue")


class NevesDownloadsApp(DownloadHandler, TrayHandler, ClipboardHandler, ctk.CTk):
    """Janela principal do aplicativo."""

    def __init__(self):
        # O 'className' define o WM_CLASS (X11) de forma nativa, permitindo ao
        # gerenciador de janelas identificar e gerenciar corretamente o app.
        super().__init__(className=APP_WM_CLASS)

        # Configurações da janela
        self.app_name = APP_NAME
        self.title(_("window.title").format(name=APP_NAME, version=APP_VERSION))
        self.geometry("950x800")
        self.minsize(750, 650)
        self.resizable(True, True)
        self.after(500, self._set_wm_class)

        # ── Variáveis de controle (carregadas das configurações salvas) ──
        self.download_mode = tk.StringVar(value=settings.load("default_mode"))
        self.download_type = tk.StringVar(value=settings.load("default_type"))
        self.quality = tk.StringVar(value=settings.load("default_quality"))
        self.format_var = tk.StringVar(value=settings.load("default_format"))
        self.audio_format = tk.StringVar(value=settings.load("default_audio_format"))
        self.subtitle_langs = tk.StringVar(value=settings.load("default_subtitle_langs"))
        self.download_path = tk.StringVar(value=settings.load("download_path"))
        self.cookies_browser = tk.StringVar(value=settings.load("default_cookies_browser"))
        self.organize_var = tk.BooleanVar(value=settings.load("default_organize"))
        self.subtitles_var = tk.BooleanVar(value=settings.load("default_subtitles_enabled"))

        # ── Configurações de rede/desempenho (recarregadas nas configurações) ──
        self.max_concurrent = int(settings.load("max_concurrent_downloads"))
        self.limit_speed = int(settings.load("limit_speed"))
        self.retries = int(settings.load("retries"))
        self.socket_timeout = int(settings.load("socket_timeout"))
        self.proxy = settings.load("proxy")
        self.filename_template = settings.load("filename_template")
        self.embed_thumbnail = bool(settings.load("embed_thumbnail"))
        self.write_thumbnail = bool(settings.load("write_thumbnail"))
        self.confirm_exit_active = bool(settings.load("confirm_on_exit_with_active_downloads"))
        self.auto_clear_completed = bool(settings.load("auto_clear_completed"))
        # ── Novas configurações (SponsorBlock, TikTok, Multi-threading) ──
        self.sponsorblock_enabled = bool(settings.load("sponsorblock_enabled"))
        self.sponsorblock_categories = settings.load("sponsorblock_categories")
        self.concurrent_fragments = int(settings.load("concurrent_fragments"))
        self.tiktok_watermark_removal = bool(settings.load("tiktok_watermark_removal"))
        # Semáforo para limitar downloads simultâneos
        self.semaphore = threading.Semaphore(self.max_concurrent)

        # Logger e serviço
        self.logger = setup_logger()
        self.logger.info("Iniciando %s versão %s", APP_NAME, APP_VERSION)
        self.yt_service = YtDlpService()

        # Garantir diretórios
        ensure_directories()

        # Construir interface
        self._create_widgets()
        self._configure_grid()
        self._bind_right_click()

        # Fila persistente de downloads pendentes
        self.queue = DownloadQueue(persist=True)
        # Controles globais de pausa (pausar/retomar todos)
        self.global_pause_event = threading.Event()
        # Bandeja do sistema (opcional, via pystray)
        self.tray: SystemTray | None = None

        # Restaura downloads pendentes na fila do último uso
        self._restore_pending_queue()

        # Inicializa a bandeja do sistema (opcional)
        self._setup_tray()

        # Monitor de área de transferência (inicia desativado)
        self._clipboard_monitor: ClipboardMonitor | None = None
        self._clipboard_monitor_active = False

        # Bind para fechamento
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Controle de downloads ativos
        self.active_downloads = []

    # ── Menu de contexto ────────────────────────────────────────

    def _bind_right_click(self):
        """Vincula botão direito para colar URL na entry."""
        self.url_entry.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event):
        """Exibe menu de contexto na entry com opção Colar."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label=_("ctx.paste"), command=self._paste_from_clipboard)
        menu.add_separator()
        menu.add_command(label=_("ctx.clear"), command=self._clear_url_entry)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # ── Menu bar ────────────────────────────────────────────────

    def _create_menu_bar(self):
        menubar = tk.Menu(self)

        # ── Arquivo ──
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label=_("menu.file.paste_url"), command=self._paste_from_clipboard, accelerator="Ctrl+V")
        file_menu.add_separator()
        file_menu.add_command(label=_("menu.file.exit"), command=self._on_close)
        menubar.add_cascade(label=_("menu.file"), menu=file_menu)

        # ── Configurações ──
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label=_("menu.settings.title"), command=self._open_settings_window)
        settings_menu.add_separator()
        settings_menu.add_command(label=_("menu.settings.folder"), command=self._choose_folder)
        menubar.add_cascade(label=_("menu.settings"), menu=settings_menu)

        # ── Download ──
        dload_menu = tk.Menu(menubar, tearoff=0)
        dload_menu.add_command(label=_("menu.download.pause_all"), command=self._pause_all_downloads)
        dload_menu.add_command(label=_("menu.download.resume_all"), command=self._resume_all_downloads)
        dload_menu.add_separator()
        dload_menu.add_command(label=_("menu.download.background"), command=self._continue_in_background)
        menubar.add_cascade(label=_("menu.download"), menu=dload_menu)

        # ── Editar ──
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label=_("menu.edit.clear_url"), command=self._clear_url_entry)
        edit_menu.add_separator()
        edit_menu.add_command(label=_("menu.edit.select_all"), command=lambda: self._select_all_url_entry())
        edit_menu.add_separator()
        self._edit_menu = edit_menu
        edit_menu.add_command(label=_("menu.edit.clipboard_on"), command=self._toggle_clipboard_monitor)
        menubar.add_cascade(label=_("menu.edit"), menu=edit_menu)

        # ── Exibir ──
        view_menu = tk.Menu(menubar, tearoff=0)
        self._appearance_var = tk.StringVar(value=ctk.get_appearance_mode())
        view_menu.add_radiobutton(
            label=_("menu.view.light"), variable=self._appearance_var, value="Light", command=self._set_appearance_light
        )
        view_menu.add_radiobutton(
            label=_("menu.view.dark"), variable=self._appearance_var, value="Dark", command=self._set_appearance_dark
        )
        view_menu.add_radiobutton(
            label=_("menu.view.system"),
            variable=self._appearance_var,
            value="System",
            command=self._set_appearance_system,
        )
        view_menu.add_separator()
        view_menu.add_command(label=_("menu.view.history"), command=self._show_history)
        menubar.add_cascade(label=_("menu.view"), menu=view_menu)

        # ── Historico ──
        hist_menu = tk.Menu(menubar, tearoff=0)
        hist_menu.add_command(label=_("menu.history.view"), command=self._show_history)
        hist_menu.add_command(label=_("menu.history.clear"), command=self._clear_history)
        menubar.add_cascade(label=_("menu.history"), menu=hist_menu)

        # ── Ajuda ──
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label=_("menu.help.update_app"), command=self._check_app_update)
        help_menu.add_command(label=_("menu.help.update_ytdlp"), command=self._check_ytdlp_update)
        help_menu.add_separator()
        help_menu.add_command(
            label=_("menu.help.get_help"),
            command=lambda: self._open_email("nevestecnologias@gmail.com", subject=_("email.subject.help")),
        )
        help_menu.add_command(
            label=_("menu.help.report_issues"),
            command=lambda: self._open_email("nevestecnologias@gmail.com", subject=_("email.subject.bug")),
        )
        help_menu.add_command(
            label=_("menu.help.share_ideas"),
            command=lambda: self._open_email("nevestecnologias@gmail.com", subject=_("email.subject.idea")),
        )
        help_menu.add_separator()
        help_menu.add_command(label=_("menu.help.about"), command=self._show_about)
        menubar.add_cascade(label=_("menu.help"), menu=help_menu)

        self.config(menu=menubar)

        # Atalhos
        self.bind("<Control-v>", lambda e: self._paste_from_clipboard())

    def _set_appearance_light(self):
        ctk.set_appearance_mode("Light")
        settings.save("appearance_mode", "light")

    def _set_appearance_dark(self):
        ctk.set_appearance_mode("Dark")
        settings.save("appearance_mode", "dark")

    def _set_appearance_system(self):
        ctk.set_appearance_mode("System")
        settings.save("appearance_mode", "system")

    def _set_wm_class(self):
        """Garante que o WM_CLASS (X11) seja aplicado corretamente."""
        try:
            self._apply_wm_class_via_xprop()
        except Exception as e:
            self.logger.warning("Nao foi possivel definir WM_CLASS: %s", e)

    def _apply_wm_class_via_xprop(self):
        """Força o WM_CLASS via xprop (fallback) em todas as janelas X11 do processo."""
        try:
            import os
            import re
            import subprocess

            self.update_idletasks()
            pid = os.getpid()
            result = subprocess.run(["xprop", "-root", "_NET_CLIENT_LIST"], capture_output=True, text=True, timeout=3)
            ids = re.findall(r"0x[0-9a-fA-F]+", result.stdout or "")
            for wid in ids:
                pid_check = subprocess.run(
                    ["xprop", "-id", wid, "_NET_WM_PID"], capture_output=True, text=True, timeout=3
                )
                if str(pid) in pid_check.stdout:
                    subprocess.run(
                        [
                            "xprop",
                            "-id",
                            wid,
                            "-f",
                            "WM_CLASS",
                            "8s",
                            "-set",
                            "WM_CLASS",
                            f"{APP_WM_CLASS},{APP_WM_CLASS}",
                        ],
                        timeout=3,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
        except Exception:
            pass

    def _open_email(self, to: str, subject: str = ""):
        """Abre o cliente de e-mail padrão via mailto:."""
        import urllib.parse

        params = urllib.parse.urlencode({"subject": subject})
        url = f"mailto:{to}?{params}"
        self.logger.info("Abrindo email: %s", url)
        try:
            import webbrowser

            webbrowser.open(url)
        except Exception as e:
            self.logger.error("Erro ao abrir email: %s", e)
            messagebox.showinfo(_("dialog.contact.title"), _("dialog.contact.body").format(to=to))

    def _show_about(self):
        """Exibe janela Sobre o aplicativo."""
        win = ctk.CTkToplevel(self)
        win.title(_("about.title").format(name=APP_NAME))
        win.geometry("520x420")
        win.minsize(480, 400)
        win.resizable(False, False)
        win.transient(self)
        win.after(100, win.grab_set)

        scroll = ctk.CTkScrollableFrame(win)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            scroll,
            text=APP_NAME,
            font=ctk.CTkFont(size=26, weight="bold"),
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            scroll,
            text=_("about.version").format(version=APP_VERSION),
            font=ctk.CTkFont(size=14),
        ).pack(pady=(0, 15))

        ctk.CTkLabel(
            scroll,
            text=_("about.description"),
            font=ctk.CTkFont(size=13),
            justify="left",
            wraplength=460,
        ).pack(pady=(0, 15))

        ctk.CTkLabel(
            scroll,
            text=_("about.developer"),
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            scroll,
            text=_("about.contact"),
            font=ctk.CTkFont(size=12),
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            scroll,
            text=_("about.license"),
            font=ctk.CTkFont(size=11),
            justify="left",
            wraplength=460,
        ).pack(pady=(5, 10))

        ctk.CTkButton(win, text=_("btn.close"), command=win.destroy, width=100).pack(pady=(0, 15))

    # ── Widgets da janela principal ─────────────────────────────

    def _create_widgets(self):
        """Cria todos os widgets da janela."""
        self._create_menu_bar()

        # Frame principal com padding
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # Título
        self.title_label = ctk.CTkLabel(self.main_frame, text=APP_NAME, font=ctk.CTkFont(size=32, weight="bold"))
        self.title_label.grid(row=0, column=0, columnspan=4, pady=(0, 5), sticky="w")

        # Subtítulo
        self.sub_label = ctk.CTkLabel(self.main_frame, text=_("subtitle"), font=ctk.CTkFont(size=14))
        self.sub_label.grid(row=1, column=0, columnspan=4, pady=(0, 20), sticky="w")

        # URL (com menu de contexto)
        self.url_label = ctk.CTkLabel(
            self.main_frame,
            text=_("url_label"),
            font=ctk.CTkFont(size=13),
        )
        self.url_label.grid(row=2, column=0, columnspan=4, sticky="w", pady=(0, 5))

        self.url_entry = ctk.CTkTextbox(
            self.main_frame,
            height=60,
            font=ctk.CTkFont(size=14),
            wrap="char",
        )
        self.url_entry.insert("1.0", "")
        self.url_entry.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(0, 15))

        # ── Tipo de download + Qualidade + Cookies (tudo na mesma linha) ──
        self.type_label = ctk.CTkLabel(self.main_frame, text=_("type.label"), font=ctk.CTkFont(size=13, weight="bold"))
        self.type_label.grid(row=4, column=0, sticky="w", pady=(0, 5))

        self.type_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.type_frame.grid(row=5, column=0, columnspan=4, sticky="ew", pady=(0, 10))

        self.radio_video_type = ctk.CTkRadioButton(
            self.type_frame,
            text=_("type.video"),
            variable=self.download_type,
            value="video",
            font=ctk.CTkFont(size=13),
            command=self._on_type_changed,
        )
        self.radio_video_type.pack(side="left", padx=(0, 15))

        self.radio_audio_type = ctk.CTkRadioButton(
            self.type_frame,
            text=_("type.audio"),
            variable=self.download_type,
            value="audio",
            font=ctk.CTkFont(size=13),
            command=self._on_type_changed,
        )
        self.radio_audio_type.pack(side="left", padx=(0, 25))

        # Qualidade (inline)
        self.quality_label = ctk.CTkLabel(self.type_frame, text=_("quality.label"), font=ctk.CTkFont(size=13))
        self.quality_label.pack(side="left", padx=(0, 5))

        self.quality_menu = ctk.CTkOptionMenu(
            self.type_frame, variable=self.quality, values=QUALITY_OPTIONS, width=160, font=ctk.CTkFont(size=12)
        )
        self.quality_menu.pack(side="left")

        # ── Opções condicionais ──
        self.video_options_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.video_options_frame.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(0, 10))
        self.video_options_frame.grid_columnconfigure(0, weight=1)

        self.organize_check = ctk.CTkCheckBox(
            self.video_options_frame,
            text=_("organize"),
            variable=self.organize_var,
            font=ctk.CTkFont(size=13),
        )
        self.organize_check.grid(row=0, column=0, sticky="w")

        # Frame para opções de áudio (inicialmente oculto)
        self.audio_options_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.audio_options_frame.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(0, 10))
        self.audio_options_frame.grid_columnconfigure(0, weight=1)

        self.audio_fmt_label = ctk.CTkLabel(self.audio_options_frame, text=_("audio_format"), font=ctk.CTkFont(size=13))
        self.audio_fmt_label.grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.audio_format_menu = ctk.CTkOptionMenu(
            self.audio_options_frame,
            variable=self.audio_format,
            values=AUDIO_FORMAT_OPTIONS,
            width=200,
            font=ctk.CTkFont(size=13),
        )
        self.audio_format_menu.grid(row=0, column=0, sticky="w", padx=(140, 0))

        # ── Modo de download (vídeo único / playlist) + Organizar ──
        self.mode_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.mode_frame.grid(row=7, column=0, columnspan=4, sticky="ew", pady=(0, 10))

        self.radio_video = ctk.CTkRadioButton(
            self.mode_frame, text=_("mode.video"), variable=self.download_mode, value="video", font=ctk.CTkFont(size=13)
        )
        self.radio_video.pack(side="left", padx=(0, 15))

        self.radio_playlist_all = ctk.CTkRadioButton(
            self.mode_frame,
            text=_("mode.playlist_all"),
            variable=self.download_mode,
            value="playlist_all",
            font=ctk.CTkFont(size=13),
        )
        self.radio_playlist_all.pack(side="left", padx=(0, 15))

        self.radio_playlist_select = ctk.CTkRadioButton(
            self.mode_frame,
            text=_("mode.playlist_select"),
            variable=self.download_mode,
            value="playlist_select",
            font=ctk.CTkFont(size=13),
        )
        self.radio_playlist_select.pack(side="left", padx=(0, 25))

        self.subtitles_check = ctk.CTkCheckBox(
            self.mode_frame, text=_("subtitles"), variable=self.subtitles_var, font=ctk.CTkFont(size=13)
        )
        self.subtitles_check.pack(side="left", padx=(0, 5))

        self.sub_langs_entry = ctk.CTkEntry(
            self.mode_frame,
            textvariable=self.subtitle_langs,
            width=120,
            height=28,
            font=ctk.CTkFont(size=12),
            placeholder_text="pt,en",
        )
        self.sub_langs_entry.pack(side="left")

        # Estado inicial: mostrar opções de vídeo
        self._on_type_changed()

        # ── Botões de ação ──
        self.btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_frame.grid(row=8, column=0, columnspan=4, sticky="ew", pady=(15, 5))
        self.btn_frame.grid_columnconfigure(0, weight=1)
        self.btn_frame.grid_columnconfigure(1, weight=0)

        self.download_button = ctk.CTkButton(
            self.btn_frame,
            text=_("btn.start_download"),
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self._on_download_clicked,
            fg_color="#2b8c3e",
            hover_color="#1e6b30",
        )
        self.download_button.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.clear_completed_button = ctk.CTkButton(
            self.btn_frame,
            text=_("btn.clear_completed"),
            height=50,
            width=180,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._clear_completed_downloads,
            fg_color="#b02b2b",
            hover_color="#7a1f1f",
        )
        self.clear_completed_button.grid(row=0, column=1)

        # ── Área para cartões de download ──
        self.downloads_frame = ctk.CTkScrollableFrame(
            self.main_frame, label_text=_("downloads_active"), height=200, fg_color="transparent"
        )
        self.downloads_frame.grid(row=9, column=0, columnspan=4, sticky="nsew", pady=(5, 0))

        # Ajuste de pesos
        self.main_frame.grid_rowconfigure(9, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=0)
        self.main_frame.grid_columnconfigure(2, weight=0)
        self.main_frame.grid_columnconfigure(3, weight=0)

    def _configure_grid(self):
        """Configura pesos da grade principal."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _on_type_changed(self):
        """Alterna entre opções de vídeo e áudio."""
        if self.download_type.get() == "audio":
            self.video_options_frame.grid_remove()
            self.audio_options_frame.grid()
            self.subtitles_var.set(False)
            self.subtitles_check.configure(state="disabled")
        else:
            self.audio_options_frame.grid_remove()
            self.video_options_frame.grid()
            self.subtitles_check.configure(state="normal")

    def _choose_folder(self):
        dialog = FolderBrowser(self, initial_path=self.download_path.get(), title=_("folder.select"))
        self.wait_window(dialog)
        if dialog.result_path:
            self.download_path.set(dialog.result_path)
            settings.save("download_path", dialog.result_path)
            self.logger.info("Pasta de destino alterada: %s", dialog.result_path)

    def _open_settings_window(self):
        """Abre a janela de configurações avançadas persistentes."""
        SettingsWindow(
            self,
            on_saved=self._apply_settings,
        )

    def _apply_settings(self):
        """Aplica as configurações salvas na janela principal (sem reiniciar)."""
        self.logger.info("Aplicando novas configurações.")

        self.download_mode.set(settings.load("default_mode"))
        self.download_type.set(settings.load("default_type"))
        self.quality.set(settings.load("default_quality"))
        self.format_var.set(settings.load("default_format"))
        self.audio_format.set(settings.load("default_audio_format"))
        self.subtitle_langs.set(settings.load("default_subtitle_langs"))
        self.cookies_browser.set(settings.load("default_cookies_browser"))
        self.organize_var.set(bool(settings.load("default_organize")))
        self.subtitles_var.set(bool(settings.load("default_subtitles_enabled")))

        self.max_concurrent = int(settings.load("max_concurrent_downloads"))
        self.limit_speed = int(settings.load("limit_speed"))
        self.retries = int(settings.load("retries"))
        self.socket_timeout = int(settings.load("socket_timeout"))
        self.proxy = settings.load("proxy")
        self.filename_template = settings.load("filename_template")
        self.embed_thumbnail = bool(settings.load("embed_thumbnail"))
        self.write_thumbnail = bool(settings.load("write_thumbnail"))
        self.confirm_exit_active = bool(settings.load("confirm_on_exit_with_active_downloads"))
        self.auto_clear_completed = bool(settings.load("auto_clear_completed"))
        self.sponsorblock_enabled = bool(settings.load("sponsorblock_enabled"))
        self.sponsorblock_categories = settings.load("sponsorblock_categories")
        self.concurrent_fragments = int(settings.load("concurrent_fragments"))
        self.tiktok_watermark_removal = bool(settings.load("tiktok_watermark_removal"))

        # Atualiza idioma
        set_language(settings.load("default_language") or "pt-BR")

        self._on_type_changed()

    # ── Auto-atualização do yt-dlp ──────────────────────────────

    def _check_ytdlp_update(self):
        """Verifica e opcionalmente instala a versão mais recente do yt-dlp."""
        from app.services.updater import check_latest_version, get_current_version

        current = get_current_version()
        self.logger.info("Versão atual do yt-dlp: %s", current)

        def _check():
            latest = check_latest_version()
            self.after(0, lambda: self._show_update_result(current, latest))

        threading.Thread(target=_check, daemon=True).start()

    def _show_update_result(self, current: str, latest: str | None):
        """Exibe o resultado da verificação de atualização."""
        if latest is None:
            messagebox.showinfo(
                _("dialog.update.title"),
                _("dialog.update.check_failed").format(current=current),
            )
            return

        if current == latest:
            messagebox.showinfo(
                _("dialog.update.title"),
                _("dialog.update.up_to_date").format(current=current, latest=latest),
            )
        else:
            resposta = messagebox.askyesno(
                _("dialog.update.title"),
                _("dialog.update.ask").format(current=current, latest=latest),
                icon="question",
            )
            if resposta:
                self._run_ytdlp_update()

    def _run_ytdlp_update(self):
        """Executa a atualização do yt-dlp em background."""
        from app.services.updater import update_ytdlp

        self.logger.info("Iniciando atualização do yt-dlp...")

        def _update():
            result = update_ytdlp()
            self.after(0, lambda: self._show_update_complete(result))

        threading.Thread(target=_update, daemon=True).start()

    def _show_update_complete(self, result: dict):
        """Exibe o resultado da atualização."""
        if result["success"]:
            messagebox.showinfo(
                _("dialog.update.title"),
                _("dialog.update.complete").format(message=result["message"]),
            )
        else:
            messagebox.showerror(
                _("dialog.update.error_title"),
                _("dialog.update.error_hint").format(message=result["message"]),
            )

    # ── Auto-atualização do aplicativo (GitHub Releases) ────────

    def _check_app_update(self):
        """Verifica se há uma nova versão do aplicativo no GitHub."""
        from app.services.app_updater import check_for_update

        self.logger.info("Verificando atualização do aplicativo...")

        def _check():
            result = check_for_update()
            self.after(0, lambda: self._show_app_update_result(result))

        threading.Thread(target=_check, daemon=True).start()

    def _show_app_update_result(self, result: dict | None):
        """Exibe o resultado da verificação de atualização do app."""
        if result is None:
            messagebox.showerror(
                _("dialog.update.title"),
                _("app_updater.failed").format(error="Não foi possível conectar ao GitHub."),
            )
            return

        if not result["available"]:
            messagebox.showinfo(
                _("dialog.update.title"),
                _("app_updater.up_to_date").format(version=result["current"]),
            )
            return

        resposta = messagebox.askyesno(
            _("dialog.update.title"),
            _("app_updater.ask_update").format(version=result["latest"]),
            icon="question",
        )
        if resposta:
            self._run_app_update(result["release"])

    def _run_app_update(self, release: dict):
        """Baixa e instala a atualização do aplicativo."""
        from app.services.app_updater import download_release_asset, install_update

        # Encontra o AppImage nos assets
        appimage_asset = None
        for asset in release.get("assets", []):
            if asset["name"].endswith(".AppImage"):
                appimage_asset = asset
                break

        if not appimage_asset:
            messagebox.showerror(
                _("dialog.update.title"),
                _("app_updater.no_asset"),
            )
            return

        self.logger.info("Baixando atualização: %s", appimage_asset["name"])

        def _download():
            import tempfile
            from pathlib import Path

            dest = Path(tempfile.gettempdir()) / appimage_asset["name"]

            success = download_release_asset(
                appimage_asset["browser_download_url"],
                dest,
            )

            if not success:
                self.after(
                    0,
                    lambda: messagebox.showerror(
                        _("dialog.update.title"),
                        _("app_updater.failed").format(error="Falha no download."),
                    ),
                )
                return

            result = install_update(dest)
            self.after(0, lambda: self._show_install_result(result))

        threading.Thread(target=_download, daemon=True).start()

    def _show_install_result(self, result: dict):
        """Exibe o resultado da instalação da atualização."""
        if result["success"]:
            if result.get("requires_restart"):
                messagebox.showinfo(
                    _("dialog.update.title"),
                    result["message"] + "\n\n" + _("app_updater.restart_required"),
                )
            else:
                messagebox.showinfo(
                    _("dialog.update.title"),
                    result["message"],
                )
        else:
            messagebox.showerror(
                _("dialog.update.title"),
                result["message"],
            )

    # ── Fechamento ──────────────────────────────────────────────

    def _on_close(self):
        active = self._has_active_downloads()
        if active > 0 and self.confirm_exit_active:
            resposta = messagebox.askyesnocancel(
                _("dialog.exit.title"),
                _("dialog.exit.body").format(count=active),
                icon="warning",
            )
            if resposta is None:
                return
            if resposta:
                self._continue_in_background()
                return

        self.logger.info("Encerrando aplicativo.")
        self._stop_clipboard_monitor()
        self.queue.save()
        if self.tray:
            self.tray.stop()
        self.destroy()
