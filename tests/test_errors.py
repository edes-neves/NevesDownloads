"""Testes unitários para app.services.errors."""

from app.services.errors import friendly_error, friendly_text, log_error


class TestFriendlyError:
    """Testes para a função friendly_error."""

    def test_video_privado(self):
        error = Exception("This video is private")
        result = friendly_error(error)
        assert result["nome"] == "video_privado"
        assert "privado" in result["amigavel"].lower()
        assert "🔒" in result["icone"]
        assert "cookie" in result["dica"].lower()

    def test_video_indisponivel(self):
        error = Exception("This video has been removed")
        result = friendly_error(error)
        assert result["nome"] == "video_indisponivel"
        assert "indisponível" in result["amigavel"].lower() or "removido" in result["amigavel"].lower()

    def test_regiao_bloqueada(self):
        error = Exception("not available in your country")
        result = friendly_error(error)
        assert result["nome"] == "regiao_bloqueada"
        assert "região" in result["amigavel"].lower() or "geográfica" in result["dica"].lower()

    def test_idade_restrita(self):
        error = Exception("age-restricted content")
        result = friendly_error(error)
        assert result["nome"] == "idade_restrita"
        assert "idade" in result["amigavel"].lower()

    def test_login_necessario(self):
        error = Exception("sign in to continue")
        result = friendly_error(error)
        assert result["nome"] == "login_necessario"

    def test_ffmpeg_faltando(self):
        error = Exception("ffmpeg is not installed")
        result = friendly_error(error)
        assert result["nome"] == "ffmpeg_faltando"

    def test_url_invalida(self):
        error = Exception("unsupported URL format")
        result = friendly_error(error)
        assert result["nome"] == "url_invalida"

    def test_timeout(self):
        error = Exception("timed out")
        result = friendly_error(error)
        assert result["nome"] == "timeout"

    def test_rate_limit(self):
        error = Exception("429 Too Many Requests")
        result = friendly_error(error)
        assert result["nome"] == "rate_limit"

    def test_erro_rede(self):
        error = Exception("Connection refused")
        result = friendly_error(error)
        assert result["nome"] == "erro_rede"

    def test_erro_generico(self):
        error = Exception("algum erro completamente novo")
        result = friendly_error(error)
        assert result["nome"] == "generico"
        assert "inesperado" in result["amigavel"].lower()

    def test_retorna_todas_chaves(self):
        error = Exception("test")
        result = friendly_error(error)
        assert "amigavel" in result
        assert "dica" in result
        assert "icone" in result
        assert "tecnico" in result
        assert "nome" in result


class TestFriendlyText:
    """Testes para a função friendly_text."""

    def test_retorna_string(self):
        error = Exception("This video is private")
        result = friendly_text(error)
        assert isinstance(result, str)
        assert "privado" in result.lower()

    def test_inclui_icone(self):
        error = Exception("ffmpeg is not installed")
        result = friendly_text(error)
        assert "▶" in result


class TestLogError:
    """Testes para a função log_error."""

    def test_nao_levanta_excecao(self):
        error = Exception("test error")
        # Não deve levantar exceção
        log_error(error, contexto="teste")
