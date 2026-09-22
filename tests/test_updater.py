"""Testes unitários para app.services.updater."""

from unittest.mock import MagicMock, patch

from app.services.updater import (
    _check_via_pypi,
    check_latest_version,
    get_current_version,
    update_ytdlp,
)


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
    """Testes para check_latest_version (HTTP via PyPI + fallback pip)."""

    @patch("app.services.updater._check_via_pypi", return_value=None)
    @patch("app.services.updater.subprocess.run")
    def test_sucesso_via_pip(self, mock_run, mock_pypi):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="yt-dlp (2025.12.23)\n",
            stderr="",
        )
        version = check_latest_version()
        assert version == "2025.12.23"

    @patch("app.services.updater._check_via_pypi", return_value=None)
    @patch("app.services.updater.subprocess.run")
    def test_timeout_retorna_none(self, mock_run, mock_pypi):
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="pip", timeout=30)
        version = check_latest_version()
        assert version is None

    @patch("app.services.updater._check_via_pypi", return_value=None)
    @patch("app.services.updater.subprocess.run")
    def test_erro_retorna_none(self, mock_run, mock_pypi):
        mock_run.side_effect = FileNotFoundError("pip not found")
        version = check_latest_version()
        assert version is None

    @patch("app.services.updater._check_via_pypi", return_value="2026.9.15")
    @patch("app.services.updater.subprocess.run")
    def test_http_sucesso_nao_chama_pip(self, mock_run, mock_pypi):
        version = check_latest_version()
        assert version == "2026.9.15"
        mock_run.assert_not_called()


class TestPypiHttpCheck:
    """Testes para _check_via_pypi (consulta direta ao PyPI)."""

    @patch("app.services.updater.urllib.request.urlopen")
    def test_http_ok(self, mock_urlopen):
        import io

        mock_urlopen.return_value = io.StringIO('{"info": {"version": "2026.1.1"}}')
        assert _check_via_pypi() == "2026.1.1"

    @patch("app.services.updater.urllib.request.urlopen")
    def test_http_json_invalido_retorna_none(self, mock_urlopen):
        import io

        mock_urlopen.return_value = io.StringIO("não é json")
        assert _check_via_pypi() is None

    @patch("app.services.updater.urllib.request.urlopen")
    def test_http_erro_rede_retorna_none(self, mock_urlopen):
        import urllib.error

        mock_urlopen.side_effect = urllib.error.URLError("offline")
        assert _check_via_pypi() is None


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
