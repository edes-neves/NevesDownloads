"""Testes unitários para DownloadCard - formatação de progresso e callbacks."""

from unittest.mock import MagicMock


class TestFormatSize:
    """Testes estáticos para _format_size."""

    def test_bytes(self):
        from app.ui.download_card import DownloadCard

        assert DownloadCard._format_size(0) == "0 B"
        assert DownloadCard._format_size(512) == "512 B"
        assert DownloadCard._format_size(1023) == "1023 B"

    def test_kilobytes(self):
        from app.ui.download_card import DownloadCard

        assert DownloadCard._format_size(1024) == "1.0 KB"
        assert DownloadCard._format_size(1536) == "1.5 KB"
        assert DownloadCard._format_size(1024 * 1023) == "1023.0 KB"

    def test_megabytes(self):
        from app.ui.download_card import DownloadCard

        assert DownloadCard._format_size(1024 * 1024) == "1.0 MB"
        assert DownloadCard._format_size(1024 * 1024 * 50) == "50.0 MB"
        assert DownloadCard._format_size(1024 * 1024 * 1023) == "1023.0 MB"

    def test_gigabytes(self):
        from app.ui.download_card import DownloadCard

        assert DownloadCard._format_size(1024 * 1024 * 1024) == "1.00 GB"
        assert DownloadCard._format_size(1024 * 1024 * 1024 * 5) == "5.00 GB"

    def test_boundary_1023_bytes(self):
        from app.ui.download_card import DownloadCard

        assert DownloadCard._format_size(1023).endswith(" B")

    def test_boundary_1024_bytes(self):
        from app.ui.download_card import DownloadCard

        assert DownloadCard._format_size(1024).endswith(" KB")


