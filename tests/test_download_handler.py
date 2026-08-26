"""Testes unitários para DownloadHandler - extração de URLs."""

from app.ui.download_handler import DownloadHandler


class TestExtractUrls:
    """Testes para _extract_urls (método estático)."""

    def test_single_url(self):
        text = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        urls = DownloadHandler._extract_urls(text)
        assert urls == ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]

    def test_multiple_urls(self):
        text = "https://youtube.com/watch?v=abc\nhttps://youtu.be/xyz"
        urls = DownloadHandler._extract_urls(text)
        assert len(urls) == 2
        assert "https://youtube.com/watch?v=abc" in urls
        assert "https://youtu.be/xyz" in urls

    def test_url_with_surrounding_text(self):
        text = "Olhe esse vídeo: https://youtube.com/watch?v=abc e me diga o que achou"
        urls = DownloadHandler._extract_urls(text)
        assert urls == ["https://youtube.com/watch?v=abc"]

    def test_empty_text(self):
        assert DownloadHandler._extract_urls("") == []

    def test_none_text(self):
        assert DownloadHandler._extract_urls(None) == []

    def test_no_urls(self):
        text = "Isso não contém nenhuma URL"
        assert DownloadHandler._extract_urls(text) == []

    def test_trailing_punctuation_stripped(self):
        text = "https://youtube.com/watch?v=abc."
        urls = DownloadHandler._extract_urls(text)
        assert urls == ["https://youtube.com/watch?v=abc"]

    def test_trailing_comma_stripped(self):
        text = "https://youtube.com/watch?v=abc,"
        urls = DownloadHandler._extract_urls(text)
        assert urls == ["https://youtube.com/watch?v=abc"]

    def test_trailing_semicolon_stripped(self):
        text = "https://youtube.com/watch?v=abc;"
        urls = DownloadHandler._extract_urls(text)
        assert urls == ["https://youtube.com/watch?v=abc"]

    def test_trailing_parenthesis_stripped(self):
        text = "veja (https://youtube.com/watch?v=abc)"
        urls = DownloadHandler._extract_urls(text)
        assert urls == ["https://youtube.com/watch?v=abc"]

    def test_duplicate_urls_removed(self):
        text = "https://youtube.com/watch?v=abc https://youtube.com/watch?v=abc"
        urls = DownloadHandler._extract_urls(text)
        assert len(urls) == 1

    def test_tiktok_url(self):
        text = "https://www.tiktok.com/@user/video/1234567890"
        urls = DownloadHandler._extract_urls(text)
        assert len(urls) == 1
        assert "tiktok.com" in urls[0]

    def test_instagram_url(self):
        text = "https://www.instagram.com/reel/ABC123/"
        urls = DownloadHandler._extract_urls(text)
        assert len(urls) == 1
        assert "instagram.com" in urls[0]

    def test_mixed_text_and_urls(self):
        text = "Baixe aqui: https://youtube.com/watch?v=abc\nE também: https://youtu.be/xyz\nMas não isso aqui"
        urls = DownloadHandler._extract_urls(text)
        assert len(urls) == 2

    def test_url_with_special_chars_in_path(self):
        text = "https://example.com/path/to/page?query=value&other=123"
        urls = DownloadHandler._extract_urls(text)
        assert urls == ["https://example.com/path/to/page?query=value&other=123"]

    def test_http_not_just_https(self):
        text = "http://example.com/video.mp4"
        urls = DownloadHandler._extract_urls(text)
        assert urls == ["http://example.com/video.mp4"]

    def test_www_vs_non_www(self):
        text = "https://www.youtube.com/watch?v=abc"
        urls = DownloadHandler._extract_urls(text)
        assert urls == ["https://www.youtube.com/watch?v=abc"]

    def test_url_at_end_of_line(self):
        text = "confira https://youtube.com/watch?v=abc"
        urls = DownloadHandler._extract_urls(text)
        assert urls == ["https://youtube.com/watch?v=abc"]

    def test_url_with_angled_brackets_stripped(self):
        text = "https://youtube.com/watch?v=abc>"
        urls = DownloadHandler._extract_urls(text)
        assert urls == ["https://youtube.com/watch?v=abc"]

    def test_preserves_order(self):
        text = "https://first.com\nhttps://second.com\nhttps://third.com"
        urls = DownloadHandler._extract_urls(text)
        assert urls[0] == "https://first.com"
        assert urls[1] == "https://second.com"
        assert urls[2] == "https://third.com"
