#!/usr/bin/env python3
"""
KICK.EXE - Contribution Stunt Track generator
=============================================
Reads Abhiraj Jain's REAL GitHub contribution data and renders it as an
animated "stunt track" SVG for the profile README.

Data source (no token, no secrets):
    https://github.com/users/<user>/contributions
This public endpoint returns exactly what his public profile shows,
including the anonymized private-contribution counts he has already chosen
to publish (Settings > "Include private contributions on my profile").
Nothing private beyond those published daily counts is used.

Usage:
    python3 generate_stunt_track.py --user Jainabhi90 --out-dir ../assets/graphs
    python3 generate_stunt_track.py --from-json ../data/contributions.json --out-dir ../assets/graphs
    python3 generate_stunt_track.py --static-only ...

Outputs per theme (dark / light):
    stunt-track-<theme>.svg   animated (SMIL rider + CSS trail)
    stunt-track-<theme>-static.svg  same data, no motion (fallback / reduced motion)

The rider marker is a deliberately simple swappable token. The art owner
replaces the group marked RIDER-ART with the Kick sprite; geometry and
timing are data-driven and must not change.
"""
import argparse, json, re, sys, urllib.request
from datetime import date, timedelta

CELL, GAP = 10.0, 3.0
PITCH = CELL + GAP
WEEKS = 53
GRID_W = WEEKS * PITCH - GAP          # 676
GRID_H = 7 * PITCH - GAP              # 82
M_LEFT, M_RIGHT = 34.0, 20.0
TRACK_TOP = 64.0                       # y where the track lane begins
M_TOP = TRACK_TOP + 58.0               # grid top (lane above the grid)
M_BOTTOM_LABELS = 56.0                 # stats strip under grid
WIDTH = M_LEFT + GRID_W + M_RIGHT      # 730
HEIGHT = M_TOP + GRID_H + M_BOTTOM_LABELS

THEMES = {
    "dark": {
        "bg": "#0D1117", "panel": "#161B22", "text": "#F5F5F5",
        "muted": "#8B949E", "grid_line": "#1c232d",
        "l0": "#161B22", "l1": "#4d1d20", "l2": "#8f2327",
        "l3": "#E5252A", "l4": "#FFD338",
        "track": "#2a3440", "track_mark": "#FFD338",
        "rider": "#E5252A", "rider_core": "#F5F5F5", "trail": "#E5252A",
        "ramp": "#1f2937",
    },
    "light": {
        "bg": "#F5F5F5", "panel": "#FFFFFF", "text": "#0D1117",
        "muted": "#5b6470", "grid_line": "#e3ddd2",
        "l0": "#e8e2d8", "l1": "#f0b7b8", "l2": "#e0676b",
        "l3": "#E5252A", "l4": "#B8860B",
        "track": "#d8d2c6", "track_mark": "#B8860B",
        "rider": "#E5252A", "rider_core": "#0D1117", "trail": "#E5252A",
        "ramp": "#ddd6c8",
    },
}

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]



def load_rider_b64(out_dir):
    """RIDER-ART: embedded Kick sprite (exact-character art approved by the user
    on WhatsApp 2026-11-19 09:20 IST: dark close-up avatar, full-body Kick and
    Kick skateboarding). PNG lives at <repo>/assets/kick-rider.png; embedded as
    base64 so the SVG survives GitHub's camo proxy (external image hrefs inside
    SVG break). Missing file falls back to the original circle token."""
    import base64, os
    p = os.path.join(out_dir, "..", "kick-rider.png")
    if not os.path.exists(p):
        return None
    return base64.b64encode(open(p, "rb").read()).decode("ascii")

# sprite display size and anchor: board center of the trimmed sprite sits at
# ~67.7% across, ~84.9% down the frame, so the motion pivot lands under the board.
RIDER_W, RIDER_H = 22.0, 38.0
RIDER_AX, RIDER_AY = 14.9, 32.3

