from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import calendar as _cal

from ..core.model import Schedule, cents_to_str


def _load_font(size: int):  # pragma: no cover - depends on system fonts
    from PIL import ImageFont

    candidates = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def render_calendar_png(
    schedule: Schedule,
    out_path: str | Path,
    *,
    size: Tuple[int, int] = (3840, 2160),
    theme: str = "dark",
    bills_by_day: Optional[Dict[int, List[Tuple[str, int]]]] = None,
) -> None:  # pragma: no cover - visual artifact
    """Generate a clean, balanced month-view calendar PNG.

    Layout
    - Centered month title (Month Year), small objective line under it.
    - Weekday header (Sun..Sat) on its own row.
    - Month grid (rows of 7). Each cell shows:
        - Day number (top-left)
        - Action badge (top-right)
        - Up to 3 compact lines (payout, deposits, first bill)
        - Closing at bottom-right
    """
    try:
        from PIL import Image, ImageDraw
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "Pillow (PIL) is required. Install with `pip install pillow`."
        ) from e

    width, height = size
    # Global header scale based on overall width
    scale = max(0.5, min(1.4, width / 3840))

    # Colors
    bg = (12, 14, 18) if theme == "dark" else (245, 246, 250)
    fg = (232, 236, 244) if theme == "dark" else (24, 26, 30)
    sub = (168, 176, 190) if theme == "dark" else (90, 96, 108)
    off_fill = (58, 62, 72) if theme == "dark" else (220, 224, 232)
    work_fill = (36, 140, 86) if theme == "dark" else (52, 168, 98)
    large_fill = (184, 104, 44) if theme == "dark" else (214, 144, 84)

    grid_gap = int(24 * scale)
    margin = int(80 * scale)

    # Month grid
    now = datetime.now()
    first_wkday, num_days = _cal.monthrange(now.year, now.month)  # Mon=0..Sun=6
    offset = (first_wkday + 1) % 7  # make Sunday column 0
    cols = 7
    rows = (offset + num_days + cols - 1) // cols
    cell_w = (width - 2 * margin - (cols - 1) * grid_gap) // cols
    cell_h = (height - 2 * margin - (rows - 1) * grid_gap) // rows

    # Fonts (header uses global scale; cells use per-cell scale)
    cs = max(0.5, min(1.2, min(cell_w, cell_h) / 260))
    title_font = _load_font(int(88 * scale))
    obj_font = _load_font(int(30 * scale))
    wday_font = _load_font(int(36 * scale))
    day_font = _load_font(int(40 * cs))
    badge_font = _load_font(int(22 * cs))
    small_font = _load_font(int(20 * cs))
    close_font = _load_font(int(42 * cs))

    img = Image.new("RGB", (width, height), color=bg)
    draw = ImageDraw.Draw(img)

    def text_size(text: str, font) -> Tuple[int, int]:
        bbox = draw.textbbox((0, 0), text, font=font)
        return int(bbox[2] - bbox[0]), int(bbox[3] - bbox[1])

    # Header
    month_title = f"{_cal.month_name[now.month]} {now.year}"
    wt, ht = text_size(month_title, title_font)
    cx = width // 2
    header_y = margin // 2 + ht // 2
    try:
        draw.text((cx, header_y), month_title, fill=fg, font=title_font, anchor="mm")
    except TypeError:
        draw.text(
            (cx - wt / 2, header_y - ht / 2), month_title, fill=fg, font=title_font
        )

    w, b2b, delta, large, sp = schedule.objective
    obj_line = (
        f"work={w}  b2b={b2b}  |Δ|={cents_to_str(delta)}  L={large}  pen={sp}  "
        f"final={cents_to_str(schedule.final_closing_cents)}"
    )
    wo, ho = text_size(obj_line, obj_font)
    obj_y = header_y + ht // 2 + int(6 * scale) + ho // 2
    try:
        draw.text((cx, obj_y), obj_line, fill=sub, font=obj_font, anchor="mm")
    except TypeError:
        draw.text((cx - wo / 2, obj_y - ho / 2), obj_line, fill=sub, font=obj_font)

    # Weekday header
    y_labels = obj_y + ho // 2 + int(16 * scale)
    headers = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for i, name in enumerate(headers):
        x = margin + i * (cell_w + grid_gap) + cell_w // 2
        try:
            draw.text((x, y_labels), name, fill=sub, font=wday_font, anchor="mm")
        except TypeError:
            ww, hh = text_size(name, wday_font)
            draw.text((x - ww / 2, y_labels - hh / 2), name, fill=sub, font=wday_font)

    grid_top = y_labels + text_size("Sun", wday_font)[1] // 2 + int(18 * scale)

    def draw_badge(x1: int, y1: int, text: str, stroke: Tuple[int, int, int]):
        x2 = x1 + int(70 * scale)
        y2 = y1 + int(40 * scale)
        r = (y2 - y1) // 2
        draw.rounded_rectangle([x1, y1, x2, y2], radius=r, outline=stroke, width=3)
        try:
            draw.text(
                ((x1 + x2) / 2, (y1 + y2) / 2),
                text,
                fill=stroke,
                font=badge_font,
                anchor="mm",
            )
        except TypeError:
            wt, ht2 = text_size(text, badge_font)
            draw.text(
                (x1 + (x2 - x1 - wt) / 2, y1 + (y2 - y1 - ht2) / 2),
                text,
                fill=stroke,
                font=badge_font,
            )

    # Month cells
    for d in range(1, num_days + 1):
        r = (offset + (d - 1)) // cols
        c = (offset + (d - 1)) % cols
        x0 = margin + c * (cell_w + grid_gap)
        y0 = grid_top + r * (cell_h + grid_gap)
        x1 = x0 + cell_w
        y1 = y0 + cell_h

        row = schedule.ledger[d - 1] if d - 1 < len(schedule.ledger) else None
        if row:
            fill = (
                large_fill
                if row.action == "L"
                else (work_fill if row.action != "O" else off_fill)
            )
            text_col = fg
        else:
            fill, text_col = off_fill, sub
        draw.rounded_rectangle([x0, y0, x1, y1], radius=int(16 * cs), fill=fill)

        pad = int(12 * cs)
        # Day number
        draw.text((x0 + pad, y0 + pad), str(d), fill=text_col, font=day_font)

        # Action badge
        if row:
            draw_badge(x1 - pad - int(60 * cs), y0 + pad, row.action, text_col)

        # Info lines (up to 3)
        if row:
            lines: List[str] = []
            if row.net_cents:
                lines.append(f"Pay {cents_to_str(row.net_cents)}")
            if row.deposit_cents:
                lines.append(f"Deps {cents_to_str(row.deposit_cents)}")
            items = bills_by_day.get(d, []) if bills_by_day else []
            if items:
                nm, amt = items[0]
                lines.append(f"• {nm} {cents_to_str(amt)}")
            if len(lines) < 3 and len(items) > 1:
                lines.append(f"… +{len(items) - 1} more")

            avail_w = x1 - x0 - 2 * pad
            yy = y0 + pad + int(40 * cs)
            lh = int(24 * cs)
            for i, t in enumerate(lines[:2]):
                s = t
                while text_size(s, small_font)[0] > avail_w and len(s) > 2:
                    s = s[:-2] + "…"
                draw.text(
                    (x0 + pad, yy + i * lh),
                    s,
                    fill=text_col if not s.startswith("… ") else sub,
                    font=small_font,
                )

            # Closing
            close = cents_to_str(row.closing_cents)
            wc, hc = text_size(close, close_font)
            draw.text(
                (x1 - pad - wc, y1 - pad - hc), close, fill=text_col, font=close_font
            )

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_path), format="PNG", optimize=True)
