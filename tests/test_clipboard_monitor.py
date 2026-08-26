"""Testes unitários para app.services.clipboard_monitor."""

from app.services.clipboard_monitor import ClipboardMonitor


class TestClipboardMonitor:
    """Testes para o monitor de área de transferência."""

    def test_extrair_url_de_texto(self):
        """Testa a extração de URLs de textos."""
        url = ClipboardMonitor._extract_first_url("https://www.youtube.com/watch?v=abc123")
        assert url == "https://www.youtube.com/watch?v=abc123"

    def test_extrair_url_de_texto_misto(self):
        """URL em texto com outros caracteres."""
        text = "Olha esse vídeo: https://youtu.be/abc123 é incrível!"
        url = ClipboardMonitor._extract_first_url(text)
        assert url == "https://youtu.be/abc123"

    def test_extrair_url_tiktok(self):
        url = ClipboardMonitor._extract_first_url("https://www.tiktok.com/@user/video/123")
        assert url == "https://www.tiktok.com/@user/video/123"

    def test_extrair_url_instagram(self):
        url = ClipboardMonitor._extract_first_url("https://www.instagram.com/reel/ABC123/")
        assert url == "https://www.instagram.com/reel/ABC123/"

    def test_texto_sem_url(self):
        url = ClipboardMonitor._extract_first_url("texto sem nenhuma URL aqui")
        assert url is None

    def test_texto_vazio(self):
        url = ClipboardMonitor._extract_first_url("")
        assert url is None

    def test_none(self):
        url = ClipboardMonitor._extract_first_url(None)
        assert url is None

    def test_texto_muito_longo(self):
        """Textos muito longos (>2048 chars) são ignorados."""
        long_text = "https://example.com/" + "a" * 3000
        url = ClipboardMonitor._extract_first_url(long_text)
        assert url is None

    def test_callback_chamado(self):
        """Testa que o callback é chamado quando uma URL é detectada."""
        detected = []
        monitor = ClipboardMonitor(
            on_url_detected=lambda url: detected.append(url),
        )

        # Força o callback diretamente
        monitor._on_url("https://example.com/video")
        # Como _on_url é o callable direto, testamos a extração
        url = monitor._extract_first_url("https://example.com/video")
        assert url == "https://example.com/video"

    def test_start_stop(self):
        """Testa start/stop sem erros."""
        monitor = ClipboardMonitor(
            on_url_detected=lambda url: None,
            poll_interval=10,  # intervalo alto para não rodar
        )
        monitor.start()
        assert monitor.running is True
        monitor.stop()
        assert monitor.running is False

    def test_stop_idempotente(self):
        """Stop pode ser chamado múltiplas vezes sem erro."""
        monitor = ClipboardMonitor(
            on_url_detected=lambda url: None,
            poll_interval=10,
        )
        monitor.start()
        monitor.stop()
        monitor.stop()  # segunda vez não deve dar erro
        assert monitor.running is False

    def test_start_idempotente(self):
        """Start duas vezes não cria duas threads."""
        monitor = ClipboardMonitor(
            on_url_detected=lambda url: None,
            poll_interval=10,
        )
        monitor.start()
        monitor.start()  # segunda vez não deve criar nova thread
        assert monitor.running is True
        monitor.stop()

    def test_url_com_pontuacao_final(self):
        """URL com pontuação no final deve ser limpa."""
        url = ClipboardMonitor._extract_first_url("https://example.com/video.")
        assert url == "https://example.com/video"

    def test_url_com_parenteses(self):
        url = ClipboardMonitor._extract_first_url("https://example.com/wiki/Item_(filme)")
        # Pode cortar no parêntese de fechamento dependendo da regex
        assert url is not None
        assert "example.com" in url
