"""
CLI-оркестратор пайплайна ИнфоПовод.

Использование:
    python pipeline.py --status
    python pipeline.py --import-json
    python pipeline.py --import-saved [--dry-run]
    python pipeline.py --collect [--since YYYY-MM-DD]
    python pipeline.py --gate
    python pipeline.py --analyze [--limit 300] [--force]
    python pipeline.py --embed [--rebuild]
    python pipeline.py --export [--format csv|json|md]
    python pipeline.py --enrich-sources [--dry-run]
    python pipeline.py --serve [--port 8766]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).parent
DB_PATH = HERE / "data" / "messages.db"
CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))


def _get_con() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


def _count(table: str, where: str = "") -> int:
    try:
        con = _get_con()
        sql = f"SELECT COUNT(*) FROM {table}" + (f" WHERE {where}" if where else "")
        return con.execute(sql).fetchone()[0]
    except Exception:
        return -1
    finally:
        con.close()


def cmd_status() -> None:
    print("=" * 50)
    print("  Статус пайплайна ИнфоПовод")
    print("=" * 50)

    msgs = _count("messages")
    filtered = _count("messages_filtered") if msgs >= 0 else -1
    enriched = _count("enrichments") if msgs >= 0 else -1

    index_path = HERE / "vectors" / "faiss.index"
    meta_path = HERE / "vectors" / "meta.pkl"
    if index_path.exists() and meta_path.exists():
        import pickle
        with open(meta_path, "rb") as f:
            meta = pickle.load(f)
        vectors = len(meta)
    else:
        vectors = 0

    def fmt(n: int) -> str:
        return str(n) if n >= 0 else "—"

    print(f"  messages:          {fmt(msgs):>7}")
    print(f"  messages_filtered: {fmt(filtered):>7}")
    print(f"  enrichments:       {fmt(enriched):>7}")
    print(f"  vectors (FAISS):   {vectors:>7}")

    if msgs > 0 and enriched >= 0:
        pct = enriched / msgs * 100
        print(f"\n  LLM-прогресс: {pct:.1f}% ({enriched}/{msgs})")
        remaining = msgs - enriched
        calls_needed = (remaining + CFG["batch_size"] - 1) // CFG["batch_size"]
        print(f"  Осталось обработать: ~{remaining} постов (~{calls_needed} вызовов LLM)")
    print("=" * 50)


def cmd_import_json(result_json: str | None = None) -> None:
    from import_json import import_messages
    path = Path(result_json) if result_json else HERE / CFG.get("result_json", "result.json")
    import_messages(path, DB_PATH)


def cmd_collect(since: str | None = None) -> None:
    import asyncio
    from collect import collect_channel
    asyncio.run(collect_channel(DB_PATH, since_override=since))


def cmd_gate() -> None:
    from local_gate import rebuild_filtered, print_stats
    cfg_gate = CFG.get("local_gate", {})
    stats = rebuild_filtered(
        db_path=DB_PATH,
        keywords=cfg_gate.get("keywords", []),
        min_len=cfg_gate.get("min_len", 150),
        filter_on_analyzed_at=True,
    )
    print_stats(stats, min_len=cfg_gate.get("min_len", 150))


def cmd_analyze(limit: int = 0, force: bool = False) -> None:
    from llm_analyze import run_analyze
    result = run_analyze(
        db_path=DB_PATH,
        batch_size=CFG["batch_size"],
        limit=limit,
        force=force,
    )
    print(f"Обработано: {result['processed']}, ошибок: {result['errors']}")
    if result.get("stopped_rate_limit"):
        print("Остановлено по rate limit — запустите снова завтра.")


def cmd_embed(rebuild: bool = False) -> None:
    from embed import build_index
    build_index(
        db_path=DB_PATH,
        rebuild=rebuild,
    )


def cmd_export(fmt: str = "md") -> None:
    from export import export_csv, export_json, export_markdown
    out_dir = HERE / "output"
    out_dir.mkdir(exist_ok=True)
    if fmt == "csv":
        path = export_csv(DB_PATH, out_dir)
    elif fmt == "json":
        path = export_json(DB_PATH, out_dir)
    else:
        path = export_markdown(DB_PATH, out_dir)
    print(f"Экспортировано: {path}")


def cmd_import_saved(dry_run: bool = False) -> None:
    import asyncio
    from import_saved import import_saved_messages
    asyncio.run(import_saved_messages(db_path=DB_PATH, dry_run=dry_run))


def cmd_enrich_sources(dry_run: bool = False) -> None:
    import asyncio
    from enrich_saved_sources import enrich_saved_sources
    asyncio.run(enrich_saved_sources(db_path=DB_PATH, dry_run=dry_run))


def cmd_serve(port: int = 8766) -> None:
    import subprocess, sys
    from embed_client import is_server_up
    if not is_server_up():
        subprocess.Popen([sys.executable, str(HERE / "embed_server.py")], cwd=str(HERE))
        print("embed_server запущен на порту 8767 (загружает модель в фоне)")
    import uvicorn
    uvicorn.run(
        "web.app:app",
        host="127.0.0.1",
        port=port,
        reload=False,
        app_dir=str(HERE),
    )


def main() -> None:
    p = argparse.ArgumentParser(description="ИнфоПовод pipeline")
    p.add_argument("--status", action="store_true", help="Статус пайплайна")
    p.add_argument("--import-json", metavar="FILE", nargs="?", const="", help="Импорт result.json")
    p.add_argument("--collect", action="store_true", help="Сбор новых постов через Telethon")
    p.add_argument("--since", metavar="YYYY-MM-DD", help="С какой даты собирать")
    p.add_argument("--gate", action="store_true", help="Перестроить messages_filtered")
    p.add_argument("--analyze", action="store_true", help="LLM-обогащение постов")
    p.add_argument("--limit", type=int, default=0, help="Лимит постов для --analyze (0=все)")
    p.add_argument("--force", action="store_true", help="Переобработать уже обогащённые посты")
    p.add_argument("--embed", action="store_true", help="Построить FAISS-индекс")
    p.add_argument("--rebuild", action="store_true", help="Перестроить индекс с нуля")
    p.add_argument("--import-saved", action="store_true", help="Импорт Избранного из обоих аккаунтов")
    p.add_argument("--enrich-sources", action="store_true", help="Добавить источники из Избранного в список каналов")
    p.add_argument("--dry-run", action="store_true", help="Для --import-saved и --enrich-sources: только показать, не писать")
    p.add_argument("--export", metavar="FORMAT", nargs="?", const="md", help="Экспорт (csv|json|md)")
    p.add_argument("--serve", action="store_true", help="Запустить веб-интерфейс")
    p.add_argument("--port", type=int, default=CFG.get("web_port", 8766))

    args = p.parse_args()

    if args.status:
        cmd_status()
    elif args.import_json is not None:
        cmd_import_json(args.import_json or None)
    elif args.collect:
        cmd_collect(args.since)
    elif args.gate:
        cmd_gate()
    elif args.analyze:
        cmd_analyze(args.limit, args.force)
    elif args.embed:
        cmd_embed(args.rebuild)
    elif args.import_saved:
        cmd_import_saved(args.dry_run)
    elif args.enrich_sources:
        cmd_enrich_sources(args.dry_run)
    elif args.export is not None:
        cmd_export(args.export)
    elif args.serve:
        cmd_serve(args.port)
    else:
        p.print_help()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
