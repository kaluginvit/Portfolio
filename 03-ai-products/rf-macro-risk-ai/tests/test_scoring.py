"""
Tests for the scoring engine (scoring.py).

All tests are pure Python — no LLM, no web search, no external APIs.
Run with: uv run pytest tests/test_scoring.py -v
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scoring import (
    DEPOSIT_ACCESS_WEIGHTS,
    SEVERITY_MULTIPLIERS,
    compute_crisis_score,
    compute_deposit_access_score,
    deposit_access_risk_from_score,
    get_novelty_multiplier,
    record_criterion_events,
    risk_level_from_score,
    severity_multiplier,
)

# ─────────────────────── fixtures / helpers ──────────────────────────────────

STANDARD_THRESHOLDS = {
    "green":  {"min": 0,  "max": 19},
    "yellow": {"min": 20, "max": 39},
    "orange": {"min": 40, "max": 69},
    "red":    {"min": 70, "max": 999},
}


def _criteria_by_id(items: list[tuple[str, int]]) -> dict:
    return {cid: {"weight": w, "cooldown_days": 14} for cid, w in items}


# ─────────────────────── severity_multiplier ────────────────────────────────

class TestSeverityMultiplier:
    def test_known_statuses(self):
        assert severity_multiplier("quiet")        == 0.0
        assert severity_multiplier("watch")        == 0.25
        assert severity_multiplier("warming_up")   == 0.50
        assert severity_multiplier("triggered")    == 1.00
        assert severity_multiplier("critical")     == 1.50
        assert severity_multiplier("cooling_down") == 0.25

    def test_unknown_returns_zero(self):
        assert severity_multiplier("unknown_xyz") == 0.0
        assert severity_multiplier("") == 0.0


# ─────────────────────── compute_crisis_score ────────────────────────────────

class TestComputeCrisisScore:
    def test_single_triggered(self):
        c_by_id = _criteria_by_id([("c1", 10)])
        result = compute_crisis_score([{"id": "c1", "status": "triggered"}], c_by_id, {})
        assert result == 10  # 10 * 1.0 * 1.0

    def test_single_critical(self):
        c_by_id = _criteria_by_id([("c1", 10)])
        result = compute_crisis_score([{"id": "c1", "status": "critical"}], c_by_id, {})
        assert result == 15  # 10 * 1.5

    def test_quiet_contributes_zero(self):
        c_by_id = _criteria_by_id([("c1", 20)])
        result = compute_crisis_score([{"id": "c1", "status": "quiet"}], c_by_id, {})
        assert result == 0

    def test_multiple_criteria_sum(self):
        # 10*1.0 + 5*0.25 = 10 + 1.25 → rounds to 11
        c_by_id = _criteria_by_id([("a", 10), ("b", 5)])
        statuses = [{"id": "a", "status": "triggered"}, {"id": "b", "status": "watch"}]
        assert compute_crisis_score(statuses, c_by_id, {}) == 11

    def test_unknown_criterion_id_skipped(self):
        c_by_id = _criteria_by_id([("known", 20)])
        result = compute_crisis_score([{"id": "unknown", "status": "triggered"}], c_by_id, {})
        assert result == 0

    def test_empty_list(self):
        assert compute_crisis_score([], {}, {}) == 0

    def test_novelty_reduces_score_when_in_cooldown(self):
        now = datetime.now(timezone.utc)
        future = (now + timedelta(days=7)).isoformat()
        ledger = {"events": {"c1": {"cooldown_until": future}}}
        c_by_id = _criteria_by_id([("c1", 40)])
        # novelty = 0.25, severity triggered = 1.0 → 40 * 1.0 * 0.25 = 10
        result = compute_crisis_score([{"id": "c1", "status": "triggered"}], c_by_id, ledger, now=now)
        assert result == 10


# ─────────────────────── threshold boundaries ────────────────────────────────

class TestRiskLevelFromScore:
    @pytest.mark.parametrize("score,expected", [
        (0,  "green"),
        (19, "green"),
        (20, "yellow"),
        (39, "yellow"),
        (40, "orange"),
        (69, "orange"),
        (70, "red"),
        (200, "red"),
    ])
    def test_threshold_boundaries(self, score, expected):
        assert risk_level_from_score(score, STANDARD_THRESHOLDS) == expected

    def test_black_override_takes_priority_over_score(self):
        c_by_id = {"shock_crit": {"triggers_black": True, "weight": 10}}
        c_status = {"shock_crit": "triggered"}
        # Even score=5 (would be green) → black because triggers_black
        result = risk_level_from_score(5, STANDARD_THRESHOLDS, c_status, c_by_id)
        assert result == "black"

    def test_black_not_triggered_when_status_watch(self):
        c_by_id = {"shock_crit": {"triggers_black": True, "weight": 10}}
        c_status = {"shock_crit": "watch"}
        result = risk_level_from_score(5, STANDARD_THRESHOLDS, c_status, c_by_id)
        assert result == "green"

    def test_non_black_criterion_does_not_trigger_black(self):
        c_by_id = {"normal_crit": {"triggers_black": False, "weight": 10}}
        c_status = {"normal_crit": "critical"}
        result = risk_level_from_score(50, STANDARD_THRESHOLDS, c_status, c_by_id)
        assert result == "orange"  # score based, not black


# ─────────────────────── deposit_access_score ────────────────────────────────

class TestDepositAccessScore:
    def test_all_quiet_gives_zero(self):
        assert compute_deposit_access_score({}) == 0

    def test_bank_holidays_triggered_gives_40(self):
        assert compute_deposit_access_score({"bank_holidays_national": "triggered"}) == 40

    def test_bank_holidays_critical_gives_60(self):
        # 40 * 1.5 = 60
        assert compute_deposit_access_score({"bank_holidays_national": "critical"}) == 60

    def test_weights_sum_all_triggered(self):
        all_triggered = {cid: "triggered" for cid in DEPOSIT_ACCESS_WEIGHTS}
        score = compute_deposit_access_score(all_triggered)
        assert score == sum(DEPOSIT_ACCESS_WEIGHTS.values())  # 100

    def test_missing_criterion_treated_as_quiet(self):
        # Only one criterion, rest missing → only its weight counted
        score = compute_deposit_access_score({"interbank_liquidity_stress": "triggered"})
        assert score == 10  # DEPOSIT_ACCESS_WEIGHTS["interbank_liquidity_stress"] = 10


class TestDepositAccessRiskFromScore:
    @pytest.mark.parametrize("score,expected", [
        (0,  "green"),
        (9,  "green"),
        (10, "yellow"),
        (29, "yellow"),
        (30, "red"),
        (100, "red"),
    ])
    def test_deposit_risk_boundaries(self, score, expected):
        assert deposit_access_risk_from_score(score) == expected


# ─────────────────────── novelty / cooldown ──────────────────────────────────

class TestNoveltyMultiplier:
    def test_no_ledger_entry_returns_1(self):
        assert get_novelty_multiplier("c1", {}) == 1.0

    def test_expired_cooldown_returns_1(self):
        now = datetime.now(timezone.utc)
        past = (now - timedelta(days=1)).isoformat()
        ledger = {"events": {"c1": {"cooldown_until": past}}}
        assert get_novelty_multiplier("c1", ledger, now=now) == 1.0

    def test_active_cooldown_returns_025(self):
        now = datetime.now(timezone.utc)
        future = (now + timedelta(days=7)).isoformat()
        ledger = {"events": {"c1": {"cooldown_until": future}}}
        assert get_novelty_multiplier("c1", ledger, now=now) == 0.25

    def test_malformed_cooldown_returns_1(self):
        ledger = {"events": {"c1": {"cooldown_until": "not-a-date"}}}
        assert get_novelty_multiplier("c1", ledger) == 1.0


# ─────────────────────── record_criterion_events ─────────────────────────────

class TestRecordCriterionEvents:
    def test_triggered_adds_event(self):
        ledger = {}
        c_by_id = {"c1": {"cooldown_days": 7}}
        record_criterion_events(ledger, [{"id": "c1", "status": "triggered"}], c_by_id)
        assert "c1" in ledger["events"]
        assert ledger["events"]["c1"]["trigger_count"] == 1

    def test_quiet_does_not_add_event(self):
        ledger = {}
        c_by_id = {"c1": {"cooldown_days": 7}}
        record_criterion_events(ledger, [{"id": "c1", "status": "quiet"}], c_by_id)
        # setdefault creates events key, but it should be empty
        assert ledger.get("events", {}) == {}

    def test_trigger_count_increments_on_repeat(self):
        c_by_id = {"c1": {"cooldown_days": 7}}
        ledger = {}
        record_criterion_events(ledger, [{"id": "c1", "status": "triggered"}], c_by_id)
        record_criterion_events(ledger, [{"id": "c1", "status": "triggered"}], c_by_id)
        assert ledger["events"]["c1"]["trigger_count"] == 2

    def test_cooldown_days_zero_sets_now_as_cooldown(self):
        now = datetime.now(timezone.utc)
        ledger = {}
        c_by_id = {"force_majeure": {"cooldown_days": 0}}
        record_criterion_events(ledger, [{"id": "force_majeure", "status": "critical"}], c_by_id, now=now)
        cooldown = ledger["events"]["force_majeure"]["cooldown_until"]
        parsed = datetime.fromisoformat(cooldown)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        # cooldown_days=0 → cooldown_until == now (not in future)
        assert parsed <= now + timedelta(seconds=1)
