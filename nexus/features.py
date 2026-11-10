"""Shared, per-frame causal landmarks and timestamp-aware sequence features."""
from __future__ import annotations

import numpy as np

FEATURE_VERSION = "holistic-xy-body-hands-face-v1"
BODY = [0, 11, 12, 13, 14, 15, 16, 23, 24]
FACE = [1, 4, 33, 133, 362, 263, 61, 291, 13, 14, 70, 63, 105, 66, 107, 336, 296, 334, 293, 300]
POINTS = len(BODY) + 42 + len(FACE)


def quality_from_points(frame):
    """Reconstruct quality from normalized cached masks (diagnostic proxy)."""
    return {"body": bool(frame[1, 2] and frame[2, 2]),
            "hands": int(frame[9:30, 2].any()) + int(frame[30:51, 2].any())}


def active_sequence(frames, times):
    """Shared visible-hand window policy; only supplied frames are used."""
    frames, times = np.asarray(frames), np.asarray(times)
    keep = np.array([q["body"] and q["hands"] > 0 for q in map(quality_from_points, frames)])
    frames, times = frames[keep], times[keep]
    if len(times) < 2:
        raise ValueError("Insufficient tracked hands; do not silently exclude sample")
    keep = times >= times[-1] - 4.0
    return frames[keep], times[keep]


def handshape_points(frames):
    """Wrist-relative finger geometry scaled by palm width; keep orientation.

    Pad to POINTS to reuse the fixed sequence resampler. Body-relative position
    is preserved separately by the original feature vector, not discarded.
    """
    frames = np.asarray(frames, dtype=np.float32)
    result = np.zeros_like(frames)
    for source, target in ((9, 0), (30, 21)):
        hand = frames[:, source:source + 21]
        valid = (hand[:, 0, 2] > 0) & (hand[:, 5, 2] > 0) & (hand[:, 17, 2] > 0)
        width = np.linalg.norm(hand[:, 5, :2] - hand[:, 17, :2], axis=1)
        valid &= np.isfinite(width) & (width >= .01)
        local = np.zeros_like(hand)
        local[valid, :, :2] = np.clip((hand[valid, :, :2] - hand[valid, :1, :2]) / width[valid, None, None], -4, 4)
        local[valid, :, 2] = hand[valid, :, 2]
        local[local[:, :, 2] == 0] = 0
        result[:, target:target + 21] = local
    return result


def model_vector(frames, timestamps, steps=24, representation="body_v1"):
    base = sequence_vector(frames, timestamps, steps)
    if representation == "body_v1":
        return base
    if representation == "body_plus_handshape_v1":
        return np.concatenate((base, sequence_vector(handshape_points(frames), timestamps, steps)))
    raise ValueError("Unknown model representation")


def normalize_points(points: np.ndarray, shoulders: np.ndarray | None) -> np.ndarray:
    """Frame-local normalization; missing points remain zero with a mask."""
    result = np.asarray(points, dtype=np.float32).copy()
    if shoulders is None:
        return np.zeros_like(result)
    center = shoulders.mean(axis=0)
    scale = float(np.linalg.norm(shoulders[0] - shoulders[1]))
    if not np.isfinite(scale) or scale < 0.04:
        return np.zeros_like(result)
    mask = result[:, 2] > 0
    result[mask, :2] = np.clip((result[mask, :2] - center) / scale, -4, 4)
    result[~mask] = 0
    return result


class LandmarkExtractor:
    def __init__(self):
        import mediapipe as mp
        self.detector = mp.solutions.holistic.Holistic(
            static_image_mode=False, model_complexity=1, smooth_landmarks=False,
            enable_segmentation=False, refine_face_landmarks=False,
            min_detection_confidence=0.5, min_tracking_confidence=0.5,
        )

    def process(self, bgr: np.ndarray):
        import cv2
        height, width = bgr.shape[:2]
        if width > 640:
            bgr = cv2.resize(bgr, (640, round(height * 640 / width)))
        result = self.detector.process(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        points = np.zeros((POINTS, 3), dtype=np.float32)
        cursor = 0
        for landmarks, indices in ((result.pose_landmarks, BODY), (result.left_hand_landmarks, range(21)),
                                    (result.right_hand_landmarks, range(21)), (result.face_landmarks, FACE)):
            if landmarks:
                for i, j in enumerate(indices):
                    p = landmarks.landmark[j]
                    visible = p.visibility >= 0.5 if landmarks is result.pose_landmarks else True
                    if visible:
                        points[cursor + i] = [p.x, p.y, 1]
            cursor += len(indices)
        shoulders = points[[1, 2], :2] if points[1, 2] and points[2, 2] else None
        normalized = normalize_points(points, shoulders)
        quality = {"body": shoulders is not None, "face": result.face_landmarks is not None,
                   "hands": int(result.left_hand_landmarks is not None) + int(result.right_hand_landmarks is not None)}
        return normalized, quality, points

    def close(self):
        self.detector.close()


def sequence_vector(frames: np.ndarray, timestamps: np.ndarray, steps: int = 24) -> np.ndarray:
    """Resample *available* frames. No global learned preprocessing here.

    Interpolation is restricted to this supplied clip/prefix. Never supply future
    frames in live use. A new prefix may change the resampled vector.
    """
    frames = np.asarray(frames, dtype=np.float32)
    times = np.asarray(timestamps, dtype=np.float64)
    if frames.ndim != 3 or frames.shape[1:] != (POINTS, 3) or len(frames) < 2:
        raise ValueError("Need at least two valid landmark frames")
    if times.shape != (len(frames),) or not np.isfinite(frames).all() or not np.isfinite(times).all():
        raise ValueError("Invalid sequence values")
    if np.any(np.diff(times) <= 0):
        raise ValueError("Timestamps must increase strictly")
    target = np.linspace(times[0], times[-1], steps)
    flat = frames.reshape(len(frames), -1)
    sampled = np.stack([np.interp(target, times, flat[:, i]) for i in range(flat.shape[1])], axis=1)
    # Retain temporal order plus aggregate position/motion; masks are explicit.
    return np.concatenate((sampled.ravel(), sampled.mean(0), sampled.std(0))).astype(np.float32)
