"""
Monitor de área de transferência (clipboard monitor).

Verifica periodicamente se uma URL foi copiada para a área de transferência
e notifica o aplicativo principal quando detecta. Funciona em segundo plano
com intervalo configurável (padrão: 1.5 segundos).

Compatível com X11 (xclip/xsel) e Wayland (wl-paste) no Linux.
"""

import logging
import re
import subprocess
import threading
from collections.abc import Callable

logger = logging.getLogger("neves_downloads")

URL_PATTERN = re.compile(r'https?://[^\s,;<>"\']+')
_POLL_INTERVAL = 1.5  # segundos


class ClipboardMonitor:
    """
    Monitora a área de transferência em busca de URLs.

    Uso:
        monitor = ClipboardMonitor(on_url_detected=callback)
        monitor.start()
        ...
        monitor.stop()
    """

    def __init__(self, on_url_detected: Callable[[str], None], poll_interval: float = _POLL_INTERVAL):
        """
        Args:
            on_url_detected: Chamado com a URL encontrada quando uma nova URL
                             é detectada na área de transferência.
            poll_interval: Intervalo em segundos entre verificações.
        """
        self._on_url = on_url_detected
        self._interval = poll_interval
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_clipboard = ""
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def start(self):
        """Inicia o monitor em uma thread daemon."""
        if self._running:
            logger.debug("Clipboard monitor já está rodando.")
            return

        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="ClipboardMonitor")
        self._thread.start()
        logger.info("Clipboard monitor iniciado.")

    def stop(self):
        """Para o monitor."""
        if not self._running:
            return
        self._stop_event.set()
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)
        logger.info("Clipboard monitor parado.")

    def _poll_loop(self):
        """Loop principal de monitoramento."""
        while not self._stop_event.is_set():
            try:
                text = self._read_clipboard()
                if text and text != self._last_clipboard:
                    self._last_clipboard = text
                    url = self._extract_first_url(text)
                    if url:
                        logger.debug(f"URL detectada na área de transferência: {url}")
                        self._on_url(url)
            except Exception as e:
                logger.debug(f"Erro ao ler clipboard: {e}")
            self._stop_event.wait(self._interval)

    @staticmethod
    def _read_clipboard() -> str | None:
        """Lê o conteúdo atual da área de transferência no Linux."""
        # Tenta xclip (X11)
        try:
            result = subprocess.run(
                ["xclip", "-selection", "clipboard", "-o"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except FileNotFoundError:
            pass
        except subprocess.TimeoutExpired:
            pass

        # Tenta xsel (X11)
        try:
            result = subprocess.run(
                ["xsel", "--clipboard", "--output"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except FileNotFoundError:
            pass
        except subprocess.TimeoutExpired:
            pass

        # Tenta wl-paste (Wayland)
        try:
            result = subprocess.run(
                ["wl-paste"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except FileNotFoundError:
            pass
        except subprocess.TimeoutExpired:
            pass

        return None

    @staticmethod
    def _extract_first_url(text: str) -> str | None:
        """Extrai a primeira URL http/https de um texto."""
        if not text:
            return None
        # Não processar textos muito longos (provavelmente não são URLs)
        if len(text) > 2048:
            return None
        match = URL_PATTERN.search(text)
        if match:
            url = match.group(0)
            url = url.rstrip(".,;!?)]}>")
            return url
        return None
