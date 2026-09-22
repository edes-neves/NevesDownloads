"""Testes para app.services.notifications (notificações de sistema best-effort)."""

from unittest.mock import patch

from app.services import notifications


class TestNotifySystem:
    """Verifica o dispatch de notificações por plataforma, em modo best-effort."""

    def test_linux_usa_notify_send(self):
        with (
            patch.object(notifications.sys, "platform", "linux"),
            patch.object(notifications.shutil, "which", return_value="/usr/bin/notify-send"),
            patch.object(notifications.subprocess, "run") as mock_run,
        ):
            notifications.notify_system("Titulo", "Mensagem")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "notify-send" in args[0]
        assert "Mensagem" in args[-1]

    def test_linux_sem_notify_send_nao_chama(self):
        with (
            patch.object(notifications.sys, "platform", "linux"),
            patch.object(notifications.shutil, "which", return_value=None),
            patch.object(notifications.subprocess, "run") as mock_run,
        ):
            notifications.notify_system("Titulo", "Mensagem")
        mock_run.assert_not_called()

    def test_macos_usa_osascript(self):
        with (
            patch.object(notifications.sys, "platform", "darwin"),
            patch.object(notifications.subprocess, "run") as mock_run,
        ):
            notifications.notify_system("Titulo", "Mensagem")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "osascript"
        assert "Titulo" in args[-1]

    def test_windows_usa_powershell(self):
        with (
            patch.object(notifications.sys, "platform", "win32"),
            patch.object(notifications.subprocess, "run") as mock_run,
        ):
            notifications.notify_system("Titulo", "Mensagem")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "powershell"
        assert "Mensagem" in args[-1]

    def test_erro_nao_propagado(self):
        """Falha na notificação deve ser silenciosa (não levantar exceção)."""
        with (
            patch.object(notifications.sys, "platform", "linux"),
            patch.object(notifications.shutil, "which", return_value="/usr/bin/notify-send"),
            patch.object(notifications.subprocess, "run", side_effect=OSError("falhou")),
        ):
            notifications.notify_system("Titulo", "Mensagem")

    def test_icon_argumento_aceito(self):
        with (
            patch.object(notifications.sys, "platform", "linux"),
            patch.object(notifications.shutil, "which", return_value="/usr/bin/notify-send"),
            patch.object(notifications.subprocess, "run") as mock_run,
        ):
            notifications.notify_system("Titulo", "Mensagem", icon="critical")
        mock_run.assert_called_once()
