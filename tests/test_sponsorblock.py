"""Testes unitários para app.services.sponsorblock."""

from app.core.sponsorblock import DEFAULT_CATEGORIES
from app.services.sponsorblock import get_categories_labels


class TestGetCategoriesLabels:
    """Testes para categorias do SponsorBlock."""

    def test_retorna_dict(self):
        labels = get_categories_labels()
        assert isinstance(labels, dict)
        assert "sponsor" in labels
        assert "selfpromo" in labels
        assert "intro" in labels

    def test_sponsor_tem_label(self):
        labels = get_categories_labels()
        assert len(labels["sponsor"]) > 0

    def test_todas_categorias_presentes(self):
        labels = get_categories_labels()
        for cat in DEFAULT_CATEGORIES:
            assert cat in labels

    def test_labels_nao_vazios(self):
        labels = get_categories_labels()
        for key, val in labels.items():
            assert isinstance(key, str) and key
            assert isinstance(val, str) and val
