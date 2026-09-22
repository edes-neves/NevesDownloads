"""Testes para o serviço de corte de mídia (app.services.media_editor)."""

import subprocess
import threading
from pathlib import Path

import pytest

from app.services import media_editor
from app.services.media_editor import (
    build_cut_command,
    cut_media,
    format_timestamp,
    get_media_duration,
    make_cut_output,
    parse_duration_from_ffmpeg,
    parse_timestamp,
)
from app.ui.cut_window import _format_duration_label


class TestFormatDurationLabel:
    """Testes do helper de exibição da duração na janela de corte."""

    def test_formata_hh_mm_ss(self):
        assert _format_duration_label(3723.5) == "01:02:03"

    def test_duracao_desconhecida(self):
        assert _format_duration_label(None) == "--"


class TestParseTimestamp:
    def test_horas_minutos_segundos(self):
        assert parse_timestamp("1:02:03") == 3723.0

    def test_minutos_segundos(self):
        assert parse_timestamp("02:03") == 123.0

    def test_segundos_sozinho(self):
        assert parse_timestamp("45") == 45.0

    def test_segundos_com_decimal(self):
        assert parse_timestamp("45.5") == 45.5

    def test_com_espacos(self):
        assert parse_timestamp("  0:00:30  ") == 30.0

    @pytest.mark.parametrize("texto", ["", "abc", "1:2:3:4", "aa:bb", "1:a5"])
    def test_invalidos_lancam_valor_erro(self, texto):
        with pytest.raises(ValueError):
            parse_timestamp(texto)


class TestFormatTimestamp:
    def test_completo(self):
        assert format_timestamp(3723) == "01:02:03.000"

    def test_fracoes(self):
        assert format_timestamp(123.5) == "00:02:03.500"

    def test_zero(self):
        assert format_timestamp(0) == "00:00:00.000"

    def test_negativo_vira_zero(self):
        assert format_timestamp(-5) == "00:00:00.000"


class TestParseDurationFromFfmpeg:
    def test_extrai_duracao(self):
        saida = "  Duration: 00:01:02.50, start: 0.000000, bitrate: 1234 kb/s"
        assert parse_duration_from_ffmpeg(saida) == 62.5

    def test_sem_duracao(self):
        assert parse_duration_from_ffmpeg("sem informacao de duracao") is None

    def test_none(self):
        assert parse_duration_from_ffmpeg(None) is None


class TestGetMediaDuration:
    def test_usa_subprocess_e_parseia(self, tmp_path, monkeypatch):
        arquivo = tmp_path / "v.mp4"
        arquivo.write_bytes(b"x")

        def fake_run(cmd, **kwargs):
            assert cmd[0] == "/usr/bin/ffmpeg"
            assert "-i" in cmd

            class R:
                stderr = "  Duration: 00:03:00.00, start: 0"

            return R()

        monkeypatch.setattr(media_editor.subprocess, "run", fake_run)
        assert get_media_duration(arquivo, ffmpeg_location="/usr/bin/ffmpeg") == 180.0

    def test_erro_subprocess_retorna_none(self, tmp_path, monkeypatch):
        def fake_run(cmd, **kwargs):
            raise OSError("falhou")

        monkeypatch.setattr(media_editor.subprocess, "run", fake_run)
        assert get_media_duration(tmp_path / "x.mp4", ffmpeg_location="/usr/bin/ffmpeg") is None

    def test_sem_ffmpeg_retorna_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(media_editor, "_locate_ffmpeg", lambda: None)
        assert get_media_duration(tmp_path / "x.mp4") is None


class TestMakeCutOutput:
    def test_nome_com_sufixo(self, tmp_path):
        origem = tmp_path / "video.mp4"
        assert make_cut_output(origem) == tmp_path / "video_cortado.mp4"

    def test_preserva_extensao(self, tmp_path):
        origem = tmp_path / "musica.mp3"
        assert make_cut_output(origem) == tmp_path / "musica_cortado.mp3"

    def test_evita_sobrescrever(self, tmp_path):
        origem = tmp_path / "video.mp4"
        (tmp_path / "video_cortado.mp4").write_bytes(b"a")
        assert make_cut_output(origem) == tmp_path / "video_cortado(2).mp4"


