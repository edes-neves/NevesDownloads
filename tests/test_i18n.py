"""Testes unitários para app.i18n — módulo de internacionalização."""

from __future__ import annotations

import pytest

from app.i18n import _EN_US, _PT_BR, _TRANSLATIONS, _, get_language, set_language


@pytest.fixture(autouse=True)
def _reset_language():
    """Garante que cada teste comece com pt-BR como idioma padrão."""
    set_language("pt-BR")
    yield
    set_language("pt-BR")


# ── Idioma padrão ─────────────────────────────────────────────


class TestDefaultLanguage:
    """Verifica que o idioma padrão é pt-BR."""

    def test_default_is_pt_br(self):
        assert get_language() == "pt-BR"

    def test_default_menu_file(self):
        assert _("menu.file") == "Arquivo"

    def test_default_subtitle(self):
        assert "simples" in _("subtitle").lower()


# ── set_language / get_language ────────────────────────────────


class TestSetLanguage:
    """Verifica que set_language altera o idioma corretamente."""

    def test_set_pt_br(self):
        set_language("pt-BR")
        assert get_language() == "pt-BR"

    def test_set_en_us(self):
        set_language("en-US")
        assert get_language() == "en-US"

    def test_invalid_falls_back_to_pt_br(self):
        set_language("fr-FR")
        assert get_language() == "pt-BR"

    def test_invalid_empty_string(self):
        set_language("")
        assert get_language() == "pt-BR"

    def test_switch_back_and_forth(self):
        set_language("en-US")
        assert get_language() == "en-US"
        set_language("pt-BR")
        assert get_language() == "pt-BR"
        set_language("en-US")
        assert get_language() == "en-US"


# ── Função _() — tradução ─────────────────────────────────────


class TestTranslation:
    """Verifica que _() retorna a string correta para cada idioma."""

    def test_pt_br_menu(self):
        set_language("pt-BR")
        assert _("menu.file") == "Arquivo"
        assert _("menu.settings") == "Configurações"
        assert _("menu.download") == "Download"
        assert _("menu.edit") == "Editar"
        assert _("menu.view") == "Exibir"
        assert _("menu.help") == "Ajuda"
        assert _("menu.history") == "Historico"

    def test_en_us_menu(self):
        set_language("en-US")
        assert _("menu.file") == "File"
        assert _("menu.settings") == "Settings"
        assert _("menu.download") == "Download"
        assert _("menu.edit") == "Edit"
        assert _("menu.view") == "View"
        assert _("menu.help") == "Help"
        assert _("menu.history") == "History"

    def test_pt_br_buttons(self):
        set_language("pt-BR")
        assert _("btn.save") == "Salvar"
        assert _("btn.cancel") == "Cancelar"
        assert _("btn.close") == "Fechar"
        assert _("btn.start_download") == "INICIAR DOWNLOAD"
        assert _("btn.restore_defaults") == "Restaurar padrões"

    def test_en_us_buttons(self):
        set_language("en-US")
        assert _("btn.save") == "Save"
        assert _("btn.cancel") == "Cancel"
        assert _("btn.close") == "Close"
        assert _("btn.start_download") == "START DOWNLOAD"
        assert _("btn.restore_defaults") == "Restore defaults"

    def test_pt_br_errors(self):
        set_language("pt-BR")
        assert "privado" in _("error.video_privado").lower()
        assert "ffmpeg" in _("error.ffmpeg_nao_encontrado").lower()

    def test_en_us_errors(self):
        set_language("en-US")
        assert "private" in _("error.video_privado").lower()
        assert "ffmpeg" in _("error.ffmpeg_nao_encontrado").lower()

    def test_pt_br_download_card(self):
        set_language("pt-BR")
        assert _("card.pause") == "Pausar"
        assert _("card.resume") == "Retomar"
        assert _("card.cancel") == "Cancelar"
        assert _("card.completed") == "Concluído"
        assert _("card.error") == "Erro"

    def test_en_us_download_card(self):
        set_language("en-US")
        assert _("card.pause") == "Pause"
        assert _("card.resume") == "Resume"
        assert _("card.cancel") == "Cancel"
        assert _("card.completed") == "Completed"
        assert _("card.error") == "Error"


# ── Fallback para chaves inexistentes ─────────────────────────


