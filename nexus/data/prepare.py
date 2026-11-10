"""Prepare a small ASL Citizen train/dev subset, never the final test set.

Run `python -m nexus.data.prepare`. No videos/features are redistributed.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import random
import zipfile
from pathlib import Path

from nexus.data.remote_zip import RemoteZipReader

URL = "https://download.microsoft.com/download/b/8/8/b88c0bae-e6c1-43e1-8726-98cf5af36ca4/ASL_Citizen.zip"
LICENSE_URL = "https://www.microsoft.com/en-us/research/project/asl-citizen/dataset-license/"


def choose_rows(train, val, config):
    train_signers = {r["Participant ID"] for r in train}
    val_signers = {r["Participant ID"] for r in val}
    if train_signers & val_signers:
        raise ValueError("Signer leakage between official train and validation metadata")
    selected = []
    for split, rows in (("train", train), ("val", val)):
        for row in rows:
            if row["Gloss"] in config["vocabulary"]:
                selected.append({**row, "split": split, "role": "known"})
        for gloss in config["vocabulary"]:
            if not any(r["Gloss"] == gloss for r in rows):
                raise ValueError(f"Missing class {gloss} in {split}")
    rng = random.Random(config["seed"])
    for gloss in config["negative_glosses"]:
        candidates = sorted((r for r in val if r["Gloss"] == gloss), key=lambda r: r["Video file"])
        if len(candidates) < config["negative_clips_per_gloss"]:
            raise ValueError(f"Insufficient negative examples: {gloss}")
        for row in rng.sample(candidates, config["negative_clips_per_gloss"]):
            selected.append({**row, "split": "val", "role": "unknown"})
    names = [r["Video file"] for r in selected]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate source files in selected set")
    return selected


def main():
    config = json.loads(Path("configs/recognition.json").read_text())
    root = Path("data/asl_citizen")
    root.mkdir(parents=True, exist_ok=True)
    (root / "videos").mkdir(exist_ok=True)
    manifest = {"dataset": "ASL Citizen", "source": URL, "license": LICENSE_URL,
                "seed": config["seed"], "config_sha256": hashlib.sha256(Path("configs/recognition.json").read_bytes()).hexdigest(),
                "test_accessed": False, "samples": [], "metadata_sha256": {}}
    with RemoteZipReader(URL, budget=config["download_budget_mib"] * 1024**2) as reader, zipfile.ZipFile(reader) as archive:
        splits = {}
        for split in ("train", "val"):
            raw = archive.read(f"ASL_Citizen/splits/{split}.csv")
            manifest["metadata_sha256"][split] = hashlib.sha256(raw).hexdigest()
            splits[split] = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
        rows = choose_rows(splits["train"], splits["val"], config)
        total = sum(archive.getinfo("ASL_Citizen/videos/" + r["Video file"]).compress_size for r in rows)
        if total + reader.transferred > reader.budget:
            raise ValueError("Selected subset exceeds transfer budget before download")
        print(f"Selected {len(rows)} clips; compressed videos {total/1e6:.1f} MB", flush=True)
        for index, row in enumerate(rows):
            name = row["Video file"]
            if Path(name).name != name or "/" in name or "\\" in name:
                raise ValueError("Unsafe dataset filename")
            info = archive.getinfo("ASL_Citizen/videos/" + name)
            if info.file_size > 16 * 1024**2:
                raise ValueError("Unexpectedly large individual video")
            path = root / "videos" / name
            if path.exists():
                raw = path.read_bytes()
                import zlib
                if len(raw) != info.file_size or zlib.crc32(raw) != info.CRC:
                    raise ValueError(f"Existing file failed CRC: {name}; remove that file and retry")
            else:
                raw = archive.read(info)  # zipfile validates CRC before writing
                path.write_bytes(raw)
            manifest["samples"].append({"id": name, "path": path.as_posix(), "label": row["Gloss"],
                                        "signer": row["Participant ID"], "split": row["split"], "role": row["role"],
                                        "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
            if (index + 1) % 10 == 0:
                print(f"Downloaded/verified {index+1}/{len(rows)}", flush=True)
        manifest["archive_bytes"] = reader.size
        manifest["archive_etag"] = reader.etag
        manifest["transferred_bytes"] = reader.transferred
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Saved data/asl_citizen/manifest.json; final test remains untouched.", flush=True)


if __name__ == "__main__":
    main()
