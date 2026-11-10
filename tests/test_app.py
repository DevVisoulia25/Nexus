import struct

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from nexus.app import app, decode_packet


def test_home_status_and_no_raw_data_route():
    with TestClient(app) as client:
        assert client.get("/").status_code == 200
        assert client.get("/api/status").json()["experimental"] is True
        assert client.get("/data/asl_citizen/manifest.json").status_code == 404


def test_foreign_browser_origin_is_rejected():
    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws", headers={"origin": "https://example.com"}):
                pass


def test_frame_protocol_validates_size_and_timestamp():
    ok, jpg = cv2.imencode(".jpg", np.zeros((32, 32, 3), dtype=np.uint8))
    payload = struct.pack("<dI", 1234.0, 7) + jpg.tobytes()
    timestamp, seq, image = decode_packet(payload)
    assert timestamp == 1.234 and seq == 7 and image.shape == (32, 32, 3)
    with pytest.raises(ValueError):
        decode_packet(b"bad")
    with pytest.raises(ValueError):
        decode_packet(struct.pack("<dI", float("nan"), 0) + jpg.tobytes())


def test_candidate_status_does_not_reuse_baseline_evaluation(tmp_path, monkeypatch):
    monkeypatch.setattr("nexus.app.MODEL_PATH", tmp_path / "candidate.npz")
    with TestClient(app) as client:
        status = client.get("/api/status").json()
        assert status["evaluation"] is None
        assert status["model_name"] == "candidate.npz"
        assert not status["recognition_validated"]
