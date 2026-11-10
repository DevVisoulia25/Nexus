import numpy as np
import pytest

from nexus.features import POINTS, normalize_points, sequence_vector, handshape_points


def test_frame_normalization_translation_and_scale_invariant():
    points = np.zeros((POINTS, 3), dtype=np.float32)
    points[:2] = [[0.3, 0.4, 1], [0.6, 0.7, 1]]
    shoulders = np.array([[0.3, 0.4], [0.7, 0.4]])
    expected = normalize_points(points, shoulders)
    shifted = points.copy()
    shifted[:2, :2] = shifted[:2, :2] * 2 + 0.1
    actual = normalize_points(shifted, shoulders * 2 + 0.1)
    np.testing.assert_allclose(actual, expected, atol=1e-6)
    assert np.all(actual[2:] == 0)


def test_sequence_uses_temporal_order_and_validates_time():
    frames = np.zeros((4, POINTS, 3), dtype=np.float32)
    frames[:, 0, 0] = [0, 1, 2, 3]
    forward = sequence_vector(frames, np.array([0, 1, 2, 3]))
    reverse = sequence_vector(frames[::-1], np.array([0, 1, 2, 3]))
    assert not np.array_equal(forward, reverse)
    with pytest.raises(ValueError, match="increase"):
        sequence_vector(frames, np.array([0, 1, 1, 3]))
    with pytest.raises(ValueError):
        sequence_vector(frames * np.nan, np.arange(4))


def test_missing_shoulders_do_not_invent_landmarks():
    assert not normalize_points(np.ones((POINTS, 3)), None).any()


def test_handshape_is_translation_and_scale_invariant_and_keeps_orientation():
    rng = np.random.default_rng(42)
    frames = np.ones((3, POINTS, 3), dtype=np.float32)
    frames[:, :, :2] = rng.uniform(-.2, .2, (3, POINTS, 2))
    shifted = frames.copy()
    shifted[:, :, :2] = frames[:, :, :2] * 2 + .5
    np.testing.assert_allclose(handshape_points(frames), handshape_points(shifted), atol=2e-6)
    mirrored = frames.copy()
    mirrored[:, :, 0] *= -1
    assert not np.allclose(handshape_points(frames), handshape_points(mirrored))


def test_missing_or_collapsed_palm_does_not_invent_finger_shape():
    frames = np.ones((3, POINTS, 3), dtype=np.float32)
    assert not handshape_points(frames).any()
    frames[:, 14, 0] = 2
    frames[:, 9, 2] = 0
    assert not handshape_points(frames).any()
