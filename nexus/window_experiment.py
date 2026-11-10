"""R004: align visible-hand training windows, then ablate short-sign policy.

Candidate model is saved separately; never silently replaces the app model.
All thresholds use development data and are not independent validation.
"""
import json
import time
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression

from nexus.features import sequence_vector, active_sequence
from nexus.model import SignModel
from nexus.replay import evaluate, load_samples


def main():
    started = time.perf_counter()
    samples, manifest_hash = load_samples()
    original = SignModel("models/signs-baseline.npz")
    vectors = [sequence_vector(*active_sequence(frames, times), original.metadata["steps"])
               for _, frames, times in samples]
    x = np.asarray(vectors)
    y = np.array([s["label"] for s, _, _ in samples])
    train = np.array([s["split"] == "train" for s, _, _ in samples])
    known = np.array([s["split"] == "val" and s["role"] == "known" for s, _, _ in samples])
    unknown = np.array([s["role"] == "unknown" for s, _, _ in samples])
    mean, scale = x[train].mean(0), np.maximum(x[train].std(0), .05)
    x = (x - mean) / scale
    clf = LogisticRegression(C=.1, class_weight="balanced", max_iter=2000, random_state=20261107)
    clf.fit(x[train], y[train])
    scores = clf.decision_function(x)
    sorted_scores = np.sort(scores, axis=1)
    margins = sorted_scores[:, -1] - sorted_scores[:, -2]
    threshold = float(np.nextafter(np.quantile(margins[unknown], .9, method="higher"), np.inf))
    predicted = clf.classes_[scores.argmax(1)]
    accepted = margins >= threshold
    metadata = {**original.metadata, "rejection_margin": threshold,
                "sequence_policy": "visible_hands_last_4s", "manifest_sha256": manifest_hash,
                "experiment": "R004", "calibration": "same observed unknown dev set; not independently validated"}
    np.savez_compressed("models/signs-active-candidate.npz", mean=mean, scale=scale,
                        coef=clf.coef_, intercept=clf.intercept_, classes=clf.classes_, metadata=json.dumps(metadata))
    candidate = SignModel("models/signs-active-candidate.npz")
    short_policy = {"min_seconds": .25, "min_frames": 3, "finalize_on_release": True}
    report = {"experiment": "R004", "test_evaluated": False, "promoted": False,
              "manifest_sha256": manifest_hash,
              "aligned_complete_clip_accuracy": float((predicted[known] == y[known]).mean()),
              "aligned_complete_clip_known_accepted": int(accepted[known].sum()),
              "aligned_complete_clip_correct_accepted": int(((predicted == y) & accepted & known).sum()),
              "unknown_calibration_rejected": int((~accepted[unknown]).sum()),
              "ablation": {}, "short_policy": short_policy,
              "limitations": ["Previously observed development set", "No new negative webcam examples",
                              "Cached-feature replay is not wall-clock real-time", "No synthetic trailing frames; unfinished attempts stay unfinished"]}
    for name, model, policy in [("baseline_original_engine", original, {}),
                                ("aligned_original_engine", candidate, {}),
                                ("baseline_short_engine", original, short_policy),
                                ("aligned_short_engine", candidate, short_policy)]:
        report["ablation"][name] = evaluate(model, samples, policy)[0]
    report["wall_s"] = time.perf_counter() - started
    Path("artifacts/recognition/window_experiment.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