class TestFallback:
    """Verifica que chaves inexistentes retornam a própria chave."""

    def test_missing_key_returns_key(self):
        assert _("nonexistent.key") == "nonexistent.key"

    def test_missing_key_empty(self):
        assert _("") == ""

    def test_missing_key_random(self):
        assert _("abc123_xyz") == "abc123_xyz"


# ── Strings com formatação ────────────────────────────────────


class TestFormatting:
    """Verifica que strings com .format() funcionam em ambos idiomas."""

    def test_window_title_pt_br(self):
        set_language("pt-BR")
        result = _("window.title").format(name="Test", version="1.0")
        assert result == "Test v1.0"

    def test_window_title_en_us(self):
        set_language("en-US")
        result = _("window.title").format(name="Test", version="1.0")
        assert result == "Test v1.0"

    def test_batch_progress_pt_br(self):
        set_language("pt-BR")
        result = _("batch.progress").format(current=3, total=10, ok=2)
        assert "3" in result
        assert "10" in result
        assert "2" in result

    def test_batch_progress_en_us(self):
        set_language("en-US")
        result = _("batch.progress").format(current=3, total=10, ok=2)
        assert "3" in result
        assert "10" in result
        assert "2" in result

    def test_updater_updated_pt_br(self):
        set_language("pt-BR")
        result = _("updater.updated").format(old="2024.1.1", new="2025.1.1")
        assert "2024.1.1" in result
        assert "2025.1.1" in result

    def test_updater_updated_en_us(self):
        set_language("en-US")
        result = _("updater.updated").format(old="2024.1.1", new="2025.1.1")
        assert "2024.1.1" in result
        assert "2025.1.1" in result

    def test_batch_multiple_urls_pt_br(self):
        set_language("pt-BR")
        result = _("batch.multiple_urls").format(count=5)
        assert "5" in result

    def test_batch_multiple_urls_en_us(self):
        set_language("en-US")
        result = _("batch.multiple_urls").format(count=5)
        assert "5" in result


# ── Completude dos dicionários ────────────────────────────────


class TestDictionaryCompleteness:
    """Verifica que PT_BR e EN_US têm as mesmas chaves."""

    def test_same_keys(self):
        pt_keys = set(_PT_BR.keys())
        en_keys = set(_EN_US.keys())
        assert pt_keys == en_keys, f"Chaves apenas em PT: {pt_keys - en_keys}\nChaves apenas em EN: {en_keys - pt_keys}"

    def test_no_empty_values_pt_br(self):
        for key, val in _PT_BR.items():
            assert val, f"Valor vazio para chave '{key}' em PT-BR"

    def test_no_empty_values_en_us(self):
        for key, val in _EN_US.items():
            assert val, f"Valor vazio para chave '{key}' em EN-US"

    def test_all_keys_are_strings(self):
        for key in _PT_BR:
            assert isinstance(key, str), f"Chave não é string: {key}"
        for key in _EN_US:
            assert isinstance(key, str), f"Chave não é string: {key}"

    def test_translations_dict_has_both_languages(self):
        assert "pt-BR" in _TRANSLATIONS
        assert "en-US" in _TRANSLATIONS

    def test_translations_match_dictionaries(self):
        assert _TRANSLATIONS["pt-BR"] is _PT_BR
        assert _TRANSLATIONS["en-US"] is _EN_US

    def test_total_keys_reasonable(self):
        """Garante que temos um número razoável de chaves (regressão)."""
        assert len(_PT_BR) >= 150, f"Poucas chaves em PT-BR: {len(_PT_BR)}"
        assert len(_EN_US) >= 150, f"Poucas chaves em EN-US: {len(_EN_US)}"

    def test_format_placeholders_match(self):
        """Verifica que chaves com placeholders .format() existem em ambos idiomas."""
        import re

        placeholder_re = re.compile(r"\{(\w+)\}")
        mismatched = []
        for key in _PT_BR:
            pt_placeholders = set(placeholder_re.findall(_PT_BR[key]))
            en_placeholders = set(placeholder_re.findall(_EN_US.get(key, "")))
            if pt_placeholders != en_placeholders:
                mismatched.append(key)
        assert not mismatched, f"Placeholders .format() inconsistentes entre PT e EN: {mismatched}"
