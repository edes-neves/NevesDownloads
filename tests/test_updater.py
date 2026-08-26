"""Testes unitários para app.services.updater."""

from unittest.mock import MagicMock, patch

from app.services.updater import check_latest_version, get_current_version, update_ytdlp


class TestGetCurrentVersion:
    """Testes para get_current_version."""

    def test_retorna_string(self):
        version = get_current_version()
        assert isinstance(version, str)
        assert version != ""

    def test_versao_formato(self):
        version = get_current_version()
        # Formato esperado: YYYY.MM.DD ou similar
        assert "." in version or version == "desconhecida"


class TestCheckLatestVersion:
    """Testes para check_latest_version."""

    @patch("app.services.updater.subprocess.run")
    def test_sucesso(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="yt-dlp (2025.12.23)\n",
            stderr="",
        )
        version = check_latest_version()
        assert version == "2025.12.23"

    @patch("app.services.updater.subprocess.run")
    def test_timeout_retorna_none(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pip", timeout=30)
        version = check_latest_version()
        assert version is None

    @patch("app.services.updater.subprocess.run")
    def test_erro_retorna_none(self, mock_run):
        mock_run.side_effect = FileNotFoundError("pip not found")
        version = check_latest_version()
        assert version is None


class TestUpdateYtdlp:
    """Testes para update_ytdlp."""

    @patch("app.services.updater.subprocess.run")
    @patch("app.services.updater.get_current_version")
    def test_sucesso(self, mock_version, mock_run):
        mock_version.return_value = "2025.01.01"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Successfully installed yt-dlp-2025.02.02",
            stderr="",
        )
        result = update_ytdlp()
        assert result["success"] is True
        assert result["old_version"] == "2025.01.01"

    @patch("app.services.updater.subprocess.run")
    @patch("app.services.updater.get_current_version")
    def test_falha_retorno_nao_zero(self, mock_version, mock_run):
        mock_version.return_value = "2025.01.01"
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Permission denied",
        )
        result = update_ytdlp()
        assert result["success"] is False
        assert "Permission denied" in result["message"]

    @patch("app.services.updater.subprocess.run")
    @patch("app.services.updater.get_current_version")
    def test_timeout(self, mock_version, mock_run):
        import subprocess

        mock_version.return_value = "2025.01.01"
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pip", timeout=120)
        result = update_ytdlp()
        assert result["success"] is False
        assert "tempo" in result["message"].lower()

    @patch("app.services.updater.subprocess.run")
    @patch("app.services.updater.get_current_version")
    def test_erro_inesperado(self, mock_version, mock_run):
        mock_version.return_value = "2025.01.01"
        mock_run.side_effect = OSError("disk full")
        result = update_ytdlp()
        assert result["success"] is False
        assert "inesperado" in result["message"].lower()
