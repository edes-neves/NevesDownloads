"""
Mixin de integração com a bandeja do sistema (tray icon).

Gerencia o ícone na bandeja, mostrar/ocultar janela, e continuar
em segundo plano. Projetado para ser misturado em NevesDownloadsApp
via herança múltipla.
"""

import contextlib
from tkinter import messagebox

from app.i18n import _
from app.services.tray_manager import SystemTray


class TrayHandler:
    """Mixin que fornece integração com a bandeja do sistema."""

    tray: "SystemTray | None"

    def _setup_tray(self):
        """Inicializa a bandeja do sistema (se disponível)."""
        if not self.tray:
            from app.utils.resources import get_resource_path

            icon_path = get_resource_path("assets/Icone.png")
            self.tray = SystemTray(
                self.app_name if hasattr(self, "app_name") else "Neves Downloads",
                icon_path=icon_path if icon_path.exists() else None,
            )

        if not self.tray.available:
            return

        self.tray.on_show = self._show_from_tray
        self.tray.on_quit = self._quit_from_tray
        self.tray.on_pause_all = self._pause_all_downloads
        self.tray.on_resume_all = self._resume_all_downloads
        self.tray.start()

    def _show_from_tray(self):
        """Restaura a janela a partir da bandeja."""
        self.after(0, self._present_window)

    def _present_window(self):
        """Mostra, deiconifica e traz a janela para frente."""
        self.deiconify()
        self.state("normal")
        self.lift()
        self.focus_force()

    def _quit_from_tray(self):
        """Sai definitivamente a partir do menu da bandeja."""
        self.after(0, self._force_quit)

    def _force_quit(self):
        """Sai definitivamente, cancelando downloads."""
        self.logger.info("Saindo via bandeja do sistema.")
        self._stop_clipboard_monitor()
        for d in self.active_downloads:
            ce = d.get("cancel_event")
            if ce is not None:
                ce.set()
        self.queue.save()
        self.destroy()

    # ── Background / fechamento ─────────────────────────────────

    def _has_active_downloads(self) -> int:
        """Retorna quantos downloads estão em andamento (incluindo pausados)."""
        self._cleanup_active_downloads()
        count = 0
        for d in self.active_downloads:
            thread = d.get("thread")
            if thread and getattr(thread, "is_alive", lambda: False)():
                count += 1
        return count

    def _continue_in_background(self):
        """Minimiza/hide a janela mantendo os downloads rodando em segundo plano."""
        self.logger.info("Continuando em segundo plano. Downloads permanecem ativos.")
        if self.tray and self.tray.available:
            if self.tray._icon is None:
                self.tray.on_show = self._show_from_tray
                self.tray.on_quit = self._quit_from_tray
                self.tray.on_pause_all = self._pause_all_downloads
                self.tray.on_resume_all = self._resume_all_downloads
                self.tray.start()
            self.withdraw()
            self.after(100, self._show_background_hint)
        else:
            messagebox.showinfo(
                _("dialog.background.title"),
                _("dialog.background.body"),
            )
            self.iconify()

    def _show_background_hint(self):
        """Mostra uma dica não-bloqueante ao continuar em segundo plano (com tray)."""
        with contextlib.suppress(Exception):
            self.try_notify(_("tray.notification_title"), _("tray.notification_body"))

    def try_notify(self, title: str, message: str):
        """Envia notificação nativa via notify-send (se disponível)."""
        import shutil as _shutil

        if _shutil.which("notify-send"):
            import subprocess

            subprocess.Popen(["notify-send", title, message], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
