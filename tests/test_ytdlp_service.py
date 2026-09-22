"""Testes unitários para app.services.ytdlp_service (métodos utilitários + novos parâmetros)."""

import sys
import tempfile
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

from yt_dlp.utils import DownloadError

from app.core.exceptions import DownloadCancelledError
from app.services.ytdlp_service import YtDlpService, _is_transient_error, _locate_ffmpeg


class TestLocateFfmpeg:
    """Testes para a localização do FFmpeg (bundled ou PATH)."""

    def test_prefere_bundled_meipass(self, tmp_path, monkeypatch):
        ffmpeg = tmp_path / "ffmpeg.exe"
        ffmpeg.write_bytes(b"falso binario")
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
        monkeypatch.setattr(sys, "platform", "win32", raising=False)
        monkeypatch.setattr("app.services.ytdlp_service.shutil.which", lambda _n, **k: None, raising=False)
        assert _locate_ffmpeg() == str(ffmpeg)

    def test_nao_encontra_sem_bundled(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", False, raising=False)
        monkeypatch.setattr("app.services.ytdlp_service.shutil.which", lambda _n, **k: None, raising=False)
        monkeypatch.setattr(sys, "platform", "linux", raising=False)
        assert _locate_ffmpeg() is None

    def test_nao_busca_se_meipass_nao_e_diretorio(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "inexistente"), raising=False)
        monkeypatch.setattr(sys, "platform", "linux", raising=False)
        monkeypatch.setattr("app.services.ytdlp_service.shutil.which", lambda _n, **k: None, raising=False)
        assert _locate_ffmpeg() is None


class TestYtDlpService:
    """Testes para métodos utilitários do YtDlpService."""

    def setup_method(self):
        self.service = YtDlpService()

    def test_sanitize_filename(self):
        result = YtDlpService._sanitize_filename("Meu Vídeo: Teste <legal>")
        assert "<" not in result
        assert ">" not in result
        assert ":" not in result

    def test_sanitize_filename_limpo(self):
        result = YtDlpService._sanitize_filename("video normal")
        assert result == "video normal"

    def test_sanitize_filename_pontos_excesso(self):
        result = YtDlpService._sanitize_filename("...video...")
        assert not result.startswith(".")
        assert not result.endswith(".")

    def test_is_ffmpeg_available_retorna_bool(self):
        result = self.service.is_ffmpeg_available()
        assert isinstance(result, bool)

    def test_is_ffmpeg_cache(self):
        """Segunda chamada deve usar cache."""
        first = self.service.is_ffmpeg_available()
        second = self.service.is_ffmpeg_available()
        assert first == second

    def test_build_base_opts(self):
        opts = self.service._build_base_opts()
        assert "quiet" in opts
        assert "no_warnings" in opts
        assert "socket_timeout" in opts
        assert "retries" in opts

    def test_build_base_opts_com_proxy(self):
        opts = self.service._build_base_opts(proxy="socks5://127.0.0.1:1080")
        assert opts["proxy"] == "socks5://127.0.0.1:1080"

    def test_build_base_opts_com_cookies(self):
        opts = self.service._build_base_opts(cookies_browser="firefox")
        assert opts["cookiesfrombrowser"] == ("firefox",)

    def test_build_base_opts_custom_retries(self):
        opts = self.service._build_base_opts(retries=5, socket_timeout=60)
        assert opts["retries"] == 5
        assert opts["fragment_retries"] == 5
        assert opts["socket_timeout"] == 60


