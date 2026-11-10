import hashlib
import json
import zipfile

import pytest

from nexus.cloud_bundle import import_bundle


def test_bundle_rejects_traversal_before_writing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    payload = b"bad"
    with zipfile.ZipFile("bad.zip", "w") as archive:
        archive.writestr("../outside.txt", payload)
        archive.writestr("bundle_hashes.json", json.dumps({"../outside.txt": hashlib.sha256(payload).hexdigest()}))
    with pytest.raises(ValueError, match="Unsafe"):
        import_bundle("bad.zip")
    assert not (tmp_path.parent / "outside.txt").exists()


def test_bundle_preserves_existing_different_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    target = tmp_path / "models/signs-baseline.npz"
    target.parent.mkdir()
    target.write_bytes(b"original")
    with zipfile.ZipFile("bundle.zip", "w") as archive:
        archive.writestr("models/signs-baseline.npz", b"new")
        archive.writestr("bundle_hashes.json", json.dumps({"models/signs-baseline.npz": hashlib.sha256(b"new").hexdigest()}))
    with pytest.raises(ValueError, match="Refusing"):
        import_bundle("bundle.zip")
    assert target.read_bytes() == b"original"
