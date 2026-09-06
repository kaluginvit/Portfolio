"""Валидация JSON-структуры n8n воркфлоу."""
import json
import pathlib

WORKFLOWS_DIR = pathlib.Path(__file__).parent.parent / "n8n-workflows"


def _load_workflows():
    return list(WORKFLOWS_DIR.glob("*.json"))


def test_workflows_exist():
    files = _load_workflows()
    assert len(files) > 0, "Нет JSON-файлов в n8n-workflows/"


def test_workflows_valid_json():
    for f in _load_workflows():
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
        assert isinstance(data, dict), f"{f.name} не является объектом"


def test_workflows_have_nodes():
    for f in _load_workflows():
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
        assert "nodes" in data, f"{f.name}: отсутствует ключ 'nodes'"
        assert isinstance(data["nodes"], list), f"{f.name}: nodes не список"


def test_workflows_have_connections():
    for f in _load_workflows():
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
        assert "connections" in data, f"{f.name}: отсутствует ключ 'connections'"
