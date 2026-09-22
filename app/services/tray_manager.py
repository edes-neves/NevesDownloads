"""
Gerenciador da bandeja do sistema (tray icon).

Permite que o aplicativo continue rodando em segundo plano mesmo com a
janela principal fechada/oculta, mantendo os downloads ativos.

Se o pacote `pystray` não estiver instalado, o sistema degrada graciosamente:
o fechamento volta a minimizar a janela (iconify) em vez de usar a bandeja.
"""

from __future__ import annotations

import logging
import threading
import typing
from pathlib import Path

from app.i18n import _

logger = logging.getLogger("neves_downloads")

try:
    import pystray
    from PIL import Image, ImageDraw

    _TRAY_AVAILABLE = True
except Exception:
    # Ambientes headless/sem display X: o pystray levanta DisplayNameError
    # (não-ImportError) ao importar; a bandeja então fica desabilitada.
    _TRAY_AVAILABLE = False
    logger.info("pystray indisponível (sem display) - bandeja do sistema desabilitada.")


class SystemTray:
    """Abstração sobre a bandeja do sistema."""

    def __init__(self, app_name: str, icon_path: Path | None = None):
        self.app_name = app_name
        self.icon_path = icon_path
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None
        self._paused: bool = False
        self.on_show: typing.Callable[[], None] | None = None
        self.on_quit: typing.Callable[[], None] | None = None
        self.on_pause_all: typing.Callable[[], None] | None = None
        self.on_resume_all: typing.Callable[[], None] | None = None

    @property
    def available(self) -> bool:
        return _TRAY_AVAILABLE

    def _create_image(self) -> Image.Image:
        """Cria a imagem do ícone (do arquivo, se existir, senão um desenho simples)."""
        if self.icon_path and self.icon_path.exists():
            try:
                img: Image.Image = Image.open(self.icon_path)
                img = img.resize((64, 64), Image.Resampling.LANCZOS)
                return img
            except Exception as e:
                logger.error("Erro ao carregar ícone do tray: %s", e)

        # Ícone fallback: círculo verde com a letra 'N'
        img = Image.new("RGB", (64, 64), (43, 140, 62))
        d = ImageDraw.Draw(img)
        d.text((20, 10), "N", fill=(255, 255, 255))
        return img

    def _build_menu(self):
        menu_items = [
            pystray.MenuItem(_("tray.show_hide"), self._on_show, default=True),
        ]
        if self.on_pause_all:
            menu_items.append(pystray.MenuItem(_("tray.pause_all"), self._on_pause_all))
        if self.on_resume_all:
            menu_items.append(pystray.MenuItem(_("tray.resume_all"), self._on_resume_all))
        menu_items.append(pystray.Menu.SEPARATOR)
        menu_items.append(pystray.MenuItem(_("tray.quit"), self._on_quit))
        return pystray.Menu(*menu_items)

    def start(self):
        """Inicia a bandeja em uma thread daemon separada."""
        if not _TRAY_AVAILABLE:
            logger.warning("Bandeja não iniciada: pystray indisponível.")
            return False

        def _run():
            try:
                self._icon = pystray.Icon(
                    self.app_name,
                    self._create_image(),
                    self.app_name,
                    self._build_menu(),
                )
                self._icon.run()
            except Exception as e:
                logger.error("Erro ao iniciar bandeja: %s", e)
                self._icon = None

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        logger.info("Bandeja do sistema iniciada.")
        return True

    def stop(self):
        """Para a bandeja (se estiver rodando)."""
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception as e:
                logger.error("Erro ao parar bandeja: %s", e)

    # ── Callbacks internos ──
    def update_menu(self):
        """Atualiza o menu do ícone da bandeja (se estiver em execução)."""
        if self._icon is None:
            return
        try:
            self._icon.menu = self._build_menu()
        except Exception as e:
            logger.warning("Falha ao atualizar menu da bandeja: %s", e)

    def _on_show(self, icon=None, item=None):
        if self.on_show:
            self.on_show()

    def _on_quit(self, icon=None, item=None):
        if self.on_quit:
            self.on_quit()

    def _on_pause_all(self, icon=None, item=None):
        if self.on_pause_all:
            self.on_pause_all()

    def _on_resume_all(self, icon=None, item=None):
        if self.on_resume_all:
            self.on_resume_all()
