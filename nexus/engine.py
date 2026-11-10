"""Bounded recognition state, independent of camera and web transport."""
from collections import deque

import numpy as np


class RecognitionSession:
    def __init__(self, model, max_seconds=4.0, max_frames=60,
                 min_seconds=0.8, min_frames=6, finalize_on_release=False):
        self.model = model
        self.max_seconds = max_seconds
        self.frames = deque(maxlen=max_frames)
        self.times = deque(maxlen=max_frames)
        self.last_timestamp = None
        self.last_decode = -float("inf")
        self.pending_label = None
        self.streak = 0
        self.emitted = None
        self.no_hands_since = None
        self.event_id = 0
        self.min_seconds = min_seconds
        self.min_frames = min_frames
        self.finalize_on_release = finalize_on_release

    def finish_attempt(self):
        """Optional boundary decision using only already observed frames."""
        if (not self.finalize_on_release or self.emitted is not None
                or len(self.frames) < self.min_frames
                or self.times[-1] - self.times[0] < self.min_seconds):
            return None
        label = self.model.predict(np.array(self.frames), np.array(self.times))["label"]
        if label:
            self.event_id += 1
            self.emitted = label
            return {"id": self.event_id, "label": label}
        return None

    def clear_context(self):
        self.frames.clear()
        self.times.clear()
        self.pending_label = None
        self.streak = 0
        self.emitted = None
        self.last_decode = -float("inf")
        self.no_hands_since = None

    def update(self, points, quality, timestamp):
        if not np.isfinite(timestamp) or (self.last_timestamp is not None and timestamp <= self.last_timestamp):
            raise ValueError("Frame timestamps must increase")
        gap = self.last_timestamp is not None and timestamp - self.last_timestamp > 0.75
        if gap:
            self.clear_context()
        self.last_timestamp = timestamp
        if quality["hands"] == 0 or not quality["body"]:
            self.no_hands_since = timestamp if self.no_hands_since is None else self.no_hands_since
            if timestamp - self.no_hands_since >= 0.5:
                # Loss of body framing is not evidence of a completed sign.
                event = self.finish_attempt() if quality["body"] else None
                self.clear_context()
                self.no_hands_since = timestamp
                return {"state": "idle" if quality["body"] else "framing", "label": None,
                        "gap": gap, "event": event}
            return {"state": "framing" if not quality["body"] else "idle", "label": None, "gap": gap}
        self.no_hands_since = None
        self.frames.append(points)
        self.times.append(timestamp)
        while self.times and timestamp - self.times[0] > self.max_seconds:
            self.times.popleft()
            self.frames.popleft()
        duration = self.times[-1] - self.times[0]
        if duration < self.min_seconds or len(self.frames) < self.min_frames:
            return {"state": "collecting", "label": None, "window_s": duration, "gap": gap}
        if timestamp - self.last_decode < 0.4:
            return {"state": "tracking", "label": self.pending_label, "window_s": duration, "gap": gap}
        self.last_decode = timestamp
        prediction = self.model.predict(np.array(self.frames), np.array(self.times))
        label = prediction["label"]
        if label and label == self.pending_label:
            self.streak += 1
        else:
            self.pending_label, self.streak = label, 1 if label else 0
        event = None
        # One event per gesture attempt. Return hands out of view or reset before repeating.
        if label and self.streak >= 3 and self.emitted is None:
            self.event_id += 1
            self.emitted = label
            event = {"id": self.event_id, "label": label}
        return {"state": "candidate" if label else "unknown", "label": label,
                "window_s": duration, "gap": gap, "event": event}
