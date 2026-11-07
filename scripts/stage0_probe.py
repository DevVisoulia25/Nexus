"""Bounded, dependency-free public artifact audit; never loads model weights.

Run from the repository root: python scripts/stage0_probe.py
Downloads metadata and validation annotations only; does not access test data.
"""
import csv
import hashlib
import io
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "stage0"
CAP = 2 * 1024 * 1024


def fetch(url, cap=CAP, partial=False):
    headers = {"User-Agent": "ASL-Stage0-Feasibility/0.1"}
    if partial:
        headers["Range"] = f"bytes=0-{cap-1}"
    started = time.perf_counter()
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:
        raw = r.read(cap if partial else cap + 1)
        if len(raw) > cap:
            raise ValueError("Response exceeds bounded metadata download limit")
        info = {"url": url, "status": r.status, "bytes_read": len(raw),
                "content_type": r.headers.get("Content-Type"),
                "content_length": r.headers.get("Content-Length"),
                "content_range": r.headers.get("Content-Range"),
                "elapsed_s": round(time.perf_counter() - started, 3),
                "sha256_of_bytes_read": hashlib.sha256(raw).hexdigest()}
    return raw, info


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"run_utc": datetime.now(timezone.utc).isoformat(), "checks": {},
              "scope": "Metadata, validation annotations, and bounded checkpoint byte probes; no model execution"}

    def attempt(name, fn):
        try:
            report["checks"][name] = {"ok": True, **fn()}
        except Exception as exc:
            report["checks"][name] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        print(name, json.dumps(report["checks"][name], ensure_ascii=True), flush=True)
        (OUT / "probe_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    def hf():
        raw, info = fetch("https://huggingface.co/api/models/ZechengLi19/Uni-Sign?blobs=true")
        d = json.loads(raw)
        (OUT / "unisign_metadata.json").write_bytes(raw)
        return {**info, "revision": d.get("sha"), "license": d.get("cardData", {}).get("license"),
                "files": [x for x in d.get("siblings", []) if "how2sign" in x["rfilename"]]}

    def dataverse():
        raw, info = fetch("https://dataverse.csuc.cat/api/datasets/:persistentId/?persistentId=doi:10.34810/data693")
        d = json.loads(raw)["data"]["latestVersion"]
        (OUT / "wicv_dataverse_metadata.json").write_bytes(raw)
        return {**info, "version": [d.get("versionNumber"), d.get("versionMinorNumber")],
                "license": d.get("license"), "termsOfUse": d.get("termsOfUse"),
                "files": [{"id": x["dataFile"]["id"], "name": x["dataFile"]["filename"],
                           "size": x["dataFile"]["filesize"], "restricted": x.get("restricted"),
                           "checksum": x["dataFile"].get("checksum")} for x in d.get("files", [])]}

    annotations = {}

    def annotation(label, file_id):
        raw, info = fetch("https://drive.google.com/uc?export=download&id=" + file_id)
        if b"<html" in raw[:1000].lower() or b"<!doctype" in raw[:1000].lower():
            raise ValueError("Received HTML instead of annotations")
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), delimiter="\t"))
        required = {"SENTENCE_NAME", "START_REALIGNED", "END_REALIGNED"} if label == "realigned" else {"SENTENCE_NAME", "START", "END"}
        if not rows or not required.issubset(rows[0]):
            raise ValueError(f"Unexpected annotation schema: {list(rows[0]) if rows else []}")
        annotations[label] = rows
        (OUT / f"how2sign_{label}_val.tsv").write_bytes(raw)
        return {**info, "rows": len(rows), "columns": list(rows[0])}

    attempt("unisign_catalog", hf)
    attempt("wicv_catalog", dataverse)
    attempt("validation_original", lambda: annotation("original", "1aBQUClTlZB504JtDISJ0DJlbuYUZCGu3"))
    attempt("validation_realigned", lambda: annotation("realigned", "1Vpag7VPfdTCCJSao8Pz14rlPfekRMggI"))

    def checkpoint_probe():
        catalog = report["checks"]["unisign_catalog"]
        if not catalog.get("ok"):
            raise ValueError("No verified checkpoint revision")
        url = f"https://huggingface.co/ZechengLi19/Uni-Sign/resolve/{catalog['revision']}/how2sign_pose_only_slt.pth"
        raw, info = fetch(url, cap=65536, partial=True)
        return {**info, "zip_magic": raw[:4] == b"PK\x03\x04", "full_download": False,
                "compatibility_verified": False}

    attempt("unisign_checkpoint_bytes", checkpoint_probe)

    def alignment():
        original = {r["SENTENCE_NAME"]: r for r in annotations["original"]}
        realigned = {r["SENTENCE_NAME"]: r for r in annotations["realigned"]}
        shared = sorted(original.keys() & realigned.keys())
        ds, de, invalid = [], [], 0
        for key in shared:
            a, b = original[key], realigned[key]
            start, end = float(b["START_REALIGNED"]), float(b["END_REALIGNED"])
            invalid += int(start < 0 or end <= start)
            ds.append(abs(start - float(a["START"])))
            de.append(abs(end - float(a["END"])))
        def describe(values):
            s = sorted(values)
            return {"median_s": s[len(s)//2], "max_s": s[-1], "over_0_5s": sum(x > .5 for x in s)}
        return {"shared_ids": len(shared), "original_only": len(original.keys()-realigned.keys()),
                "realigned_only": len(realigned.keys()-original.keys()), "invalid_realigned_intervals": invalid,
                "original_duplicate_ids": len(annotations["original"])-len(original),
                "realigned_duplicate_ids": len(annotations["realigned"])-len(realigned),
                "start_shift": describe(ds), "end_shift": describe(de),
                "note": "Timestamp differences only; does not establish semantic alignment or decoded-video validity"}

    if len(annotations) == 2:
        attempt("validation_alignment", alignment)


if __name__ == "__main__":
    main()
