"""Toast (notificação in-app) exibido no canto inferior direito da tela."""

import contextlib

import customtkinter as ctk

_ACTIVE: list = []


def _fade(top, alpha: float, duration_ms: int):
    """Anima o fade-in/out do toast e o destrói ao final."""
    step = 0.18 if alpha < 1.0 else -0.18
    alpha = max(0.0, min(1.0, alpha + step))
    try:
        top.attributes("-alpha", alpha)
    except Exception:
        # Janela já destruída (ou sem suporte a alpha) — encerra o toast.
        with contextlib.suppress(Exception):
            top.destroy()
        return
    if alpha >= 1.0:
        top.after(duration_ms, lambda: _fade(top, alpha, duration_ms))
    elif alpha <= 0.0:
        with contextlib.suppress(Exception):
            top.destroy()
    else:
        top.after(25, lambda: _fade(top, alpha, duration_ms))


def show_toast(parent, message: str, kind: str = "ok", duration_ms: int = 4500) -> None:
    """Exibe um toast informativo no canto inferior direito.

    ``kind`` pode ser ``"ok"`` (verde) ou ``"error"`` (vermelho).
    """
    try:
        root = parent.winfo_toplevel()
    except Exception:
        return

    top = ctk.CTkToplevel(root)
    top.overrideredirect(True)
    with contextlib.suppress(Exception):
        top.attributes("-topmost", True)

    width, height = 360, 84
    with contextlib.suppress(Exception):
        x = top.winfo_screenwidth() - width - 25
        y = top.winfo_screenheight() - height - 60
        top.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

    frame = ctk.CTkFrame(
        top,
        fg_color="#1e6b30" if kind == "ok" else "#7a1f1f",
        corner_radius=12,
    )
    frame.pack(fill="both", expand=True)

    ctk.CTkLabel(
        frame,
        text=message,
        font=ctk.CTkFont(size=13),
        text_color="#ffffff",
        justify="left",
        anchor="w",
        wraplength=320,
    ).pack(fill="both", expand=True, padx=14, pady=12)

    with contextlib.suppress(Exception):
        top.attributes("-alpha", 0.0)

    _ACTIVE.append(top)
    top.after(50, lambda: _fade(top, 0.0, duration_ms))


def dismiss_all() -> None:
    """Fecha todos os toasts abertos (usado no encerramento da janela)."""
    for top in list(_ACTIVE):
        with contextlib.suppress(Exception):
            top.destroy()
    _ACTIVE.clear()
