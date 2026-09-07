"""
Deterministic scoring replay — no LLM, no web search required.

Usage:
    uv run python scripts/replay_scoring.py
    uv run python scripts/replay_scoring.py --sample sample_data/sample_criteria_status.json
    uv run python scripts/replay_scoring.py --criteria criteria_small.json

This script demonstrates the scoring engine on saved criteria status data.
Useful for:
  - Demonstrating the portfolio without spending API credits
  - Testing scoring logic with known inputs
  - CI smoke test of the scoring module
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scoring import (
    compute_crisis_score,
    compute_deposit_access_score,
    deposit_access_risk_from_score,
    risk_level_from_score,
)


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_criteria_by_id(criteria_data: dict) -> dict:
    return {c["id"]: c for c in criteria_data.get("criteria", [])}


def main():
    parser = argparse.ArgumentParser(description="Replay scoring on saved criteria status")
    parser.add_argument(
        "--sample",
        default=str(ROOT / "sample_data" / "sample_criteria_status.json"),
        help="Path to sample criteria status JSON",
    )
    parser.add_argument(
        "--criteria",
        default=str(ROOT / "criteria.json"),
        help="Path to criteria definition JSON",
    )
    args = parser.parse_args()

    sample_path = Path(args.sample)
    criteria_path = Path(args.criteria)

    if not sample_path.exists():
        print(f"[ERROR] Sample file not found: {sample_path}", file=sys.stderr)
        sys.exit(1)
    if not criteria_path.exists():
        print(f"[ERROR] Criteria file not found: {criteria_path}", file=sys.stderr)
        sys.exit(1)

    sample = load_json(sample_path)
    criteria_data = load_json(criteria_path)

    criteria_status_list = sample.get("criteria_status", [])
    criteria_by_id = build_criteria_by_id(criteria_data)
    thresholds = criteria_data.get("thresholds", {})

    # Build {id: status} dict for helper functions
    criteria_status_by_id = {item["id"]: item["status"] for item in criteria_status_list}

    # ── Crisis score ──────────────────────────────────────────────────────────
    crisis_score = compute_crisis_score(criteria_status_list, criteria_by_id, ledger={})
    risk_level = risk_level_from_score(crisis_score, thresholds, criteria_status_by_id, criteria_by_id)

    # ── Deposit access score ──────────────────────────────────────────────────
    deposit_score = compute_deposit_access_score(criteria_status_by_id)
    deposit_risk = deposit_access_risk_from_score(deposit_score)

    # ── Triggered criteria ────────────────────────────────────────────────────
    triggered = [
        item for item in criteria_status_list
        if item["status"] in ("triggered", "critical", "warming_up")
    ]

    # ── Output ────────────────────────────────────────────────────────────────
    level_emoji = {
        "green": "[GREEN]", "yellow": "[YELLOW]", "orange": "[ORANGE]",
        "red": "[RED]", "black": "[BLACK]",
    }
    deposit_emoji = {"green": "[GREEN]", "yellow": "[YELLOW]", "red": "[RED]"}

    print("\n" + "=" * 60)
    print("  RF MACRO RISK SCORING — REPLAY MODE")
    print(f"  Sample: {sample_path.name}")
    print(f"  Criteria: {criteria_path.name}")
    print("=" * 60)
    print(f"\n  Crisis Score:    {crisis_score}")
    print(f"  Risk Level:      {level_emoji.get(risk_level, '')} {risk_level.upper()}")
    print(f"\n  Deposit Score:   {deposit_score}")
    print(f"  Deposit Risk:    {deposit_emoji.get(deposit_risk, '')} {deposit_risk.upper()}")

    if triggered:
        print(f"\n  Active criteria ({len(triggered)}):")
        for item in triggered:
            cdef = criteria_by_id.get(item["id"], {})
            name = cdef.get("name", item["id"])
            weight = cdef.get("weight", "?")
            print(f"    [{item['status']:12s}] {name}  (weight={weight})")
    else:
        print("\n  No active criteria.")

    print("\n" + "=" * 60)
    print(f"  Scenario note: {sample.get('_scenario', 'n/a')}")
    print("=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
