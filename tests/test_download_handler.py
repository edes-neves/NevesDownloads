"""Testes unitários para DownloadHandler - extração de URLs."""

from app.ui.download_handler import DownloadHandler


class TestPasteFromClipboard:
    """Testes para _paste_from_clipboard (colagem empilhando URLs)."""

    def _make(self, initial: str = "", clipboard: str | Exception = ""):
        class Fake:
            def __init__(self, text, clip):
                self._text = text
                self._clip = clip

            def clipboard_get(self):
                if isinstance(self._clip, Exception):
                    raise self._clip
                return self._clip

            def _get_url_text(self):
                return self._text.strip()

            def _set_url_text(self, text):
                self._text = text

        fake = Fake(initial, clipboard)
        DownloadHandler._paste_from_clipboard(fake)
        return fake._text

    def test_cola_em_campo_vazio(self):
        assert self._make(initial="", clipboard="https://youtu.be/abc") == "https://youtu.be/abc"

    def test_empilha_quando_ja_existe_texto(self):
        text = self._make(initial="https://youtube.com/watch?v=1", clipboard="https://youtube.com/watch?v=2")
        assert text == "https://youtube.com/watch?v=1\nhttps://youtube.com/watch?v=2"

    def test_empilha_varias_urls(self):
        text = self._make(initial="https://a.com\nhttps://b.com", clipboard="https://c.com")
        assert text == "https://a.com\nhttps://b.com\nhttps://c.com"

    def test_remove_espacos_do_clipboard(self):
        text = self._make(initial="https://a.com", clipboard="  https://b.com  ")
        assert text == "https://a.com\nhttps://b.com"

    def test_remove_nova_linha_final_do_clipboard(self):
        text = self._make(initial="https://a.com", clipboard="https://b.com\n")
        assert text == "https://a.com\nhttps://b.com"

    def test_clipboard_vazio_nao_altera(self):
        assert self._make(initial="https://a.com", clipboard="") == "https://a.com"

    def test_clipboard_vazio_em_campo_vazio(self):
        assert self._make(initial="", clipboard="") == ""

    def test_erro_ao_ler_clipboard_nao_altera(self):
        assert self._make(initial="https://a.com", clipboard=RuntimeError("clipboard vazio")) == "https://a.com"


class TestUrlsFromFile:
    """Testes para _urls_from_file (leitura de lista de URLs de arquivo)."""

    def test_lê_arquivo_com_urls(self, tmp_path):
        arquivo = tmp_path / "lista.txt"
        arquivo.write_text(
            "https://youtube.com/watch?v=1\nlinha sem url\nhttps://youtu.be/2\n",
            encoding="utf-8",
        )
        urls = DownloadHandler._urls_from_file(arquivo)
        assert urls == ["https://youtube.com/watch?v=1", "https://youtu.be/2"]

    def test_arquivo_inexistente_retorna_vazio(self, tmp_path):
        assert DownloadHandler._urls_from_file(tmp_path / "nao_existe.txt") == []

    def test_arquivo_vazio(self, tmp_path):
        arquivo = tmp_path / "vazio.txt"
        arquivo.write_text("", encoding="utf-8")
        assert DownloadHandler._urls_from_file(arquivo) == []

    def test_ignora_duplicadas(self, tmp_path):
        arquivo = tmp_path / "dup.txt"
        arquivo.write_text("https://youtube.com/watch?v=1\nhttps://youtube.com/watch?v=1\n", encoding="utf-8")
        assert DownloadHandler._urls_from_file(arquivo) == ["https://youtube.com/watch?v=1"]


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
