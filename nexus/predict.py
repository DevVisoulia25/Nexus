"""Recognize one complete isolated-sign video with the same local feature path."""
import argparse
import json
import time

from nexus.extract import extract_video
from nexus.model import SignModel


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("--model", default="models/signs.npz")
    args = parser.parse_args()
    started = time.perf_counter()
    frames, timestamps, stats = extract_video(args.video, sample_fps=6, max_seconds=30)
    model = SignModel(args.model)
    t = time.perf_counter()
    prediction = model.predict(frames, timestamps)
    decode_ms = (time.perf_counter() - t) * 1000
    print(json.dumps({"prediction": prediction, "features": stats, "classifier_ms": decode_ms,
                      "wall_s": time.perf_counter() - started,
                      "note": "Whole isolated clip diagnostic; margin is not calibrated confidence."}, indent=2))


if __name__ == "__main__":
    main()
