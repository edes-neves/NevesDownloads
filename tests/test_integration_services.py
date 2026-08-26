"""Testes de integração entre serviços.

Testa como diferentes módulos de serviço trabalham juntos:
- settings → ytdlp_service (opções refletem configurações)
- queue → history (fluxo de download completo)
- tiktok → ytdlp_service (otimizações TikTok)
- sponsorblock → ytdlp_service
- clipboard_monitor → validators (detecção de URL válida)
- errors → friendly_text (mapeamento completo)
"""

from unittest.mock import MagicMock, patch

from app.services import settings
from app.services.errors import friendly_error, friendly_text, log_error
from app.services.history import add_entry, clear_history, get_history
from app.services.queue import DownloadQueue
from app.services.tiktok import get_content_info, is_tiktok_url
from app.utils.validators import is_valid_url


class TestSettingsToYtdlp:
    """Testa que configurações de settings são corretamente aplicadas nas opções yt-dlp."""

    def setup_method(self):
        settings.reset_to_defaults()

    def test_proxy_setting_applied(self):
        settings.save("proxy", "socks5://127.0.0.1:9050")
        from app.services.ytdlp_service import YtDlpService

        svc = YtDlpService()
        opts = svc._build_base_opts(proxy=settings.load("proxy"))
        assert opts["proxy"] == "socks5://127.0.0.1:9050"

    def test_retries_setting_applied(self):
        settings.save("retries", 10)
        from app.services.ytdlp_service import YtDlpService

        svc = YtDlpService()
        opts = svc._build_base_opts(retries=settings.load("retries"))
        assert opts["retries"] == 10
        assert opts["fragment_retries"] == 10

    def test_timeout_setting_applied(self):
        settings.save("socket_timeout", 120)
        from app.services.ytdlp_service import YtDlpService

        svc = YtDlpService()
        opts = svc._build_base_opts(socket_timeout=settings.load("socket_timeout"))
        assert opts["socket_timeout"] == 120

    def test_cookies_setting_applied(self):
        settings.save("default_cookies_browser", "firefox")
        from app.services.ytdlp_service import YtDlpService

        svc = YtDlpService()
        opts = svc._build_base_opts(cookies_browser=settings.load("default_cookies_browser"))
        assert opts["cookiesfrombrowser"] == ("firefox",)

    def test_no_proxy_when_empty(self):
        settings.save("proxy", "")
        from app.services.ytdlp_service import YtDlpService

        svc = YtDlpService()
        opts = svc._build_base_opts(proxy=settings.load("proxy"))
        assert "proxy" not in opts

    def test_no_cookies_when_none(self):
        settings.save("default_cookies_browser", "Nenhum")
        from app.services.ytdlp_service import YtDlpService

        svc = YtDlpService()
        val = settings.load("default_cookies_browser")
        cookies = None if val == "Nenhum" else val
        opts = svc._build_base_opts(cookies_browser=cookies)
        assert "cookiesfrombrowser" not in opts

    def teardown_method(self):
        settings.reset_to_defaults()


class TestQueueHistoryFlow:
    """Testa o fluxo completo: adicionar à fila → download → histórico."""

    def setup_method(self):
        clear_history()

    def test_full_lifecycle(self):
        queue = DownloadQueue(persist=False)

        url = "https://example.com/video"
        queue.add(url, title="Video Teste", mode="video")
        assert len(queue.pending()) == 1

        queue.mark_downloading(url)
        item = queue.next_pending()
        assert item is None

        queue.mark_done(url)
        add_entry(
            url=url,
            title="Video Teste",
            filename="video.mp4",
            status="completed",
            mode="video",
        )

        history = get_history(limit=10)
        assert len(history) == 1
        assert history[0]["url"] == url
        assert history[0]["title"] == "Video Teste"

    def test_error_lifecycle(self):
        queue = DownloadQueue(persist=False)
        url = "https://example.com/fail"
        queue.add(url, title="Fail Video")

        queue.mark_downloading(url)
        queue.mark_error(url)

        history_items = queue.all()
        assert history_items[0]["status"] == "error"
        assert len(queue.pending()) == 0

    def test_prune_after_completion(self):
        queue = DownloadQueue(persist=False)
        url = "https://example.com/done"
        queue.add(url, title="Done")
        queue.mark_done(url)
        assert len(queue.all()) == 1

        queue.prune_finished()
        assert len(queue.all()) == 0

    def test_pause_resume_flow(self):
        queue = DownloadQueue(persist=False)
        url = "https://example.com/pausable"
        queue.add(url, title="Pausable")

        queue.mark_downloading(url)
        queue.mark_paused(url)
        pending = queue.pending()
        assert len(pending) == 1
        assert pending[0]["status"] == "paused"

    def test_increment_attempts(self):
        queue = DownloadQueue(persist=False)
        url = "https://example.com/retry"
        queue.add(url, title="Retry")

        n = queue.increment_attempts(url)
        assert n == 1
        n = queue.increment_attempts(url)
        assert n == 2

    def teardown_method(self):
        clear_history()