class TestBuildCutCommand:
    def _cmd(self, strategy="copy", end=None, nome="video.mp4"):
        return build_cut_command("ffmpeg", Path(nome), Path("out.mp4"), 30.0, end, strategy)

    def test_copia_inclui_ss_to_e_c_copy(self):
        cmd = self._cmd(end=60.0)
        assert cmd[0] == "ffmpeg"
        assert "-ss" in cmd and "00:00:30.000" in cmd
        assert "-to" in cmd and "00:01:00.000" in cmd
        assert "-c" in cmd and "copy" in cmd
        assert cmd[-1] == "out.mp4"

    def test_sem_fim_nao_informa_to(self):
        cmd = self._cmd(end=None)
        assert "-to" not in cmd

    def test_reencode_video(self):
        cmd = self._cmd(strategy="reencode", end=10.0)
        assert "libx264" in cmd and "-c:a" in cmd and "aac" in cmd

    def test_reencode_audio(self):
        cmd = build_cut_command("ffmpeg", Path("musica.mp3"), Path("out.mp3"), 1.0, 5.0, "reencode")
        assert "libx264" not in cmd
        assert "-c:a" in cmd and "aac" in cmd


class FakeProc:
    """Processo FFmpeg fake para _run_ffmpeg."""

    def __init__(self, returncode=0, stderr="", timeout_then_success=False):
        self.returncode = returncode
        self._stderr = stderr
        self.terminated = False
        self.killed = False
        self._wait_calls = 0
        self._timeout_then_success = timeout_then_success

    def wait(self, timeout=None):
        self._wait_calls += 1
        if self._timeout_then_success and self._wait_calls == 1:
            raise subprocess.TimeoutExpired(cmd="ffmpeg", timeout=timeout)
        return self.returncode

    def communicate(self):
        return ("", self._stderr)

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.killed = True


class TestRunFfmpeg:
    def test_sucesso(self, monkeypatch):
        monkeypatch.setattr(media_editor.subprocess, "Popen", lambda *a, **k: FakeProc(0, ""))
        codigo, _ = media_editor._run_ffmpeg(["ffmpeg", "-i", "x"], None)
        assert codigo == 0

    def test_falha_retorna_stderr(self, monkeypatch):
        proc = FakeProc(1, "estouro da pilha do codec")
        monkeypatch.setattr(media_editor.subprocess, "Popen", lambda *a, **k: proc)
        codigo, saida = media_editor._run_ffmpeg(["ffmpeg", "-i", "x"], None)
        assert codigo == 1
        assert "codec" in saida

    def test_cancelamento_termina_processo(self, monkeypatch):
        proc = FakeProc(0, "", timeout_then_success=True)
        monkeypatch.setattr(media_editor.subprocess, "Popen", lambda *a, **k: proc)
        cancel = threading.Event()
        cancel.set()
        codigo, saida = media_editor._run_ffmpeg(["ffmpeg", "-i", "x"], cancel)
        assert codigo == -1
        assert proc.terminated
        assert saida == "cancelled"

    def test_popen_falha(self, monkeypatch):
        monkeypatch.setattr(
            media_editor.subprocess, "Popen", lambda *a, **k: (_ for _ in ()).throw(OSError("sem ffmpeg"))
        )
        codigo, saida = media_editor._run_ffmpeg(["ffmpeg"], None)
        assert codigo == -1
        assert "sem ffmpeg" in saida


