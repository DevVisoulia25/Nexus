import json
import struct

import cv2
import numpy as np
from fastapi.testclient import TestClient

from nexus.app import app
from nexus.features import POINTS


def test_websocket_decisions_are_new_per_frame_and_include_provenance(tmp_path, monkeypatch):
    model_path = tmp_path / "model.npz"
    model_path.write_bytes(b"test-model-provenance")
    monkeypatch.setattr("nexus.app.MODEL_PATH", model_path)

    class Model:
        metadata = {"experimental": True}

        def __init__(self, path):
            pass

        def predict(self, frames, times):
            return {"candidate": "BOOK", "accepted": False, "label": None, "margin": 1.5}

    class Extractor:
        def process(self, image):
            points = np.ones((POINTS, 3), np.float32)
            return points, {"body": True, "hands": 1, "face": True}, points

        def close(self):
            pass

    monkeypatch.setattr("nexus.app.SignModel", Model)
    monkeypatch.setattr("nexus.app.LandmarkExtractor", Extractor)
    _, jpeg = cv2.imencode(".jpg", np.zeros((32, 32, 3), np.uint8))
    with TestClient(app) as client, client.websocket_connect("/ws", headers={"origin": "http://localhost", "host": "localhost"}) as ws:
        ready = ws.receive_json()
        assert ready["model"]["name"] == "model.npz" and len(ready["model"]["sha256"]) == 64
        responses = []
        for i in range(7):
            ws.send_bytes(struct.pack("<dI", i * 200., i) + jpeg.tobytes())
            responses.append(ws.receive_json())
        assert responses[5]["diagnostics"][0]["candidate"] == "BOOK"
        assert not responses[5]["diagnostics"][0]["accepted"]
        assert responses[6]["diagnostics"] == []  # No stale decision counted twice.
        assert set(responses[5]["diagnostics"][0]) == {"candidate", "accepted", "score", "evidence_frames", "evidence_start_s", "evidence_end_s"}
    assert sorted(p.name for p in tmp_path.iterdir()) == ["model.npz"]
