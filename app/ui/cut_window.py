"""
Janela para cortar um trecho de vídeo/áudio já baixado (FFmpeg).

O usuário escolhe o arquivo e informa início/fim (HH:MM:SS); o corte roda em
thread dedicada (remux rápido por padrão) e o resultado é avisado via toast +
notificação do sistema.
"""

from __future__ import annotations

import contextlib
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from app.i18n import _
from app.services.media_editor import (
    _locate_ffmpeg,
    cut_media,
    get_media_duration,
    make_cut_output,
    parse_timestamp,
)
from app.services.notifications import notify_system

_MEDIA_FILETYPES = (
    (
        _("cut.filetype"),
        "*.mp4 *.mkv *.webm *.avi *.mov *.m4v *.mp3 *.m4a *.aac *.ogg *.opus *.wav *.flac",
    ),
    (_("cut.all_files"), "*.*"),
)


def _format_duration_label(seconds: float | None) -> str:
    """Formata duração legível (ou '--' quando desconhecida)."""
    if seconds is None:
        return "--"
    hours = int(seconds // 3600)
    minutes = int(seconds % 3600 // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class CutFileWindow(ctk.CTkToplevel):
    """Janela modal de corte de um trecho do arquivo selecionado."""

    def __init__(self, parent, initial_file: str | None = None):
        super().__init__(parent)
        self._app = parent
        self._ffmpeg = _locate_ffmpeg()
        self._duration: float | None = None
        self._busy = False

        self.title(_("cut.title"))
        self.geometry("560x340")
        self.resizable(False, False)
        self.transient(parent)
        self.after(100, self.grab_set)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.cancel_event = threading.Event()
        self._destroyed = False

        self.grid_columnconfigure(1, weight=1)

        self._path_var = ctk.StringVar()
        self._start_var = ctk.StringVar()
        self._end_var = ctk.StringVar()

        self._build_widgets()

        if initial_file:
            self._set_file(initial_file)

    def _build_widgets(self):
        padx = 12
        pady = 6

        # ── Arquivo ──
        ctk.CTkLabel(self, text=_("cut.file"), anchor="w").grid(row=0, column=0, sticky="w", padx=padx, pady=pady)
        entry = ctk.CTkEntry(self, textvariable=self._path_var, height=30, state="readonly")
        entry.grid(row=0, column=1, sticky="ew", padx=padx, pady=pady)
        ctk.CTkButton(
            self,
            text=_("cut.browse"),
            width=100,
            height=30,
            font=ctk.CTkFont(size=12),
            command=self._browse,
        ).grid(row=0, column=2, sticky="e", padx=(0, padx), pady=pady)

        # ── Duração ──
        self._duration_label = ctk.CTkLabel(
            self,
            text=_("cut.duration").format(duration="--"),
            anchor="w",
            font=ctk.CTkFont(size=12),
        )
        self._duration_label.grid(row=1, column=0, columnspan=3, sticky="w", padx=padx, pady=(2, pady))

        # ── Início / Fim ──
        ctk.CTkLabel(self, text=_("cut.range"), anchor="w").grid(row=2, column=0, sticky="w", padx=padx, pady=pady)
        start = ctk.CTkEntry(self, textvariable=self._start_var, height=30, width=140, placeholder_text="HH:MM:SS")
        start.grid(row=2, column=1, sticky="w", padx=padx, pady=pady)
        end = ctk.CTkEntry(self, textvariable=self._end_var, height=30, width=140, placeholder_text="HH:MM:SS")
        end.grid(row=2, column=2, sticky="w", padx=(0, padx), pady=pady)

        ctk.CTkLabel(
            self,
            text=_("cut.end_hint"),
            anchor="w",
            font=ctk.CTkFont(size=11),
        ).grid(row=3, column=1, columnspan=2, sticky="w", padx=padx, pady=(0, 4))

        # ── Saída ──
        self._output_label = ctk.CTkLabel(self, text="", anchor="w", wraplength=520)
        self._output_label.grid(row=4, column=0, columnspan=3, sticky="w", padx=padx, pady=pady)

        # ── Status ──
        self._status_label = ctk.CTkLabel(self, text="", anchor="w", wraplength=520)
        self._status_label.grid(row=5, column=0, columnspan=3, sticky="w", padx=padx, pady=pady)

        if not self._ffmpeg:
            self._set_status(_("cut.no_ffmpeg"), error=True)

        # ── Ações ──
        self._cut_btn = ctk.CTkButton(
            self,
            text=_("cut.cut"),
            height=32,
            font=ctk.CTkFont(size=13),
            command=self._on_cut,
            fg_color="#1f7f4d",
            hover_color="#166039",
        )
        self._cut_btn.grid(row=6, column=1, sticky="e", padx=padx, pady=(8, padx))
        ctk.CTkButton(
            self,
            text=_("btn.close"),
            height=32,
            font=ctk.CTkFont(size=13),
            command=self._on_close,
        ).grid(row=6, column=2, sticky="w", padx=(0, padx), pady=(8, padx))

    # ── Helpers ────────────────────────────────────────────────

    def _set_status(self, text: str, error: bool = False):
        self._status_label.configure(text=text, text_color="#d9534f" if error else "")

    def _set_file(self, path: str):
        """Define o arquivo a cortar e atualiza duração/saída."""
        if not path or not Path(path).is_file():
            self._set_status(_("cut.no_file"), error=True)
            return
        self._path_var.set(path)
        self._duration = get_media_duration(path, ffmpeg_location=self._ffmpeg)
        self._duration_label.configure(text=_("cut.duration").format(duration=_format_duration_label(self._duration)))
        self._output_label.configure(text=_("cut.output").format(path=make_cut_output(path)))
        self._set_status("")

    def _browse(self):
        path = filedialog.askopenfilename(parent=self, title=_("cut.browse_title"), filetypes=_MEDIA_FILETYPES)
        if not path:
            return
        self._set_file(path)

    def _on_close(self):
        self.cancel_event.set()
        self._destroyed = True
        self.destroy()

    def _validate(self) -> tuple[float, float | None]:
        """Valida as entradas. Levanta ValueError com mensagem i18n no erro."""
        path = self._path_var.get().strip()
        if not path:
            raise ValueError(_("cut.no_file"))
        if not self._ffmpeg:
            raise ValueError(_("cut.no_ffmpeg"))

        try:
            start = parse_timestamp(self._start_var.get())
            end: float | None = None
            if self._end_var.get().strip():
                end = parse_timestamp(self._end_var.get())
        except ValueError:
            raise ValueError(_("cut.invalid_time")) from None

        if self._duration is not None:
            if start >= self._duration:
                raise ValueError(_("cut.start_gte_duration"))
            if end is not None and end > self._duration:
                end = self._duration
        if end is not None and end <= start:
            raise ValueError(_("cut.end_lt_start"))
        return start, end

    def _on_cut(self):
        if self._busy:
            return
        try:
            start, end = self._validate()
        except ValueError as exc:
            self._set_status(str(exc), error=True)
            return

        path = self._path_var.get().strip()
        output_path = make_cut_output(path)
        self._busy = True
        self._cut_btn.configure(state="disabled", text=_("cut.working"))
        self._set_status(_("cut.working"))

        def worker():
            result = cut_media(
                path,
                output_path,
                start,
                end=end,
                ffmpeg_location=self._ffmpeg,
                cancel_event=self.cancel_event,
            )
            if not self._destroyed:
                self.after(0, lambda: self._on_cut_done(result))

        threading.Thread(target=worker, daemon=True).start()

    def _on_cut_done(self, result: dict):
        if self._destroyed:
            return
        self._busy = False
        self._cut_btn.configure(state="normal", text=_("cut.cut"))

        if result.get("status") == "completed":
            output = result.get("output", "")
            self._app.logger.info("Corte concluído: %s", output)
            with contextlib.suppress(Exception):
                self._app._show_toast(_("cut.toast_done").format(Path(output).name))
            if getattr(self._app, "notifications_enabled", True):
                notify_system(title=_("cut.system_title"), message=_("cut.system_done").format(path=output))
            self.destroy()
            return

        if result.get("status") == "cancelled":
            self._set_status(_("cut.cancelled"), error=True)
            return

        self._app.logger.error("Falha ao cortar: %s", result.get("error"))
        self._set_status(_("cut.error").format(error=result.get("error", "")), error=True)
