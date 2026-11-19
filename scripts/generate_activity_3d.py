#!/usr/bin/env python3
"""
KICK.EXE - "Contribution city" 3D activity generator
=====================================================
Renders the same PUBLIC contribution data as the stunt track as an
isometric 3D bar chart (one bar per day, height follows the daily count),
inspired by the profile-3d-contrib night view the owner referenced on
WhatsApp 2026-11-19. Same data rules as generate_stunt_track.py: public
contribution counts only, nothing private beyond published anonymized
counts.

Reads the cached snapshot written by generate_stunt_track.py (run it
first, as the workflow does); no network of its own.

Usage:
    python3 generate_activity_3d.py --out-dir assets/graphs
"""
import argparse, json, os
from datetime import date

W, H = 894, 640
TILE_W, TILE_H = 26.0, 13.0          # 2:1 isometric tile
X0, Y0 = 148.0, 190.0                # iso origin (front corner of week0/day0)
MAX_BAR = 115.0
MONO = "ui-monospace,Menlo,Consolas,monospace"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

THEMES = {
    "dark": {
        "bg": "#0D1117", "panel": "#10151C", "text": "#F5F5F5", "muted": "#8B949E",
        "line": "#1E2630", "accent": "#E5252A", "mark": "#FFD338",
        "base": "#1c232d",
        "levels": ["#1c232d", "#8f2327", "#c02428", "#E5252A", "#FFD338"],
    },
    "light": {
        "bg": "#F5F5F5", "panel": "#FFFFFF", "text": "#0D1117", "muted": "#5b6470",
        "line": "#e3ddd2", "accent": "#E5252A", "mark": "#B8860B",
        "base": "#e8e2d8",
        "levels": ["#e8e2d8", "#f0b7b8", "#e0676b", "#E5252A", "#B8860B"],
    },
}


def shade(hex_color, factor):
    """Darken a #rrggbb color by factor (0..1) for iso side faces."""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return "#{:02x}{:02x}{:02x}".format(int(r * factor), int(g * factor), int(b * factor))


def weeks_from_days(days):
    """Group the flat day list into 53 weeks x 7 days (same shape as the
    stunt track: each entry keyed by its real weekday)."""
    by_date = {d["date"]: d for d in days}
    first = date.fromisoformat(days[0]["date"])
    last = date.fromisoformat(days[-1]["date"])
    # week 0 starts on the Sunday on/before the first date
    from datetime import timedelta
    start = first - timedelta(days=(first.weekday() + 1) % 7)
    weeks = []
    d = start
    while d <= last:
        col = []
        for dow in range(7):
            day = d + timedelta(days=dow)
            col.append(by_date.get(day.isoformat()))
        weeks.append(col)
        d += timedelta(days=7)
    return weeks


def cube(sx, sy, h, color):
    """One iso bar: top diamond plus left/right faces. (sx, sy) is the
    center of the cell's base diamond; the bar rises h px above it."""
    hw, hh = TILE_W / 2, TILE_H / 2
    top_cx, top_cy = sx, sy - h
    top = (f"M {top_cx:.1f} {top_cy - hh:.1f} L {top_cx + hw:.1f} {top_cy:.1f} "
           f"L {top_cx:.1f} {top_cy + hh:.1f} L {top_cx - hw:.1f} {top_cy:.1f} Z")
    out = []
    if h > 0:
        left = (f"M {top_cx - hw:.1f} {top_cy:.1f} L {top_cx:.1f} {top_cy + hh:.1f} "
                f"L {top_cx:.1f} {top_cy + hh + h:.1f} L {top_cx - hw:.1f} {top_cy + h:.1f} Z")
        right = (f"M {top_cx + hw:.1f} {top_cy:.1f} L {top_cx:.1f} {top_cy + hh:.1f} "
                 f"L {top_cx:.1f} {top_cy + hh + h:.1f} L {top_cx + hw:.1f} {top_cy + h:.1f} Z")
        out.append(f'<path d="{left}" fill="{shade(color, 0.55)}"/>')
        out.append(f'<path d="{right}" fill="{shade(color, 0.78)}"/>')
    out.append(f'<path d="{top}" fill="{color}"/>')
    return "\n".join(out)