class TestCutMedia:
    def _setup(self, tmp_path, monkeypatch, run_results=(0,), duration=100.0):
        entrada = tmp_path / "video.mp4"
        entrada.write_bytes(b"conteudo")
        saida = tmp_path / "video_cortado.mp4"
        chamadas = []

        monkeypatch.setattr(media_editor, "_locate_ffmpeg", lambda: "/usr/bin/ffmpeg")
        monkeypatch.setattr(media_editor, "get_media_duration", lambda p, ffmpeg_location=None: duration)
        if run_results is not None:

            def fake_run(cmd, cancel_event=None):
                chamadas.append(cmd)
                return run_results[min(len(chamadas) - 1, len(run_results) - 1)], ""

            monkeypatch.setattr(media_editor, "_run_ffmpeg", fake_run)
        return entrada, saida, chamadas

    def test_ffmpeg_faltando(self, tmp_path, monkeypatch):
        monkeypatch.setattr(media_editor, "_locate_ffmpeg", lambda: None)
        resultado = cut_media(tmp_path / "v.mp4", tmp_path / "out.mp4", 0.0)
        assert resultado["status"] == "error"
        assert "ffmpeg" in resultado["error"]

    def test_entrada_inexistente(self, tmp_path, monkeypatch):
        monkeypatch.setattr(media_editor, "_locate_ffmpeg", lambda: "/usr/bin/ffmpeg")
        resultado = cut_media(tmp_path / "nao.mp4", tmp_path / "out.mp4", 0.0)
        assert resultado["status"] == "error"
        assert "entrada" in resultado["error"]

    def test_inicio_negativo(self, tmp_path, monkeypatch):
        entrada, saida, _ = self._setup(tmp_path, monkeypatch)
        assert cut_media(entrada, saida, -1.0)["status"] == "error"

    def test_fim_nao_maior_que_inicio(self, tmp_path, monkeypatch):
        entrada, saida, _ = self._setup(tmp_path, monkeypatch)
        assert cut_media(entrada, saida, 30.0, end=30.0)["status"] == "error"

    def test_inicio_alem_da_duracao(self, tmp_path, monkeypatch):
        entrada, saida, _ = self._setup(tmp_path, monkeypatch, duration=50.0)
        assert cut_media(entrada, saida, 60.0)["status"] == "error"

    def test_sucesso_sem_fim_usa_dur_provida(self, tmp_path, monkeypatch):
        entrada, saida, _chamadas = self._setup(tmp_path, monkeypatch, run_results=(0,), duration=100.0)
        saida.write_bytes(b"new")
        resultado = cut_media(entrada, saida, 10.0)
        assert resultado["status"] == "completed"
        assert resultado["output"] == str(saida)
        assert resultado["duration"] == 90.0

    def test_fim_maior_que_duracao_e_ajustado(self, tmp_path, monkeypatch):
        entrada, saida, chamadas = self._setup(tmp_path, monkeypatch, run_results=(0,), duration=50.0)
        saida.write_bytes(b"new")
        resultado = cut_media(entrada, saida, 10.0, end=200.0)
        assert resultado["status"] == "completed"
        assert "00:00:50.000" in " ".join(chamadas[0])

    def test_fallback_para_reencode_quando_copia_falha(self, tmp_path, monkeypatch):
        entrada, saida, chamadas = self._setup(tmp_path, monkeypatch, run_results=(1, 0), duration=100.0)
        saida.write_bytes(b"new")
        resultado = cut_media(entrada, saida, 10.0, end=None)
        assert resultado["status"] == "completed"
        assert len(chamadas) == 2
        assert "-c" in chamadas[0] and "copy" in chamadas[0]
        assert "libx264" in chamadas[1]

    def test_cancelamento(self, tmp_path, monkeypatch):
        entrada, saida, _ = self._setup(tmp_path, monkeypatch, run_results=None)
        monkeypatch.setattr(
            media_editor,
            "_run_ffmpeg",
            lambda cmd, cancel_event=None: (-1, "cancelled"),
        )
        assert cut_media(entrada, saida, 10.0)["status"] == "cancelled"

    def test_falha_em_ambas_estrategias(self, tmp_path, monkeypatch):
        entrada, saida, chamadas = self._setup(tmp_path, monkeypatch, run_results=(1, 1))
        resultado = cut_media(entrada, saida, 10.0)
        assert resultado["status"] == "error"
        assert len(chamadas) == 2
        assert not saida.exists()
