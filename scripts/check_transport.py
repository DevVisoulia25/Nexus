"""Local WebSocket integration check using generated blank frames, not a camera.

Requires a trained model and running local server. No visual content is uploaded
outside loopback. Exercises real decoding/landmarks and reconnect behavior.
"""
import asyncio
import argparse
import json
import struct
import time
from pathlib import Path

import cv2
import numpy as np
from websockets.asyncio.client import connect


async def main(port=8765, output="artifacts/recognition/transport.json"):
    _, jpg = cv2.imencode(".jpg", np.zeros((480, 640, 3), np.uint8))
    timings = []
    for attempt in range(2):
        async with connect(f"ws://127.0.0.1:{port}/ws", origin=f"http://127.0.0.1:{port}", max_size=512*1024) as ws:
            ready = json.loads(await asyncio.wait_for(ws.recv(), 15))
            assert ready["type"] == "ready"
            for seq in range(5):
                timestamp = time.perf_counter() * 1000
                await ws.send(struct.pack("<dI", timestamp, seq) + jpg.tobytes())
                result = json.loads(await asyncio.wait_for(ws.recv(), 10))
                assert result["seq"] == seq and result["quality"]["hands"] == 0
                assert result["result"].get("event") is None and result["result"]["label"] is None
                timings.append(time.perf_counter() * 1000 - timestamp)
        await asyncio.sleep(0.5)
    report = {"sessions": 2, "blank_frames": 10, "false_events": 0, "port": port,
              "roundtrip_ms_p50": float(np.median(timings)), "roundtrip_ms_p95": float(np.percentile(timings, 95)),
              "scope": "Generated blank frames through actual local WebSocket/decoder/landmark path; not ASL or webcam validation"}
    Path("artifacts/recognition").mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--output", default="artifacts/recognition/transport.json")
    args = parser.parse_args()
    asyncio.run(main(args.port, args.output))
