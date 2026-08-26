from pathlib import Path
from tkinter import ttk

import customtkinter as ctk

from app.i18n import _


class FolderBrowser(ctk.CTkToplevel):
    """
    Diálogo de seleção de pasta que oculta pastas ocultas (que começam com '.').
    """

    def __init__(self, master, initial_path: str = "", title: str | None = None):
        super().__init__(master)
        self.title(title or _("folder.title"))
        self.geometry("550x480")
        self.minsize(480, 400)
        self.transient(master)
        self.after(100, self.grab_set)

        self.result_path: str | None = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Barra de caminho ──
        path_frame = ctk.CTkFrame(self, fg_color="transparent")
        path_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15, 5))
        path_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(path_frame, text=_("folder.label"), font=ctk.CTkFont(size=13)).grid(row=0, column=0, padx=(0, 8))

        self.path_var = ctk.StringVar(value=initial_path or str(Path.home()))
        self.path_entry = ctk.CTkEntry(path_frame, textvariable=self.path_var, height=32, font=ctk.CTkFont(size=13))
        self.path_entry.grid(row=0, column=1, sticky="ew")

        # ── Lista de pastas (ttk.Treeview) ──
        style = ttk.Style()
        style.configure("Folder.Treeview", rowheight=28, font=("sans-serif", 12))
        style.configure("Folder.Treeview.Heading", font=("sans-serif", 12, "bold"))

        tree_frame = ctk.CTkFrame(self)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse", style="Folder.Treeview")
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # ── Barra inferior ──
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 15))

        ctk.CTkButton(btn_frame, text=_("folder.back"), width=80, command=self._go_up).pack(side="left")

        ctk.CTkButton(
            btn_frame,
            text=_("folder.save"),
            width=100,
            fg_color="#2b8c3e",
            hover_color="#1e6b30",
            command=self._on_select,
        ).pack(side="right", padx=(5, 0))

        ctk.CTkButton(btn_frame, text=_("folder.cancel"), width=80, command=self.destroy).pack(side="right")

        # ── Eventos ──
        self.tree.bind("<Double-1>", self._on_double_click)
        self.path_entry.bind("<Return>", lambda e: self._navigate_to_entry())

        # ── Navegar para o caminho inicial ──
        start = Path(initial_path) if initial_path else Path.home()
        if not start.is_dir():
            start = Path.home()
        self._navigate(start)

    def _navigate(self, folder: Path):
        """Lista as subpastas visíveis (sem ocultas) de uma pasta."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.path_var.set(str(folder))

        try:
            entries = sorted(folder.iterdir(), key=lambda p: p.name.lower())
        except PermissionError:
            return

        for entry in entries:
            if entry.is_dir() and not entry.name.startswith("."):
                self.tree.insert("", "end", iid=str(entry), text=f"  {entry.name}")

    def _on_double_click(self, event):
        """Ao duplo-clique, entra na pasta selecionada."""
        sel = self.tree.selection()
        if sel:
            self._navigate(Path(sel[0]))

    def _go_up(self):
        """Volta para a pasta pai."""
        current = Path(self.path_var.get())
        parent = current.parent
        if parent != current:
            self._navigate(parent)

    def _navigate_to_entry(self):
        """Navega para o caminho digitado na barra."""
        text = self.path_var.get().strip()
        p = Path(text)
        if p.is_dir():
            self._navigate(p)

    def _on_select(self):
        """Confirma a seleção."""
        self.result_path = self.path_var.get().strip()
        self.destroy()
