"""
Публикация последнего отчёта на сайт и в Telegram.
Работает после любого прогона — через lc_money_alert_bot.py, API или вручную (Claude Code).

Запуск:
  python tools/publish.py
  python tools/publish.py --data docs/data.json
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from analysis_core import _update_inline_data, _auto_git_push, _call_reporter


def _gh_auth_switch(repo_root: Path) -> None:
    """Переключает gh на аккаунт-владелец репозитория (берёт из git remote origin)."""
    try:
        url = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            cwd=str(repo_root), text=True, timeout=10,
        ).strip()
        # https://github.com/OWNER/repo.git  или  git@github.com:OWNER/repo.git
        if "github.com/" in url:
            owner = url.split("github.com/")[-1].split("/")[0].replace(".git", "")
        elif "github.com:" in url:
            owner = url.split("github.com:")[-1].split("/")[0]
        else:
            print("  gh switch: не удалось определить владельца из remote URL")
            return
        result = subprocess.run(
            ["gh", "auth", "switch", "--user", owner],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            print(f"  gh auth switch → {owner} OK")
        else:
            print(f"  gh switch warn: {result.stderr.strip()}")
    except Exception as e:
        print(f"  gh switch error: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Публикация отчёта: обновить index.html + git push + Telegram"
    )
    parser.add_argument(
        "--data",
        default=str(ROOT / "docs" / "data.json"),
        help="Путь к data.json (по умолчанию: docs/data.json)",
    )
    args = parser.parse_args()

    data_path = Path(args.data).resolve()
    if not data_path.exists():
        print(f"❌ Файл не найден: {data_path}")
        sys.exit(1)

    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)

    run_id = data.get("run_id", "?")
    risk = data.get("risk_level", "?")
    score = data.get("total_score", "?")
    print(f"📄 Отчёт: run #{run_id} | {risk} | {score} pts")
    print()

    print("1/3 Обновляю index.html...")
    _update_inline_data(data_path, data)

    print("2/3 Git push → GitHub Pages...")
    _gh_auth_switch(ROOT)
    _auto_git_push(data_path, data)

    print("3/3 Telegram-репортёр...")
    _call_reporter(data_path)

    print("\n✅ Публикация завершена")


if __name__ == "__main__":
    main()
