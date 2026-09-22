"""Testes unitários para app.services.settings."""

from app.services import settings


class TestSettings:
    """Testes para o módulo de configurações."""

    def setup_method(self):
        """Reseta configurações antes de cada teste."""
        settings.reset_to_defaults()

    def test_load_default(self):
        """Carrega uma configuração padrão."""
        value = settings.load("download_path")
        assert value is not None
        assert isinstance(value, str)

    def test_load_inexistente_retorna_default(self):
        """Chave inexistente retorna valor padrão."""
        value = settings.load("chave_que_nao_existe")
        assert value is None

    def test_load_none_retorna_tudo(self):
        """load(None) retorna todas as configurações."""
        config = settings.load()
        assert isinstance(config, dict)
        assert "download_path" in config
        assert "appearance_mode" in config

    def test_save_e_load(self):
        """Salva e recarrega uma configuração."""
        settings.save("max_concurrent_downloads", 5)
        assert settings.load("max_concurrent_downloads") == 5

    def test_sanitize_invalid_value(self):
        """Valor inválido para seleção retorna default."""
        settings.save("appearance_mode", "invalido")
        assert settings.load("appearance_mode") == "system"

    def test_sanitize_invalid_int(self):
        """Valor não-inteiro para campo inteiro retorna default."""
        settings.save("max_concurrent_downloads", "nao_e_numero")
        assert settings.load("max_concurrent_downloads") == 3

    def test_save_bool(self):
        settings.save("embed_thumbnail", True)
        assert settings.load("embed_thumbnail") is True
        settings.save("embed_thumbnail", False)
        assert settings.load("embed_thumbnail") is False

    def test_save_proxy(self):
        settings.save("proxy", "socks5://127.0.0.1:1080")
        assert settings.load("proxy") == "socks5://127.0.0.1:1080"

    def test_reset_to_defaults(self):
        """Reset restaura todos os valores padrão."""
        settings.save("max_concurrent_downloads", 10)
        settings.save("proxy", "http://proxy.test:8080")
        settings.reset_to_defaults()
        assert settings.load("max_concurrent_downloads") == 3
        assert settings.load("proxy") == ""

    def test_load_all(self):
        """load_all retorna dict completo."""
        config = settings.load_all()
        assert isinstance(config, dict)
        # Deve ter todas as chaves dos defaults
        for key in settings.SETTINGS_DEFAULTS:
            assert key in config

    def test_valores_validos_para_quality(self):
        """Qualidades válidas são aceitas."""
        for q in ["4K / 2160p", "Full HD / 1080p", "HD / 720p", "480p", "360p"]:
            settings.save("default_quality", q)
            assert settings.load("default_quality") == q

    def test_quality_invalida(self):
        settings.save("default_quality", "8K / 4320p")
        assert settings.load("default_quality") == "Melhor disponivel"

    def test_formato_video(self):
        settings.save("default_format", "WebM")
        assert settings.load("default_format") == "WebM"

    def test_formato_audio(self):
        settings.save("default_audio_format", "FLAC")
        assert settings.load("default_audio_format") == "FLAC"

    def test_cookies_browser(self):
        settings.save("default_cookies_browser", "firefox")
        assert settings.load("default_cookies_browser") == "firefox"

    def test_filename_template(self):
        settings.save("filename_template", "%(uploader)s - %(title)s.%(ext)s")
        assert settings.load("filename_template") == "%(uploader)s - %(title)s.%(ext)s"

    def test_limit_speed(self):
        settings.save("limit_speed", 1048576)
        assert settings.load("limit_speed") == 1048576

    def test_cookies_file_path_default(self):
        assert settings.load("cookies_file_path") == ""

    def test_cookies_file_path_save(self):
        settings.save("cookies_file_path", "/tmp/cookies.txt")
        assert settings.load("cookies_file_path") == "/tmp/cookies.txt"

    def test_playlist_audio_single_default(self):
        assert settings.load("playlist_audio_single") is False

    def test_playlist_audio_single_save(self):
        settings.save("playlist_audio_single", True)
        assert settings.load("playlist_audio_single") is True

    def test_transient_retries_default(self):
        assert settings.load("transient_retries") == 2

    def test_transient_retries_save(self):
        settings.save("transient_retries", 5)
        assert settings.load("transient_retries") == 5

    def test_notifications_enabled_default(self):
        assert settings.load("notifications_enabled") is True

    def test_notifications_enabled_save(self):
        settings.save("notifications_enabled", False)
        assert settings.load("notifications_enabled") is False
