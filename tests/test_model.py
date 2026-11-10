import json

import numpy as np

from nexus.features import FEATURE_VERSION
from nexus.model import SignModel


def test_background_winner_is_never_displayed_as_sign(tmp_path, monkeypatch):
    monkeypatch.setattr("nexus.model.sequence_vector", lambda *args: np.array([1., 0.]))
    path = tmp_path / "candidate.npz"
    metadata = {"feature_version": FEATURE_VERSION, "steps": 24,
                "rejection_kind": "background_logit_gap", "background_threshold": 0.}
    np.savez(path, mean=np.zeros(2), scale=np.ones(2), coef=np.array([[1., 0.], [5., 0.]]),
             intercept=np.zeros(2), classes=np.array(["HELLO", "__OTHER__"]), metadata=json.dumps(metadata))
    result = SignModel(path).predict(None, None)
    assert result["candidate"] == "HELLO"
    assert result["label"] is None and not result["accepted"]
