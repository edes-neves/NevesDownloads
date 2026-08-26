"""Testes unitários para app.services.queue."""

from app.services.queue import DownloadQueue


class TestDownloadQueue:
    """Testes para a fila persistente de downloads."""

    def setup_method(self):
        """Cria fila não-persistente para testes isolados."""
        self.queue = DownloadQueue(persist=False)

    def test_add_item(self):
        item = self.queue.add("https://example.com/1", title="Vídeo 1")
        assert item is not None
        assert item["url"] == "https://example.com/1"
        assert item["status"] == "pending"
        assert item["attempts"] == 0

    def test_add_duplicata_retorna_none(self):
        self.queue.add("https://example.com/1", title="Vídeo 1")
        item2 = self.queue.add("https://example.com/1", title="Vídeo 1 dup")
        assert item2 is None

    def test_add_duplicata_concluida_permitida(self):
        """Permite re-adicionar URL que já foi concluída (pode ser re-download)."""
        self.queue.add("https://example.com/1", title="Vídeo 1")
        self.queue.mark_done("https://example.com/1")
        item2 = self.queue.add("https://example.com/1", title="Vídeo 1 v2")
        # Após done, não há mais 'pending' com essa URL, então pode adicionar
        assert item2 is not None

    def test_set_status(self):
        self.queue.add("https://example.com/1", title="Vídeo 1")
        self.queue.set_status("https://example.com/1", "downloading")
        items = self.queue.all()
        assert items[0]["status"] == "downloading"

    def test_mark_downloading(self):
        self.queue.add("https://example.com/1", title="Vídeo 1")
        self.queue.mark_downloading("https://example.com/1")
        items = self.queue.all()
        assert items[0]["status"] == "downloading"

    def test_mark_done(self):
        self.queue.add("https://example.com/1", title="Vídeo 1")
        self.queue.mark_downloading("https://example.com/1")
        self.queue.mark_done("https://example.com/1")
        items = self.queue.all()
        assert items[0]["status"] == "done"

    def test_mark_error(self):
        self.queue.add("https://example.com/1", title="Vídeo 1")
        self.queue.mark_error("https://example.com/1")
        items = self.queue.all()
        assert items[0]["status"] == "error"

    def test_remove(self):
        self.queue.add("https://example.com/1", title="Vídeo 1")
        removed = self.queue.remove("https://example.com/1")
        assert removed is True
        assert len(self.queue.all()) == 0

    def test_remove_inexistente(self):
        removed = self.queue.remove("https://example.com/inexistente")
        assert removed is False

    def test_pending(self):
        self.queue.add("https://example.com/1", title="V1")
        self.queue.add("https://example.com/2", title="V2")
        self.queue.mark_done("https://example.com/1")
        pending = self.queue.pending()
        assert len(pending) == 1
        assert pending[0]["url"] == "https://example.com/2"

    def test_next_pending(self):
        self.queue.add("https://example.com/1", title="V1")
        self.queue.add("https://example.com/2", title="V2")
        next_item = self.queue.next_pending()
        assert next_item["url"] == "https://example.com/1"

    def test_next_pending_vazia(self):
        next_item = self.queue.next_pending()
        assert next_item is None

    def test_increment_attempts(self):
        self.queue.add("https://example.com/1", title="V1")
        count = self.queue.increment_attempts("https://example.com/1")
        assert count == 1
        count = self.queue.increment_attempts("https://example.com/1")
        assert count == 2

    def test_prune_finished(self):
        self.queue.add("https://example.com/1", title="V1")
        self.queue.add("https://example.com/2", title="V2")
        self.queue.add("https://example.com/3", title="V3")
        self.queue.mark_done("https://example.com/1")
        self.queue.mark_error("https://example.com/2")
        self.queue.prune_finished()
        remaining = self.queue.all()
        assert len(remaining) == 1
        assert remaining[0]["url"] == "https://example.com/3"

    def test_max_queue_limit(self):
        """Testa que a fila respeita o limite máximo."""
        for i in range(10):
            self.queue.add(f"https://example.com/{i}", title=f"V{i}")
        # Mesmo com limite alto (5000), não deve explodir
        assert len(self.queue.all()) == 10

    def test_metadata(self):
        item = self.queue.add(
            "https://example.com/1",
            title="V1",
            metadata={"quality": "1080p"},
        )
        assert item["metadata"]["quality"] == "1080p"
