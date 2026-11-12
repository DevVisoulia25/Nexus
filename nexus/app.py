"""Loopback-only webcam app. Frames are processed in memory, never saved."""
from __future__ import annotations

import asyncio
import argparse
import hashlib
from concurrent.futures import ThreadPoolExecutor
import json
import struct
import time
from pathlib import Path
from urllib.parse import urlparse

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from nexus.engine import RecognitionSession
from nexus.features import LandmarkExtractor
from nexus.model import SignModel
from nexus.diagnostics import DiagnosticModel

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs/recognition.json").read_text())
app = FastAPI(title="Nexus", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=ROOT / "web"), name="static")
active_sessions = 0
MODEL_PATH = ROOT / "models/signs.npz"
SESSION_OPTIONS = {}


@app.get("/")
def index():
    return FileResponse(ROOT / "web/index.html")


@app.get("/api/status")
def status():
    report_path = ROOT / "artifacts/recognition/baseline.json"
    report = json.loads(report_path.read_text()) if report_path.exists() and MODEL_PATH == ROOT / "models/signs.npz" else None
    return {"model_ready": MODEL_PATH.exists(), "model_name": MODEL_PATH.name,
            "recognition_validated": False, "session_options": SESSION_OPTIONS, "labels": CONFIG["display_labels"],
            "experimental": True, "retention": "Server saves no camera frames or landmarks. Guided browser recording is optional and local.",
            "evaluation": None if not report else {k: report[k] for k in (
                "status", "known_dev_n", "closed_set_accuracy", "known_coverage_after_rejection", "test_evaluated")}}


def packet_header(payload):
    if len(payload) < 16 or len(payload) > 512 * 1024:
        raise ValueError("Frame payload outside size limit")
    timestamp_ms, seq = struct.unpack("<dI", payload[:12])
    if not np.isfinite(timestamp_ms) or timestamp_ms < 0:
        raise ValueError("Invalid capture timestamp")
    return timestamp_ms / 1000, seq


def decode_packet(payload):
    timestamp, seq = packet_header(payload)
    image = cv2.imdecode(np.frombuffer(payload[12:], np.uint8), cv2.IMREAD_COLOR)
    if image is None or image.shape[0] * image.shape[1] > 1280 * 720:
        raise ValueError("Invalid frame or resolution above 720p")
    return timestamp, seq, image


@app.websocket("/ws")
async def webcam(websocket: WebSocket):
    global active_sessions
    # Only a page served by this exact local server may open a browser session.
    origin = websocket.headers.get("origin", "")
    parsed = urlparse(origin)
    if parsed.scheme not in {"http", "https"} or parsed.netloc != websocket.headers.get("host") or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        await websocket.close(code=1008, reason="Open Nexus from the local server")
        return
    if active_sessions >= 1:
        await websocket.close(code=1013, reason="One active camera session at a time")
        return
    if not MODEL_PATH.exists():
        await websocket.close(code=1013, reason="Train the local model first")
        return
    active_sessions += 1
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_running_loop()
    extractor = None
    try:
        await websocket.accept()
        extractor = await loop.run_in_executor(executor, LandmarkExtractor)
        model = DiagnosticModel(SignModel(MODEL_PATH))
        session = RecognitionSession(model, max_seconds=CONFIG["max_window_seconds"], **SESSION_OPTIONS)
        await websocket.send_json({"type": "ready", "model": {"name": MODEL_PATH.name,
                                  "sha256": hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest(),
                                  "metadata": model.model.metadata},
                                  "session_options": {"max_seconds": CONFIG["max_window_seconds"],
                                                      "min_seconds": session.min_seconds, "min_frames": session.min_frames,
                                                      "finalize_on_release": session.finalize_on_release}})
        last_seq = -1

        def process(payload):
            started = time.perf_counter()
            timestamp, seq, frame = decode_packet(payload)
            points, quality, overlay = extractor.process(frame)
            model.begin_frame()
            result = session.update(points, quality, timestamp)
            return {"type": "frame", "seq": seq, "capture_ms": timestamp * 1000,
                    "processing_ms": (time.perf_counter() - started) * 1000,
                    "quality": quality, "points": overlay.tolist(), "result": result,
                    "diagnostics": list(model.decisions)}

        while True:
            # Browser sends the next frame only after the prior response.
            payload = await asyncio.wait_for(websocket.receive_bytes(), timeout=15)
            # Decode JPEG only once, inside the worker. Header validation is
            # cheap and does not block the async server with image processing.
            _, seq = packet_header(payload)
            if seq <= last_seq:
                raise ValueError("Stale frame sequence")
            last_seq = seq
            result = await loop.run_in_executor(executor, process, payload)
            await websocket.send_json(result)
    except WebSocketDisconnect:
        pass
    except (ValueError, asyncio.TimeoutError):
        try:
            await websocket.close(code=1008, reason="Invalid or stalled session; start again")
        except RuntimeError:
            pass
    except Exception:
        try:
            await websocket.close(code=1011, reason="Processing failed; stop and start again")
        except RuntimeError:
            pass
        raise
    finally:
        if extractor is not None:
            await loop.run_in_executor(executor, extractor.close)
        executor.shutdown(wait=False, cancel_futures=True)
        active_sessions -= 1


def main():
    global MODEL_PATH, SESSION_OPTIONS
    import uvicorn
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=str(MODEL_PATH))
    parser.add_argument("--short-signs", action="store_true", help="Experimental short-sign boundary policy")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    MODEL_PATH = Path(args.model).resolve()
    if args.short_signs:
        SESSION_OPTIONS = {"min_seconds": .25, "min_frames": 3, "finalize_on_release": True}
    uvicorn.run(app, host="127.0.0.1", port=args.port, ws_max_size=512 * 1024, ws_max_queue=1, access_log=False)


if __name__ == "__main__":
    main()
