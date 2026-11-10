"""Original-timing video replay through decoding, landmarks and recognition.

No browser/network is involved. Sign semantic latency is not measured. Frames
that are stale are dropped instead of accumulating an unbounded queue.
"""
import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np

from nexus.engine import RecognitionSession
from nexus.features import LandmarkExtractor
from nexus.model import SignModel


def run_clip(path, model):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not cap.isOpened() or not np.isfinite(fps) or fps <= 0:
        cap.release()
        raise ValueError("Missing source FPS/video")
    detector = LandmarkExtractor()
    session = RecognitionSession(model, min_seconds=.25, min_frames=3, finalize_on_release=True)
    processed = dropped = sampled_out = index = 0
    timings, ages, events = [], [], []
    next_sample = 0.
    started = time.perf_counter()
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            # ASL Citizen source clips are CFR. Source frame availability is
            # index/FPS, never the time at which fast decoding returns it.
            timestamp = index / fps
            index += 1
            if timestamp > 30:
                raise ValueError("Replay duration cap exceeded")
            now = time.perf_counter() - started
            if timestamp > now:
                time.sleep(timestamp - now)
            if timestamp + 1e-6 < next_sample:
                sampled_out += 1
                continue
            if time.perf_counter() - started - timestamp > .25:
                dropped += 1
                continue
            next_sample = timestamp + 1 / 6
            before = time.perf_counter()
            points, quality, _ = detector.process(frame)
            result = session.update(points, quality, timestamp)
            timings.append((time.perf_counter() - before) * 1000)
            ages.append((time.perf_counter() - started - timestamp) * 1000)
            processed += 1
            if result.get("event"):
                events.append({"label": result["event"]["label"], "source_evidence_end_s": timestamp,
                               "emitted_elapsed_s": time.perf_counter() - started})
    finally:
        detector.close()
        cap.release()
    return {"processed_frames": processed, "stale_dropped_frames": dropped, "sampling_skipped_frames": sampled_out,
            "decoded_frames": index, "wall_s": time.perf_counter() - started,
            "processing_ms_p50": float(np.median(timings)) if timings else None,
            "frame_result_age_ms_p95": float(np.percentile(ages, 95)) if ages else None,
            "events": events, "max_inflight": 1, "timestamp_source": "CFR index/FPS"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/signs-active-candidate.npz")
    args = parser.parse_args()
    samples = json.loads(Path("data/asl_citizen/manifest.json").read_text())["samples"]
    # Fixed selection by manifest order, before running predictions.
    chosen = [s for s in samples if s["split"] == "val" and s["role"] == "known"][:3]
    model = SignModel(args.model)
    public, private = [], []
    for sample in chosen:
        result = run_clip(sample["path"], model)
        private.append({"id": sample["id"], "reference": sample["label"], **result})
        public.append(result)
        print(f"Completed timed replay {len(public)}/{len(chosen)}", flush=True)
    report = {"mode": "original-timing CFR video replay; local decoder/landmarks/engine",
              "selection": "first three known validation clips in existing manifest order",
              "model": Path(args.model).name, "test_evaluated": False, "clips": public,
              "limitations": ["No browser/network/camera", "Frame-result age is not semantic sign latency",
                              "Three predetermined clips are an engineering smoke check, not a quality benchmark"]}
    Path("artifacts/recognition/timed_replay.json").write_text(json.dumps(report, indent=2))
    Path("artifacts/recognition/private/timed_clips.json").write_text(json.dumps(private, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