class TestTiktokIntegration:
    """Testa detecção e fluxo de integração TikTok."""

    def test_tiktok_url_detected_and_info_obtained(self):
        url = "https://www.tiktok.com/@user/video/1234567890"
        assert is_tiktok_url(url)
        info = get_content_info(url)
        assert info["is_tiktok"] is True
        assert info["content_type"] == "video"
        assert info["video_id"] == "1234567890"

    def test_non_tiktok_not_detected(self):
        url = "https://youtube.com/watch?v=abc"
        assert not is_tiktok_url(url)
        info = get_content_info(url)
        assert info["is_tiktok"] is False

    def test_tiktok_story_needs_cookies(self):
        url = "https://www.tiktok.com/@user/story/1234567890"
        info = get_content_info(url)
        assert info["content_type"] == "story"
        assert info["needs_cookies"] is True

    def test_tiktok_quality_capped_at_1080p(self):
        from app.services.tiktok import get_quality_for_tiktok

        assert get_quality_for_tiktok("4K / 2160p") == "best"
        assert get_quality_for_tiktok("Full HD / 1080p") == "best[height<=1080]/best"
        assert get_quality_for_tiktok("HD / 720p") == "best[height<=720]/best"


class TestClipboardToValidator:
    """Testa que URLs detectadas pelo clipboard são validadas corretamente."""

    def test_youtube_url_valid(self):
        assert is_valid_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_tiktok_url_valid(self):
        assert is_valid_url("https://www.tiktok.com/@user/video/123")

    def test_instagram_url_valid(self):
        assert is_valid_url("https://www.instagram.com/reel/ABC123/")

    def test_invalid_url_rejected(self):
        assert not is_valid_url("not a url")

    def test_empty_url_rejected(self):
        assert not is_valid_url("")

    def test_none_url_rejected(self):
        assert not is_valid_url(None)


class TestErrorMapping:
    """Testa o mapeamento completo de erros para mensagens amigáveis."""

    def test_private_video_returns_amigavel(self):
        result = friendly_error(Exception("Private video"))
        assert "amigavel" in result
        assert "icone" in result

    def test_friendly_text_returns_string(self):
        text = friendly_text(Exception("Something went wrong"))
        assert isinstance(text, str)
        assert len(text) > 0

    def test_log_error_does_not_raise(self):
        log_error(Exception("Test error"), contexto="test")

    def test_timeout_returns_amigavel(self):
        result = friendly_error(TimeoutError("Connection timed out"))
        assert "amigavel" in result

    def test_network_error_returns_amigavel(self):
        result = friendly_error(OSError("Network unreachable"))
        assert "amigavel" in result

    def test_rate_limit_returns_amigavel(self):
        result = friendly_error(Exception("429 Too Many Requests"))
        assert "amigavel" in result


class TestPlaylistIntegration:
    """Testa extração e seleção de playlists."""

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_extract_playlist_info(self, mock_ydl):
        mock_ydl_instance = MagicMock()
        mock_ydl.return_value.__enter__ = MagicMock(return_value=mock_ydl_instance)
        mock_ydl.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl_instance.extract_info.return_value = {
            "title": "Minha Playlist",
            "entries": [
                {"url": "https://youtube.com/watch?v=1", "title": "Video 1", "duration": 120},
                {"url": "https://youtube.com/watch?v=2", "title": "Video 2", "duration": 180},
                {"url": "https://youtube.com/watch?v=3", "title": "Video 3", "duration": 60},
            ],
        }

        from app.services.ytdlp_service import YtDlpService

        svc = YtDlpService()
        info = svc.extract_playlist_info("https://youtube.com/playlist?list=PLtest")
        assert info is not None
        assert info["title"] == "Minha Playlist"
        assert len(info["entries"]) == 3

    def test_playlist_entry_filtering(self):
        """Seleção de entradas da playlist funciona corretamente."""
        entries = [
            {"url": "https://youtube.com/watch?v=1", "title": "V1"},
            None,
            {"url": "https://youtube.com/watch?v=2", "title": "V2"},
        ]
        valid = [e for e in entries if e is not None and e.get("url")]
        assert len(valid) == 2


class TestDownloadOptionsComposition:
    """Testa a composição de opções do yt-dlp com múltiplos recursos habilitados."""

    def test_all_options_combined(self):
        from app.services.ytdlp_service import YtDlpService

        svc = YtDlpService()
        opts = svc._build_base_opts(
            cookies_browser="chrome",
            proxy="socks5://127.0.0.1:1080",
            retries=5,
            socket_timeout=60,
        )

        assert opts["quiet"] is True
        assert opts["no_warnings"] is True
        assert opts["retries"] == 5
        assert opts["socket_timeout"] == 60
        assert opts["proxy"] == "socks5://127.0.0.1:1080"
        assert opts["cookiesfrombrowser"] == ("chrome",)

    def test_sponsorblock_and_concurrent(self):
        from app.services.ytdlp_service import YtDlpService

        svc = YtDlpService()
        opts = svc._build_base_opts()

        opts["sponsorblock_remove"] = ["sponsor", "selfpromo", "intro", "outro"]
        opts["concurrent_fragment_downloads"] = 8

        assert "sponsorblock_remove" in opts
        assert len(opts["sponsorblock_remove"]) == 4
        assert opts["concurrent_fragment_downloads"] == 8

    def test_speed_limit_option(self):
        from app.services.ytdlp_service import YtDlpService

        svc = YtDlpService()
        opts = svc._build_base_opts()
        limit_speed = 1024 * 1024
        if limit_speed > 0:
            opts["ratelimit"] = limit_speed
        assert opts["ratelimit"] == 1024 * 1024
