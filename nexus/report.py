"""Summarize guided diagnostic JSON without training or changing thresholds."""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def summarize(report):
    if report.get("schema_version") != 1 or report.get("application") != "Nexus guided diagnostics":
        raise ValueError("Unsupported diagnostic report")
    attempts = report.get("attempts")
    if not isinstance(attempts, list) or len(attempts) > 120:
        raise ValueError("Invalid attempt count")
    ids, groups = set(), defaultdict(list)
    for row in attempts:
        if row["id"] in ids:
            raise ValueError("Duplicate attempt ID")
        ids.add(row["id"])
        if len(row["frames"]) > 240 or row["purpose"] not in {"debug", "calibration", "evaluation"}:
            raise ValueError("Invalid frame count or purpose")
        if row.get("label_verification") != "user_intent_only_not_ASL_verified":
            raise ValueError("Unexpected label-verification claim")
        if not isinstance(row["duration_ms"], (int, float)) or not 0 <= row["duration_ms"] <= 120000:
            raise ValueError("Invalid duration")
        model = row.get("model") or {}
        groups[(row["purpose"], model.get("sha256"), row["protocol"])].append(row)
    results = []
    for (purpose, model_hash, protocol), rows in groups.items():
        completed = [r for r in rows if r["end_reason"] == "completed"]
        known = [r for r in completed if r["intended"]["label"] != "__OTHER__"]
        movement = [r for r in completed if r["intended"]["label"] == "__OTHER__"]
        movement_minutes = sum(r["duration_ms"] for r in movement) / 60000
        false_events = sum(len(r["events"]) for r in movement)
        per_label = {}
        for label in sorted({r["intended"]["label"] for r in known}):
            selected = [r for r in known if r["intended"]["label"] == label]
            per_label[label] = {"completed_attempts": len(selected),
                                "outcomes": dict(Counter(r["outcome"] for r in selected))}
        results.append({"purpose": purpose, "model_sha256": model_hash, "protocol": protocol,
                        "attempts": len(rows), "completed": len(completed), "interrupted": len(rows) - len(completed),
                        "observed_outcomes": dict(Counter(r["outcome"] for r in completed)),
                        "per_intended_label": per_label, "movement_minutes": movement_minutes,
                        "movement_false_events": false_events,
                        "movement_false_events_per_minute": false_events / movement_minutes if movement_minutes else None,
                        "synthetic_fixture": any("SYNTHETIC" in (r.get("model") or {}).get("name", "") for r in rows)})
    return {"groups": results, "training_performed": False, "thresholds_changed": False,
            "limitations": ["User intent is not verified ASL ground truth", "Do not call these outcomes ASL accuracy",
                            "Interrupted attempts are counted separately", "Purposes and model hashes are never pooled",
                            "Synthetic fixture results are engineering checks only"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.report.stat().st_size > 32 * 1024**2:
        raise ValueError("Report exceeds 32 MiB limit")
    output = json.dumps(summarize(json.loads(args.report.read_text(encoding="utf-8-sig"))), indent=2)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
