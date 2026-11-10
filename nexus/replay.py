"""Causal cached-feature replay diagnostic; no future frames or test examples.

Runs without sleeping: this measures recognition decisions, NOT real-time
throughput, camera processing latency, or end-to-end caption latency.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from nexus.engine import RecognitionSession
from nexus.features import FEATURE_VERSION, quality_from_points
from nexus.model import SignModel


def load_samples():
    manifest_path = Path("data/asl_citizen/manifest.json")
    manifest = json.loads(manifest_path.read_text())
    train_signers = {s["signer"] for s in manifest["samples"] if s["split"] == "train"}
    dev_signers = {s["signer"] for s in manifest["samples"] if s["split"] == "val"}
    if train_signers & dev_signers:
        raise ValueError("Signer leakage")
    result = []
    for sample in manifest["samples"]:
        if sample["split"] not in {"train", "val"}:
            raise ValueError("Diagnostic must not access final test")
        with np.load(Path("features/asl_citizen") / (sample["id"] + ".npz"), allow_pickle=False) as data:
            if str(data["version"]) != FEATURE_VERSION or str(data["source_sha256"]) != sample["sha256"]:
                raise ValueError("Stale feature cache")
            result.append((sample, data["frames"], data["timestamps"]))
    return result, hashlib.sha256(manifest_path.read_bytes()).hexdigest()


class Observer:
    def __init__(self, model, forced=False):
        self.model, self.forced = model, forced
        self.predictions = []

    def predict(self, frames, times):
        result = self.model.predict(frames, times)
        self.predictions.append(result)
        return {**result, "label": result["candidate"] if self.forced else result["label"]}


def replay(model, frames, times, forced=False, session_options=None):
    observer = Observer(model, forced)
    session = RecognitionSession(observer, **(session_options or {}))
    events = []
    for frame, timestamp in zip(frames, times):
        result = session.update(frame, quality_from_points(frame), float(timestamp))
        if result.get("event"):
            events.append({**result["event"], "timestamp_s": float(timestamp)})
    return events, observer.predictions


def evaluate(model, samples, session_options=None):
    rows = []
    for sample, frames, times in samples:
        if sample["split"] != "val":
            continue
        whole = model.predict(frames, times)
        events, predictions = replay(model, frames, times, session_options=session_options)
        forced_events, _ = replay(model, frames, times, forced=True, session_options=session_options)
        rows.append({"id": sample["id"], "role": sample["role"], "reference": sample["label"],
                     "whole_candidate": whole["candidate"], "whole_accepted": whole["accepted"],
                     "events": events, "forced_events": forced_events,
                     "decode_count": len(predictions),
                     "accepted_windows": sum(p["accepted"] for p in predictions)})
    known = [r for r in rows if r["role"] == "known"]
    unknown = [r for r in rows if r["role"] == "unknown"]
    summary = {"known_clips": len(known), "unknown_clips": len(unknown),
               "whole_clip_correct": sum(r["whole_candidate"] == r["reference"] for r in known),
               "known_clips_without_decodes": sum(r["decode_count"] == 0 for r in known),
               "known_clips_with_any_event": sum(bool(r["events"]) for r in known),
               "known_first_event_correct": sum(bool(r["events"]) and r["events"][0]["label"] == r["reference"] for r in known),
               "known_first_forced_event_correct": sum(bool(r["forced_events"]) and r["forced_events"][0]["label"] == r["reference"] for r in known),
               "unknown_clips_with_false_event": sum(bool(r["events"]) for r in unknown)}
    return summary, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/signs.npz")
    parser.add_argument("--output", default="artifacts/recognition/replay.json")
    args = parser.parse_args()
    samples, manifest_hash = load_samples()
    summary, rows = evaluate(SignModel(args.model), samples)
    report = {"experiment": "R003", "manifest_sha256": manifest_hash,
              "model_sha256": hashlib.sha256(Path(args.model).read_bytes()).hexdigest(),
              "mode": "causal cached-feature diagnostic, accelerated execution",
              "limitations": ["Not real-time replay or latency measurement", "Quality flags reconstructed from cached masks",
                              "Small previously observed development set", "No ordinary-movement negatives"],
              "test_evaluated": False, **summary}
    Path(args.output).write_text(json.dumps(report, indent=2))
    private = Path("artifacts/recognition/private")
    private.mkdir(parents=True, exist_ok=True)
    (private / (Path(args.output).stem + "_clips.json")).write_text(json.dumps(rows, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
