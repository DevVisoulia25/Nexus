"""Package only this account's local research features for private notebook use.

Never commit, publish or share the resulting archive. No video is included.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath


def export_bundle():
    manifest = Path("data/asl_citizen/manifest.json")
    samples = json.loads(manifest.read_text())["samples"]
    paths = [manifest, Path("models/signs-baseline.npz")]
    paths += [Path("features/asl_citizen") / (s["id"] + ".npz") for s in samples]
    if any(s["split"] not in {"train", "val"} for s in samples):
        raise ValueError("Final test is not allowed in this development bundle")
    if sum(p.stat().st_size for p in paths) > 16 * 1024**2:
        raise ValueError("Feature bundle exceeded the small experiment budget")
    output = Path("artifacts/recognition/private/colab_features.zip")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        hashes = {}
        for path in paths:
            raw = path.read_bytes()
            archive.writestr(path.as_posix(), raw)
            hashes[path.as_posix()] = hashlib.sha256(raw).hexdigest()
        archive.writestr("bundle_hashes.json", json.dumps(hashes))
    print(f"Private bundle: {output} ({output.stat().st_size} bytes). Do not publish or commit it.")


def import_bundle(path):
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) > 1000 or sum(i.file_size for i in entries) > 16 * 1024**2:
            raise ValueError("Unexpected bundle size")
        names = [i.filename for i in entries]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate entries")
        hashes = json.loads(archive.read("bundle_hashes.json"))
        if set(names) != set(hashes) | {"bundle_hashes.json"}:
            raise ValueError("Unexpected bundle contents")
        contents = {}
        for name, expected in hashes.items():
            p = PurePosixPath(name)
            allowed = name in {"data/asl_citizen/manifest.json", "models/signs-baseline.npz"} or (
                p.parent == PurePosixPath("features/asl_citizen") and p.suffix == ".npz")
            if not allowed or "\\" in name or ":" in name or ".." in p.parts:
                raise ValueError("Unsafe bundle path")
            raw = archive.read(name)
            if hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError("Hash mismatch")
            contents[name] = raw
        # Validate every entry before writing any files; existing differing files are preserved.
        for name, raw in contents.items():
            if Path(name).exists() and Path(name).read_bytes() != raw:
                raise ValueError(f"Refusing to replace different existing file: {name}")
        for name, raw in contents.items():
            Path(name).parent.mkdir(parents=True, exist_ok=True)
            Path(name).write_bytes(raw)
        Path("artifacts/recognition/private").mkdir(parents=True, exist_ok=True)
    print("Imported private feature bundle; no raw video included.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--import-file")
    args = parser.parse_args()
    import_bundle(args.import_file) if args.import_file else export_bundle()


if __name__ == "__main__":
    main()