class TestDownloadCardLogic:
    """Testes de lógica do DownloadCard usando mock de widgets."""

    def _make_card(self):
        """Cria um DownloadCard com widgets mockados."""
        from app.ui.download_card import DownloadCard

        card = MagicMock(spec=DownloadCard)
        card.cancelled = False
        card._paused = False
        card.last_update = {}
        card.progress_bar = MagicMock()
        card.info_label = MagicMock()
        card.cancel_btn = MagicMock()
        card.pause_btn = MagicMock()
        card.cancel_callback = None
        card.pause_callback = None
        card.resume_callback = None
        # Vincula os métodos reais
        card.update_progress = lambda data: DownloadCard.update_progress(card, data)
        card._on_cancel = lambda: DownloadCard._on_cancel(card)
        card._on_pause = lambda: DownloadCard._on_pause(card)
        card.set_paused = lambda paused: DownloadCard.set_paused(card, paused)
        card._format_size = DownloadCard._format_size
        card._format_eta = DownloadCard._format_eta
        return card

    def test_cancel_sets_flag_and_disables_button(self):
        card = self._make_card()
        card._on_cancel()
        assert card.cancelled is True
        card.cancel_btn.configure.assert_called_with(state="disabled", text="Cancelando...")

    def test_cancel_calls_callback(self):
        card = self._make_card()
        cb = MagicMock()
        card.cancel_callback = cb
        card._on_cancel()
        cb.assert_called_once()

    def test_pause_calls_pause_callback(self):
        card = self._make_card()
        cb = MagicMock()
        card.pause_callback = cb
        card._on_pause()
        cb.assert_called_once()
        assert card._paused is True

    def test_resume_calls_resume_callback(self):
        card = self._make_card()
        card._paused = True
        cb = MagicMock()
        card.resume_callback = cb
        card._on_pause()
        cb.assert_called_once()
        assert card._paused is False

    def test_set_paused_updates_button_text(self):
        card = self._make_card()
        card.set_paused(True)
        card.pause_btn.configure.assert_called_with(text="Retomar", fg_color="#8c6b2b", hover_color="#6b4f1e")
        card.set_paused(False)
        card.pause_btn.configure.assert_called_with(text="Pausar", fg_color="#2b6b8c", hover_color="#1e4f6b")

    def test_update_progress_with_total_bytes(self):
        card = self._make_card()
        data = {
            "downloaded_bytes": 500,
            "total_bytes": 1000,
            "speed": 1024 * 1024,
            "eta": 65,
        }
        card.update_progress(data)
        card.progress_bar.set.assert_called_with(0.5)
        info_text = card.info_label.configure.call_args[1].get("text", "")
        assert "50%" in info_text

    def test_update_progress_with_estimate(self):
        card = self._make_card()
        data = {
            "downloaded_bytes": 250,
            "total_bytes_estimate": 1000,
            "speed": 0,
            "eta": 0,
        }
        card.update_progress(data)
        card.progress_bar.set.assert_called_with(0.25)

    def test_update_progress_speed_formatting_bytes(self):
        card = self._make_card()
        data = {"downloaded_bytes": 100, "total_bytes": 200, "speed": 500, "eta": 0}
        card.update_progress(data)
        info_text = card.info_label.configure.call_args[1]["text"]
        assert "B/s" in info_text

    def test_update_progress_speed_formatting_kb(self):
        card = self._make_card()
        data = {"downloaded_bytes": 100, "total_bytes": 200, "speed": 5000, "eta": 0}
        card.update_progress(data)
        info_text = card.info_label.configure.call_args[1]["text"]
        assert "KB/s" in info_text

    def test_update_progress_speed_formatting_mb(self):
        card = self._make_card()
        data = {"downloaded_bytes": 100, "total_bytes": 200, "speed": 2 * 1024 * 1024, "eta": 0}
        card.update_progress(data)
        info_text = card.info_label.configure.call_args[1]["text"]
        assert "MB/s" in info_text

    def test_update_progress_eta_with_hours(self):
        card = self._make_card()
        data = {"downloaded_bytes": 100, "total_bytes": 200, "speed": 0, "eta": 3661}
        card.update_progress(data)
        info_text = card.info_label.configure.call_args[1]["text"]
        assert "ETA: 01:01:01" in info_text

    def test_update_progress_eta_without_hours(self):
        card = self._make_card()
        data = {"downloaded_bytes": 100, "total_bytes": 200, "speed": 0, "eta": 125}
        card.update_progress(data)
        info_text = card.info_label.configure.call_args[1]["text"]
        assert "ETA: 02:05" in info_text

    def test_update_progress_eta_zero_shows_dashes(self):
        card = self._make_card()
        data = {"downloaded_bytes": 100, "total_bytes": 200, "speed": 0, "eta": 0}
        card.update_progress(data)
        info_text = card.info_label.configure.call_args[1]["text"]
        assert "ETA: --" in info_text

    def test_update_progress_eta_float_does_not_crash(self):
        """ETA fracionário (float do yt-dlp) não deve estourar formatação."""
        card = self._make_card()
        data = {"downloaded_bytes": 100, "total_bytes": 200, "speed": 0, "eta": 65.5}
        card.update_progress(data)
        info_text = card.info_label.configure.call_args[1]["text"]
        assert "ETA: 01:05" in info_text

    def test_update_progress_finished_sets_bar_to_1(self):
        card = self._make_card()
        data = {"downloaded_bytes": 1000, "total_bytes": 1000, "speed": 0, "eta": 0, "status": "finished"}
        card.update_progress(data)
        card.progress_bar.set.assert_called_with(1.0)
        card.cancel_btn.configure.assert_called_with(state="disabled", text="Concluído")

    def test_update_progress_error_disables_button(self):
        card = self._make_card()
        data = {"downloaded_bytes": 0, "total_bytes": 0, "speed": 0, "eta": 0, "status": "error"}
        card.update_progress(data)
        card.cancel_btn.configure.assert_called_with(state="disabled", text="Erro")

    def test_update_progress_cancelled_skipped(self):
        card = self._make_card()
        card.cancelled = True
        card.update_progress({"status_text": "test"})
        card.info_label.configure.assert_not_called()

    def test_update_progress_status_text(self):
        card = self._make_card()
        card.update_progress({"status_text": "Baixando..."})
        card.info_label.configure.assert_called_with(text="Baixando...")

    def test_update_progress_status_text_moves_batch_bar(self):
        card = self._make_card()
        card.update_progress({"status_text": "2/5 videos (1 ok)", "current": 2, "total": 5})
        card.progress_bar.set.assert_called_with(0.4)

    def test_update_progress_status_text_batch_real_progress(self):
        card = self._make_card()
        card.update_progress({"status_text": "1/2 videos (0 ok)", "progress": 0.73})
        card.progress_bar.set.assert_called_with(0.73)

    def test_update_progress_status_text_no_total_keeps_bar(self):
        card = self._make_card()
        card.update_progress({"status_text": "Erro na extração de info", "status": "error"})
        card.progress_bar.set.assert_not_called()

    def test_update_progress_no_total_shows_downloaded_only(self):
        card = self._make_card()
        data = {"downloaded_bytes": 500, "speed": 0, "eta": 0}
        card.update_progress(data)
        info_text = card.info_label.configure.call_args[1]["text"]
        assert "500 B" in info_text
