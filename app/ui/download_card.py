import customtkinter as ctk

from app.i18n import _


class DownloadCard(ctk.CTkFrame):
    """
    Cartão que exibe o progresso de um download individual.
    """

    def __init__(
        self,
        master,
        title: str | None = None,
        cancel_callback=None,
        pause_callback=None,
        resume_callback=None,
        **kwargs,
    ):
        super().__init__(master, corner_radius=8, border_width=0, **kwargs)
        self.title = title or _("card.preparing")
        self.cancel_callback = cancel_callback
        self.pause_callback = pause_callback
        self.resume_callback = resume_callback
        self.cancelled = False
        self._paused = False

        # Configuração do layout interno
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=0)

        # Título
        self.title_label = ctk.CTkLabel(self, text=self.title, font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        self.title_label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(8, 2))

        # Barra de progresso
        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal", height=12)
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(2, 2))
        self.progress_bar.set(0.0)

        # Detalhes: porcentagem, velocidade, tamanho, ETA
        self.info_label = ctk.CTkLabel(self, text="0%  0 MB/s  0 MB  ETA: --", font=ctk.CTkFont(size=12))
        self.info_label.grid(row=2, column=0, sticky="w", padx=10, pady=(2, 8))

        # Frame para os botões (pausar + cancelar) no canto direito
        self.btn_anchor = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_anchor.grid(row=2, column=1, sticky="e", padx=10, pady=(2, 8))

        # Botão pausar/retomar
        self.pause_btn = ctk.CTkButton(
            self.btn_anchor,
            text=_("card.pause"),
            width=60,
            height=25,
            font=ctk.CTkFont(size=11),
            command=self._on_pause,
            fg_color="#2b6b8c",
            hover_color="#1e4f6b",
        )
        self.pause_btn.pack(side="left", padx=(0, 5))

        # Botão cancelar
        self.cancel_btn = ctk.CTkButton(
            self.btn_anchor,
            text=_("card.cancel"),
            width=70,
            height=25,
            font=ctk.CTkFont(size=11),
            command=self._on_cancel,
            fg_color="#b02b2b",
            hover_color="#7a1f1f",
        )
        self.cancel_btn.pack(side="left")

        # Armazenar última atualização para cálculos
        self.last_update: dict[str, float] = {}

    def _on_cancel(self):
        """Callback do botão cancelar."""
        self.cancelled = True
        if self.cancel_callback:
            self.cancel_callback()
        self.cancel_btn.configure(state="disabled", text=_("card.cancelling"))

    def _on_pause(self):
        """Callback do botão pausar/retomar."""
        if self._paused:
            self.set_paused(False)
            if self.resume_callback:
                self.resume_callback()
        else:
            self.set_paused(True)
            if self.pause_callback:
                self.pause_callback()

    def set_paused(self, paused: bool):
        """Atualiza o estado visual de pausa."""
        self._paused = paused
        if paused:
            self.pause_btn.configure(text=_("card.resume"), fg_color="#8c6b2b", hover_color="#6b4f1e")
        else:
            self.pause_btn.configure(text=_("card.pause"), fg_color="#2b6b8c", hover_color="#1e4f6b")

    def set_resumed(self):
        """Força o estado de retomada visual."""
        self.set_paused(False)

    def disable_pause(self):
        """Desabilita o botão pausar (ex.: download concluído)."""
        self.pause_btn.configure(state="disabled")

    def update_progress(self, data: dict):
        """
        Atualiza a interface com os dados de progresso.
        Se 'status_text' estiver presente, exibe-o diretamente na info_label.
        Caso contrário, exibe os detalhes do progresso (porcentagem, velocidade, etc.).
        """
        if self.cancelled:
            return

        # Se houver texto de status personalizado, usa-o e retorna (não atualiza barra)
        if "status_text" in data:
            self.info_label.configure(text=data["status_text"])
            # Atualiza também status final se houver
            if data.get("status") == "finished":
                self.progress_bar.set(1.0)
                self.cancel_btn.configure(state="disabled", text=_("card.completed"))
            elif data.get("status") in ("error", "cancelled"):
                self.cancel_btn.configure(state="disabled", text=_("card.error"))
            return

        # Caso contrário, processa normalmente
        pct = 0.0
        if "total_bytes" in data and data["total_bytes"] > 0:
            pct = data.get("downloaded_bytes", 0) / data["total_bytes"]
        elif "total_bytes_estimate" in data and data["total_bytes_estimate"] > 0:
            pct = data.get("downloaded_bytes", 0) / data["total_bytes_estimate"]
        self.progress_bar.set(pct)

        parts = []
        # Porcentagem
        parts.append(f"{int(pct * 100)}%")

        # Velocidade
        speed = data.get("speed", 0)
        if speed:
            if speed > 1024 * 1024:
                speed_str = f"{speed / (1024 * 1024):.1f} MB/s"
            elif speed > 1024:
                speed_str = f"{speed / 1024:.1f} KB/s"
            else:
                speed_str = f"{speed:.0f} B/s"
            parts.append(speed_str)
        else:
            parts.append("0 MB/s")

        # Tamanho baixado / total
        downloaded = data.get("downloaded_bytes", 0)
        total = data.get("total_bytes") or data.get("total_bytes_estimate", 0)
        if total > 0:
            downloaded_str = self._format_size(downloaded)
            total_str = self._format_size(total)
            parts.append(f"{downloaded_str} / {total_str}")
        else:
            parts.append(self._format_size(downloaded))

        # ETA
        eta = data.get("eta", 0)
        if eta and eta > 0:
            hours = eta // 3600
            minutes = (eta % 3600) // 60
            seconds = eta % 60
            if hours > 0:
                eta_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                eta_str = f"{minutes:02d}:{seconds:02d}"
            parts.append(f"ETA: {eta_str}")
        else:
            parts.append("ETA: --")

        self.info_label.configure(text="  ".join(parts))

        # Atualizar status final
        if data.get("status") == "finished":
            self.progress_bar.set(1.0)
            self.cancel_btn.configure(state="disabled", text=_("card.completed"))
        elif data.get("status") in ("error", "cancelled"):
            self.cancel_btn.configure(state="disabled", text=_("card.error"))

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Formata bytes para string legível."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
