"""Read ZIP directory + train/dev CSV only; no videos or test labels."""
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nexus.data.remote_zip import RemoteZipReader

URL = "https://download.microsoft.com/download/b/8/8/b88c0bae-e6c1-43e1-8726-98cf5af36ca4/ASL_Citizen.zip"
out = Path("data/asl_citizen")
out.mkdir(parents=True, exist_ok=True)
with RemoteZipReader(URL, budget=32 * 1024**2) as reader, zipfile.ZipFile(reader) as archive:
    entries = archive.infolist()
    small = [{"name": i.filename, "bytes": i.file_size} for i in entries if not i.filename.lower().endswith((".mp4", ".mov"))]
    print(json.dumps({"archive_bytes": reader.size, "entries": len(entries), "metadata": small[:100]}, indent=2), flush=True)
    for entry in entries:
        name = Path(entry.filename).name
        if name.lower() in {"train.csv", "val.csv"}:
            if entry.file_size > 16 * 1024**2:
                raise ValueError("Metadata too large")
            content = archive.read(entry)
            (out / name).write_bytes(content)
            print(name, content[:500].decode("utf-8-sig"), flush=True)
    (out / "archive_catalog.json").write_text(json.dumps({"url": URL, "size": reader.size, "etag": reader.etag, "bytes_read": reader.transferred, "entries": [{"name": i.filename, "compressed_bytes": i.compress_size, "bytes": i.file_size, "crc32": i.CRC} for i in entries]}, indent=2))
    print("Total bytes read:", reader.transferred)
