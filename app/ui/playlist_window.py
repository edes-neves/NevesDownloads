from tkinter import messagebox
from typing import Any

import customtkinter as ctk

from app.i18n import _


class PlaylistWindow(ctk.CTkToplevel):
    """
    Janela modal para exibir vídeos de uma playlist e permitir seleção.
    """

    def __init__(self, master, playlist_info: dict[str, Any], callback=None):
        super().__init__(master)
        self.title(_("playlist.title"))
        self.geometry("700x500")
        self.minsize(600, 400)
        self.transient(master)
        self.after(100, self.grab_set)  # modal - adiado para garantir que a janela está visível

        self.playlist_info = playlist_info
        self.callback = callback
        self.selected_urls: list[str] = []

        # Configura layout
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_columnconfigure(0, weight=1)

        # Cabeçalho
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header.grid_columnconfigure(1, weight=1)

        playlist_title = playlist_info.get("title", "Playlist")
        count = len(playlist_info.get("entries", []))
        ctk.CTkLabel(
            header,
            text=_("playlist.header").format(title=playlist_title),
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text=_("playlist.count").format(count=count),
            font=ctk.CTkFont(size=13),
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Frame com lista rolável
        self.list_frame = ctk.CTkScrollableFrame(self, label_text=_("playlist.videos_label"))
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Variáveis de checkboxes
        self.check_vars = []
        self._filtered_entries = []
        for entry in playlist_info.get("entries", []):
            if entry is None:
                continue
            self._filtered_entries.append(entry)
            title = entry.get("title", _("playlist.untitled"))
            duration = entry.get("duration", 0)
            if duration:
                minutes = duration // 60
                seconds = duration % 60
                duration_str = f"{minutes:02d}:{seconds:02d}"
            else:
                duration_str = "??:??"

            var = ctk.IntVar(value=1)  # marcado por padrão
            cb = ctk.CTkCheckBox(
                self.list_frame, text=f"{title} ({duration_str})", variable=var, font=ctk.CTkFont(size=13)
            )
            cb.pack(anchor="w", pady=2)
            self.check_vars.append(var)

        # Botões de ação
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        btn_frame.grid_columnconfigure(2, weight=1)
        btn_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkButton(btn_frame, text=_("playlist.select_all"), width=120, command=self._select_all).grid(
            row=0, column=0, padx=5
        )

        ctk.CTkButton(btn_frame, text=_("playlist.deselect_all"), width=120, command=self._deselect_all).grid(
            row=0, column=1, padx=5
        )

        ctk.CTkButton(
            btn_frame,
            text=_("playlist.download_selected"),
            width=140,
            command=self._confirm,
            fg_color="#2b8c3e",
            hover_color="#1e6b30",
        ).grid(row=0, column=2, padx=5)

        ctk.CTkButton(btn_frame, text=_("playlist.cancel"), width=100, command=self.destroy).grid(
            row=0, column=3, padx=5
        )

    def _select_all(self):
        for var in self.check_vars:
            var.set(1)

    def _deselect_all(self):
        for var in self.check_vars:
            var.set(0)

    def _confirm(self):
        # Coleta URLs selecionadas
        selected = []
        for idx, var in enumerate(self.check_vars):
            if var.get() == 1:
                entry = self._filtered_entries[idx]
                if entry.get("url"):
                    selected.append(entry["url"])
        if not selected:
            messagebox.showwarning(_("playlist.none_selected"), _("playlist.none_selected_body"))
            return
        self.selected_urls = selected
        if self.callback:
            self.callback(selected)
        self.destroy()
