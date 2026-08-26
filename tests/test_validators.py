"""Testes unitários para app.utils.validators."""

from app.utils.validators import is_valid_url


class TestIsValidUrl:
    """Testes para a função is_valid_url."""

    def test_url_http_valida(self):
        assert is_valid_url("http://example.com") is True

    def test_url_https_valida(self):
        assert is_valid_url("https://www.youtube.com/watch?v=abc123") is True

    def test_url_com_path(self):
        assert is_valid_url("https://www.youtube.com/playlist?list=PLxxxx") is True

    def test_url_vazia(self):
        assert is_valid_url("") is False

    def test_none(self):
        assert is_valid_url(None) is False

    def test_texto_qualquer(self):
        assert is_valid_url("nao e uma url") is False

    def test_url_ftp_nao_suportada(self):
        assert is_valid_url("ftp://files.example.com/file.zip") is False

    def test_url_com_espacos_no_inicio(self):
        assert is_valid_url("  https://example.com") is True

    def test_url_tiktok(self):
        assert is_valid_url("https://www.tiktok.com/@user/video/123456") is True

    def test_url_instagram(self):
        assert is_valid_url("https://www.instagram.com/reel/ABC123/") is True

    def test_url_com_subdominio(self):
        assert is_valid_url("https://m.youtube.com/watch?v=abc") is True

    def test_url_com_porta(self):
        assert is_valid_url("https://example.com:8080/path") is True
