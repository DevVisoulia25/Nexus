"""In-memory prediction tracing; never retains camera images or landmarks."""


class DiagnosticModel:
    def __init__(self, model):
        self.model = model
        self.decisions = []

    def begin_frame(self):
        self.decisions.clear()

    def predict(self, frames, timestamps):
        result = self.model.predict(frames, timestamps)
        self.decisions.append({"candidate": result.get("candidate"),
                               "accepted": bool(result.get("accepted", result.get("label") is not None)),
                               "score": result.get("margin"), "evidence_frames": len(frames),
                               "evidence_start_s": float(timestamps[0]), "evidence_end_s": float(timestamps[-1])})
        return result
