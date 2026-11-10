"""Portable linear temporal classifier; model arrays use NPZ, never pickle."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from nexus.features import FEATURE_VERSION, sequence_vector, model_vector


class SignModel:
    def __init__(self, path="models/signs.npz"):
        with np.load(path, allow_pickle=False) as data:
            self.mean = data["mean"]
            self.scale = data["scale"]
            self.coef = data["coef"]
            self.intercept = data["intercept"]
            self.classes = data["classes"].tolist()
            self.metadata = json.loads(str(data["metadata"]))
            self.references = data["reference_vectors"] if "reference_vectors" in data else None
        if self.metadata["feature_version"] != FEATURE_VERSION:
            raise ValueError("Model/feature version mismatch")

    def predict(self, frames, timestamps):
        if self.metadata.get("sequence_policy") == "visible_hands_last_4s":
            from nexus.features import active_sequence
            frames, timestamps = active_sequence(frames, timestamps)
        if self.metadata.get("representation"):
            vector = model_vector(frames, timestamps, self.metadata["steps"], self.metadata["representation"])
        else:
            vector = sequence_vector(frames, timestamps, self.metadata["steps"])
        standardized = (vector - self.mean) / self.scale
        scores = self.coef @ standardized + self.intercept
        order = np.argsort(scores)[::-1]
        margin = float(scores[order[0]] - scores[order[1]])
        # Model score/margin are internal diagnostics, not translation confidence.
        if self.metadata.get("rejection_kind") == "background_logit_gap":
            background = self.classes.index("__OTHER__")
            known_order = [i for i in order if i != background]
            best = known_order[0]
            gap = float(scores[best] - scores[background])
            accepted = gap > self.metadata["background_threshold"]
            return {"label": self.classes[best] if accepted else None,
                    "candidate": self.classes[best], "margin": gap, "accepted": accepted}
        elif self.metadata.get("rejection_kind") == "nearest_training_distance":
            distance = float(np.sqrt(((self.references - standardized) ** 2).mean(-1)).min())
            accepted = distance < self.metadata["distance_threshold"]
        else:
            accepted = margin >= self.metadata["rejection_margin"]
        return {"label": self.classes[order[0]] if accepted else None,
                "candidate": self.classes[order[0]], "margin": margin, "accepted": accepted}