def fetch_html(user: str) -> str:
    url = f"https://github.com/users/{user}/contributions"
    req = urllib.request.Request(url, headers={"User-Agent": "kick-exe-generator"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:
        # transient network/API failure: no writes, so last good assets are
        # preserved, but fail LOUDLY (workflow annotation + nonzero exit)
        # so a broken data source never looks like a successful run
        print(f"::warning::KICK.EXE contribution fetch failed: {e}. "
              f"Kept last good assets; investigate the data source.", file=sys.stderr)
        sys.exit(1)


def parse_html(html: str):
    """Parse the public contributions page -> [{date, level, count}] oldest first."""
    cell_re = re.compile(r'<td\b[^>]*class="ContributionCalendar-day"[^>]*>')
    tip_re = re.compile(r'<tool-tip\b[^>]*for="([^"]+)"[^>]*>([^<]+)</tool-tip>')
    def attr(tag, name):
        m = re.search(name + r'="([^"]*)"', tag)
        return m.group(1) if m else None
    tips = dict(tip_re.findall(html))
    days = []
    for tag in cell_re.findall(html):
        tip = tips.get(attr(tag, "id"), "")
        m = re.match(r"(\d+) contribution", tip)
        days.append({
            "date": attr(tag, "data-date"),
            "level": int(attr(tag, "data-level") or 0),
            "count": int(m.group(1)) if m else 0,
        })
    if not days:
        raise SystemExit("no contribution cells found; page layout changed?")
    return days


def weeks_from_days(days):
    """Regroup the flat list into 53 weeks x 7 days.

    The public contributions page emits cells ROW-major: one row per weekday
    (Sun..Sat), each row chronological. The current (last) week is partial:
    future days have no cell, so trailing rows can be shorter. Rows are split
    where the date jumps backwards, then mapped to weekdays by real date.
    """
    rows, current = [], []
    for d in days:
        if current and d["date"] <= current[-1]["date"]:
            rows.append(current)
            current = []
        current.append(d)
    rows.append(current)
    by_dow = {}
    for row in rows:
        wd = (date.fromisoformat(row[0]["date"]).weekday() + 1) % 7  # Sun=0
        by_dow[wd] = row
    weeks = []
    for w in range(WEEKS):
        col = []
        for dow in range(7):
            row = by_dow.get(dow, [])
            col.append(row[w] if w < len(row) else None)
        weeks.append(col)
    # sanity: within a column, present dates must be consecutive
    for col in weeks:
        seq = [d["date"] for d in col if d]
        for a, b in zip(seq, seq[1:]):
            if (date.fromisoformat(b) - date.fromisoformat(a)).days != 1:
                raise SystemExit(f"week grouping broken: {a} -> {b}")
    return weeks


def build_track(weeks):
    """Weekly totals -> track elevation path (SVG) above the grid.

    Elevation uses a centered 3-week moving average of weekly totals so the
    course reads as connected runs instead of spikes; raw daily counts stay
    untouched in the grid cells below. Scale is linear from 0 to the max
    smoothed weekly total; the scale factor is printed for the docs."""
    totals = [sum(d["count"] for d in col if d) for col in weeks]
    smooth = []
    for w in range(len(totals)):
        window = totals[max(0, w - 1):w + 2]
        smooth.append(sum(window) / len(window))
    peak = max(smooth) or 1
    max_rise = 46.0
    pts = []
    for w, s in enumerate(smooth):
        x = M_LEFT + w * PITCH + PITCH / 2
        y = M_TOP - 10 - (s / peak) * max_rise
        pts.append((x, y, s))
    # smooth path (Catmull-Rom -> bezier)
    d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f} "
    for i in range(1, len(pts)):
        x0, y0, _ = pts[i - 1]
        x1, y1, _ = pts[i]
        mx = (x0 + x1) / 2
        d += f"C {mx:.1f} {y0:.1f} {mx:.1f} {y1:.1f} {x1:.1f} {y1:.1f} "
    return d, totals, peak, pts


def month_labels(weeks):
    labels, last = [], None
    for w, col in enumerate(weeks):
        first = next((d for d in col if d), None)
        if not first:
            continue
        m = int(first["date"][5:7])
        if m != last and w < WEEKS - 1:
            x = M_LEFT + w * PITCH
            labels.append((x, MONTHS[m - 1]))
            last = m
    return labels


def svg(theme_name, t, weeks, days, totals, peak, track_d, animated=True, rider_b64=None, track_end=None):
    total_contribs = sum(d["count"] for d in days)
    active_days = sum(1 for d in days if d["count"] > 0)
    best = max(days, key=lambda d: d["count"])
    best_date = date.fromisoformat(best["date"]).strftime("%b %-d, %Y")

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH:.0f} {HEIGHT:.0f}" '
                 f'width="{WIDTH:.0f}" height="{HEIGHT:.0f}" role="img" '
                 f'aria-label="Contribution stunt track: {total_contribs} GitHub contributions in the last year, rendered as a skateboard stunt course.">')
    parts.append(f'<title>KICK.EXE contribution stunt track - {total_contribs} contributions in the last year</title>')
    parts.append(f'<desc>Real GitHub contribution data for Jainabhi90. Each column is one week; '
                 f'cell color and track elevation follow actual daily and weekly contribution counts. '
                 f'{active_days} active days; best day {best["count"]} contributions on {best_date}.</desc>')
    if animated:
        parts.append(f'''<style>
.trail {{ stroke-dasharray: 6 8; animation: trailmove 1.2s linear infinite; }}
@keyframes trailmove {{ to {{ stroke-dashoffset: -28; }} }}
.pulse {{ animation: pulse 2.4s ease-in-out infinite; transform-origin: center; transform-box: fill-box; }}
@keyframes pulse {{ 0%,100% {{ opacity:.25 }} 50% {{ opacity:.7 }} }}
</style>''')
    parts.append(f'<rect width="{WIDTH:.0f}" height="{HEIGHT:.0f}" fill="{t["bg"]}" rx="10"/>')
    parts.append(f'<rect x="10" y="10" width="{WIDTH-20:.0f}" height="{HEIGHT-20:.0f}" fill="none" '
                 f'stroke="{t["grid_line"]}" stroke-width="1.5" rx="8"/>')
    # header
    parts.append(f'<text x="{M_LEFT:.0f}" y="34" fill="{t["text"]}" font-family="ui-monospace,Menlo,Consolas,monospace" '
                 f'font-size="17" font-weight="700" letter-spacing="2">CONTRIBUTION STUNT TRACK</text>')
    parts.append(f'<text x="{WIDTH - M_RIGHT:.0f}" y="34" text-anchor="end" fill="{t["muted"]}" '
                 f'font-family="ui-monospace,Menlo,Consolas,monospace" font-size="12">'
                 f'{total_contribs} contributions in the last year</text>')

    # week ramps (decorative elevation markers behind the track for strong weeks)
    for w, tot in enumerate(totals):
        if tot >= max(3, peak * 0.45):
            x = M_LEFT + w * PITCH
            parts.append(f'<path d="M {x:.1f} {M_TOP:.1f} L {x + PITCH:.1f} {M_TOP - 14:.1f} L {x + PITCH:.1f} {M_TOP:.1f} Z" '
                         f'fill="{t["ramp"]}"/>')

    # track line + in-asset methodology label
    parts.append(f'<text x="{M_LEFT:.0f}" y="{M_TOP - 60:.0f}" fill="{t["muted"]}" '
                 f'font-family="ui-monospace,Menlo,Consolas,monospace" font-size="8" letter-spacing="0.5">'
                 f'TRACK HEIGHT = 3-WEEK AVG OF WEEKLY TOTALS (SMOOTHED)</text>')
    parts.append(f'<path d="{track_d}" fill="none" stroke="{t["track"]}" stroke-width="3" stroke-linecap="round"/>')

    # current week is still running: mark its column in the asset itself
    cur_x = M_LEFT + (WEEKS - 1) * PITCH - 3
    parts.append(f'<rect x="{cur_x:.1f}" y="{M_TOP - 4:.0f}" width="{PITCH + 4:.0f}" height="{GRID_H + 8:.0f}" '
                 f'fill="none" stroke="{t["track_mark"]}" stroke-width="1" stroke-dasharray="3 3" rx="3"/>')
    parts.append(f'<text x="{WIDTH - M_RIGHT:.0f}" y="{M_TOP - 60:.0f}" text-anchor="end" fill="{t["track_mark"]}" '
                 f'font-family="ui-monospace,Menlo,Consolas,monospace" font-size="8">DASHED COLUMN = THIS WEEK SO FAR</text>')
    if animated:
        parts.append(f'<path class="trail" d="{track_d}" fill="none" stroke="{t["trail"]}" '
                     f'stroke-width="1.4" opacity="0.8"/>')

    # grid cells
    for w, col in enumerate(weeks):
        for dow, d in enumerate(col):
            if not d:
                continue
            x = M_LEFT + w * PITCH
            y = M_TOP + dow * PITCH
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL:.0f}" height="{CELL:.0f}" rx="2" '
                         f'fill="{t["l" + str(d["level"])]}"><title>{d["count"]} contributions on {d["date"]}</title></rect>')

    # month labels
    for x, label in month_labels(weeks):
        parts.append(f'<text x="{x:.1f}" y="{M_TOP - 48:.0f}" fill="{t["muted"]}" '
                     f'font-family="ui-monospace,Menlo,Consolas,monospace" font-size="9">{label}</text>')

    # rider (RIDER-ART: embedded Kick sprite; id and animateMotion preserved,
    # circle token kept as fallback when assets/kick-rider.png is absent)
    if rider_b64:
        art = (f'<image href="data:image/png;base64,{rider_b64}" '
               f'x="{-RIDER_AX}" y="{-RIDER_AY}" width="{RIDER_W:.0f}" height="{RIDER_H:.0f}"/>')
    else:
        art = (f'<circle class="pulse" r="10" fill="{t["rider"]}"/>\n'
               f'  <circle r="5.5" fill="{t["rider"]}" stroke="{t["rider_core"]}" stroke-width="2"/>')
    if animated:
        rider = (f'<g id="rider">\n  {art}\n  '
                 f'<animateMotion dur="24s" repeatCount="indefinite" rotate="auto" path="{track_d}"/>\n</g>')
    else:
        # static fallback: park the rider at the track start (same pose as t=0
        # of the animated version; the end position would cover the legend)
        ex, ey = track_end if track_end else (M_LEFT, M_TOP - 10)
        rider = f'<g id="rider" transform="translate({ex:.1f} {ey:.1f})">\n  {art}\n</g>'
    parts.append(rider)

    # stats strip
    sy = M_TOP + GRID_H + 30
    stats = [
        (f"{total_contribs}", "CONTRIBUTIONS"),
        (f"{active_days}", "ACTIVE DAYS"),
        (f"{best['count']}", f"BEST DAY - {best_date.upper()}"),
        (f"{max(sum(d['count'] for d in c if d) for c in weeks)}", "PEAK WEEK (STILL RUNNING)"),
    ]
    seg = GRID_W / len(stats)
    for i, (num, label) in enumerate(stats):
        cx = M_LEFT + seg * i + 4
        parts.append(f'<text x="{cx:.1f}" y="{sy:.0f}" fill="{t["l3"]}" '
                     f'font-family="ui-monospace,Menlo,Consolas,monospace" font-size="15" font-weight="700">{num}</text>')
        parts.append(f'<text x="{cx:.1f}" y="{sy + 14:.0f}" fill="{t["muted"]}" '
                     f'font-family="ui-monospace,Menlo,Consolas,monospace" font-size="7" letter-spacing="0.5">{label}</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="Jainabhi90")
    ap.add_argument("--from-json", help="skip network, read data/contributions.json")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--static-only", action="store_true")
    args = ap.parse_args()

    if args.from_json:
        payload = json.load(open(args.from_json))
        days = payload["data"]
    else:
        days = parse_html(fetch_html(args.user))
        # no timestamps in the payload: unchanged data must produce an
        # unchanged file so the workflow commits only on real change
        payload = {"user": args.user,
                   "source": f"https://github.com/users/{args.user}/contributions",
                   "total_contributions": sum(d["count"] for d in days),
                   "data": days}
        path = f"{args.out_dir}/../data/contributions.json"
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(payload, f, indent=1)

    weeks = weeks_from_days(days)
    track_d, totals, peak, pts = build_track(weeks)
    rider_b64 = load_rider_b64(args.out_dir)
    track_end = (pts[0][0], pts[0][1])  # static parks at track start
    print(f"weeks={len(weeks)} days={len(days)} total={sum(d['count'] for d in days)} "
          f"peak_week={peak} track_scale=linear(0..{peak})")

    for name, theme in THEMES.items():
        if not args.static_only:
            with open(f"{args.out_dir}/stunt-track-{name}.svg", "w") as f:
                f.write(svg(name, theme, weeks, days, totals, peak, track_d, animated=True, rider_b64=rider_b64, track_end=track_end))
        with open(f"{args.out_dir}/stunt-track-{name}-static.svg", "w") as f:
            f.write(svg(name, theme, weeks, days, totals, peak, track_d, animated=False, rider_b64=rider_b64, track_end=track_end))
    print("wrote stunt-track-{dark,light}.svg + static variants to", args.out_dir)


if __name__ == "__main__":
    main()
