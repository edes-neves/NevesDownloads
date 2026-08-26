"""
Mixin de monitoramento da área de transferência (clipboard).

Gerencia o ClipboardMonitor, incluindo ativar/desativar e tratar
URLs detectadas. Projetado para ser misturado em NevesDownloadsApp
via herança múltipla.
"""

from app.i18n import _
from app.services.clipboard_monitor import ClipboardMonitor


class ClipboardHandler:
    """Mixin que fornece monitoramento de clipboard para a janela principal."""

    _clipboard_monitor: "ClipboardMonitor | None"
    _clipboard_monitor_active: bool

    def _toggle_clipboard_monitor(self):
        """Ativa/desativa o monitor de área de transferência."""
        if self._clipboard_monitor_active:
            self._stop_clipboard_monitor()
        else:
            self._start_clipboard_monitor()

    def _start_clipboard_monitor(self):
        """Inicia o monitor de área de transferência."""
        if self._clipboard_monitor and self._clipboard_monitor.running:
            return

        self._clipboard_monitor = ClipboardMonitor(
            on_url_detected=self._on_clipboard_url_detected,
        )
        self._clipboard_monitor.start()
        self._clipboard_monitor_active = True
        self._edit_menu.entryconfigure(4, label=_("menu.edit.clipboard_off"))
        self.logger.info("Monitor de área de transferência ativado.")

    def _stop_clipboard_monitor(self):
        """Para o monitor de área de transferência."""
        if self._clipboard_monitor:
            self._clipboard_monitor.stop()
            self._clipboard_monitor = None
        self._clipboard_monitor_active = False
        self._edit_menu.entryconfigure(4, label=_("menu.edit.clipboard_on"))
        self.logger.info("Monitor de área de transferência desativado.")

    def _on_clipboard_url_detected(self, url: str):
        """Chamado quando uma URL é detectada na área de transferência."""
        self.after(0, lambda: self._handle_clipboard_url(url))

    def _handle_clipboard_url(self, url: str):
        """Trata a URL detectada no clipboard (roda na thread da UI)."""
        current = self._get_url_text()
        if url in current:
            return

        if not current.strip():
            self._set_url_text(url)
            self.logger.info(f"URL auto-detectada: {url}")
        else:
            new_text = current.strip() + "\n" + url
            self._set_url_text(new_text)
            self.logger.info(f"URL adicionada do clipboard: {url}")
