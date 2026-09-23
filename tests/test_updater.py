"""Testes unitários para app.services.updater."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services import updater
from app.services.updater import (
    _check_via_pypi,
    check_latest_version,
    get_current_version,
    get_user_ytdlp_path,
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


class TestUserYtdlpPath:
    """Caminho do yt-dlp independente do usuário, por plataforma."""

    def test_linux_padrao(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        assert get_user_ytdlp_path() == Path.home() / ".local" / "share" / "NevesDownloads" / "yt-dlp"

    def test_linux_respeita_xdg_data_home(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "platform", "linux")
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
        assert get_user_ytdlp_path() == tmp_path / "data" / "NevesDownloads" / "yt-dlp"

    def test_windows_usa_localappdata(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\Teste\AppData\Local")
        path = get_user_ytdlp_path()
        assert path.name == "yt-dlp.exe"
        assert "NevesDownloads" in path.parts

    def test_macos_usa_application_support(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "darwin")
        expected = Path.home() / "Library" / "Application Support" / "NevesDownloads" / "yt-dlp"
        assert get_user_ytdlp_path() == expected


class TestBinaryVersion:
    """Testes para _binary_version."""

    def test_sucesso(self, monkeypatch):
        proc = MagicMock(returncode=0, stdout="2026.1.1\n", stderr="")
        monkeypatch.setattr(updater.subprocess, "run", lambda *a, **k: proc)
        assert updater._binary_version(Path("/tmp/yt-dlp")) == "2026.1.1"

    def test_returncode_diferente_retorna_none(self, monkeypatch):
        proc = MagicMock(returncode=1, stdout="", stderr="nope")
        monkeypatch.setattr(updater.subprocess, "run", lambda *a, **k: proc)
        assert updater._binary_version(Path("/tmp/yt-dlp")) is None

    def test_oserror_retorna_none(self, monkeypatch):
        def _boom(*a, **k):
            raise OSError("sem execucao")

        monkeypatch.setattr(updater.subprocess, "run", _boom)
        assert updater._binary_version(Path("/tmp/yt-dlp")) is None


class _FakeResp:
    """Resposta HTTP fake (context manager + .read) para _download_standalone."""

    def __init__(self, data: bytes):
        self._data = data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size: int = -1):
        if size is None or size < 0:
            chunk, self._data = self._data, b""
            return chunk
        chunk, self._data = self._data[:size], self._data[size:]
        return chunk


class TestDownloadStandalone:
    """Testes para _download_standalone (download atômico + validação)."""

    def test_download_valido_substitui_target(self, tmp_path, monkeypatch):
        target = tmp_path / "NevesDownloads" / "yt-dlp"
        monkeypatch.setattr(updater.urllib.request, "urlopen", lambda *a, **k: _FakeResp(b"BINARY"))
        monkeypatch.setattr(updater, "_binary_version", lambda p: "2026.1.1")
        updater._download_standalone(target)
        assert target.read_bytes() == b"BINARY"
        assert list(tmp_path.rglob("*.tmp")) == []

    def test_download_invalido_nao_deixa_tmp(self, tmp_path, monkeypatch):
        target = tmp_path / "yt-dlp"
        monkeypatch.setattr(updater.urllib.request, "urlopen", lambda *a, **k: _FakeResp(b"<html>"))
        monkeypatch.setattr(updater, "_binary_version", lambda p: None)
        with pytest.raises(RuntimeError):
            updater._download_standalone(target)
        assert not target.exists()
        assert not (tmp_path / "yt-dlp.tmp").exists()

    def test_download_vazio_levanta(self, tmp_path, monkeypatch):
        target = tmp_path / "yt-dlp"
        monkeypatch.setattr(updater.urllib.request, "urlopen", lambda *a, **k: _FakeResp(b""))
        monkeypatch.setattr(updater, "_binary_version", lambda p: None)
        with pytest.raises(RuntimeError):
            updater._download_standalone(target)


class TestUpdatePackaged:
    """Testes para _update_packaged (yt-dlp independente do usuário)."""

    def test_existente_atualiza_via_minus_U(self, tmp_path, monkeypatch):
        target = tmp_path / "yt-dlp"
        target.write_bytes(b"old")
        versoes = iter(["2025.1.1", "2026.1.1"])
        monkeypatch.setattr(updater, "get_user_ytdlp_path", lambda: target)
        monkeypatch.setattr(updater, "_binary_version", lambda p: next(versoes))
        chamadas = []

        def _fake_run(cmd, *a, **k):
            chamadas.append(cmd)
            return MagicMock(returncode=0, stdout="", stderr="")

        monkeypatch.setattr(updater.subprocess, "run", _fake_run)
        result = updater._update_packaged()
        assert result["success"] is True
        assert chamadas == [[str(target), "-U"]]

    def test_nao_existente_baixa_standalone(self, tmp_path, monkeypatch):
        target = tmp_path / "NevesDownloads" / "yt-dlp"
        monkeypatch.setattr(updater, "get_user_ytdlp_path", lambda: target)
        monkeypatch.setattr(updater, "_binary_version", lambda p: "2026.1.1")
        monkeypatch.setattr(updater, "_download_standalone", lambda p: None)
        result = updater._update_packaged()
        assert result["success"] is True
        assert "2026.1.1" in result["message"]

    def test_falha_retorna_comandos_manuais(self, tmp_path, monkeypatch):
        target = tmp_path / "yt-dlp"
        target.write_bytes(b"old")
        monkeypatch.setattr(updater, "get_user_ytdlp_path", lambda: target)
        monkeypatch.setattr(updater, "_binary_version", lambda p: None)

        def _boom(*a, **k):
            raise RuntimeError("boom")

        monkeypatch.setattr(updater.subprocess, "run", _boom)
        result = updater._update_packaged()
        assert result["success"] is False
        assert "curl" in result["command"]
        assert "boom" in result["message"]

    def test_fallback_download_quando_minus_U_falha(self, tmp_path, monkeypatch):
        target = tmp_path / "yt-dlp"
        target.write_bytes(b"old")
        versoes = iter(["2025.1.1", "2026.1.1"])
        monkeypatch.setattr(updater, "get_user_ytdlp_path", lambda: target)
        monkeypatch.setattr(updater, "_binary_version", lambda p: next(versoes))
        monkeypatch.setattr(updater, "_download_standalone", lambda p: None)
        monkeypatch.setattr(
            updater.subprocess,
            "run",
            lambda *a, **k: MagicMock(returncode=1, stdout="", stderr="deu ruim"),
        )
        result = updater._update_packaged()
        assert result["success"] is True


class TestFrozenMode:
    """Em modo empacotado nunca usamos sys.executable como Python.

    Nunca devemos dispará-lo como se fosse Python — isso abriria outra
    instância da aplicação.
    """

    def test_update_ytdlp_frozen_delega_para_standalone(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        chamadas = []

        def _fake_packaged():
            chamadas.append(True)
            return {"success": True, "old_version": "a", "new_version": "b", "message": "ok"}

        monkeypatch.setattr(updater, "_update_packaged", _fake_packaged)

        def _boom(*args, **kwargs):
            raise AssertionError("update_ytdlp não pode invocar subprocess (sys.executable é o app)")

        monkeypatch.setattr(updater.subprocess, "run", _boom)
        result = update_ytdlp()
        assert result["success"] is True
        assert chamadas == [True]

    def test_update_ytdlp_frozen_falha_inclui_comandos_manuais(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(
            updater,
            "_update_packaged",
            lambda: {
                "success": False,
                "old_version": "2025.1.1",
                "new_version": None,
                "message": "não rolou",
                "command": updater.get_manual_update_commands(),
            },
        )
        result = update_ytdlp()
        assert result["success"] is False
        assert "curl" in result["command"]

    def test_check_via_pip_frozen_ignorado(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(updater, "_check_via_pypi", lambda: None)

        def _boom(*args, **kwargs):
            raise AssertionError("subprocess.run não deveria ser chamado em modo frozen")

        monkeypatch.setattr(updater.subprocess, "run", _boom)
        assert check_latest_version() is None
        assert updater._check_via_pip() is None

    def test_nao_frozen_continua_using_pip(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", False, raising=False)
        result = MagicMock(returncode=0, stdout="yt-dlp (2025.12.23)\n", stderr="")
        monkeypatch.setattr(updater.subprocess, "run", MagicMock(return_value=result))
        assert updater._check_via_pip() == "2025.12.23"
