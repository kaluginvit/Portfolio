"""Хранит счётчик нарушений в violations.json."""
import json
from pathlib import Path

_FILE = Path(__file__).parent / "violations.json"


def _load() -> dict:
    if _FILE.exists():
        try:
            return json.loads(_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save(data: dict) -> None:
    _FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_count(user_id: int) -> int:
    return _load().get(str(user_id), 0)


def increment(user_id: int) -> int:
    data = _load()
    key = str(user_id)
    data[key] = data.get(key, 0) + 1
    _save(data)
    return data[key]
