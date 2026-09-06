"""Smoke-тесты пайплайна ИнфоПовод: структура и конфигурация."""
import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent


def test_config_is_valid_json():
    with open(ROOT / "config.json", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict)


def test_pipeline_scripts_exist():
    required = ["pipeline.py", "collect.py", "embed.py", "search.py",
                "llm_analyze.py", "export_finetune.py", "schema.py"]
    for name in required:
        assert (ROOT / name).exists(), f"Отсутствует {name}"


def test_schema_has_tables():
    content = (ROOT / "schema.py").read_text(encoding="utf-8")
    assert "CREATE TABLE" in content or "Table" in content or "dataclass" in content


def test_web_dir_exists():
    assert (ROOT / "web").is_dir()


def test_requirements_parseable():
    reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    lines = [l.strip() for l in reqs.splitlines() if l.strip() and not l.startswith("#")]
    assert len(lines) > 0
