"""Testes unitários para app.services.ytdlp_service (métodos utilitários + novos parâmetros)."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.services.ytdlp_service import YtDlpService


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
