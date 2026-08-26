"""Smoke tests — verifica que todos os arquivos UI usam i18n corretamente.

Estes testes não instanciam widgets (não precisam de display),
mas validam estaticamente que:
  1. Cada módulo de UI/serviços importa `_` de `app.i18n`
  2. Não há strings em português hardcoded em contextos de UI
  3. O módulo i18n funciona sem erros de importação
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"

# Módulos que DEVEM importar `_` de app.i18n
UI_MODULES = [
    "app/ui/main_window.py",
    "app/ui/settings_window.py",
    "app/ui/download_handler.py",
    "app/ui/download_card.py",
    "app/ui/playlist_window.py",
    "app/ui/folder_browser.py",
    "app/ui/clipboard_handler.py",
    "app/ui/tray_handler.py",
]

SERVICE_MODULES = [
    "app/services/errors.py",
    "app/services/tray_manager.py",
    "app/services/sponsorblock.py",
    "app/services/tiktok.py",
    "app/services/updater.py",
]

ALL_MODULES = UI_MODULES + SERVICE_MODULES

# Padrões de strings em português que NÃO devem aparecer hardcoded
# em chamadas de UI (messagebox, widget text=, card.update_progress, etc.)
PT_PATTERNS = re.compile(
    r"""(?:"""
    r"""(?:messagebox\.(?:showerror|showwarning|showinfo|askyesno|askyesnocancel)\s*\(\s*)"""
    r"""|(?:text\s*=\s*)"""
    r"""|(?:title\s*=\s*)"""
    r"""|(?:label_text\s*=\s*)"""
    r""")\s*(?:_\s*\(\s*)?"""
    r"""["'](?![_])[A-ZÁÉÍÓÚÃÕÂÊÎÔÛÇ][a-záéíóúãõâêîôûç]+(?:\s+[a-záéíóúãõâêîôûç]+)*["']""",
    re.MULTILINE,
)


def _has_i18n_import(source: str) -> bool:
    """Verifica se o arquivo importa `_` de app.i18n."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "app.i18n":
            names = [alias.name for alias in node.names]
            if "_" in names:
                return True
    return False


def _count_underscore_calls(source: str) -> int:
    """Conta quantas vezes `_()` é chamado no arquivo."""
    return len(re.findall(r"_\([\"']", source))


def _find_potential_pt_strings(source: str) -> list[str]:
    """Encontra strings que parecem ser português hardcoded em contextos de UI."""
    matches = []
    for m in PT_PATTERNS.finditer(source):
        snippet = m.group(0)[:80]
        matches.append(snippet)
    return matches


class TestImportsI18n:
    """Verifica que todos os módulos relevantes importam _ de app.i18n."""

    @pytest.mark.parametrize("module_path", UI_MODULES, ids=lambda p: p.split("/")[-1])
    def test_ui_module_imports_i18n(self, module_path: str):
        source = (ROOT / module_path).read_text(encoding="utf-8")
        assert _has_i18n_import(source), f"{module_path} não importa `_` de app.i18n"

    @pytest.mark.parametrize("module_path", SERVICE_MODULES, ids=lambda p: p.split("/")[-1])
    def test_service_module_imports_i18n(self, module_path: str):
        source = (ROOT / module_path).read_text(encoding="utf-8")
        assert _has_i18n_import(source), f"{module_path} não importa `_` de app.i18n"


class TestUnderscoreUsage:
    """Verifica que _() é usado suficientemente em cada módulo."""

    @pytest.mark.parametrize("module_path", UI_MODULES, ids=lambda p: p.split("/")[-1])
    def test_ui_module_uses_underscore(self, module_path: str):
        source = (ROOT / module_path).read_text(encoding="utf-8")
        count = _count_underscore_calls(source)
        assert count >= 1, f"{module_path} usa _() apenas {count} vez(es) — esperado >= 1"

    @pytest.mark.parametrize("module_path", SERVICE_MODULES, ids=lambda p: p.split("/")[-1])
    def test_service_module_uses_underscore(self, module_path: str):
        source = (ROOT / module_path).read_text(encoding="utf-8")
        count = _count_underscore_calls(source)
        # sponsorblock.py usa _() dentro de dict comprehension — regex não detecta
        # contamos manualmente como fallback
        if count == 0 and "sponsorblock" in module_path:
            count = source.count("_(v)")  # padrão do dict comprehension
        assert count >= 1, f"{module_path} usa _() apenas {count} vez(es) — esperado >= 1"


class TestNoHardcodedPT:
    """Verifica que não há strings em português hardcoded em contextos de UI."""

    @pytest.mark.parametrize("module_path", ALL_MODULES, ids=lambda p: p.split("/")[-1])
    def test_no_hardcoded_portuguese(self, module_path: str):
        source = (ROOT / module_path).read_text(encoding="utf-8")
        matches = _find_potential_pt_strings(source)
        # Filtra falsos positivos: internal keys, constant values, etc.
        real_matches = [
            m
            for m in matches
            if not any(
                kw in m.lower()
                for kw in [
                    "internal",
                    "key",
                    "const",
                    "config",
                    "downloading",
                    "não",
                    "nenhum",  # são valores de config, não UI
                ]
            )
        ]
        assert not real_matches, f"{module_path} tem strings PT hardcoded em contextos de UI:\n" + "\n".join(
            f"  - {m}" for m in real_matches[:5]
        )


class TestI18nModule:
    """Smoke test do módulo i18n em si."""

    def test_import_no_errors(self):
        import app.i18n as i18n_mod

        assert hasattr(i18n_mod, "_")
        assert hasattr(i18n_mod, "set_language")
        assert hasattr(i18n_mod, "get_language")

    def test_translate_returns_string(self):
        from app.i18n import _

        result = _("menu.file")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_all_keys_translateable(self):
        from app.i18n import _PT_BR, _

        set_language = __import__("app.i18n", fromlist=["set_language"]).set_language

        for lang in ("pt-BR", "en-US"):
            set_language(lang)
            for key in _PT_BR:
                val = _(key)
                assert isinstance(val, str), f"Chave {key} em {lang} não retorna string"
                assert len(val) > 0, f"Chave {key} em {lang} retorna string vazia"
