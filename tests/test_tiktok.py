"""Testes unitários para app.services.tiktok."""

from app.services.tiktok import (
    detect_content_type,
    extract_video_id,
    get_content_info,
    get_quality_for_tiktok,
    is_tiktok_url,
    normalize_url,
)


class TestIsTiktokUrl:
    """Testes para detecção de URLs do TikTok."""

    def test_video_padrao(self):
        assert is_tiktok_url("https://www.tiktok.com/@user/video/1234567890") is True

    def test_video_com_query(self):
        assert is_tiktok_url("https://www.tiktok.com/@user/video/1234567890?lang=pt") is True

    def test_link_curto_vm(self):
        assert is_tiktok_url("https://vm.tiktok.com/abc123/") is True

    def test_link_curto_vt(self):
        assert is_tiktok_url("https://vt.tiktok.com/abc123/") is True

    def test_story(self):
        assert is_tiktok_url("https://www.tiktok.com/@user/story/1234567890") is True

    def test_photo(self):
        assert is_tiktok_url("https://www.tiktok.com/@user/photo/1234567890") is True

    def test_url_nao_tiktok(self):
        assert is_tiktok_url("https://www.youtube.com/watch?v=abc") is False

    def test_url_vazia(self):
        assert is_tiktok_url("") is False

    def test_none(self):
        assert is_tiktok_url(None) is False

    def test_url_parcial(self):
        assert is_tiktok_url("tiktok.com/video/123") is False  # sem https://


class TestExtractVideoId:
    """Testes para extração de ID do vídeo TikTok."""

    def test_video_padrao(self):
        url = "https://www.tiktok.com/@user/video/1234567890"
        assert extract_video_id(url) == "1234567890"

    def test_story(self):
        url = "https://www.tiktok.com/@user/story/9876543210"
        assert extract_video_id(url) == "9876543210"

    def test_photo(self):
        url = "https://www.tiktok.com/@user/photo/1112223333"
        assert extract_video_id(url) == "1112223333"

    def test_link_curto(self):
        url = "https://vm.tiktok.com/abc123/"
        assert extract_video_id(url) is None  # links curtos não têm ID na URL

    def test_url_nao_tiktok(self):
        assert extract_video_id("https://youtube.com/watch?v=abc") is None


class TestDetectContentType:
    """Testes para detecção de tipo de conteúdo."""

    def test_video(self):
        assert detect_content_type("https://www.tiktok.com/@user/video/123") == "video"

    def test_photo(self):
        assert detect_content_type("https://www.tiktok.com/@user/photo/123") == "photo"

    def test_story(self):
        assert detect_content_type("https://www.tiktok.com/@user/story/123") == "story"

    def test_link_curto(self):
        assert detect_content_type("https://vm.tiktok.com/abc123/") == "video"

    def test_url_nao_tiktok(self):
        assert detect_content_type("https://youtube.com/watch?v=abc") == "unknown"

    def test_url_vazia(self):
        assert detect_content_type("") == "unknown"


class TestNormalizeUrl:
    """Testes para normalização de URLs."""

    def test_remove_query_params(self):
        url = "https://www.tiktok.com/@user/video/123?lang=pt&share=1"
        result = normalize_url(url)
        assert "?" not in result
        assert result == "https://www.tiktok.com/@user/video/123"

    def test_remove_slash_final(self):
        url = "https://www.tiktok.com/@user/video/123/"
        result = normalize_url(url)
        assert not result.endswith("/")

    def test_url_vazia(self):
        assert normalize_url("") == ""

    def test_url_sem_query(self):
        url = "https://www.tiktok.com/@user/video/123"
        assert normalize_url(url) == url


class TestGetQualityForTiktok:
    """Testes para seleção de qualidade otimizada para TikTok."""

    def test_best(self):
        assert get_quality_for_tiktok("Melhor disponivel") == "best"

    def test_4k_limitado(self):
        """TikTok não vai além de 1080p, mesmo pedindo 4K."""
        assert get_quality_for_tiktok("4K / 2160p") == "best"

    def test_1080p(self):
        result = get_quality_for_tiktok("Full HD / 1080p")
        assert "1080" in result

    def test_720p(self):
        result = get_quality_for_tiktok("HD / 720p")
        assert "720" in result


class TestGetContentInfo:
    """Testes para informações de conteúdo TikTok."""

    def test_video_tiktok(self):
        info = get_content_info("https://www.tiktok.com/@user/video/123456")
        assert info["is_tiktok"] is True
        assert info["content_type"] == "video"
        assert info["video_id"] == "123456"

    def test_photo_tiktok(self):
        info = get_content_info("https://www.tiktok.com/@user/photo/123456")
        assert info["content_type"] == "photo"
        assert info["content_type_label"] == "Foto / Carrossel"

    def test_story_precisa_cookies(self):
        info = get_content_info("https://www.tiktok.com/@user/story/123456")
        assert info["needs_cookies"] is True

    def test_url_nao_tiktok(self):
        info = get_content_info("https://youtube.com/watch?v=abc")
        assert info["is_tiktok"] is False

    def test_video_nao_precisa_cookies(self):
        info = get_content_info("https://www.tiktok.com/@user/video/123456")
        assert info["needs_cookies"] is False
