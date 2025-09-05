from __future__ import annotations

import json
from ._shared import _load_default_plan, dp_solve, _cors_headers, handle_preflight


def handler(request):
    pf = handle_preflight(request)
    if pf is not None:
        return pf
    try:
        body = request.get_json() if hasattr(request, "get_json") else json.loads(request.body or "{}")
    except Exception:
        body = {}
    fmt = str(body.get("format", "md")).lower()
    if fmt not in ("md", "csv", "json"):
        return json.dumps({"error": "format must be one of md|csv|json"}), 400, {"Content-Type": "application/json"}

    plan = _load_default_plan()
    schedule = dp_solve(plan)
    # Import renderers lazily to avoid deployment mismatches during cold starts
    from cashflow.io.render import render_markdown as _rmd, render_csv as _rcsv, render_json as _rjson

    if fmt == "md":
        content = _rmd(schedule)
    elif fmt == "csv":
        content = _rcsv(schedule)
    else:
        content = _rjson(schedule)
    origin = None
    try:
        origin = request.headers.get("origin")  # type: ignore[attr-defined]
    except Exception:
        pass
    return json.dumps({"format": fmt, "content": content}), 200, _cors_headers(origin)
