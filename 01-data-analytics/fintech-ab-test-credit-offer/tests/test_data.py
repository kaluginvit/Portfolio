"""Smoke-тесты: целостность данных и работоспособность утилит."""
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))


def test_raw_data_exists():
    raw_dir = ROOT / "data" / "raw"
    files = list(raw_dir.glob("*.csv"))
    assert len(files) > 0, "Нет CSV-файлов в data/raw/"


def test_processed_dir_exists():
    assert (ROOT / "data" / "processed").exists()


def test_src_modules_importable():
    import data_processing  # noqa: F401
    import ab_analysis      # noqa: F401


def test_notebooks_exist():
    notebooks = list((ROOT / "notebooks").glob("*.ipynb"))
    assert len(notebooks) > 0, "Нет ноутбуков"
