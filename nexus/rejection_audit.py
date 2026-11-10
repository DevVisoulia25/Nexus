"""Audit feature extrapolation and rejected known signs without changing model."""
import json
from pathlib import Path

import numpy as np

from nexus.features import active_sequence, sequence_vector
from nexus.model import SignModel
from nexus.replay import load_samples


def main():
    model = SignModel("models/signs-background-candidate.npz")
    samples, manifest_hash = load_samples()
    rows = []
    for sample, frames, timestamps in samples:
        active, times = active_sequence(frames, timestamps)
        vector = sequence_vector(active, times, 24)
        x = (vector - model.mean) / model.scale
        prediction = model.predict(frames, timestamps)
        rows.append({"id": sample["id"], "label": sample["label"], "split": sample["split"], "role": sample["role"],
                     "standardized_rms": float(np.sqrt(np.mean(x*x))),
                     "max_abs_standardized": float(np.abs(x).max()),
                     "fraction_abs_over_5": float((np.abs(x) > 5).mean()),
                     "active_frames": len(times), "candidate": prediction["candidate"], "gate_score": prediction["margin"],
                     "accepted": prediction["accepted"]})
    groups = {}
    for name, selected in (("known_train", [r for r in rows if r["split"] == "train"]),
                           ("known_dev", [r for r in rows if r["split"] == "val" and r["role"] == "known"]),
                           ("unknown_dev", [r for r in rows if r["role"] == "unknown"])):
        groups[name] = {"n": len(selected)}
        for field in ("standardized_rms", "max_abs_standardized", "fraction_abs_over_5", "active_frames", "gate_score"):
            values = [r[field] for r in selected]
            groups[name][field] = {"p50": float(np.median(values)), "p95": float(np.percentile(values, 95)),
                                  "min": float(min(values)), "max": float(max(values))}
    per_class = {}
    for label in model.classes:
        selected = [r for r in rows if r["split"] == "val" and r["role"] == "known" and r["label"] == label]
        if selected:
            per_class[label] = {"n": len(selected), "forced_correct": sum(r["candidate"] == label for r in selected),
                                "accepted_correct": sum(r["candidate"] == label and r["accepted"] for r in selected)}
    report = {"experiment": "R007_audit", "manifest_sha256": manifest_hash,
              "groups": groups, "known_dev_per_class": per_class, "test_evaluated": False,
              "scope": "Whole available clips; diagnostics only, no threshold tuning or model change"}
    Path("artifacts/recognition/rejection_audit.json").write_text(json.dumps(report, indent=2))
    Path("artifacts/recognition/private/rejection_audit_clips.json").write_text(json.dumps(rows, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
