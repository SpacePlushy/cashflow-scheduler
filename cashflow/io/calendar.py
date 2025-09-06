from __future__ import annotations

from pathlib import Path
from typing import Tuple

from ..core.model import Schedule, cents_to_str


def _try_load_font(size: int):  # pragma: no cover - depends on system fonts
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
            pass
    return ImageFont.load_default()


def render_calendar_png(
    schedule: Schedule,
    out_path: str | Path,
    *,
    size: Tuple[int, int] = (3840, 2160),
    theme: str = "dark",
):  # pragma: no cover - visual artifact
    """Render a 30-day calendar to a PNG file (wallpaper-friendly)."""
    try:
        from PIL import Image, ImageDraw
    except Exception as e:
        raise RuntimeError(
            "Pillow (PIL) is required. Install with `pip install pillow`."
        ) from e

    width, height = size
    bg = (12, 14, 18) if theme == "dark" else (245, 246, 250)
    fg = (235, 238, 243) if theme == "dark" else (20, 22, 26)
    sub = (180, 188, 201) if theme == "dark" else (60, 68, 80)
    grid_gap = 24
    margin = 80
    cols, rows = 6, 5
    cell_w = (width - 2 * margin - (cols - 1) * grid_gap) // cols
    cell_h = (height - 2 * margin - (rows - 1) * grid_gap) // rows

    action_colors = {
        "O": ((48, 52, 61), (200, 200, 205)),
        "S": ((24, 99, 125), (235, 245, 245)),
        "M": ((64, 120, 165), (236, 246, 255)),
        "L": ((182, 98, 36), (252, 241, 233)),
        "SS": ((30, 132, 73), (232, 246, 233)),
    }

    img = Image.new("RGB", (width, height), color=bg)
    draw = ImageDraw.Draw(img)

    # Fonts
    try:
        title_font = _try_load_font(64)
        label_font = _try_load_font(36)
        small_font = _try_load_font(28)
        num_font = _try_load_font(52)
        close_font = _try_load_font(60)
    except Exception as e:
        raise RuntimeError("Pillow fonts not available") from e

    # Measure helper
    def _wh(text: str, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Header
    title = "Cashflow Schedule"
    w_title, _ = _wh(title, title_font)
    draw.text((margin, margin // 2), title, fill=fg, font=title_font)

    w, b2b, delta, large, sp = schedule.objective
    subtitle = (
        f"work={w}  b2b={b2b}  |Δ|={cents_to_str(delta)}  "
        f"L={large}  pen={sp}  final={cents_to_str(schedule.final_closing_cents)}"
    )
    draw.text((margin + w_title + 24, margin // 2 + 12), subtitle, fill=sub, font=label_font)

    # Cells
    for row in schedule.ledger:
        day = row.day
        r = (day - 1) // cols
        c = (day - 1) % cols
        x0 = margin + c * (cell_w + grid_gap)
        y0 = margin + 60 + r * (cell_h + grid_gap)
        x1 = x0 + cell_w
        y1 = y0 + cell_h

        fill, txt = action_colors.get(row.action, ((70, 70, 70), fg))
        draw.rounded_rectangle([x0, y0, x1, y1], radius=24, fill=fill)

        pad = 18
        # Day and Action tag
        draw.text((x0 + pad, y0 + pad), f"{day}", fill=txt, font=num_font)

        # Action badge (top-right), keep generous margins to avoid clipping
        tag = row.action
        tw, th = _wh(tag, label_font)
        badge_margin = max(24, int(min(cell_w, cell_h) * 0.03))
        inner_pad_x, inner_pad_y = 12, 8
        bx2 = x1 - badge_margin
        bx1 = bx2 - (tw + inner_pad_x * 2)
        by1 = y0 + badge_margin
        by2 = by1 + (th + inner_pad_y * 2)
        radius = int((th + inner_pad_y * 2) / 2)
        draw.rounded_rectangle([bx1, by1, bx2, by2], radius=radius, outline=txt, width=3)
        draw.text((bx1 + inner_pad_x, by1 + inner_pad_y), tag, fill=txt, font=label_font)

        # Metrics column layout (labels + values), no spaces for alignment.
        y = y0 + pad + 78
        label_x = x0 + pad
        col_gap = max(120, min(220, cell_w // 3))
        value_x = x0 + pad + col_gap

        def _row(lbl: str, val: str, y: int):
            draw.text((label_x, y), lbl, fill=sub, font=small_font)
            draw.text((value_x, y), val, fill=txt, font=small_font)

        _row("Deposits", cents_to_str(row.deposit_cents), y)
        y += 34
        _row("Bills", cents_to_str(row.bills_cents), y)
        y += 34
        _row("Net", cents_to_str(row.net_cents), y)

        close = cents_to_str(row.closing_cents)
        cw, ch = _wh(close, close_font)
        draw.text((x1 - pad - cw, y1 - pad - ch), close, fill=txt, font=close_font)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_path), format="PNG", optimize=True)
