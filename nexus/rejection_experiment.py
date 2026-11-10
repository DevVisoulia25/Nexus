"""R002: change only the rejection gate; preserve classifier and features.

Compare visual distance to training examples against classifier score margin,
at the same observed negative-development rejection rate. This is development
calibration, never a final-test result. Retain the baseline if coverage worsens.
"""
import json
from pathlib import Path

import numpy as np

from nexus.features import sequence_vector


def main():
    path = Path("models/signs.npz")
    original = path.read_bytes()
    with np.load(path, allow_pickle=False) as data:
        arrays = {key: data[key] for key in data.files}
    metadata = json.loads(str(arrays["metadata"]))
    if metadata.get("rejection_kind") == "nearest_training_distance":
        raise ValueError("R002 already applied; run nexus.train first to regenerate the original baseline")
    manifest = json.loads(Path("data/asl_citizen/manifest.json").read_text())
    samples = manifest["samples"]
    vectors = []
    for sample in samples:
        with np.load(Path("features/asl_citizen") / (sample["id"] + ".npz"), allow_pickle=False) as data:
            vectors.append(sequence_vector(data["frames"], data["timestamps"], metadata["steps"]))
    x = (np.asarray(vectors) - arrays["mean"]) / arrays["scale"]
    train = np.array([s["split"] == "train" for s in samples])
    known = np.array([s["split"] == "val" and s["role"] == "known" for s in samples])
    unknown = np.array([s["role"] == "unknown" for s in samples])
    scores = x @ arrays["coef"].T + arrays["intercept"]
    predictions = arrays["classes"][scores.argmax(1)]
    correct = predictions == np.array([s["label"] for s in samples])
    distances = np.sqrt(np.maximum(((x[:, None, :] - x[train][None, :, :]) ** 2).mean(-1), 0)).min(1)
    # 20 negative dev examples: accept strictly below the second smallest
    # distance, matching the original gate's one accepted negative example.
    threshold = float(np.nextafter(np.sort(distances[unknown])[1], -np.inf))
    accepted = distances < threshold
    baseline = json.loads(Path("artifacts/recognition/baseline.json").read_text())
    coverage = float(accepted[known].mean())
    correct_accepted = float((accepted & correct)[known].mean())
    reject = float((~accepted[unknown]).mean())
    retain = correct_accepted > baseline["known_correct_and_accepted_rate"] and reject >= baseline["unknown_rejection_rate_calibration_set"]
    report = {"experiment": "R002", "hypothesis": "Distance to training visual features offers better rejection than score margin",
              "changed_factor": "rejection gate only; identical features, classifier, examples and observed negative rejection target",
              "baseline_known_coverage": baseline["known_coverage_after_rejection"], "candidate_known_coverage": coverage,
              "baseline_correct_and_accepted": baseline["known_correct_and_accepted_rate"], "candidate_correct_and_accepted": correct_accepted,
              "baseline_unknown_rejection": baseline["unknown_rejection_rate_calibration_set"], "candidate_unknown_rejection": reject,
              "distance_threshold": threshold, "retained": retain, "test_evaluated": False,
              "limitation": "Same small development set used to calibrate and select; ordinary movement and webcam behavior untested"}
    if retain:
        Path("models/signs-baseline.npz").write_bytes(original)
        metadata["rejection_kind"] = "nearest_training_distance"
        metadata["distance_threshold"] = threshold
        metadata["calibration"] = "R002 distance gate at same 95% negative-development rejection as baseline; not independently validated"
        arrays["metadata"] = np.array(json.dumps(metadata))
        arrays["reference_vectors"] = x[train].astype(np.float32)
        np.savez_compressed(path, **arrays)
    Path("artifacts/recognition/rejection_experiment.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
