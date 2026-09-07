"""
Tests for workflow_utils.py — logic extracted from n8n Code nodes.
Pure Python, no n8n instance required.
"""
import pytest
from workflow_utils import (
    apply_warmth_decay,
    classify_error_severity,
    compute_consensus_score,
    is_duplicate_event,
    make_event_key,
    warmth_to_bucket,
)


# ─────────────────────── Error Classification ────────────────────────────────

class TestClassifyErrorSeverity:
    def test_timeout_is_critical(self):
        assert classify_error_severity("Connection timeout") == "CRITICAL"

    def test_econnrefused_is_critical(self):
        assert classify_error_severity("ECONNREFUSED") == "CRITICAL"

    def test_401_unauthorized_is_critical(self):
        assert classify_error_severity("Request failed: 401 Unauthorized") == "CRITICAL"

    def test_500_server_error_is_critical(self):
        assert classify_error_severity("HTTP 500 Internal Server Error") == "CRITICAL"

    def test_rate_limit_is_warning(self):
        assert classify_error_severity("Rate limit exceeded") == "WARNING"

    def test_429_is_warning(self):
        assert classify_error_severity("Error 429 Too Many Requests") == "WARNING"

    def test_generic_error_is_info(self):
        assert classify_error_severity("Something went slightly wrong") == "INFO"

    def test_empty_string_is_info(self):
        assert classify_error_severity("") == "INFO"

    def test_case_insensitive(self):
        assert classify_error_severity("TIMEOUT exceeded") == "CRITICAL"
        assert classify_error_severity("rate limit hit") == "WARNING"


# ─────────────────────── Warmth Decay ────────────────────────────────────────

class TestApplyWarmthDecay:
    def test_no_decay_for_zero_days(self):
        # 0 days inactive → no decay
        result = apply_warmth_decay(50, days_inactive=0)
        assert result == 50

    def test_one_day_decay(self):
        # 50 * 0.9^1 = 45
        result = apply_warmth_decay(50, days_inactive=1)
        assert result == 45

    def test_seven_days_decay(self):
        # 50 * 0.9^7 ≈ 23.9 → 24
        result = apply_warmth_decay(50, days_inactive=7)
        assert result == 24

    def test_reply_boost_adds_30(self):
        # 50 * 0.9^1 = 45 + 30 = 75
        result = apply_warmth_decay(50, days_inactive=1, has_recent_reply=True)
        assert result == 75

    def test_reply_boost_capped_at_100(self):
        # 100 * 0.9^0 = 100 + 30 would be 130 → capped at 100
        result = apply_warmth_decay(100, days_inactive=0, has_recent_reply=True)
        assert result == 100

    def test_negative_days_treated_as_zero(self):
        result = apply_warmth_decay(60, days_inactive=-5)
        assert result == 60

    def test_full_decay_over_30_days(self):
        # 50 * 0.9^30 ≈ 2.4 → 2
        result = apply_warmth_decay(50, days_inactive=30)
        assert result <= 5  # significantly decayed

    def test_zero_warmth_stays_zero(self):
        assert apply_warmth_decay(0, days_inactive=10) == 0


class TestWarmthBucket:
    @pytest.mark.parametrize("warmth,bucket", [
        (100, "hot"),
        (70,  "hot"),
        (69,  "warm"),
        (40,  "warm"),
        (39,  "cool"),
        (15,  "cool"),
        (14,  "cold"),
        (0,   "cold"),
    ])
    def test_bucket_boundaries(self, warmth, bucket):
        assert warmth_to_bucket(warmth) == bucket


# ─────────────────────── Idempotency ─────────────────────────────────────────

class TestIdempotency:
    def test_same_event_produces_same_key(self):
        event = {"id": "lead-123", "source": "linkedin", "email": "a@b.com"}
        k1 = make_event_key(event)
        k2 = make_event_key(event)
        assert k1 == k2

    def test_different_events_produce_different_keys(self):
        e1 = {"id": "lead-1", "source": "linkedin"}
        e2 = {"id": "lead-2", "source": "linkedin"}
        assert make_event_key(e1) != make_event_key(e2)

    def test_empty_event_produces_stable_key(self):
        k = make_event_key({})
        assert len(k) == 16  # first 16 chars of SHA-256

    def test_duplicate_detection(self):
        event = {"id": "e1", "source": "twitter"}
        key = make_event_key(event)
        processed = {key}
        assert is_duplicate_event(key, processed) is True

    def test_new_event_not_duplicate(self):
        event = {"id": "new-lead", "source": "email"}
        key = make_event_key(event)
        assert is_duplicate_event(key, set()) is False

    def test_key_fields_selection(self):
        event = {"id": "X", "source": "A", "extra": "ignored"}
        key_with_extra = make_event_key(event, key_fields=["id", "source", "extra"])
        key_without_extra = make_event_key(event, key_fields=["id", "source"])
        assert key_with_extra != key_without_extra


# ─────────────────────── Consensus Scoring ───────────────────────────────────

class TestComputeConsensusScore:
    def test_equal_scores_agree(self):
        result = compute_consensus_score([0.8, 0.8, 0.8])
        assert result["score"] == 0.8
        assert result["agreement"] is True
        assert result["divergence"] == 0.0

    def test_high_divergence_disagrees(self):
        result = compute_consensus_score([0.9, 0.3, 0.6])
        assert result["agreement"] is False
        assert result["divergence"] == pytest.approx(0.6, abs=0.01)

    def test_weighted_consensus(self):
        # GPT weight 2, Claude weight 1: (0.8*2 + 0.5*1) / 3 ≈ 0.7
        result = compute_consensus_score([0.8, 0.5], weights=[2.0, 1.0])
        assert abs(result["score"] - 0.7) < 0.01

    def test_empty_scores(self):
        result = compute_consensus_score([])
        assert result["score"] == 0.0
        assert result["agreement"] is False

    def test_single_score_always_agrees(self):
        result = compute_consensus_score([0.75])
        assert result["agreement"] is True
        assert result["score"] == 0.75

    def test_weights_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="weights length"):
            compute_consensus_score([0.8, 0.6], weights=[1.0])

    def test_borderline_agreement_below_030(self):
        # 0.89 - 0.60 = 0.29 → agree
        result = compute_consensus_score([0.89, 0.60])
        assert result["agreement"] is True

    def test_just_over_030_disagrees(self):
        # 0.91 - 0.60 = 0.31 → disagree
        result = compute_consensus_score([0.91, 0.60])
        assert result["agreement"] is False
