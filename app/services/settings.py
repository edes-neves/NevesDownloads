import json
import logging
from typing import Any

from app.core.settings_schema import SETTINGS_DEFAULTS, SETTINGS_TYPE_BOOL, SETTINGS_TYPE_INT, SETTINGS_VALID_VALUES
from app.utils.paths import get_app_data_dir

logger = logging.getLogger("neves_downloads")

CONFIG_FILE = get_app_data_dir() / "config.json"


def _sanitize(key: str, value: Any) -> Any:
    """Normaliza o valor conforme o tipo esperado (evita corromper o config)."""
    if key not in SETTINGS_DEFAULTS:
        return value

    # Validação para campos do tipo seleção
    if key in SETTINGS_VALID_VALUES:
        if value not in SETTINGS_VALID_VALUES[key]:
            return SETTINGS_DEFAULTS[key]
        return value

    # Validação para booleanos
    if key in SETTINGS_TYPE_BOOL:
        return bool(value)

    # Validação para inteiros
    if key in SETTINGS_TYPE_INT:
        try:
            return int(value)
        except (TypeError, ValueError):
            return SETTINGS_DEFAULTS[key]

    # Strings gerais
    if value is None:
        return SETTINGS_DEFAULTS[key]
    return value


def load(key: str | None = None) -> Any:
    config = _read()
    if key is None:
        return config
    return config.get(key, SETTINGS_DEFAULTS.get(key))


def save(key: str, value: Any):
    config = _read()
    config[key] = _sanitize(key, value)
    _write(config)


def load_all() -> dict:
    """Retorna o dicionário completo de configurações já sanado."""
    return _read()


def reset_to_defaults():
    """Restaura todas as configurações para os valores padrão."""
    _write(dict(SETTINGS_DEFAULTS))
    logger.info("Configurações restauradas para os padrões.")


def _read() -> dict:
    if not CONFIG_FILE.exists():
        return dict(SETTINGS_DEFAULTS)
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            data = json.load(f)
            # Mescla defaults e sana valores inválidos
            merged = {}
            for k, v in SETTINGS_DEFAULTS.items():
                if k in data:
                    merged[k] = _sanitize(k, data[k])
                else:
                    merged[k] = v
            return merged
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Erro ao ler config: {e}")
        return dict(SETTINGS_DEFAULTS)


def _write(config: dict):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except OSError as e:
        logger.error(f"Erro ao salvar config: {e}")