def svg(theme_name, t, weeks, days):
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"] > 0)
    best = max(days, key=lambda d: d["count"])
    best_date = date.fromisoformat(best["date"]).strftime("%b %-d, %Y")
    first, last = days[0]["date"], days[-1]["date"]
    f_y, f_m = int(first[:4]), int(first[5:7])
    l_y, l_m = int(last[:4]), int(last[5:7])
    rng = f"{MONTHS[f_m-1].upper()} {f_y} - {MONTHS[l_m-1].upper()} {l_y}"

    cells = []
    for w, col in enumerate(weeks):
        for dow, d in enumerate(col):
            if d:
                cells.append((w + dow, w, dow, d))
    cells.sort()  # painter's order: back to front

    peak = max(d["count"] for d in days) or 1
    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
                 f'aria-label="3D activity graph: {total} GitHub contributions in the last year rendered as an isometric bar city.">')
    parts.append(f'<title>KICK.EXE contribution city - 3D activity, {total} contributions in the last year</title>')
    parts.append(f'<desc>Isometric 3D bar chart of the same public contribution data as the stunt track: '
                 f'one bar per day, height follows the daily contribution count. {active} active days; '
                 f'best day {best["count"]} contributions on {best_date}.</desc>')
    parts.append(f'<rect width="{W}" height="{H}" fill="{t["bg"]}" rx="10"/>')
    parts.append(f'<rect x="10" y="10" width="{W-20}" height="{H-20}" fill="none" stroke="{t["line"]}" stroke-width="1.5" rx="8"/>')
    parts.append(f'<rect x="10" y="10" width="64" height="5" fill="{t["accent"]}" rx="2.5"/>')
    parts.append(f'<text x="30" y="54" fill="{t["text"]}" font-family="{MONO}" font-size="23" font-weight="700" letter-spacing="2">CONTRIBUTION CITY // 3D ACTIVITY</text>')
    parts.append(f'<text x="{W-24}" y="54" text-anchor="end" fill="{t["muted"]}" font-family="{MONO}" font-size="14">{rng}</text>')

    for _, w, dow, d in cells:
        sx = X0 + (w - dow) * (TILE_W / 2)
        sy = Y0 + (w + dow) * (TILE_H / 2)
        level = d.get("level")
        if level is None:
            c = d["count"]
            level = 0 if c == 0 else (1 if c <= 2 else (2 if c <= 5 else (3 if c <= 9 else 4)))
        color = t["levels"][min(level, 4)]
        h = 0.0 if d["count"] == 0 else min(MAX_BAR, 5.0 + d["count"] / peak * (MAX_BAR - 5.0))
        parts.append(f'<g><title>{d["count"]} contributions on {d["date"]}</title>{cube(sx, sy, h, color)}</g>')

    # footer: summary + level legend
    fy = H - 46
    parts.append(f'<text x="30" y="{fy}" fill="{t["accent"]}" font-family="{MONO}" font-size="19" font-weight="700">{total}</text>')
    parts.append(f'<text x="30" y="{fy+22}" fill="{t["muted"]}" font-family="{MONO}" font-size="11" letter-spacing="0.5">CONTRIBUTIONS / YEAR</text>')
    parts.append(f'<text x="230" y="{fy}" fill="{t["accent"]}" font-family="{MONO}" font-size="19" font-weight="700">{active}</text>')
    parts.append(f'<text x="230" y="{fy+22}" fill="{t["muted"]}" font-family="{MONO}" font-size="11" letter-spacing="0.5">ACTIVE DAYS</text>')
    parts.append(f'<text x="400" y="{fy}" fill="{t["accent"]}" font-family="{MONO}" font-size="19" font-weight="700">{best["count"]}</text>')
    parts.append(f'<text x="400" y="{fy+22}" fill="{t["muted"]}" font-family="{MONO}" font-size="11" letter-spacing="0.5">BEST DAY - {best_date.upper()}</text>')
    lx = W - 230
    parts.append(f'<text x="{lx-14}" y="{fy+4}" text-anchor="end" fill="{t["muted"]}" font-family="{MONO}" font-size="11">LESS</text>')
    for i, col in enumerate(t["levels"]):
        parts.append(f'<rect x="{lx + i*26}" y="{fy-8}" width="18" height="18" rx="3" fill="{col}"/>')
    parts.append(f'<text x="{lx + 5*26 + 14}" y="{fy+4}" fill="{t["muted"]}" font-family="{MONO}" font-size="11">MORE</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--from-json",
                    help="read data/contributions.json (default: <out-dir>/../data/contributions.json)")
    args = ap.parse_args()
    path = args.from_json or os.path.join(args.out_dir, "..", "data", "contributions.json")
    payload = json.load(open(path))
    days = payload["data"]
    weeks = weeks_from_days(days)
    for name, theme in THEMES.items():
        with open(f"{args.out_dir}/activity-3d-{name}.svg", "w") as f:
            f.write(svg(name, theme, weeks, days))
    print(f"days={len(days)} weeks={len(weeks)}; wrote activity-3d-{{dark,light}}.svg")


if __name__ == "__main__":
    main()
