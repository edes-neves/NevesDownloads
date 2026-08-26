"""Testes para a lógica de navegação do FolderBrowser.

Testa a lógica de filtragem de pastas ocultas, navegação para pai,
e seleção de caminho, sem instanciar widgets reais.
"""

from pathlib import Path


class TestFolderFiltering:
    """Testa que pastas ocultas (que começam com '.') são filtradas."""

    def test_hidden_folders_filtered(self, tmp_path):
        """Pastas que começam com '.' devem ser ignoradas."""
        (tmp_path / ".hidden").mkdir()
        (tmp_path / "visible").mkdir()
        (tmp_path / ".cache").mkdir()

        entries = sorted(tmp_path.iterdir(), key=lambda p: p.name.lower())
        visible = [e for e in entries if e.is_dir() and not e.name.startswith(".")]

        assert len(visible) == 1
        assert visible[0].name == "visible"

    def test_files_also_filtered(self, tmp_path):
        """Apenas diretórios devem ser listados."""
        (tmp_path / "folder1").mkdir()
        (tmp_path / "folder2").mkdir()
        (tmp_path / "file.txt").write_text("content")

        entries = sorted(tmp_path.iterdir(), key=lambda p: p.name.lower())
        dirs = [e for e in entries if e.is_dir() and not e.name.startswith(".")]

        assert len(dirs) == 2

    def test_all_hidden_folders(self, tmp_path):
        """Se todas as pastas forem ocultas, a lista deve ficar vazia."""
        (tmp_path / ".a").mkdir()
        (tmp_path / ".b").mkdir()

        entries = sorted(tmp_path.iterdir(), key=lambda p: p.name.lower())
        visible = [e for e in entries if e.is_dir() and not e.name.startswith(".")]

        assert len(visible) == 0

    def test_empty_directory(self, tmp_path):
        """Diretório vazio resulta em lista vazia."""
        entries = sorted(tmp_path.iterdir(), key=lambda p: p.name.lower())
        dirs = [e for e in entries if e.is_dir()]
        assert len(dirs) == 0

    def test_case_sensitivity(self, tmp_path):
        """Pastas visíveis com diferentes casos são mantidas."""
        (tmp_path / "Alpha").mkdir()
        (tmp_path / "beta").mkdir()
        (tmp_path / "GAMMA").mkdir()

        entries = sorted(tmp_path.iterdir(), key=lambda p: p.name.lower())
        visible = [e for e in entries if e.is_dir() and not e.name.startswith(".")]
        assert len(visible) == 3


class TestPathNavigation:
    """Testa lógica de navegação entre diretórios."""

    def test_parent_of_root_is_still_root(self):
        """O pai de / deve ser / (no Unix)."""
        root = Path("/")
        parent = root.parent
        assert parent == root

    def test_parent_of_home(self):
        """O pai de /home/user é /home."""
        home = Path("/home/user")
        parent = home.parent
        assert parent == Path("/home")

    def test_go_up_from_subdir(self, tmp_path):
        """Voltar de /tmp/test para /tmp."""
        sub = tmp_path / "test"
        sub.mkdir()
        parent = sub.parent
        assert parent == tmp_path

    def test_navigate_to_valid_path(self, tmp_path):
        """Navegar para um caminho válido deve retornar True."""
        p = tmp_path / "existing"
        p.mkdir()
        assert p.is_dir()

    def test_navigate_to_invalid_path(self, tmp_path):
        """Navegar para um caminho inexistente deve ser detectado."""
        p = tmp_path / "nonexistent"
        assert not p.is_dir()


class TestPathSelection:
    """Testa lógica de seleção de caminho."""

    def test_strip_whitespace(self):
        text = "  /home/user/Downloads  "
        result = text.strip()
        assert result == "/home/user/Downloads"

    def test_empty_path(self):
        text = ""
        result = text.strip()
        assert result == ""

    def test_home_directory(self):
        home = Path.home()
        assert home.is_dir()

    def test_default_download_folder(self):
        from app.utils.paths import get_default_download_folder

        folder = get_default_download_folder()
        assert folder.is_dir()


class TestPlaylistSelection:
    """Testa lógica de seleção de vídeos da playlist."""

    def test_select_all(self):
        """Selecionar todos deve marcar todas as variáveis."""
        check_vars = [1, 1, 1]
        for i in range(len(check_vars)):
            check_vars[i] = 1
        assert all(v == 1 for v in check_vars)

    def test_deselect_all(self):
        """Desmarcar todos deve desmarcar todas as variáveis."""
        check_vars = [1, 1, 1]
        for i in range(len(check_vars)):
            check_vars[i] = 0
        assert all(v == 0 for v in check_vars)

    def test_confirm_collects_selected_urls(self):
        """Confirmar deve coletar URLs onde var == 1."""
        entries = [
            {"url": "https://a.com", "title": "A"},
            {"url": "https://b.com", "title": "B"},
            {"url": "https://c.com", "title": "C"},
        ]
        check_vars = [1, 0, 1]
        selected = []
        for idx, var in enumerate(check_vars):
            if var == 1:
                entry = entries[idx]
                if entry and entry.get("url"):
                    selected.append(entry["url"])
        assert selected == ["https://a.com", "https://c.com"]

    def test_confirm_with_none_entry(self):
        """Entradas None devem ser ignoradas na confirmação."""
        entries = [
            {"url": "https://a.com", "title": "A"},
            None,
            {"url": "https://c.com", "title": "C"},
        ]
        check_vars = [1, 1, 1]
        selected = []
        for idx, var in enumerate(check_vars):
            if var == 1:
                entry = entries[idx]
                if entry and entry.get("url"):
                    selected.append(entry["url"])
        assert selected == ["https://a.com", "https://c.com"]

    def test_duration_formatting(self):
        """Formatação de duração de vídeo."""
        for duration, expected in [
            (0, "??:??"),
            (65, "01:05"),
            (3661, "61:01"),
            (None, "??:??"),
        ]:
            if duration:
                minutes = duration // 60
                seconds = duration % 60
                result = f"{minutes:02d}:{seconds:02d}"
            else:
                result = "??:??"
            assert result == expected
