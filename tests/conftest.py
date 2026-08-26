import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Garante que o diretório raiz do projeto esteja no path para imports
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


@pytest.fixture(autouse=True)
def _reset_i18n_language():
    """Reseta o idioma para pt-BR antes de cada teste (idioma padrão do app)."""
    from app.i18n import set_language

    set_language("pt-BR")
    yield
    set_language("pt-BR")


@pytest.fixture
def temp_app_dir(tmp_path, monkeypatch):
    """Redireciona o diretório de dados da aplicação para um diretório temporário."""
    monkeypatch.setattr("app.utils.paths.Path.home", lambda: tmp_path)
    return tmp_path / ".neves_downloads"


@pytest.fixture
def mock_ctk(monkeypatch):
    """Mock módulos tkinter/customtkinter para testes que importam código UI sem instanciar widgets."""
    mock_tk = MagicMock()
    mock_tk.Tk = MagicMock
    mock_tk.Toplevel = MagicMock
    mock_tk.Frame = MagicMock
    mock_tk.Menu = MagicMock
    mock_tk.StringVar = MagicMock
    mock_tk.IntVar = MagicMock
    mock_tk.BooleanVar = MagicMock
    mock_tk.messagebox = MagicMock()
    monkeypatch.setitem(sys.modules, "tkinter", mock_tk)
    monkeypatch.setitem(sys.modules, "tkinter.messagebox", mock_tk.messagebox)
    monkeypatch.setitem(sys.modules, "tkinter.ttk", MagicMock())

    mock_ctk = MagicMock()
    mock_ctk.CTk = MagicMock
    mock_ctk.CTkFrame = MagicMock
    mock_ctk.CTkLabel = MagicMock
    mock_ctk.CTkButton = MagicMock
    mock_ctk.CTkEntry = MagicMock
    mock_ctk.CTkOptionMenu = MagicMock
    mock_ctk.CTkRadioButton = MagicMock
    mock_ctk.CTkCheckBox = MagicMock
    mock_ctk.CTkProgressBar = MagicMock
    mock_ctk.CTkScrollableFrame = MagicMock
    mock_ctk.CTkToplevel = MagicMock
    mock_ctk.CTkFont = MagicMock(return_value=("sans-serif", 12))
    mock_ctk.StringVar = MagicMock
    mock_ctk.IntVar = MagicMock
    mock_ctk.BooleanVar = MagicMock
    mock_ctk.set_appearance_mode = MagicMock()
    mock_ctk.set_default_color_theme = MagicMock()
    mock_ctk.get_appearance_mode = MagicMock(return_value="dark")
    monkeypatch.setitem(sys.modules, "customtkinter", mock_ctk)
    return mock_ctk
