from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI

# Ensure project root is on sys.path so we can import the cashflow package
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cashflow.api.app import app as core_app  # noqa: E402

# Mount the existing FastAPI app under /api for same-origin routing
app = FastAPI()
app.mount("/api", core_app)

