"""R006: explicit training-negative class for the aligned linear model.

This tests a background-class rejection approach, not an architecture-size
increase. Calibration remains development-only; no automatic app promotion.
"""
import hashlib
import argparse
import json
import time
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

from nexus.features import FEATURE_VERSION, active_sequence, model_vector
from nexus.model import SignModel
from nexus.replay import evaluate, load_samples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--handshape", action="store_true", help="R007: change only feature representation")
    args = parser.parse_args()
    experiment = "R007" if args.handshape else "R006"
    representation = "body_plus_handshape_v1" if args.handshape else "body_v1"
    suffix = "handshape" if args.handshape else "background"
    started = time.perf_counter()
    samples, original_hash = load_samples()
    background_path = Path("data/asl_citizen/background_manifest.json")
    background = json.loads(background_path.read_text())["samples"]
    dev_signers = {s["signer"] for s, _, _ in samples if s["split"] == "val"}
    ids = {s["id"] for s, _, _ in samples}
    excluded = []
    for sample in background:
        if sample["split"] != "train" or sample["role"] != "background" or sample["signer"] in dev_signers or sample["id"] in ids:
            raise ValueError("Background split or duplication violation")
        ids.add(sample["id"])
        with np.load(Path("features/asl_citizen") / (sample["id"] + ".npz"), allow_pickle=False) as data:
            if str(data["version"]) != FEATURE_VERSION or str(data["source_sha256"]) != sample["sha256"]:
                raise ValueError("Stale background cache")
            f, t = data["frames"], data["timestamps"]
        try:
            active_sequence(f, t)
        except ValueError:
            excluded.append(sample["id"])
            continue
        samples.append((sample, f, t))
    x = np.array([model_vector(*active_sequence(f, t), 24, representation) for _, f, t in samples])
    y = np.array([s["label"] for s, _, _ in samples])
    train = np.array([s["split"] == "train" for s, _, _ in samples])
    known = np.array([s["split"] == "val" and s["role"] == "known" for s, _, _ in samples])
    unknown = np.array([s["role"] == "unknown" for s, _, _ in samples])
    mean, scale = x[train].mean(0), np.maximum(x[train].std(0), .05)
    x = (x - mean) / scale
    clf = LogisticRegression(C=.1, class_weight="balanced", max_iter=2000, random_state=20261107)
    clf.fit(x[train], y[train])
    scores = clf.decision_function(x)
    other = list(clf.classes_).index("__OTHER__")
    known_indices = [i for i in range(len(clf.classes_)) if i != other]
    top = np.array(known_indices)[scores[:, known_indices].argmax(1)]
    gaps = scores[np.arange(len(scores)), top] - scores[:, other]
    # Strict comparison at an observed quantile avoids scalar rounding issues.
    threshold = max(0., float(np.quantile(gaps[unknown], .9, method="higher")))
    accepted = gaps > threshold
    predictions = clf.classes_[top]
    metadata = {"feature_version": FEATURE_VERSION, "steps": 24, "sequence_policy": "visible_hands_last_4s",
                "rejection_kind": "background_logit_gap", "background_threshold": threshold,
                "model_kind": "temporal_logistic_regression", "experiment": experiment, "seed": 20261107,
                "representation": representation,
                "manifest_sha256": original_hash, "background_manifest_sha256": hashlib.sha256(background_path.read_bytes()).hexdigest(),
                "calibration": "Observed 20 unknown dev clips; not independent validation", "experimental": True}
    path = Path(f"models/signs-{suffix}-candidate.npz")
    np.savez_compressed(path, mean=mean, scale=scale, coef=clf.coef_, intercept=clf.intercept_,
                        classes=clf.classes_, metadata=json.dumps(metadata))
    model = SignModel(path)
    policy = {"min_seconds": .25, "min_frames": 3, "finalize_on_release": True}
    replay, rows = evaluate(model, samples, policy)
    zero_metadata = {**model.metadata, "background_threshold": 0.}
    model.metadata = zero_metadata
    zero_replay, _ = evaluate(model, samples, policy)
    report = {"experiment": experiment, "hypothesis": "Hand-relative geometry improves known/unknown separation" if args.handshape else "Explicit training-negative examples improve rejection of non-vocabulary signs",
              "changed_factors": "Only feature representation versus R006; data, linear architecture, C, seed and gate rule unchanged" if args.handshape else "Additional training negatives, explicit background output and background-logit rejection; architecture and C unchanged",
              "train_known": 147, "train_background_used": len(background) - len(excluded), "background_excluded_insufficient_tracking": len(excluded),
              "known_clips": int(known.sum()), "whole_clip_correct_forced_known": int((predictions[known] == y[known]).sum()),
              "whole_known_correct_accepted": int(((predictions == y) & accepted & known).sum()),
              "unknown_calibration_rejected": int((~accepted[unknown]).sum()),
              "replay_calibrated": replay, "replay_background_threshold_zero": zero_replay,
              "wall_s": time.perf_counter() - started, "metadata": metadata,
              "promoted": False, "test_evaluated": False,
              "limitations": ["Same observed development set used for calibration", "No ordinary-movement negatives",
                              "Cached replay not real-time latency", "No independent webcam or ASL reviewer validation"]}
    Path(f"artifacts/recognition/{suffix}_experiment.json").write_text(json.dumps(report, indent=2))
    Path(f"artifacts/recognition/private/{suffix}_clips.json").write_text(json.dumps({"rows": rows, "excluded_training_ids": excluded}, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
