"""
Mixin de orquestração de downloads.

Contém toda a lógica de iniciar, gerenciar e persistir downloads
(vídeo único, playlist, lote múltiplas URLs, fila pendente).
Projetado para ser misturado em NevesDownloadsApp via herança múltipla.
"""

import re
import threading
from pathlib import Path
from tkinter import messagebox

from app.i18n import _
from app.services.errors import friendly_error
from app.services.history import add_entry, clear_history, get_history
from app.services.tiktok import get_content_info
from app.ui.download_card import DownloadCard
from app.ui.playlist_window import PlaylistWindow


class DownloadHandler:
    """Mixin que fornece orquestração de downloads para a janela principal."""

    active_downloads: list[dict]

    # ── Helpers de URL ─────────────────────────────────────────

    def _paste_from_clipboard(self):
        """Cola o conteúdo da área de transferência na entry."""
        try:
            clipboard = self.clipboard_get()
            self._set_url_text(clipboard)
        except Exception:
            pass

    def _get_url_text(self) -> str:
        """Retorna o texto da caixa de URL (sem espaços extras)."""
        try:
            text: str = self.url_entry.get("1.0", "end")
            return text.strip()
        except TypeError:
            text2: str = self.url_entry.get()
            return text2.strip()

    def _set_url_text(self, text: str):
        """Substitui o conteúdo da caixa de URL."""
        self._clear_url_entry()
        try:
            self.url_entry.insert("1.0", text)
        except TypeError:
            self.url_entry.insert(0, text)

    def _clear_url_entry(self):
        """Limpa a caixa de URL."""
        try:
            self.url_entry.delete("1.0", "end")
        except TypeError:
            self.url_entry.delete(0, "end")

    def _select_all_url_entry(self):
        """Seleciona todo o texto da caixa de URL."""
        try:
            self.url_entry.tag_add("sel", "1.0", "end")
        except (Exception, TypeError):
            self.url_entry.select_range(0, "end")
            self.url_entry.icursor("end")

    @staticmethod
    def _extract_urls(text: str) -> list[str]:
        """Detecta e retorna todas as URLs http/https em um texto."""
        if not text:
            return []
        pattern = re.compile(r'https?://[^\s,;<>"\']+')
        urls = pattern.findall(text)
        cleaned = []
        seen = set()
        for u in urls:
            u = u.rstrip(".,;!?)]}>")
            if u and u not in seen:
                seen.add(u)
                cleaned.append(u)
        return cleaned

    def _get_cookies_browser(self) -> str | None:
        val: str = self.cookies_browser.get()
        return None if val == "Nenhum" else val

    def _cleanup_active_downloads(self):
        """Remove entradas cuja thread já terminou para evitar memory leak."""
        self.active_downloads = [d for d in self.active_downloads if d.get("thread") and d["thread"].is_alive()]
        if self._download_active and not self.active_downloads:
            self._set_download_active(False)

    # ── Click de download ──────────────────────────────────────

    def _on_download_clicked(self):
        if self._download_active:
            self._on_pause_clicked()
            return

        raw_text = self._get_url_text()
        if not raw_text:
            messagebox.showerror(_("dialog.url_empty"), _("dialog.url_empty_body"))
            return

        urls = self._extract_urls(raw_text)

        if not urls:
            messagebox.showerror(_("dialog.url_invalid"), _("dialog.url_invalid_body"))
            return

        mode = self.download_mode.get()

        if len(urls) > 1:
            self._handle_multiple_urls(urls, mode)
            return

        url = urls[0]
        from app.utils.validators import is_valid_url

        if not is_valid_url(url):
            messagebox.showerror(_("dialog.url_invalid"), _("dialog.url_invalid_single"))
            return

        if mode == "video":
            self._start_single_download(url)
        elif mode in ("playlist_all", "playlist_select"):
            self._handle_playlist(url, selectable=(mode == "playlist_select"))
        else:
            messagebox.showinfo(_("dialog.mode_unsupported"), _("dialog.mode_unsupported_body"))

    # ── Múltiplas URLs ─────────────────────────────────────────

    def _handle_multiple_urls(self, urls: list[str], mode: str):
        """Trata o caso em que várias URLs foram coladas/inseridas de uma vez."""
        self.logger.info("Detectadas %d URLs. Iniciando download em lote.", len(urls))
        self._clear_url_entry()

        if mode == "audio":
            self._start_batch_download(urls, _("batch.multiple_urls").format(count=len(urls)), mode)
            return

        resposta = messagebox.askyesnocancel(
            _("dialog.batch.title"),
            _("dialog.batch.body").format(count=len(urls)),
            icon="question",
        )
        if resposta is None:
            self._set_url_text("\n".join(urls))
            return
        if resposta:
            self._start_batch_download(urls, _("batch.multiple_urls").format(count=len(urls)), mode)
        else:
            self._show_batch_selection_window(urls)

    def _show_batch_selection_window(self, urls: list[str]):
        """Mostra janela para selecionar quais de várias URLs baixar."""
        import tkinter as tk

        import customtkinter as ctk

        win = ctk.CTkToplevel(self)
        win.title(_("batch.select_title"))
        win.geometry("620x460")
        win.minsize(500, 350)
        win.transient(self)
        win.after(100, win.grab_set)

        header = ctk.CTkLabel(
            win,
            text=_("batch.select_header").format(count=len(urls)),
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        header.pack(anchor="w", padx=15, pady=(15, 8))

        scroll = ctk.CTkScrollableFrame(win, height=340)
        scroll.pack(fill="both", expand=True, padx=15, pady=(0, 8))

        check_vars = []
        for url in urls:
            var = tk.BooleanVar(value=True)
            check_vars.append((url, var))
            ctk.CTkCheckBox(scroll, text=url, variable=var, font=ctk.CTkFont(size=12)).pack(anchor="w", padx=5, pady=3)

        def on_download():
            selected = [u for u, v in check_vars if v.get()]
            win.destroy()
            if selected:
                self._start_batch_download(
                    selected, _("batch.selection").format(count=len(selected)), self.download_type.get()
                )

        def on_select_all():
            all_on = all(v.get() for _u, v in check_vars)
            for _u, v in check_vars:
                v.set(not all_on)

        btn_frame = ctk.CTkFrame(win, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(btn_frame, text=_("batch.select_all"), width=130, command=on_select_all).pack(side="left")
        ctk.CTkButton(btn_frame, text=_("batch.cancel"), width=100, command=win.destroy).pack(side="right")
        ctk.CTkButton(
            btn_frame,
            text=_("batch.download_selected"),
            width=180,
            command=on_download,
            fg_color="#2b8c3e",
            hover_color="#1e6b30",
        ).pack(side="right", padx=(5, 0))

    # ── Download de vídeo único ────────────────────────────────

    def _start_single_download(self, url):
        if not self.yt_service.is_ffmpeg_available():
            resposta = messagebox.askyesno(
                _("dialog.ffmpeg.title"),
                _("dialog.ffmpeg.body"),
                icon="warning",
            )
            if not resposta:
                return

        tiktok_info = get_content_info(url)
        if tiktok_info["is_tiktok"]:
            self.logger.info("TikTok detectado: %s", tiktok_info["content_type_label"])
            if tiktok_info["quality_tip"]:
                self.logger.info("Dica TikTok: %s", tiktok_info["quality_tip"])

        self.logger.info("Obtendo informacoes para %s", url)

        card = DownloadCard(
            self.downloads_frame,
            title=_("card.getting_info"),
            cancel_callback=None,
        )
        card.pack(fill="x", padx=5, pady=5)

        cancel_event = threading.Event()
        cookies_browser = self._get_cookies_browser()
        mode = self.download_type.get()

        def extract_and_download():
            try:
                info = self.yt_service.extract_info(url, cookies_browser=cookies_browser)
                if not info:
                    self.after(
                        0,
                        lambda: card.update_progress({"status": "error", "status_text": _("card.info_failed")}),
                    )
                    return

                if info.get("entries"):

                    def ask_playlist():
                        resposta = messagebox.askyesno(
                            _("dialog.playlist_detected"),
                            _("dialog.playlist_detected_body"),
                            icon="question",
                        )
                        if resposta:
                            self._handle_playlist(url, selectable=True)
                        card.destroy()

                    self.after(0, ask_playlist)
                    return

                title = info.get("title", _("card.video_fallback"))

                def start_download():
                    card.title_label.configure(text=title)
                    self._start_video_download(url, title, card, cancel_event, cookies_browser, mode)

                self.after(0, start_download)

            except Exception as e:
                self.logger.error("Erro ao extrair info: %s", e)
                info = friendly_error(e)
                self.after(
                    0,
                    lambda i=info: card.update_progress(
                        {
                            "status": "error",
                            "status_text": i["amigavel"],
                        }
                    ),
                )

        thread = threading.Thread(target=extract_and_download, daemon=True)
        thread.start()

        self._cleanup_active_downloads()
        self.active_downloads.append(
            {
                "thread": thread,
                "card": card,
                "cancel_event": cancel_event,
                "url": url,
            }
        )
        self._set_download_active(True)

    def _start_video_download(self, url, title, card, cancel_event, cookies_browser, mode="video"):
        card.cancel_callback = cancel_event.set
        pause_event = threading.Event()

        card.pause_callback = lambda: pause_event.set()
        card.resume_callback = lambda: pause_event.clear()

        _thread, card, cancel_event, pause_event = self._run_download_thread(
            url=url,
            title=title,
            card=card,
            cancel_event=cancel_event,
            pause_event=pause_event,
            cookies_browser=cookies_browser,
            mode=mode,
            track_queue=True,
        )

    def _run_download_thread(
        self,
        url: str,
        title: str,
        card: DownloadCard,
        cancel_event: threading.Event,
        pause_event: threading.Event,
        cookies_browser: str | None,
        mode: str = "video",
        track_queue: bool = False,
    ) -> tuple[threading.Thread, DownloadCard, threading.Event, threading.Event]:
        """Executa o download em thread dedicada, atualizando o card de progresso.

        Retorna (thread, card, cancel_event, pause_event) para permitir
        que o chamador gerencie o ciclo de vida.
        """

        def progress_hook(d):
            self.after(0, lambda: card.update_progress(d))

        def download_thread():
            with self.semaphore:
                try:
                    if track_queue:
                        self._mark_downloading(url)
                    result = self.yt_service.download_video(
                        url=url,
                        output_path=Path(self.download_path.get()),
                        quality=self.quality.get(),
                        fmt=self.format_var.get(),
                        mode=mode,
                        audio_fmt=self.audio_format.get(),
                        subtitles=self.subtitles_var.get(),
                        subtitle_langs=self.subtitle_langs.get(),
                        organize=self.organize_var.get(),
                        progress_hook=progress_hook,
                        cancel_event=cancel_event,
                        pause_event=pause_event,
                        cookies_browser=cookies_browser,
                        proxy=self.proxy,
                        retries=self.retries,
                        socket_timeout=self.socket_timeout,
                        filename_template=self.filename_template,
                        embed_thumbnail=self.embed_thumbnail,
                        write_thumbnail=self.write_thumbnail,
                        limit_speed=self.limit_speed,
                        sponsorblock_enabled=self.sponsorblock_enabled,
                        sponsorblock_categories=self.sponsorblock_categories,
                        concurrent_fragments=self.concurrent_fragments,
                        tiktok_watermark_removal=self.tiktok_watermark_removal,
                    )
                    if result.get("status") == "completed":
                        self.after(0, lambda: card.update_progress({"status": "finished"}))
                        self.after(0, card.disable_pause)
                        self.logger.info("Download concluido: %s", result.get("filename"))
                        if track_queue:
                            self._mark_done(url)
                        add_entry(
                            url=url,
                            title=result.get("title", title),
                            filename=result.get("filename", ""),
                            status="completed",
                            mode=mode,
                            uploader=result.get("uploader", ""),
                        )
                    elif result.get("status") == "cancelled":
                        self.after(0, lambda: card.update_progress({"status": "cancelled"}))
                        self.after(0, card.disable_pause)
                        if track_queue:
                            self._mark_error(url)
                    else:
                        self.after(0, lambda: card.update_progress({"status": "error"}))
                        self.after(0, card.disable_pause)
                        if track_queue:
                            self._mark_error(url)
                        add_entry(
                            url=url,
                            title=title,
                            status="error",
                            mode=mode,
                        )
                except Exception as e:
                    self.logger.error("Erro na thread: %s", e)
                    if track_queue:
                        self._mark_error(url)
                    info = friendly_error(e)
                    self.after(
                        0,
                        lambda i=info: card.update_progress(
                            {
                                "status": "error",
                                "status_text": i["amigavel"],
                            }
                        ),
                    )
                    self.after(0, card.disable_pause)

        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()

        self._cleanup_active_downloads()
        self.active_downloads.append(
            {
                "thread": thread,
                "card": card,
                "cancel_event": cancel_event,
                "pause_event": pause_event,
                "url": url,
            }
        )
        return thread, card, cancel_event, pause_event

    # ── Playlist ───────────────────────────────────────────────

    def _handle_playlist(self, url, selectable=True):
        self.logger.info("Extraindo playlist: %s", url)

        card = DownloadCard(
            self.downloads_frame,
            title=_("card.loading_playlist"),
            cancel_callback=None,
        )
        card.pack(fill="x", padx=5, pady=5)

        cookies_browser = self._get_cookies_browser()
        mode = self.download_type.get()

        def extract_playlist():
            info = self.yt_service.extract_playlist_info(url, cookies_browser=cookies_browser)
            if not info or "entries" not in info:
                self.after(
                    0,
                    lambda: card.update_progress({"status": "error", "status_text": _("card.playlist_failed")}),
                )
                return

            entries = [e for e in info.get("entries", []) if e is not None]
            if not entries:
                self.after(
                    0,
                    lambda: card.update_progress({"status": "error", "status_text": _("card.playlist_empty")}),
                )
                return

            playlist_title = info.get("title", "Playlist")

            def open_ui():
                card.destroy()
                if not selectable:
                    urls = [e["url"] for e in entries if e.get("url")]
                    if not urls:
                        messagebox.showerror(_("dialog.error"), _("dialog.no_valid_url"))
                        return
                    self._start_batch_download(urls, playlist_title, mode)
                else:

                    def on_selection(selected_urls):
                        if selected_urls:
                            self._start_batch_download(selected_urls, playlist_title, mode)

                    PlaylistWindow(self, info, callback=on_selection)

            self.after(0, open_ui)

        thread = threading.Thread(target=extract_playlist, daemon=True)
        thread.start()

    # ── Download em lote (playlist / múltiplas URLs) ───────────

    def _start_batch_download(
        self, urls: list[str], playlist_title: str, mode: str = "video", from_queue: bool = False
    ):
        total = len(urls)
        card = DownloadCard(
            self.downloads_frame,
            title=_("batch.playlist_title").format(title=playlist_title, count=total),
        )
        card.pack(fill="x", padx=5, pady=5)

        cancel_event = threading.Event()
        pause_event = threading.Event()
        cookies_browser = self._get_cookies_browser()

        card.pause_callback = lambda: pause_event.set()
        card.resume_callback = lambda: pause_event.clear()

        if not from_queue:
            for u in urls:
                self._enqueue(u, title="", mode=mode)

        # Controle de concorrência: limita o nº de downloads simultâneos ao valor
        # configurado (max_concurrent_downloads). Cada URL é baixada em sua própria
        # thread com um cartão de progresso próprio, mostrando a barra/% real.
        sem = threading.Semaphore(self.max_concurrent)
        lock = threading.Lock()
        results: dict[str, dict] = {}
        finished_count = [0]  # nº de vídeos finalizados (ok + erro)

        def progress_general(data):
            current = data.get("current", 0) or 0
            total_items = data.get("total", total)
            ok = data.get("ok", 0)
            status = data.get("status", "")
            text = _("batch.progress").format(current=current, total=total_items, ok=ok)
            if status == "completed":
                text += f" {_('history.status_ok')}"
            elif status == "error" or status == "cancelled":
                text += f" {_('history.status_error')}"
            self.after(0, lambda: card.update_progress({"status_text": text, "status": status}))

        def download_one(url, index):
            """Baixa um único vídeo do lote, com seu próprio cartão e progresso real."""
            item_card = DownloadCard(self.downloads_frame, title=_("batch.waiting").format(index=index + 1))
            item_card.pack(fill="x", padx=5, pady=5)
            item_cancel = threading.Event()

            def progress_hook(d):
                # Envia o progresso real (barra, %, velocidade, ETA) ao cartão.
                self.after(0, lambda: item_card.update_progress(d))

            item_card.cancel_callback = item_cancel.set
            item_card.pause_callback = lambda: pause_event.set()
            item_card.resume_callback = lambda: pause_event.clear()

            self.active_downloads.append(
                {
                    "thread": threading.current_thread(),
                    "card": item_card,
                    "cancel_event": item_cancel,
                    "pause_event": pause_event,
                    "url": url,
                }
            )

            with sem:
                try:
                    with lock:
                        current = finished_count[0]
                    progress_general({"current": current + 1, "total": total, "ok": current, "status": "downloading"})

                    self._mark_downloading(url)
                    result = self.yt_service.download_video(
                        url=url,
                        output_path=Path(self.download_path.get()),
                        quality=self.quality.get(),
                        fmt=self.format_var.get(),
                        mode=mode,
                        audio_fmt=self.audio_format.get(),
                        subtitles=self.subtitles_var.get(),
                        subtitle_langs=self.subtitle_langs.get(),
                        organize=self.organize_var.get(),
                        progress_hook=progress_hook,
                        cancel_event=item_cancel if item_cancel.is_set() else cancel_event,
                        pause_event=pause_event,
                        cookies_browser=cookies_browser,
                        proxy=self.proxy,
                        retries=self.retries,
                        socket_timeout=self.socket_timeout,
                        filename_template=self.filename_template,
                        embed_thumbnail=self.embed_thumbnail,
                        write_thumbnail=self.write_thumbnail,
                        limit_speed=self.limit_speed,
                        sponsorblock_enabled=self.sponsorblock_enabled,
                        sponsorblock_categories=self.sponsorblock_categories,
                        concurrent_fragments=self.concurrent_fragments,
                        tiktok_watermark_removal=self.tiktok_watermark_removal,
                    )

                    with lock:
                        results[url] = result
                        finished_count[0] += 1
                        current = finished_count[0]

                    if result.get("status") == "completed":
                        item_card.title_label.configure(
                            text=f"{index + 1}. {result.get('title', _('batch.completed_fallback'))}"
                        )
                        self.after(0, lambda: item_card.update_progress({"status": "finished"}))
                        self.after(0, item_card.disable_pause)
                        self.logger.info("Download concluido: %s", result.get("filename"))
                        self._mark_done(url)
                        add_entry(
                            url=url,
                            title=result.get("title", ""),
                            filename=result.get("filename", ""),
                            status="completed",
                            mode=mode,
                            uploader=result.get("uploader", ""),
                        )
                    elif result.get("status") == "cancelled":
                        self.after(0, lambda: item_card.update_progress({"status": "cancelled"}))
                        self.after(0, item_card.disable_pause)
                        self._mark_error(url)
                    else:
                        self.after(0, lambda: item_card.update_progress({"status": "error"}))
                        self.after(0, item_card.disable_pause)
                        self._mark_error(url)
                        add_entry(
                            url=url,
                            title=result.get("title") or "",
                            status="error",
                            mode=mode,
                        )

                    progress_general(
                        {"current": current, "total": total, "ok": current, "status": result.get("status", "")}
                    )

                except Exception as e:
                    self.logger.error("Erro na thread do lote: %s", e)
                    info = friendly_error(e)
                    self.after(
                        0,
                        lambda i=info: item_card.update_progress({"status": "error", "status_text": i["amigavel"]}),
                    )
                    self.after(0, item_card.disable_pause)
                    self._mark_error(url)
                    with lock:
                        results[url] = {"status": "error", "error": str(e)}
                        finished_count[0] += 1
                        current = finished_count[0]
                    progress_general({"current": current, "total": total, "ok": current, "status": "error"})

        def batch_download():
            try:
                threads = []
                for i, url in enumerate(urls):
                    if cancel_event.is_set():
                        break
                    th = threading.Thread(target=download_one, args=(url, i), daemon=True)
                    threads.append(th)
                    th.start()

                for th in threads:
                    th.join()

                # Estado final no cartão-resumo.
                try:
                    success = sum(1 for r in results.values() if r.get("status") == "completed")
                    erro = len(urls) - success
                    msg = _("batch.summary").format(success=success)
                    if erro:
                        msg = _("batch.summary_errors").format(success=success, total=len(urls), errors=erro)
                    self.after(0, lambda: card.update_progress({"status": "finished", "status_text": msg}))
                    self.after(0, card.disable_pause)
                    self.logger.info("Lote concluido: %d/%d bem-sucedidos", success, len(urls))
                except Exception:
                    pass
            except Exception as e:
                self.logger.error("Erro ao iniciar lote: %s", e)

        thread = threading.Thread(target=batch_download, daemon=True)
        thread.start()
        self._cleanup_active_downloads()
        self.active_downloads.append(
            {
                "thread": thread,
                "card": card,
                "cancel_event": cancel_event,
                "pause_event": pause_event,
            }
        )
        self._set_download_active(True)

    # ── Histórico ──────────────────────────────────────────────

    def _show_history(self):
        """Exibe janela com o historico de downloads."""
        import customtkinter as ctk

        items = get_history(100)
        if not items:
            messagebox.showinfo(_("dialog.history_empty"), _("dialog.history_empty_body"))
            return

        win = ctk.CTkToplevel(self)
        win.title(_("history.title"))
        win.geometry("750x500")
        win.minsize(600, 400)
        win.transient(self)
        win.after(100, win.grab_set)

        win.grid_rowconfigure(0, weight=1)
        win.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(win, label_text=_("history.records").format(count=len(items)))
        scroll.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        for item in items:
            status_icon = _("history.status_ok") if item.get("status") == "completed" else _("history.status_error")
            mode_label = _("history.mode_audio") if item.get("mode") == "audio" else _("history.mode_video")
            ts = item.get("timestamp", "")[:16].replace("T", " ")

            line = f"[{status_icon}] [{mode_label}] {item.get('title', _('history.no_title'))}"
            if item.get("uploader"):
                line += f" - {item['uploader']}"
            line += f"  ({ts})"

            lbl = ctk.CTkLabel(
                scroll,
                text=line,
                font=ctk.CTkFont(size=12),
                anchor="w",
                wraplength=700,
            )
            lbl.pack(anchor="w", padx=5, pady=2)

        ctk.CTkButton(win, text=_("btn.fechar"), command=win.destroy, width=100).grid(row=1, column=0, pady=10)

    def _clear_history(self):
        resposta = messagebox.askyesno(_("dialog.clear_history"), _("dialog.clear_history_body"), icon="warning")
        if resposta:
            clear_history()
            messagebox.showinfo(_("dialog.history_empty"), _("dialog.history_cleared"))

    def _clear_completed_downloads(self):
        """Remove da lista apenas os cartões de downloads concluídos ou com erro."""
        for widget in list(self.downloads_frame.winfo_children()):
            if isinstance(widget, DownloadCard):
                btn_text = widget.cancel_btn.cget("text")
                if btn_text in (_("card.completed"), _("card.error")):
                    widget.destroy()

    # ── Fila persistente ───────────────────────────────────────

    def _restore_pending_queue(self):
        """Ao iniciar, retoma os itens pendentes do último uso (se houver)."""
        pendentes = self.queue.pending()
        self.queue.prune_finished()
        if not pendentes:
            return
        self.after(800, lambda: self._retry_pending_from_queue())

    def _retry_pending_from_queue(self):
        """Reinicia downloads que estavam pendentes no encerramento anterior."""
        items = self.queue.pending()
        urls = [i.get("url") for i in items if i.get("url")]
        if urls:
            mode = items[0].get("mode") or self.download_type.get()
            self.logger.info("Retomando %d download(s) pendente(s) do último uso.", len(urls))
            self._start_batch_download(
                urls,
                _("batch.queue_title").format(count=len(urls)),
                mode,
                from_queue=True,
            )

    def _enqueue(self, url: str, title: str = "", mode: str = "video", metadata: dict | None = None) -> bool:
        """Adiciona à fila persistente. Retorna True se adicionou."""
        return self.queue.add(url, title=title, mode=mode, metadata=metadata) is not None

    def _mark_downloading(self, url: str):
        self.queue.mark_downloading(url)

    def _mark_done(self, url: str):
        self.queue.mark_done(url)

    def _mark_error(self, url: str):
        self.queue.mark_error(url)

    # ── Pausar / Retomar ───────────────────────────────────────

    def _pause_all_downloads(self):
        """Pausa todos os downloads em andamento."""
        self._cleanup_active_downloads()
        self.global_pause_event.set()
        for d in self.active_downloads:
            pe = d.get("pause_event")
            if pe is not None:
                pe.set()
            card = d.get("card")
            if card:
                card.set_paused(True)
        self.logger.info("Todos os downloads pausados.")
        if self.tray:
            self._update_tray_menu()

    def _resume_all_downloads(self):
        """Retoma todos os downloads pausados."""
        self._cleanup_active_downloads()
        self.global_pause_event.clear()
        for d in self.active_downloads:
            pe = d.get("pause_event")
            if pe is not None:
                pe.clear()
            card = d.get("card")
            if card:
                card.set_paused(False)
        self.logger.info("Todos os downloads retomados.")
        if self.tray:
            self._update_tray_menu()

    def _update_tray_menu(self):
        """Atualiza os callbacks do menu da bandeja (sem recriar o menu)."""
        if self.tray and self.tray.available and self.tray._icon is not None:
            paused = self.global_pause_event.is_set()
            self.tray._paused = paused
