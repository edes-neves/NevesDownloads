"""Testes unitários para app.services.history."""

from app.services import history


class TestHistory:
    """Testes para o módulo de histórico."""

    def setup_method(self):
        """Reseta o histórico antes de cada teste."""
        history._save([])

    def test_add_entry_e_get_history(self):
        history.add_entry(
            url="https://youtube.com/watch?v=test1",
            title="Vídeo Teste",
            filename="video_teste.mp4",
            status="completed",
            mode="video",
            uploader="Canal Teste",
        )
        items = history.get_history(limit=10)
        assert len(items) == 1
        assert items[0]["url"] == "https://youtube.com/watch?v=test1"
        assert items[0]["title"] == "Vídeo Teste"
        assert items[0]["status"] == "completed"
        assert items[0]["mode"] == "video"

    def test_add_entry_audio(self):
        history.add_entry(
            url="https://youtube.com/watch?v=test2",
            title="Música Teste",
            status="completed",
            mode="audio",
        )
        items = history.get_history()
        assert len(items) == 1
        assert items[0]["mode"] == "audio"

    def test_ordem_mais_recente_primeiro(self):
        history.add_entry(url="https://a.com", title="Primeiro")
        history.add_entry(url="https://b.com", title="Segundo")
        items = history.get_history()
        assert items[0]["title"] == "Segundo"
        assert items[1]["title"] == "Primeiro"

    def test_limit_no_max(self):
        """Testa que o histórico respeita o limite de 500."""
        for i in range(510):
            history.add_entry(url=f"https://example.com/{i}", title=f"Vídeo {i}")
        items = history.get_history(limit=1000)
        assert len(items) == history.MAX_HISTORY

    def test_get_history_limit(self):
        for i in range(10):
            history.add_entry(url=f"https://example.com/{i}", title=f"Vídeo {i}")
        items = history.get_history(limit=3)
        assert len(items) == 3

    def test_clear_history(self):
        history.add_entry(url="https://example.com", title="Teste")
        assert len(history.get_history()) == 1
        history.clear_history()
        assert len(history.get_history()) == 0

    def test_timestamp_presente(self):
        history.add_entry(url="https://example.com", title="Teste")
        items = history.get_history()
        assert "timestamp" in items[0]
        assert items[0]["timestamp"]  # não vazio

    def test_historico_vazio(self):
        items = history.get_history()
        assert items == []

    def test_entry_com_status_error(self):
        history.add_entry(
            url="https://example.com/fail",
            title="Vídeo com Erro",
            status="error",
            mode="video",
        )
        items = history.get_history()
        assert items[0]["status"] == "error"
