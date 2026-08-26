import logging
import logging.handlers
import sys

from app.utils.paths import get_logs_dir

# Tamanho máximo de cada arquivo de log (5 MB)
_MAX_BYTES = 5 * 1024 * 1024
# Número de arquivos de backup a manter
_BACKUP_COUNT = 5


def setup_logger(name: str = "neves_downloads") -> logging.Logger:
    """Configura e retorna um logger com saída para console e arquivo.

    O handler de arquivo usa ``RotatingFileHandler`` para limitar o
    tamanho de cada arquivo a 5 MB e manter no máximo 5 backups.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Evitar duplicação de handlers
    if logger.handlers:
        return logger

    # Formato
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler para console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para arquivo com rotação por tamanho
    logs_dir = get_logs_dir()
    log_file = logs_dir / "app.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
