from __future__ import annotations

import json
from cashflow import __version__
from ._shared import _cors_headers, handle_preflight


def handler(request):  # Vercel Python expects a default callable
    pf = handle_preflight(request)
    if pf is not None:
        return pf
    body = json.dumps({"status": "ok", "version": __version__})
    origin = None
    try:
        origin = request.headers.get("origin")  # type: ignore[attr-defined]
    except Exception:
        pass
    return body, 200, _cors_headers(origin)
