"""Notificações nativas do sistema (best-effort) para eventos do aplicativo.

Utiliza as ferramentas do próprio SO quando disponíveis (notify-send,
osascript, PowerShell) e nunca levanta exceção: qualquer falha é registrada
em nível debug e ignorada.
"""

import logging
import shutil
import subprocess
import sys

logger = logging.getLogger("neves_downloads")


def _run(args: list[str], timeout: int = 8) -> None:
    """Executa um comando de notificação em silêncio e sem interação."""
    subprocess.run(
        args,
        timeout=timeout,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _notify_linux(title: str, message: str) -> None:
    notifier = shutil.which("notify-send")
    if not notifier:
        return
    _run([notifier, "-a", "Neves Downloads", "-i", "dialog-information", "-t", "5000", title, message])


def _notify_macos(title: str, message: str) -> None:
    import json

    script = f"display notification {json.dumps(message)} with title {json.dumps(title)}"
    _run(["osascript", "-e", script])


def _notify_windows(title: str, message: str) -> None:
    import json

    ps = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "Add-Type -AssemblyName System.Drawing; "
        "$n = New-Object System.Windows.Forms.NotifyIcon; "
        "$n.Icon = [System.Drawing.SystemIcons]::Information; "
        f"$n.BalloonTipTitle = {json.dumps(title)}; "
        f"$n.BalloonTipText = {json.dumps(message)}; "
        "$n.Visible = $true; $n.ShowBalloonTip(5000); "
        "Start-Sleep -Milliseconds 5500; $n.Dispose()"
    )
    _run(["powershell", "-NoProfile", "-Command", ps], timeout=12)


def notify_system(title: str, message: str, icon: str = "normal") -> None:
    """Envia uma notificação nativa quando possível. Silencioso em falhas."""
    try:
        if sys.platform.startswith("win"):
            _notify_windows(title, message)
        elif sys.platform == "darwin":
            _notify_macos(title, message)
        else:
            _notify_linux(title, message)
    except Exception as e:
        logger.debug("Notificacao de sistema indisponivel: %s", e)
