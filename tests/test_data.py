import pytest

from nexus.data.prepare import choose_rows


def row(signer, name, gloss):
    return {"Participant ID": signer, "Video file": name, "Gloss": gloss}


CONFIG = {"vocabulary": ["HELLO"], "seed": 42, "negative_glosses": ["BOOK"], "negative_clips_per_gloss": 1}


def test_split_leakage_fails_before_download():
    with pytest.raises(ValueError, match="leakage"):
        choose_rows([row("P1", "a", "HELLO")], [row("P1", "b", "HELLO")], CONFIG)


def test_selection_is_repeatable_and_unknown_not_in_training():
    train = [row("P1", "a", "HELLO")]
    val = [row("P2", "b", "HELLO"), row("P2", "c", "BOOK"), row("P3", "d", "BOOK")]
    first = choose_rows(train, val, CONFIG)
    assert first == choose_rows(train, val, CONFIG)
    assert [r["split"] for r in first if r["role"] == "unknown"] == ["val"]