class TestConcurrentFragments:
    """Testes para o parâmetro concurrent_fragments (multi-threading)."""

    def setup_method(self):
        self.service = YtDlpService()

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_concurrent_fragments_4(self, mock_ydl_cls):
        """concurrent_fragments=4 deve setar concurrent_fragment_downloads=4."""
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "Teste",
            "uploader": "Autor",
        }
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)

        with tempfile.TemporaryDirectory() as tmp:
            self.service.download_video(
                url="https://www.youtube.com/watch?v=abc123",
                output_path=Path(tmp),
                concurrent_fragments=4,
            )
            ydl_opts_used = mock_ydl_cls.call_args[0][0]
            assert ydl_opts_used.get("concurrent_fragment_downloads") == 4

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_concurrent_fragments_1_nao_configura(self, mock_ydl_cls):
        """concurrent_fragments=1 (default) não deve setar a opção."""
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "Teste",
            "uploader": "Autor",
        }
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)

        with tempfile.TemporaryDirectory() as tmp:
            self.service.download_video(
                url="https://www.youtube.com/watch?v=abc123",
                output_path=Path(tmp),
            )
            ydl_opts_used = mock_ydl_cls.call_args[0][0]
            assert "concurrent_fragment_downloads" not in ydl_opts_used

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_concurrent_fragments_16(self, mock_ydl_cls):
        """concurrent_fragments=16 deve setar corretamente."""
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "Teste",
            "uploader": "Autor",
        }
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)

        with tempfile.TemporaryDirectory() as tmp:
            self.service.download_video(
                url="https://www.youtube.com/watch?v=abc123",
                output_path=Path(tmp),
                concurrent_fragments=16,
            )
            ydl_opts_used = mock_ydl_cls.call_args[0][0]
            assert ydl_opts_used["concurrent_fragment_downloads"] == 16


class TestSponsorBlockIntegration:
    """Testes para integração do SponsorBlock no download."""

    def setup_method(self):
        self.service = YtDlpService()

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_sponsorblock_ativado(self, mock_ydl_cls):
        """sponsorblock_enabled=True deve setar sponsorblock_remove."""
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "Teste",
            "uploader": "Autor",
        }
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)

        with tempfile.TemporaryDirectory() as tmp:
            self.service.download_video(
                url="https://www.youtube.com/watch?v=abc123",
                output_path=Path(tmp),
                sponsorblock_enabled=True,
            )
            ydl_opts_used = mock_ydl_cls.call_args[0][0]
            assert "sponsorblock_remove" in ydl_opts_used
            cats = ydl_opts_used["sponsorblock_remove"]
            assert "sponsor" in cats
            assert "selfpromo" in cats

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_sponsorblock_categorias_custom(self, mock_ydl_cls):
        """Categorias customizadas devem ser parseadas corretamente."""
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "Teste",
            "uploader": "Autor",
        }
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)

        with tempfile.TemporaryDirectory() as tmp:
            self.service.download_video(
                url="https://www.youtube.com/watch?v=abc123",
                output_path=Path(tmp),
                sponsorblock_enabled=True,
                sponsorblock_categories="sponsor,intro,outro",
            )
            ydl_opts_used = mock_ydl_cls.call_args[0][0]
            cats = ydl_opts_used["sponsorblock_remove"]
            assert cats == ["sponsor", "intro", "outro"]

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_sponsorblock_desativado(self, mock_ydl_cls):
        """sponsorblock_enabled=False não deve setar sponsorblock_remove."""
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "Teste",
            "uploader": "Autor",
        }
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)

        with tempfile.TemporaryDirectory() as tmp:
            self.service.download_video(
                url="https://www.youtube.com/watch?v=abc123",
                output_path=Path(tmp),
                sponsorblock_enabled=False,
            )
            ydl_opts_used = mock_ydl_cls.call_args[0][0]
            assert "sponsorblock_remove" not in ydl_opts_used


