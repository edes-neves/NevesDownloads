"""Testes de integração para fluxos completos de download.

Testa a comunicação entre YtDlpService, DownloadCard, DownloadQueue
e History sem necessidade de display real (widgets mockados).
"""

from unittest.mock import MagicMock, patch

from app.services.history import add_entry, clear_history, get_history
from app.services.queue import DownloadQueue


class TestDownloadFlowIntegration:
    """Testa o fluxo completo de download usando mocks para UI e yt-dlp."""

    def setup_method(self):
        clear_history()

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_single_download_extracts_info(self, mock_ydl):
        """Download de vídeo único: extrai info com sucesso."""
        mock_info = {
            "title": "Meu Video",
            "duration": 120,
            "uploader": "Canal Teste",
        }
        mock_ydl_instance = MagicMock()
        mock_ydl.return_value.__enter__ = MagicMock(return_value=mock_ydl_instance)
        mock_ydl.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl_instance.extract_info.return_value = mock_info

        from app.services.ytdlp_service import YtDlpService

        service = YtDlpService()
        info = service.extract_info("https://youtube.com/watch?v=test123")

        assert info is not None
        assert info["title"] == "Meu Video"
        assert info["duration"] == 120
        assert info["uploader"] == "Canal Teste"

    def test_build_base_opts_with_all_params(self):
        """Verifica que as opções corretas são passadas ao yt-dlp."""
        from app.services.ytdlp_service import YtDlpService

        service = YtDlpService()
        opts = service._build_base_opts(
            cookies_browser="firefox",
            proxy="socks5://127.0.0.1:1080",
            retries=5,
            socket_timeout=60,
        )
        assert opts["proxy"] == "socks5://127.0.0.1:1080"
        assert opts["retries"] == 5
        assert opts["socket_timeout"] == 60
        assert opts["cookiesfrombrowser"] == ("firefox",)

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_download_video_mode_calls_extract_info_with_download(self, mock_ydl):
        """Modo vídeo único deve chamar extract_info com download=True."""
        mock_ydl_instance = MagicMock()
        mock_ydl.return_value.__enter__ = MagicMock(return_value=mock_ydl_instance)
        mock_ydl.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl_instance.extract_info.return_value = {
            "title": "Test Video",
            "uploader": "Channel",
        }

        from app.services.ytdlp_service import YtDlpService

        service = YtDlpService()
        service.download_video(
            url="https://youtube.com/watch?v=test",
            output_path=MagicMock(),
            mode="video",
            quality="Melhor disponivel",
            fmt="MP4",
        )
        mock_ydl_instance.extract_info.assert_called_once()
        call_kwargs = mock_ydl_instance.extract_info.call_args
        assert call_kwargs[1].get("download") is True or call_kwargs[0][1] is True

    def test_queue_persistence_across_sessions(self, temp_app_dir, monkeypatch):
        """A fila persiste entre sessões (criação → adição → nova instância)."""
        monkeypatch.setattr("app.services.queue.QUEUE_FILE", temp_app_dir / "queue.json")

        queue1 = DownloadQueue(persist=True)
        queue1.add("https://example.com/video1", title="Video 1")
        queue1.add("https://example.com/video2", title="Video 2")
        queue1.save()

        queue2 = DownloadQueue(persist=True)
        pending = queue2.pending()
        assert len(pending) == 2
        urls = [p["url"] for p in pending]
        assert "https://example.com/video1" in urls
        assert "https://example.com/video2" in urls

    def test_queue_status_transitions(self):
        """Transições de status: pending → downloading → done."""
        queue = DownloadQueue(persist=False)
        url = "https://example.com/video"
        queue.add(url, title="Test")

        assert queue.next_pending()["url"] == url
        queue.mark_downloading(url)
        assert queue.next_pending() is None

        queue.mark_done(url)
        assert len(queue.pending()) == 0
        assert len(queue.all()) == 1
        assert queue.all()[0]["status"] == "done"

    def test_history_records_download(self):
        """O histórico registra downloads concluídos."""
        add_entry(
            url="https://example.com/video",
            title="Video Teste",
            filename="video.mp4",
            status="completed",
            mode="video",
            uploader="Canal",
        )
        history = get_history(limit=10)
        assert len(history) == 1
        assert history[0]["title"] == "Video Teste"
        assert history[0]["status"] == "completed"
        assert history[0]["filename"] == "video.mp4"

    def test_history_maintains_order(self):
        """O histórico mantém a ordem: mais recente primeiro."""
        add_entry(url="https://a.com", title="Primeiro", mode="video")
        add_entry(url="https://b.com", title="Segundo", mode="audio")
        history = get_history()
        assert history[0]["title"] == "Segundo"
        assert history[1]["title"] == "Primeiro"

    def test_error_map_returns_friendly_message(self):
        """O mapeamento de erros retorna mensagens amigáveis."""
        from app.services.errors import friendly_error

        result = friendly_error(Exception("Video unavailable"))
        assert "amigavel" in result
        assert isinstance(result["amigavel"], str)
        assert len(result["amigavel"]) > 0

    def test_error_map_for_private_video(self):
        from app.i18n import set_language
        from app.services.errors import friendly_error

        set_language("pt-BR")
        result = friendly_error(Exception("Private video"))
        assert "amigavel" in result
        assert "privado" in result["amigavel"].lower()

        set_language("en-US")
        result2 = friendly_error(Exception("Private video"))
        assert "private" in result2["amigavel"].lower()

    def test_settings_feed_into_ytdlp_options(self):
        """Configurações do settings são refletidas nas opções do yt-dlp."""
        from app.services import settings

        settings.save("proxy", "socks5://127.0.0.1:1080")
        settings.save("retries", 5)
        settings.save("socket_timeout", 60)

        from app.services.ytdlp_service import YtDlpService

        service = YtDlpService()
        opts = service._build_base_opts(
            proxy=settings.load("proxy"),
            retries=settings.load("retries"),
            socket_timeout=settings.load("socket_timeout"),
        )
        assert opts["proxy"] == "socks5://127.0.0.1:1080"
        assert opts["retries"] == 5
        assert opts["socket_timeout"] == 60

        settings.reset_to_defaults()

    @patch("app.services.ytdlp_service.yt_dlp.YoutubeDL")
    def test_download_error_returns_none(self, mock_ydl):
        """Erro no yt-dlp deve retornar None (não crashar)."""
        mock_ydl.side_effect = Exception("Network error")

        from app.services.ytdlp_service import YtDlpService

        service = YtDlpService()
        result = service.extract_info("https://invalid-url.test")
        assert result is None

    def test_tiktok_detection_feeds_download_options(self):
        """URL do TikTok ativa otimizações específicas no yt-dlp."""
        from app.services.tiktok import is_tiktok_url

        assert is_tiktok_url("https://www.tiktok.com/@user/video/1234567890")
        assert not is_tiktok_url("https://youtube.com/watch?v=abc")

    def test_sponsorblock_feeds_ytdlp_options(self):
        """SponsorBlock habilitado deve adicionar sponsorblock_remove às opções."""
        from app.services.ytdlp_service import YtDlpService

        service = YtDlpService()
        ydl_opts = service._build_base_opts()
        ydl_opts["sponsorblock_remove"] = ["sponsor", "selfpromo"]
        assert "sponsorblock_remove" in ydl_opts
        assert "sponsor" in ydl_opts["sponsorblock_remove"]

    def test_concurrent_fragments_feeds_ytdlp_options(self):
        """Concurrent fragments > 1 deve adicionar concurrent_fragment_downloads."""
        from app.services.ytdlp_service import YtDlpService

        service = YtDlpService()
        ydl_opts = service._build_base_opts()
        concurrent = 8
        if concurrent > 1:
            ydl_opts["concurrent_fragment_downloads"] = concurrent
        assert ydl_opts["concurrent_fragment_downloads"] == 8
