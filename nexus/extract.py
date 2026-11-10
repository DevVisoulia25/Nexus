"""Cache CPU landmark sequences from a fixed local manifest."""
from __future__ import annotations

import hashlib
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import cv2
import numpy as np

from nexus.features import FEATURE_VERSION, LandmarkExtractor


def extract_video(path, sample_fps=12, max_seconds=15):
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError("Cannot decode video")
    fps = capture.get(cv2.CAP_PROP_FPS)
    if not np.isfinite(fps) or fps <= 0:
        capture.release()
        raise ValueError("Missing source FPS")
    detector = LandmarkExtractor()
    frames, timestamps, qualities, timings = [], [], [], []
    index, next_sample, last_time = 0, 0.0, -1.0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            pts = capture.get(cv2.CAP_PROP_POS_MSEC) / 1000
            # These dataset clips are CFR; document fallback for decoders without PTS.
            timestamp = pts if pts > last_time else index / fps
            index += 1
            last_time = timestamp
            if timestamp > max_seconds:
                raise ValueError("Clip exceeds declared duration cap; not silently truncated")
            if timestamp + 1e-6 < next_sample:
                continue
            started = time.perf_counter()
            points, quality, _ = detector.process(frame)
            timings.append(time.perf_counter() - started)
            frames.append(points)
            timestamps.append(timestamp)
            qualities.append(quality)
            next_sample = timestamp + 1 / sample_fps
    finally:
        capture.release()
        detector.close()
    if len(frames) < 2:
        raise ValueError("Insufficient decoded frames")
    return np.asarray(frames), np.asarray(timestamps), {
        "frames": len(frames), "duration_s": timestamps[-1] - timestamps[0],
        "body_fraction": sum(q["body"] for q in qualities) / len(qualities),
        "hand_fraction": sum(q["hands"] > 0 for q in qualities) / len(qualities),
        "extraction_s": sum(timings), "frame_ms_p50": float(np.median(timings) * 1000),
        "frame_ms_p95": float(np.percentile(timings, 95) * 1000),
    }


def extract_sample(args):
    sample, output, config = args
    target = output / (sample["id"] + ".npz")
    try:
        if hashlib.sha256(Path(sample["path"]).read_bytes()).hexdigest() != sample["sha256"]:
            raise ValueError("Source video hash mismatch")
        if target.exists():
            with np.load(target, allow_pickle=False) as cached:
                if str(cached["version"]) != FEATURE_VERSION or float(cached["sample_fps"]) != config["sample_fps"] or str(cached["source_sha256"]) != sample["sha256"]:
                    raise ValueError("Stale feature cache; remove this cache explicitly")
                stats = json.loads(str(cached["stats"]))
        else:
            frames, timestamps, stats = extract_video(sample["path"], config["sample_fps"], config["max_video_seconds"])
            np.savez_compressed(target, frames=frames, timestamps=timestamps, stats=json.dumps(stats),
                                version=FEATURE_VERSION, sample_fps=config["sample_fps"], source_sha256=sample["sha256"])
        return {"id": sample["id"], **stats}, None
    except Exception as exc:
        return None, {"id": sample["id"], "error": str(exc)}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, choices=[1, 2], default=1)
    args = parser.parse_args()
    config = json.loads(Path("configs/recognition.json").read_text())
    manifest_path = Path("data/asl_citizen/manifest.json")
    manifest = json.loads(manifest_path.read_text())
    output = Path("features/asl_citizen")
    output.mkdir(parents=True, exist_ok=True)
    report = {"feature_version": FEATURE_VERSION, "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
              "sample_fps": config["sample_fps"], "samples": [], "failures": []}
    started = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for i, (stats, error) in enumerate(pool.map(extract_sample, [(s, output, config) for s in manifest["samples"]])):
            if error:
                report["failures"].append(error)
            else:
                report["samples"].append(stats)
            report["wall_s"] = time.perf_counter() - started
            report["workers"] = args.workers
            (output / "report.json").write_text(json.dumps(report, indent=2))
            print(f"Extracted {i+1}/{len(manifest['samples'])}; failures={len(report['failures'])}", flush=True)
    if report["failures"]:
        raise SystemExit("Feature failures: see features/asl_citizen/report.json; do not silently drop them")


if __name__ == "__main__":
    main()
