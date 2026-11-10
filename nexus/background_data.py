"""Bounded training-only negative-sign subset; preserves original manifest.

Twenty other glosses, three train clips each, chosen before predictions. These
are negative signs, NOT a substitute for ordinary non-sign movement recordings.
"""
import csv
import hashlib
import json
import random
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from nexus.data.prepare import URL
from nexus.data.remote_zip import RemoteZipReader
from nexus.extract import extract_sample


def main():
    config = json.loads(Path("configs/recognition.json").read_text())
    original = json.loads(Path("data/asl_citizen/manifest.json").read_text())
    if hashlib.sha256(Path("data/asl_citizen/train.csv").read_bytes()).hexdigest() != original["metadata_sha256"]["train"]:
        raise ValueError("Cached training metadata differs from original verified manifest")
    with Path("data/asl_citizen/train.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    groups = {}
    excluded = set(config["vocabulary"] + config["negative_glosses"])
    dev_signers = {s["signer"] for s in original["samples"] if s["split"] == "val"}
    for row in rows:
        if row["Participant ID"] in dev_signers:
            raise ValueError("Training metadata overlaps development signers")
        if row["Gloss"] not in excluded:
            groups.setdefault(row["Gloss"], []).append(row)
    rng = random.Random(20261108)
    glosses = rng.sample(sorted(k for k, v in groups.items() if len(v) >= 3), 20)
    selected = [r for g in glosses for r in rng.sample(sorted(groups[g], key=lambda r: r["Video file"]), 3)]
    output = Path("data/asl_citizen/background_manifest.json")
    samples = []
    with RemoteZipReader(URL, budget=96 * 1024**2) as reader, zipfile.ZipFile(reader) as archive:
        infos = [archive.getinfo("ASL_Citizen/videos/" + r["Video file"]) for r in selected]
        if sum(i.compress_size for i in infos) + reader.transferred > reader.budget:
            raise ValueError("Training-negative subset exceeds 96 MiB transfer cap")
        for index, (row, info) in enumerate(zip(selected, infos)):
            name = row["Video file"]
            if Path(name).name != name or "/" in name or "\\" in name or info.file_size > 16 * 1024**2:
                raise ValueError("Unsafe or oversized member")
            path = Path("data/asl_citizen/videos") / name
            if path.exists():
                import zlib
                raw = path.read_bytes()
                if len(raw) != info.file_size or zlib.crc32(raw) != info.CRC:
                    raise ValueError("Existing video CRC mismatch")
            else:
                raw = archive.read(info)
                path.write_bytes(raw)
            samples.append({"id": name, "path": path.as_posix(), "label": "__OTHER__", "source_gloss": row["Gloss"],
                            "signer": row["Participant ID"], "split": "train", "role": "background",
                            "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
            if (index + 1) % 10 == 0:
                print(f"Downloaded/verified training negatives {index+1}/{len(selected)}", flush=True)
        transferred = reader.transferred
    output.write_text(json.dumps({"seed": 20261108, "samples": samples, "test_accessed": False,
                                 "source": URL, "transferred_bytes": transferred}, indent=2))
    failures, stats = [], []
    with ProcessPoolExecutor(max_workers=2) as pool:
        for index, (result, error) in enumerate(pool.map(extract_sample, [(s, Path("features/asl_citizen"), config) for s in samples])):
            (failures if error else stats).append(error or result)
            print(f"Background features {index+1}/{len(samples)}; failures={len(failures)}", flush=True)
    report = {"train_background_clips": len(samples), "source_glosses": len(glosses),
              "transferred_bytes": transferred, "features_completed": len(stats),
              "failure_count": len(failures), "test_accessed": False,
              "manifest_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
              "limitation": "Out-of-vocabulary signing only; no ordinary movement negatives"}
    Path("artifacts/recognition/background_data.json").write_text(json.dumps(report, indent=2))
    Path("artifacts/recognition/private/background_failures.json").write_text(json.dumps(failures, indent=2))
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit("Background extraction failed; inspect failures before training")


if __name__ == "__main__":
    main()
