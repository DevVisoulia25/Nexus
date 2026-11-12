"""Explicit test-only server for the shared guided UI and browser recorder.

The synthetic fixture is never mounted by the production application.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.responses import FileResponse
from nexus.app import app


@app.get("/__guided_check")
def fixture():
    return FileResponse(ROOT / "tests/guided_browser.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8767, access_log=False)