class TestTikTokIntegration:
    """Testes para otimizações TikTok no download."""

    def setup_method(self):
        self.service = YtDlpService()

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_tiktok_qualidade_4k_limitada_1080p(self, mock_ydl_cls):
        """URL TikTok com qualidade 4K deve ser limitada a 1080p."""
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "Teste",
            "uploader": "Autor",
        }
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)

        with tempfile.TemporaryDirectory() as tmp:
            self.service.download_video(
                url="https://www.tiktok.com/@user/video/123456",
                output_path=Path(tmp),
                quality="4K / 2160p",
            )
            ydl_opts_used = mock_ydl_cls.call_args[0][0]
            assert ydl_opts_used["format"] == "bestvideo*[height<=1080]+bestaudio/best[height<=1080]/best"

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_tiktok_watermark_removal_headers(self, mock_ydl_cls):
        """tiktok_watermark_removal=True deve setar http_headers com User-Agent."""
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "Teste",
            "uploader": "Autor",
        }
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)

        with tempfile.TemporaryDirectory() as tmp:
            self.service.download_video(
                url="https://www.tiktok.com/@user/video/123456",
                output_path=Path(tmp),
                tiktok_watermark_removal=True,
            )
            ydl_opts_used = mock_ydl_cls.call_args[0][0]
            assert "http_headers" in ydl_opts_used
            assert "Chrome" in ydl_opts_used["http_headers"]["User-Agent"]

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_tiktok_qualidade_normal(self, mock_ydl_cls):
        """URL TikTok com qualidade HD deve manter 720p (abaixo do limite)."""
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "Teste",
            "uploader": "Autor",
        }
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)

        with tempfile.TemporaryDirectory() as tmp:
            self.service.download_video(
                url="https://www.tiktok.com/@user/video/123456",
                output_path=Path(tmp),
                quality="HD / 720p",
            )
            ydl_opts_used = mock_ydl_cls.call_args[0][0]
            # 720p < 1080p, TikTok não altera; formato não é "Melhor", usa quality_map
            assert "height<=720" in ydl_opts_used["format"]

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_nao_tiktok_nao_modifica(self, mock_ydl_cls):
        """URL YouTube normal não deve sofrer alterações TikTok."""
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "Teste",
            "uploader": "Autor",
        }
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)

        with tempfile.TemporaryDirectory() as tmp:
            self.service.download_video(
                url="https://www.youtube.com/watch?v=abc123",
                output_path=Path(tmp),
                quality="4K / 2160p",
                tiktok_watermark_removal=True,
            )
            ydl_opts_used = mock_ydl_cls.call_args[0][0]
            # YouTube 4K com qualidade explícita, usa quality_map
            assert "height<=2160" in ydl_opts_used["format"]
            # Não deve ter http_headers de TikTok
            assert "http_headers" not in ydl_opts_used


class TestDownloadPlaylistParams:
    """Testes para passagem de parâmetros novos em download_playlist."""

    def setup_method(self):
        self.service = YtDlpService()

    @patch.object(YtDlpService, "download_video")
    def test_playlist_passa_sponsorblock(self, mock_dl):
        """download_playlist deve passar sponsorblock para cada download_video."""
        mock_dl.return_value = {"status": "completed", "title": "Vid"}
        with tempfile.TemporaryDirectory() as tmp:
            self.service.download_playlist(
                urls=["https://youtube.com/watch?v=1"],
                output_path=Path(tmp),
                sponsorblock_enabled=True,
                sponsorblock_categories="sponsor,intro",
            )
            mock_dl.assert_called_once()
            kwargs = mock_dl.call_args[1]
            assert kwargs["sponsorblock_enabled"] is True
            assert kwargs["sponsorblock_categories"] == "sponsor,intro"

    @patch.object(YtDlpService, "download_video")
    def test_playlist_passa_concurrent_fragments(self, mock_dl):
        """download_playlist deve passar concurrent_fragments."""
        mock_dl.return_value = {"status": "completed", "title": "Vid"}
        with tempfile.TemporaryDirectory() as tmp:
            self.service.download_playlist(
                urls=["https://youtube.com/watch?v=1"],
                output_path=Path(tmp),
                concurrent_fragments=8,
            )
            kwargs = mock_dl.call_args[1]
            assert kwargs["concurrent_fragments"] == 8

    @patch.object(YtDlpService, "download_video")
    def test_playlist_passa_tiktok_watermark(self, mock_dl):
        """download_playlist deve passar tiktok_watermark_removal."""
        mock_dl.return_value = {"status": "completed", "title": "Vid"}
        with tempfile.TemporaryDirectory() as tmp:
            self.service.download_playlist(
                urls=["https://tiktok.com/@u/video/123"],
                output_path=Path(tmp),
                tiktok_watermark_removal=True,
            )
            kwargs = mock_dl.call_args[1]
            assert kwargs["tiktok_watermark_removal"] is True

    @patch.object(YtDlpService, "download_video")
    def test_playlist_varios_videos(self, mock_dl):
        """download_playlist com 3 URLs deve chamar download_video 3 vezes."""
        mock_dl.return_value = {"status": "completed", "title": "Vid"}
        with tempfile.TemporaryDirectory() as tmp:
            results = self.service.download_playlist(
                urls=[
                    "https://youtube.com/watch?v=1",
                    "https://youtube.com/watch?v=2",
                    "https://youtube.com/watch?v=3",
                ],
                output_path=Path(tmp),
                concurrent_fragments=4,
                sponsorblock_enabled=True,
            )
            assert mock_dl.call_count == 3
            assert len(results) == 3


