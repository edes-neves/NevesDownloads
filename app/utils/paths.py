from pathlib import Path


def get_app_data_dir() -> Path:
    """Retorna o diretório de dados da aplicação (cria se não existir)."""
    home = Path.home()
    # Usa .neves_downloads na home do usuário (cross-platform)
    app_dir = home / ".neves_downloads"
    app_dir.mkdir(exist_ok=True)
    return app_dir


def get_logs_dir() -> Path:
    """Retorna o diretório de logs."""
    logs_dir = get_app_data_dir() / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def get_default_download_folder() -> Path:
    """Retorna a pasta padrão de downloads do sistema."""
    home = Path.home()
    downloads = home / "Downloads"
    if downloads.exists():
        return downloads
    return home


def ensure_directories():
    """Garante que todos os diretórios necessários existam."""
    get_app_data_dir()
    get_logs_dir()
    # Outros diretórios podem ser criados aqui
