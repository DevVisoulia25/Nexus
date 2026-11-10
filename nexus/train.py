"""Fit one regularized linear baseline on train only; report dev honestly."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

from nexus.features import FEATURE_VERSION, sequence_vector


def main():
    config = json.loads(Path("configs/recognition.json").read_text())
    manifest_file = Path("data/asl_citizen/manifest.json")
    manifest = json.loads(manifest_file.read_text())
    samples = manifest["samples"]
    X, y = [], []
    for sample in samples:
        with np.load(Path("features/asl_citizen") / (sample["id"] + ".npz"), allow_pickle=False) as data:
            if str(data["version"]) != FEATURE_VERSION or str(data["source_sha256"]) != sample["sha256"]:
                raise ValueError("Stale or mismatched feature cache")
            X.append(sequence_vector(data["frames"], data["timestamps"], config["sequence_steps"]))
        y.append(sample["label"])
    X, y = np.asarray(X), np.asarray(y)
    train = np.array([s["split"] == "train" for s in samples])
    known = np.array([s["split"] == "val" and s["role"] == "known" for s in samples])
    unknown = np.array([s["role"] == "unknown" for s in samples])
    if {s["signer"] for s in samples if s["split"] == "train"} & {s["signer"] for s in samples if s["split"] == "val"}:
        raise ValueError("Signer overlap")
    mean = X[train].mean(0)
    scale = np.maximum(X[train].std(0), 0.05)
    standardized = (X - mean) / scale
    start = time.perf_counter()
    clf = LogisticRegression(C=0.1, class_weight="balanced", max_iter=2000, random_state=config["seed"])
    clf.fit(standardized[train], y[train])
    fit_s = time.perf_counter() - start
    scores = clf.decision_function(standardized)
    sorted_scores = np.sort(scores, axis=1)
    margins = sorted_scores[:, -1] - sorted_scores[:, -2]
    predictions = clf.classes_[scores.argmax(1)]
    # Predeclared criterion: reject at least 90% of the 20 negative DEV clips.
    # This is calibration on dev, not independent rejection performance.
    threshold = float(np.nextafter(np.quantile(margins[unknown], 0.9, method="higher"), np.inf))
    accepted = margins >= threshold
    metadata = {"feature_version": FEATURE_VERSION, "steps": config["sequence_steps"],
                "rejection_margin": threshold, "seed": config["seed"], "model_kind": "temporal_logistic_regression",
                "manifest_sha256": hashlib.sha256(manifest_file.read_bytes()).hexdigest(),
                "config_sha256": hashlib.sha256(Path("configs/recognition.json").read_bytes()).hexdigest(),
                "calibration": "90th percentile of held-out-label development margins; not independent validation",
                "dataset": "ASL Citizen", "experimental": True}
    Path("models").mkdir(exist_ok=True)
    np.savez_compressed("models/signs.npz", mean=mean, scale=scale, coef=clf.coef_, intercept=clf.intercept_,
                        classes=clf.classes_, metadata=json.dumps(metadata))
    report = {"status": "development_only", "train_n": int(train.sum()), "known_dev_n": int(known.sum()),
              "unknown_dev_n": int(unknown.sum()), "fit_s": fit_s,
              "closed_set_accuracy": accuracy_score(y[known], predictions[known]),
              "closed_set_macro_f1": f1_score(y[known], predictions[known], average="macro"),
              "known_coverage_after_rejection": float(accepted[known].mean()),
              "known_correct_and_accepted_rate": float(((predictions == y) & accepted)[known].mean()),
              "unknown_rejection_rate_calibration_set": float((~accepted[unknown]).mean()),
              "classification_report": classification_report(y[known], predictions[known], output_dict=True, zero_division=0),
              "confusion_labels": clf.classes_.tolist(),
              "confusion_matrix": confusion_matrix(y[known], predictions[known], labels=clf.classes_).tolist(),
              "metadata": metadata, "test_evaluated": False,
              "limitations": ["Only ten known classes", "39 known development clips", "Rejection calibrated on same negative development set",
                              "No ordinary-movement negatives or independent webcam evaluation yet", "No competent ASL semantic review"]}
    Path("artifacts/recognition").mkdir(parents=True, exist_ok=True)
    Path("artifacts/recognition/baseline.json").write_text(json.dumps(report, indent=2))
    private = Path("artifacts/recognition/private")
    private.mkdir(exist_ok=True)
    (private / "predictions.json").write_text(json.dumps([{"id": s["id"], "reference": s["label"], "split": s["split"],
                                                          "role": s["role"], "predicted": str(p), "accepted": bool(a), "margin": float(m)}
                                                         for s, p, a, m in zip(samples, predictions, accepted, margins)], indent=2))
    print(json.dumps({k: v for k, v in report.items() if k not in {"classification_report", "confusion_matrix", "metadata"}}, indent=2))


if __name__ == "__main__":
    main()
