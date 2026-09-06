"""
Run finance pipeline stages from one place.

Examples:
    uv run python finance/refresh_finance.py --report
    uv run python finance/refresh_finance.py --analyze-local --links --videos --report
    uv run python finance/refresh_finance.py --all-local
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent
PROJECT_ROOT = ROOT.parent


def run_step(name: str, args: list[str], dry_run: bool = False) -> None:
    command = [sys.executable, *args]
    display = " ".join(command)
    print(f"\n== {name} ==")
    print(display)
    if dry_run:
        return
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(f"{name} failed with exit code {result.returncode}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--collect", action="store_true", help="Collect Telegram messages.")
    parser.add_argument("--start", default="2026-01-01")
    parser.add_argument("--end", default=None)
    parser.add_argument("--mark-read", action="store_true")
    parser.add_argument("--session-name", default=None)
    parser.add_argument("--analyze-local", action="store_true", help="Run deterministic local analysis.")
    parser.add_argument("--classify-only", action="store_true", help="Run cheap LLM categorization only.")
    parser.add_argument("--analyze-llm", action="store_true", help="Run full LLM practical analysis.")
    parser.add_argument("--all-messages", action="store_true")
    parser.add_argument("--analysis-limit", type=int)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--links", action="store_true", help="Reindex finance links.")
    parser.add_argument("--videos", action="store_true", help="Reindex downloaded video files.")
    parser.add_argument("--docs", action="store_true", help="Fetch document filenames/metadata from Telegram.")
    parser.add_argument("--report", action="store_true", help="Write health report and PROGRESS.md.")
    parser.add_argument("--all-local", action="store_true", help="Local analysis, exports, links, videos, report.")
    parser.add_argument("--expand-coverage", action="store_true", help="Process short messages (<300 chars) with local heuristic.")
    parser.add_argument("--rebalance-local", action="store_true", help="Re-run local heuristic for local-heuristic-v1 records to fix priority bias.")
    parser.add_argument("--rebalance-classify", action="store_true", help="Reclassify local-heuristic-v1 records via LLM classify-only.")
    parser.add_argument("--export-split", action="store_true", help="Export per-category and per-target_user MD files.")
    parser.add_argument("--weekly", action="store_true", help="Export weekly digest.")
    parser.add_argument("--weekly-days", type=int, default=7)
    parser.add_argument("--analyze-v2", action="store_true", help="Run full LLM pass for high-priority records (pipeline v2: insight + entities).")
    parser.add_argument("--max-tokens", type=int, default=12000, help="Max output tokens for LLM (default: 12000).")
    parser.add_argument("--temperature", type=float, default=0.25, help="LLM temperature (default: 0.25).")
    parser.add_argument("--serve", action="store_true", help="Start local web interface on port 8765.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.all_local:
        args.analyze_local = True
        args.links = True
        args.videos = True
        args.report = True

    if args.collect:
        collect_args = ["finance/collect_finance_messages.py", "--start", args.start]
        if args.end:
            collect_args += ["--end", args.end]
        if args.mark_read:
            collect_args.append("--mark-read")
        if args.session_name:
            collect_args += ["--session-name", args.session_name]
        run_step("collect", collect_args, args.dry_run)

    if args.analyze_local:
        analysis_args = ["finance/practical_finance.py", "--process-local"]
        if args.all_messages:
            analysis_args.append("--all-messages")
        if args.analysis_limit:
            analysis_args += ["--limit", str(args.analysis_limit)]
        run_step("analyze local", analysis_args, args.dry_run)

    if args.classify_only:
        classify_args = ["finance/practical_finance.py", "--classify-only"]
        if args.all_messages:
            classify_args.append("--all-messages")
        if args.analysis_limit:
            classify_args += ["--limit", str(args.analysis_limit)]
        if args.batch_size:
            classify_args += ["--batch-size", str(args.batch_size)]
        run_step("classify only", classify_args, args.dry_run)

    if args.analyze_llm:
        llm_args = ["finance/practical_finance.py", "--process"]
        if args.all_messages:
            llm_args.append("--all-messages")
        if args.analysis_limit:
            llm_args += ["--limit", str(args.analysis_limit)]
        if args.batch_size:
            llm_args += ["--batch-size", str(args.batch_size)]
        run_step("analyze llm", llm_args, args.dry_run)

    if args.expand_coverage:
        run_step("expand coverage", ["finance/practical_finance.py", "--process-local", "--all-messages"], args.dry_run)

    if args.rebalance_local:
        run_step("rebalance local priority", ["finance/practical_finance.py", "--process-local", "--force", "--all-messages", "--local-only"], args.dry_run)

    if getattr(args, "rebalance_classify", False):
        rc_args = ["finance/practical_finance.py", "--classify-only", "--force", "--all-messages", "--local-only",
                   "--max-tokens", str(args.max_tokens), "--temperature", "0.1"]
        if args.batch_size:
            rc_args += ["--batch-size", str(args.batch_size)]
        if args.analysis_limit:
            rc_args += ["--limit", str(args.analysis_limit)]
        run_step("reclassify local-heuristic via LLM", rc_args, args.dry_run)

    if args.analyze_v2:
        v2_args = ["finance/practical_finance.py", "--process", "--high-only", "--pipeline-version", "finance-practical-v2",
                   "--max-tokens", str(args.max_tokens), "--temperature", str(args.temperature)]
        if args.analysis_limit:
            v2_args += ["--limit", str(args.analysis_limit)]
        if args.batch_size:
            v2_args += ["--batch-size", str(args.batch_size)]
        run_step("analyze v2 (insight+entities)", v2_args, args.dry_run)

    export_needed = args.analyze_local or args.classify_only or args.analyze_llm or args.expand_coverage or args.rebalance_local or args.analyze_v2
    if export_needed:
        export_args = ["finance/practical_finance.py", "--export"]
        if args.export_split:
            export_args.append("--export-split")
        run_step("export analysis", export_args, args.dry_run)
    elif args.export_split:
        run_step("export split", ["finance/practical_finance.py", "--export", "--export-split"], args.dry_run)

    if args.weekly:
        run_step("weekly digest", ["finance/practical_finance.py", "--export-weekly", "--weekly-days", str(args.weekly_days)], args.dry_run)

    if args.links:
        run_step("index links", ["finance/index_links.py"], args.dry_run)

    if args.videos:
        run_step("index videos", ["finance/index_video_files.py"], args.dry_run)

    if args.docs:
        docs_args = ["finance/fetch_doc_metadata.py", "--start", args.start, "--end", args.end or "2026-08-13"]
        if args.session_name:
            docs_args += ["--session-name", args.session_name]
        run_step("fetch doc metadata", docs_args, args.dry_run)

    if args.report:
        run_step("health report", ["finance/finance_health.py", "--write-progress"], args.dry_run)

    if args.serve:
        import subprocess as _sp
        print("\n== serve ==")
        print("Starting finance API at http://localhost:8765")
        if not args.dry_run:
            _sp.run([sys.executable, "-m", "uvicorn", "finance.finance_api:app", "--port", "8765", "--reload"],
                    cwd=PROJECT_ROOT, check=False)

    if not any(
        [
            args.collect,
            args.analyze_local,
            args.classify_only,
            args.analyze_llm,
            args.expand_coverage,
            args.rebalance_local,
            args.analyze_v2,
            args.export_split,
            args.weekly,
            args.links,
            args.videos,
            args.report,
            args.serve,
        ]
    ):
        parser.print_help()


if __name__ == "__main__":
    main()
