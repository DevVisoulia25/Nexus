"""Nexus: experimental local recognition of individual ASL signs."""

import os
from pathlib import Path

# Keep third-party runtime caches inside this project, not the user's profile.
os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".cache" / "matplotlib"))

__version__ = "0.1.0"
