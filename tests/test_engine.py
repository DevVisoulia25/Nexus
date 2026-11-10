import numpy as np
import pytest

from nexus.engine import RecognitionSession
from nexus.features import POINTS


class Model:
    def predict(self, frames, timestamps):
        return {"label": "HELLO"}


FRAME = np.ones((POINTS, 3), dtype=np.float32)
QUALITY = {"body": True, "hands": 1}


def test_bounded_context_and_no_repeat_until_release():
    session = RecognitionSession(Model(), max_seconds=2, max_frames=12)
    events = []
    for t in np.arange(0, 20, 0.1):
        result = session.update(FRAME, QUALITY, float(t))
        if result.get("event"):
            events.append(result["event"])
        assert len(session.frames) <= 12
        assert session.times[-1] - session.times[0] <= 2.0001
    assert len(events) == 1
    for t in [20, 20.2, 20.4, 20.6]:
        session.update(FRAME, {"body": True, "hands": 0}, t)
    for t in np.arange(20.7, 23, 0.1):
        result = session.update(FRAME, QUALITY, float(t))
        if result.get("event"):
            events.append(result["event"])
    assert len(events) == 2


def test_gap_drops_prior_context_and_old_frames_are_rejected():
    session = RecognitionSession(Model())
    session.update(FRAME, QUALITY, 1)
    result = session.update(FRAME, QUALITY, 3)
    assert result["gap"] and len(session.frames) == 1
    with pytest.raises(ValueError, match="increase"):
        session.update(FRAME, QUALITY, 2)


def test_unknown_never_emits_event():
    class Unknown:
        def predict(self, frames, timestamps):
            return {"label": None}
    session = RecognitionSession(Unknown())
    for t in np.arange(0, 8, .1):
        assert not session.update(FRAME, QUALITY, float(t)).get("event")


def test_short_sign_finalizes_only_after_observed_release_once():
    session = RecognitionSession(Model(), min_seconds=.25, min_frames=3, finalize_on_release=True)
    for t in [0., .2, .4]:
        assert not session.update(FRAME, QUALITY, t).get("event")
    idle = {"body": True, "hands": 0}
    assert not session.update(FRAME, idle, .6).get("event")
    assert session.update(FRAME, idle, 1.11)["event"]["label"] == "HELLO"
    assert not session.update(FRAME, idle, 1.7).get("event")


def test_lost_framing_does_not_finalize_short_sign():
    session = RecognitionSession(Model(), min_seconds=.25, min_frames=3, finalize_on_release=True)
    for t in [0., .2, .4]:
        session.update(FRAME, QUALITY, t)
    for t in [.6, 1.11]:
        assert not session.update(FRAME, {"body": False, "hands": 0}, t).get("event")


def test_capture_gap_cannot_finalize_old_sign():
    session = RecognitionSession(Model(), min_seconds=.25, min_frames=3, finalize_on_release=True)
    for t in [0., .2, .4]:
        session.update(FRAME, QUALITY, t)
    assert not session.update(FRAME, {"body": True, "hands": 0}, 2).get("event")
