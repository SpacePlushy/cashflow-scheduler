from __future__ import annotations

import json
from cashflow import __version__


def handler(request):  # Vercel Python expects a default callable
    body = json.dumps({"status": "ok", "version": __version__})
    return body, 200, {"Content-Type": "application/json"}

