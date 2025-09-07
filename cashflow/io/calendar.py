from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import calendar as _cal

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
    bills_by_day: Optional[Dict[int, List[Tuple[str, int]]]] = None,
):  # pragma: no cover - visual artifact
    """Render a 30-day calendar to a PNG file (wallpaper-friendly)."""
    try:
        from PIL import Image, ImageDraw
    except Exception as e:
        raise RuntimeError(
            "Pillow (PIL) is required. Install with `pip install pillow`."
        ) from e

    width, height = size
    scale = max(0.6, min(1.5, width / 3840))
    bg = (12, 14, 18) if theme == "dark" else (245, 246, 250)
    fg = (235, 238, 243) if theme == "dark" else (20, 22, 26)
    sub = (180, 188, 201) if theme == "dark" else (60, 68, 80)
    grid_gap = 24
    margin = 80
    # Determine real calendar grid for the current month (7 columns)
    now = datetime.now()
    first_wkday, num_days = _cal.monthrange(now.year, now.month)  # Mon=0..Sun=6
    # Offset so Sunday is first column
    offset = (first_wkday + 1) % 7
    total_cells = offset + num_days
    cols = 7
    rows = (total_cells + cols - 1) // cols
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
        title_font = _try_load_font(int(84 * scale))
        sub_font = _try_load_font(int(36 * scale))
        wday_font = _try_load_font(int(40 * scale))
        label_font = _try_load_font(int(34 * scale))
        small_font = _try_load_font(int(26 * scale))
        num_font = _try_load_font(int(50 * scale))
        close_font = _try_load_font(int(60 * scale))
    except Exception as e:
        raise RuntimeError("Pillow fonts not available") from e

    # Measure helper
    def _wh(text: str, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    # Header: Month name and small objective summary
    month_title = f"{_cal.month_name[now.month]} {now.year}"
    w_title, h_title = _wh(month_title, title_font)
    center_x = width // 2
    header_y = margin // 2 + h_title // 2
    try:
        draw.text(
            (center_x, header_y), month_title, fill=fg, font=title_font, anchor="mm"
        )
    except TypeError:
        draw.text(
            (center_x - w_title / 2, header_y - h_title / 2),
            month_title,
            fill=fg,
            font=title_font,
        )

    w, b2b, delta, large, sp = schedule.objective
    subtitle = (
        f"work={w}  b2b={b2b}  |Δ|={cents_to_str(delta)}  "
        f"L={large}  pen={sp}  final={cents_to_str(schedule.final_closing_cents)}"
    )
    w_sub, h_sub = _wh(subtitle, sub_font)
    sub_y = header_y + h_title // 2 + int(8 * scale) + h_sub // 2
    try:
        draw.text((center_x, sub_y), subtitle, fill=sub, font=sub_font, anchor="mm")
    except TypeError:
        draw.text(
            (center_x - w_sub / 2, sub_y - h_sub / 2), subtitle, fill=sub, font=sub_font
        )

    # Weekday labels (Sun..Sat)
    headers = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    # Vertical layout: place weekday labels below the objective line
    _, h_label = _wh("Sun", wday_font)
    y_labels = sub_y + h_sub // 2 + int(16 * scale)
    for c, name in enumerate(headers):
        x_center = margin + c * (cell_w + grid_gap) + cell_w // 2
        try:
            draw.text((x_center, y_labels), name, fill=sub, font=wday_font, anchor="mm")
        except TypeError:
            wlbl, hlbl = _wh(name, wday_font)
            draw.text(
                (x_center - wlbl / 2, y_labels - hlbl / 2),
                name,
                fill=sub,
                font=wday_font,
            )

    # Cells, aligned to month rows of 7
    for day in range(1, num_days + 1):
        r = (offset + (day - 1)) // cols
        c = (offset + (day - 1)) % cols
        x0 = margin + c * (cell_w + grid_gap)
        # Start grid below weekday labels with some extra spacing
        grid_top = y_labels + h_label // 2 + int(24 * scale)
        y0 = grid_top + r * (cell_h + grid_gap)
        x1 = x0 + cell_w
        y1 = y0 + cell_h

        row = schedule.ledger[day - 1] if day - 1 < len(schedule.ledger) else None
        if row is not None:
            fill, txt = action_colors.get(row.action, ((70, 70, 70), fg))
        else:
            fill, txt = (
                ((48, 52, 61), sub)
                if theme == "dark"
                else ((230, 232, 238), (120, 128, 138))
            )
        draw.rounded_rectangle([x0, y0, x1, y1], radius=24, fill=fill)

        pad = 18
        # Day and Action tag
        draw.text((x0 + pad, y0 + pad), f"{day}", fill=txt, font=num_font)

        # Action badge (top-right), keep generous margins to avoid clipping
        if row is not None:
            tag = row.action
            tw, th = _wh(tag, label_font)
            badge_margin = max(24, int(min(cell_w, cell_h) * 0.03))
            inner_pad_x, inner_pad_y = 18, 12
            bx2 = x1 - badge_margin
            bx1 = bx2 - (tw + inner_pad_x * 2)
            by1 = y0 + badge_margin
            by2 = by1 + (th + inner_pad_y * 2)
            radius = int((th + inner_pad_y * 2) / 2)
            draw.rounded_rectangle(
                [bx1, by1, bx2, by2], radius=radius, outline=txt, width=3
            )
            # Center the text within the badge using the text bbox center.
            cx = (bx1 + bx2) / 2
            cy = (by1 + by2) / 2
            try:
                # Pillow >=8 supports anchor; 'mm' = middle/middle.
                draw.text((cx, cy), tag, fill=txt, font=label_font, anchor="mm")
            except TypeError:
                # Fallback: compute top-left such that bbox is centered.
                draw.text((cx - tw / 2, cy - th / 2), tag, fill=txt, font=label_font)

        # Compact info lines: payout / deposits / one or two bills
        info_y = y0 + pad + int(56 * scale)
        text_x = x0 + pad

        def ellipsize(text: str, font, max_w: int) -> str:
            if draw.textbbox((0, 0), text, font=font)[2] <= max_w:
                return text
            ell = "…"
            s = text
            while s and draw.textbbox((0, 0), s + ell, font=font)[2] > max_w:
                s = s[:-1]
            return (s + ell) if s else ell

        if row is not None:
            avail_w = x1 - pad - text_x
            line_h = int(28 * scale)
            lines = []
            if row.net_cents:
                lines.append((f"Payout {cents_to_str(row.net_cents)}", txt))
            if row.deposit_cents:
                lines.append((f"Deposits {cents_to_str(row.deposit_cents)}", txt))
            bill_items = bills_by_day.get(day, []) if bills_by_day else []
            for name, amt in bill_items[:2]:
                lines.append((f"• {name} {cents_to_str(amt)}", txt))
            extra = max(0, len(bill_items) - 2)
            if extra:
                lines.append((f"… +{extra} more", sub))

            for i, (text_line, color) in enumerate(lines[:3]):
                draw.text(
                    (text_x, info_y + i * line_h),
                    ellipsize(text_line, small_font, avail_w),
                    fill=color,
                    font=small_font,
                )

        if row is not None:
            close = cents_to_str(row.closing_cents)
            cw, ch = _wh(close, close_font)
            draw.text((x1 - pad - cw, y1 - pad - ch), close, fill=txt, font=close_font)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_path), format="PNG", optimize=True)
