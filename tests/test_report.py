import pytest
from nexus.report import summarize


def row(id, purpose="debug", reason="completed", label="__OTHER__"):
    return {"id": id, "purpose": purpose, "model": {"sha256": "model1"}, "protocol": "single-v1",
            "label_verification": "user_intent_only_not_ASL_verified", "frames": [], "duration_ms": 10000,
            "end_reason": reason, "intended": {"label": label}, "outcome": "false_event",
            "events": [{"label": "BOOK"}]}


def report(rows):
    return {"schema_version": 1, "application": "Nexus guided diagnostics", "attempts": rows}


def test_report_separates_purposes_and_excludes_interrupted_time():
    result = summarize(report([row("a"), row("b", reason="cancelled"), row("c", purpose="evaluation")]))
    assert len(result["groups"]) == 2
    debug = result["groups"][0]
    assert debug["interrupted"] == 1 and debug["movement_false_events_per_minute"] == 6
    assert not result["training_performed"] and not result["thresholds_changed"]


def test_duplicate_attempts_cannot_inflate_evidence():
    with pytest.raises(ValueError, match="Duplicate"):
        summarize(report([row("a"), row("a")]))
