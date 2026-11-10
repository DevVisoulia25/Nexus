import numpy as np

from nexus.features import POINTS, active_sequence
from nexus.replay import replay


class Model:
    def __init__(self):
        self.latest = []

    def predict(self, frames, timestamps):
        self.latest.append(float(timestamps[-1]))
        return {"candidate": "HELLO", "label": "HELLO", "accepted": True}


def test_replay_does_not_invent_release_at_end_of_clip():
    frames = np.ones((3, POINTS, 3), dtype=np.float32)
    model = Model()
    events, predictions = replay(model, frames, np.array([0., .2, .4]),
                                 session_options={"min_frames": 3, "min_seconds": .25, "finalize_on_release": True})
    assert predictions and not events
    assert max(model.latest) == .4


def test_active_window_ignores_unavailable_suffix():
    frames = np.ones((8, POINTS, 3), dtype=np.float32)
    frames[0] = 0
    frames[-1] = 999
    times = np.arange(8.)
    active, active_times = active_sequence(frames[:7], times[:7])
    assert active_times.tolist() == [2., 3., 4., 5., 6.]
    assert active.max() == 1