class TestCookiesFile:
    """Testes para o suporte a arquivo de cookies (cookies.txt)."""

    def setup_method(self):
        self.service = YtDlpService()

    def test_cookies_file_usado_se_existir(self, tmp_path):
        cookies = tmp_path / "cookies.txt"
        cookies.write_text("# Netscape HTTP Cookie File\n")
        opts = self.service._build_base_opts(cookies_browser="firefox", cookies_file=str(cookies))
        assert opts["cookiefile"] == str(cookies)
        # cookiefile tem prioridade: cookies de navegador são descartados
        assert "cookiesfrombrowser" not in opts

    def test_cookies_file_inexistente_ignorado(self):
        opts = self.service._build_base_opts(cookies_file="/nao/existe/cookies.txt")
        assert "cookiefile" not in opts

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_extract_info_passa_cookies_file(self, mock_ydl_cls, tmp_path):
        cookies = tmp_path / "cookies.txt"
        cookies.write_text("# Netscape HTTP Cookie File\n")
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {"title": "T"}
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)

        self.service.extract_info("https://youtube.com/watch?v=abc", cookies_file=str(cookies))
        ydl_opts_used = mock_ydl_cls.call_args[0][0]
        assert ydl_opts_used["cookiefile"] == str(cookies)


class TestDownloadPlaylistCompact:
    """Testes para download_playlist_compact (playlist de áudio em arquivo único)."""

    def setup_method(self):
        self.service = YtDlpService()

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_compact_configura_concat_e_audio(self, mock_ydl_cls, tmp_path):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "Minha Playlist",
            "uploader": "Artista",
            "entries": [{"id": "1"}, {"id": "2"}],
        }
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = self.service.download_playlist_compact(
            url="https://youtube.com/playlist?list=PLx",
            output_path=Path(tmp_path),
            audio_fmt="MP3",
        )
        ydl_opts_used = mock_ydl_cls.call_args[0][0]
        assert ydl_opts_used["concat_playlist"] == "always"
        assert ydl_opts_used["noplaylist"] is False
        assert ydl_opts_used["format"] == "bestaudio/best"
        pps = ydl_opts_used["postprocessors"]
        assert any(pp["key"] == "FFmpegExtractAudio" and pp["preferredcodec"] == "mp3" for pp in pps)
        assert result["status"] == "completed"
        assert str(result["filename"]).endswith("Minha Playlist.mp3")

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_compact_outro_formato_audio(self, mock_ydl_cls, tmp_path):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {
            "title": "Mix FLAC",
            "entries": [{"id": "1"}],
        }
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = self.service.download_playlist_compact(
            url="https://youtube.com/playlist?list=PLx",
            output_path=Path(tmp_path),
            audio_fmt="FLAC",
        )
        assert result["status"] == "completed"
        assert str(result["filename"]).endswith("Mix FLAC.flac")

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_compact_sem_entries_erro(self, mock_ydl_cls, tmp_path):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {"title": "Sem itens"}
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = self.service.download_playlist_compact(
            url="https://youtube.com/playlist?list=PLx",
            output_path=Path(tmp_path),
        )
        assert result["status"] == "error"

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_compact_cancelado(self, mock_ydl_cls, tmp_path):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.side_effect = DownloadCancelledError("cancelado")
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)

        cancel = __import__("threading").Event()
        cancel.set()
        result = self.service.download_playlist_compact(
            url="https://youtube.com/playlist?list=PLx",
            output_path=Path(tmp_path),
            cancel_event=cancel,
        )
        assert result["status"] == "cancelled"


