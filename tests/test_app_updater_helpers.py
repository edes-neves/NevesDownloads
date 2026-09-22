"""Testes dos helpers de validação/instalação do auto-update (app_updater)."""

from pathlib import Path
from unittest.mock import patch

from app.services import app_updater
from app.services.app_updater import _is_valid_elf, _is_valid_pe, install_update


class TestValidadores:
    """Testes para _is_valid_elf e _is_valid_pe."""

    def test_elf_valido(self, tmp_path):
        f = tmp_path / "a.AppImage"
        f.write_bytes(b"\x7fELF" + b"\x00" * 16)
        assert _is_valid_elf(f) is True

    def test_elf_invalido(self, tmp_path):
        f = tmp_path / "a.AppImage"
        f.write_bytes(b"texto qualquer")
        assert _is_valid_elf(f) is False

    def test_pe_valido(self, tmp_path):
        f = tmp_path / "a.exe"
        f.write_bytes(b"MZ" + b"\x00" * 16)
        assert _is_valid_pe(f) is True

    def test_pe_invalido(self, tmp_path):
        f = tmp_path / "a.exe"
        f.write_bytes(b"arquivo errado")
        assert _is_valid_pe(f) is False


class TestInstallUpdate:
    """Testes do fluxo de instalação por plataforma."""

    def _generic_patch(self, tmp_path, monkeypatch, is_windows):
        exe = tmp_path / ("app.exe" if is_windows else "app.AppImage")
        exe.write_bytes(b"x")
        monkeypatch.setattr(app_updater, "_IS_WINDOWS", is_windows)
        monkeypatch.setattr(
            app_updater,
            "_get_executable_path",
            lambda: exe,
        )
        return exe

    def test_rejeita_formato_invalido(self, tmp_path, monkeypatch):
        self._generic_patch(tmp_path, monkeypatch, is_windows=False)
        asset = tmp_path / "release.txt"
        asset.write_bytes(b"dados")
        result = install_update(asset)
        assert result["success"] is False
        assert "não suportado" in result["message"].lower()

    def test_windows_aceita_exe_e_pending(self, tmp_path, monkeypatch):
        self._generic_patch(tmp_path, monkeypatch, is_windows=True)
        asset = tmp_path / "release.exe"
        asset.write_bytes(b"MZ" + b"\x00" * 8)

        with patch.object(app_updater.subprocess, "Popen", return_value=None) as mock_popen:
            result = install_update(asset)

        assert result["success"] is True
        assert result["requires_restart"] is True
        assert (tmp_path / "app.exe.pending").exists()
        assert mock_popen.call_count == 1
        args, _kwargs = mock_popen.call_args
        popen = args[0]
        assert popen[0] == "cmd"
        assert Path(popen[2]).name == ".update_helper.bat"
        helper = tmp_path / ".update_helper.bat"
        assert helper.exists()
        assert "move" in helper.read_text(encoding="ascii").lower()

    def test_linux_aceita_appimage(self, tmp_path, monkeypatch):
        self._generic_patch(tmp_path, monkeypatch, is_windows=False)
        asset = tmp_path / "release.AppImage"
        asset.write_bytes(b"\x7fELF" + b"\x00" * 16)

        with patch.object(app_updater.subprocess, "Popen", return_value=None):
            result = install_update(asset)

        assert result["success"] is True
        assert result["requires_restart"] is True
        assert (tmp_path / "app.AppImage.pending").exists()
        helper = tmp_path / ".update_helper.sh"
        assert helper.exists()

    def test_windows_rejeita_nao_exe(self, tmp_path, monkeypatch):
        self._generic_patch(tmp_path, monkeypatch, is_windows=True)
        asset = tmp_path / "release.AppImage"
        asset.write_bytes(b"\x7fELF" + b"\x00" * 16)
        result = install_update(asset)
        assert result["success"] is False
