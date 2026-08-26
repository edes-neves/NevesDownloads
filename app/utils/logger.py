import logging
import sys

from app.utils.paths import get_logs_dir


def setup_logger(name: str = "neves_downloads") -> logging.Logger:
    """
    Configura e retorna um logger com saída para console e arquivo.
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

    # Handler para arquivo (logs diários)
    logs_dir = get_logs_dir()
    log_file = logs_dir / "app.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
