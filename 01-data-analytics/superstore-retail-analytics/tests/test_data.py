"""Smoke-тесты: наличие артефактов и целостность данных."""
import csv
import pathlib

ROOT = pathlib.Path(__file__).parent.parent


def test_csv_exists():
    assert (ROOT / "Sample - Superstore.csv").exists()


def test_dashboard_html_exists():
    assert (ROOT / "superstore-dashboard.html").exists()


def test_csv_has_rows():
    with open(ROOT / "Sample - Superstore.csv", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) > 1000, f"Ожидалось >1000 строк, получено {len(rows)}"


def test_csv_key_columns():
    with open(ROOT / "Sample - Superstore.csv", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
    for col in ("Sales", "Profit", "Category"):
        assert col in fieldnames, f"Колонка '{col}' не найдена"


def test_notebook_exists():
    notebooks = list(ROOT.glob("*.ipynb"))
    assert len(notebooks) > 0