class TestIsTransientError:
    """Testes para a detecção de erros transitórios."""

    def test_http_5xx(self):
        assert _is_transient_error(DownloadError("HTTP Error 503: Service Unavailable")) is True

    def test_http_429(self):
        assert _is_transient_error(DownloadError("HTTP Error 429: Too Many Requests")) is True

    def test_timeout(self):
        assert _is_transient_error(DownloadError("Connection timed out")) is True

    def test_erro_permanente(self):
        assert _is_transient_error(DownloadError("Unsupported URL")) is False

    def test_video_privado(self):
        assert _is_transient_error(DownloadError("Video unavailable")) is False


class TestTransientRetry:
    """Testes para o retry automático com backoff em erros transitórios."""

    def setup_method(self):
        self.service = YtDlpService()

    def _mock_ydl(self, mock_ydl_cls, results):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.side_effect = results
        mock_ydl_cls.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_cls.return_value.__exit__ = MagicMock(return_value=False)
        return mock_ydl

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    @patch("time.sleep", return_value=None)
    def test_transient_error_retries_then_succeeds(self, mock_sleep, mock_ydl_cls, tmp_path):
        """503 na 1ª tentativa deve ser seguido de uma 2ª bem-sucedida."""
        self._mock_ydl(
            mock_ydl_cls,
            [DownloadError("HTTP Error 503: Service Unavailable"), {"title": "Vid", "uploader": "Autor"}],
        )
        result = self.service.download_video(
            url="https://youtube.com/watch?v=abc",
            output_path=Path(tmp_path),
            transient_retries=2,
        )
        assert result["status"] == "completed"
        assert mock_ydl_cls.call_count == 2
        assert mock_sleep.called

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    @patch("time.sleep", return_value=None)
    def test_transient_error_exhausts_retries(self, mock_sleep, mock_ydl_cls, tmp_path):
        """Transient sempre falhando deve esgotar as tentativas e retornar erro."""
        self._mock_ydl(
            mock_ydl_cls,
            [DownloadError("HTTP Error 503: Service Unavailable")] * 3,
        )
        result = self.service.download_video(
            url="https://youtube.com/watch?v=abc",
            output_path=Path(tmp_path),
            transient_retries=2,
        )
        assert result["status"] == "error"
        assert mock_ydl_cls.call_count == 3

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    @patch("time.sleep", return_value=None)
    def test_non_transient_no_retry(self, mock_sleep, mock_ydl_cls, tmp_path):
        """Erro permanente não deve gerar novas tentativas."""
        self._mock_ydl(mock_ydl_cls, [DownloadError("Unsupported URL")])
        result = self.service.download_video(
            url="https://youtube.com/watch?v=abc",
            output_path=Path(tmp_path),
            transient_retries=2,
        )
        assert result["status"] == "error"
        assert mock_ydl_cls.call_count == 1

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_cancel_during_backoff_returns_cancelled(self, mock_ydl_cls, tmp_path):
        """Cancelar durante o backoff deve retornar status cancelled."""
        self._mock_ydl(mock_ydl_cls, [DownloadError("HTTP Error 503: Service Unavailable")])
        with patch.object(self.service, "_wait_interruptible", return_value=True):
            result = self.service.download_video(
                url="https://youtube.com/watch?v=abc",
                output_path=Path(tmp_path),
                cancel_event=threading.Event(),
                transient_retries=2,
            )
        assert result["status"] == "cancelled"

    @patch.object(YtDlpService, "download_video")
    def test_playlist_passa_transient_retries(self, mock_dl):
        """download_playlist deve propagar transient_retries para download_video."""
        mock_dl.return_value = {"status": "completed", "title": "Vid"}
        with tempfile.TemporaryDirectory() as tmp:
            self.service.download_playlist(
                urls=["https://youtube.com/watch?v=1"],
                output_path=Path(tmp),
                transient_retries=4,
            )
            kwargs = mock_dl.call_args[1]
            assert kwargs["transient_retries"] == 4
