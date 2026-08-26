"""Exceções de domínio da aplicação."""


class DownloadCancelledError(Exception):
    """Levantada para interromper um download em andamento."""
