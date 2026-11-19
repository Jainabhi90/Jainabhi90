#!/usr/bin/env python3
"""
KICK.EXE - "Pit wall" stats deck generator
===========================================
Static SVG panel from PUBLIC, unauthenticated GitHub data only:
  A. Big-number tiles  - contributions (as published on the profile), active
     days, current + longest streak (computed from the public daily counts),
     public repos, stars earned on own public repos
  B. Languages         - byte share stacked bar across PUBLIC repos only,
     labeled as bytes of code, never as a skill rating
  C. Velocity          - monthly totals from the public contributions page

Same data rules as generate_telemetry.py: private repos are never touched or
named; the contributions page only exposes the anonymized private counts the
owner already publishes. Network failure keeps last good assets (exit 1,
::warning::, no writes).

Usage: python3 generate_stats.py --user Jainabhi90 --out-dir assets/graphs
"""
import json, re, sys, urllib.request
from datetime import date, timedelta

W, H = 730, 336
THEMES = {
    "dark":  {"bg": "#0D1117", "panel": "#10151C", "text": "#F5F5F5", "muted": "#8B949E",
              "line": "#1E2630", "accent": "#E5252A", "mark": "#FFD338", "bar": "#8f2327"},
    "light": {"bg": "#F5F5F5", "panel": "#FFFFFF", "text": "#0D1117", "muted": "#5b6470",
              "line": "#e3ddd2", "accent": "#E5252A", "mark": "#B8860B", "bar": "#e0676b"},
}
MONO = "ui-monospace,Menlo,Consolas,monospace"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
# GitHub's own language colors, used for the stacked bar legend
LANG_COLORS = {"JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Python": "#3572A5",
               "Java": "#b07219", "HTML": "#e34c26", "CSS": "#563d7c",
               "Jupyter Notebook": "#DA5B0B", "Shell": "#89e051"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "kick-exe-generator",
                                               "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def contribution_days(user):
    html = get(f"https://github.com/users/{user}/contributions")
    cells = re.findall(r'<td\b[^>]*class="ContributionCalendar-day"[^>]*>', html)
    tips = dict(re.findall(r'<tool-tip\b[^>]*for="([^"]+)"[^>]*>([^<]+)</tool-tip>', html))
    def attr(tag, name):
        m = re.search(name + r'="([^"]*)"', tag)
        return m.group(1) if m else ""
    out = []
    for tag in cells:
        m = re.match(r"(\d+) contribution", tips.get(attr(tag, "id"), ""))
        out.append({"date": attr(tag, "data-date"), "count": int(m.group(1)) if m else 0})
    if not out:
        raise SystemExit("no contribution cells; page layout changed?")
    return out


def public_repos(user):
    repos = json.loads(get(f"https://api.github.com/users/{user}/repos?per_page=100&type=owner"))
    return [r for r in repos if not r.get("private") and not r.get("fork")]


def language_bytes(repos):
    """Aggregate language bytes across repos. Any per-repo fetch failure makes
    the whole run fail loudly (caller exits nonzero, last good assets stay):
    a silently partial aggregate would commit a WRONG language bar."""
    agg = {}
    failed = []
    for r in repos:
        try:
            for lang, b in json.loads(get(r["url"] + "/languages")).items():
                agg[lang] = agg.get(lang, 0) + b
        except Exception as e:
            failed.append(f'{r["name"]}: {e}')
    if failed:
        raise RuntimeError(f"language fetch failed for {len(failed)}/{len(repos)} repos: "
                           + "; ".join(failed[:3]))
    return sorted(agg.items(), key=lambda kv: -kv[1])


def streaks(days):
    """Current + longest streak of consecutive days with >=1 contribution.
    Current streak runs through the most recent active day; a today with zero
    contributions does not break it until tomorrow. Window: the last year the
    public page shows, labeled on the panel."""
    # the public page emits cells row-major (a row per weekday), so the flat
    # list is not chronological; sort by real date before walking streaks
    days = sorted(days, key=lambda d: d["date"])
    counts = {d["date"]: d["count"] for d in days}
    first, last = date.fromisoformat(days[0]["date"]), date.fromisoformat(days[-1]["date"])
    longest = run = 0
    d = first
    while d <= last:
        if counts.get(d.isoformat(), 0) > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0
        d += timedelta(days=1)
    current = 0
    d = last
    while d >= first and counts.get(d.isoformat(), 0) > 0:
        current += 1
        d -= timedelta(days=1)
    return current, longest


def monthly_velocity(days):
    per = {}
    for d in days:
        per[d["date"][:7]] = per.get(d["date"][:7], 0) + d["count"]
    return sorted(per.items())


def svg(t, days, repos, langs):
    total = sum(d["count"] for d in days)
    active = sum(1 for d in days if d["count"] > 0)
    current, longest = streaks(days)
    stars = sum(r["stargazers_count"] for r in repos)
    months = monthly_velocity(days)

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="GitHub stats: {total} contributions in the last year, {active} active days, '
         f'current streak {current} days, longest streak {longest} days, {len(repos)} public repos, '
         f'{stars} stars. Public data only.">']
    p.append(f'<title>KICK.EXE pit wall stats (public data)</title>')
    p.append(f'<rect width="{W}" height="{H}" fill="{t["bg"]}" rx="10"/>')
    p.append(f'<rect x="10" y="10" width="{W-20}" height="{H-20}" fill="none" stroke="{t["line"]}" stroke-width="1.5" rx="8"/>')
    p.append(f'<rect x="10" y="10" width="52" height="4" fill="{t["accent"]}" rx="2"/>')
    p.append(f'<text x="30" y="40" fill="{t["text"]}" font-family="{MONO}" font-size="15" font-weight="700" letter-spacing="2">PIT WALL // BY THE NUMBERS</text>')
    p.append(f'<text x="{W-24}" y="40" text-anchor="end" fill="{t["muted"]}" font-family="{MONO}" font-size="9">PUBLIC PROFILE DATA ONLY</text>')

    # A: number tiles, 3 cols x 2 rows
    tiles = [(f"{total}", "CONTRIBUTIONS", "LAST 365 DAYS"),
             (f"{active}", "ACTIVE DAYS", "LAST 365 DAYS"),
             (f"{stars}", "STARS EARNED", "OWN PUBLIC REPOS"),
             (f"{current}d", "CURRENT STREAK", "DAYS IN A ROW"),
             (f"{longest}d", "LONGEST STREAK", "IN THE LAST YEAR"),
             (f"{len(repos)}", "PUBLIC REPOS", "OWN, NOT FORKS")]
    tw, th, gx, gy, x0, y0 = 122, 66, 10, 10, 30, 58
    for i, (num, label, sub) in enumerate(tiles):
        x, y = x0 + (i % 3) * (tw + gx), y0 + (i // 3) * (th + gy)
        p.append(f'<rect x="{x}" y="{y}" width="{tw}" height="{th}" fill="{t["panel"]}" stroke="{t["line"]}" stroke-width="1" rx="8"/>')
        p.append(f'<text x="{x+12}" y="{y+30}" fill="{t["accent"]}" font-family="{MONO}" font-size="21" font-weight="700">{num}</text>')
        p.append(f'<text x="{x+12}" y="{y+46}" fill="{t["text"]}" font-family="{MONO}" font-size="8.5" letter-spacing="0.5">{label}</text>')
        p.append(f'<text x="{x+12}" y="{y+58}" fill="{t["muted"]}" font-family="{MONO}" font-size="7">{sub}</text>')
    p.append(f'<text x="30" y="{y0 + 2*th + gy + 16}" fill="{t["muted"]}" font-family="{MONO}" font-size="7.5">'
             f'COUNTS AS PUBLISHED ON THE PROFILE, INCL. ANONYMIZED PRIVATE CONTRIBUTION COUNTS. NO PRIVATE REPOS READ OR NAMED.</text>')

    # B: languages stacked bar + legend (right column)
    rx = 446
    p.append(f'<text x="{rx}" y="66" fill="{t["muted"]}" font-family="{MONO}" font-size="9" letter-spacing="1">LANGUAGES - BYTE SHARE, {len(repos)} PUBLIC REPOS</text>')
    grand = sum(b for _, b in langs) or 1
    top, rest = langs[:5], langs[5:]
    if rest:
        top = top + [("Other", sum(b for _, b in rest))]
    bar_y, bar_h, bx, bw_total = 78, 14, rx, 260
    x = bx
    for lang, b in top:
        wseg = max(2, b / grand * bw_total)
        col = LANG_COLORS.get(lang, t["mark"])
        p.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{wseg:.1f}" height="{bar_h}" fill="{col}"><title>{lang}: {100*b/grand:.1f}%</title></rect>')
        x += wseg
    y = bar_y + 32
    for i, (lang, b) in enumerate(top):
        col = LANG_COLORS.get(lang, t["mark"])
        lx = rx + (i % 2) * 140
        if i % 2 == 0 and i:
            y += 18
        p.append(f'<rect x="{lx}" y="{y-8}" width="8" height="8" rx="2" fill="{col}"/>')
        p.append(f'<text x="{lx+13}" y="{y}" fill="{t["text"]}" font-family="{MONO}" font-size="9">{lang} {round(100*b/grand)}%</text>')
    p.append(f'<text x="{rx}" y="{y+22}" fill="{t["muted"]}" font-family="{MONO}" font-size="7.5">SHARE OF CODE BYTES, NOT A SKILL RATING</text>')

    # C: velocity mini chart (right column)
    vy = y + 48
    p.append(f'<text x="{rx}" y="{vy}" fill="{t["muted"]}" font-family="{MONO}" font-size="9" letter-spacing="1">CONTRIBUTION VELOCITY - MONTHLY</text>')
    peak = max(v for _, v in months) or 1
    bw, gap, base = 12, 4, vy + 64
    cur_ym = date.today().strftime("%Y-%m")
    for i, (ym, v) in enumerate(months):
        h = max(2, int(v / peak * 46))
        x = rx + i * (bw + gap)
        p.append(f'<rect x="{x}" y="{base-h}" width="{bw}" height="{h}" rx="2" fill="{t["accent"] if ym == cur_ym else t["bar"]}">'
                 f'<title>{v} contributions in {ym}</title></rect>')
    first_ym = months[0][0]
    p.append(f'<text x="{rx}" y="{base+14}" fill="{t["muted"]}" font-family="{MONO}" font-size="7.5">'
             f'{MONTHS[int(first_ym[5:7])-1]}\'{first_ym[2:4]} (PARTIAL) TO NOW; RED = CURRENT MONTH, STILL RUNNING</text>')
    p.append('</svg>')
    return "\n".join(p)


def main():
    import argparse, os
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="Jainabhi90")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--from-json", action="store_true",
                    help="offline re-render from data/contributions.json + data/stats-snapshot.json")
    args = ap.parse_args()
    snap_path = os.path.join(args.out_dir, "..", "data", "stats-snapshot.json")
    if args.from_json:
        payload = json.load(open(os.path.join(args.out_dir, "..", "data", "contributions.json")))
        days = payload["data"]
        snap = json.load(open(snap_path))
        repos, langs = snap["repos"], [tuple(x) for x in snap["languages"]]
    else:
        try:
            days = contribution_days(args.user)
            repos = public_repos(args.user)
            langs = language_bytes(repos)
        except SystemExit:
            raise
        except Exception as e:
            print(f"::warning::KICK.EXE stats fetch failed: {e}. Kept last good assets; investigate the data source.", file=sys.stderr)
            sys.exit(1)
        os.makedirs(os.path.dirname(snap_path), exist_ok=True)
        with open(snap_path, "w") as f:
            json.dump({"user": args.user,
                       "repos": repos,
                       "languages": langs}, f, indent=1)
    for name, theme in THEMES.items():
        with open(f"{args.out_dir}/stats-{name}.svg", "w") as f:
            f.write(svg(theme, days, repos, langs))
    cur, lng = streaks(days)
    print(f"total={sum(d['count'] for d in days)} streak={cur}/{lng} repos={len(repos)} langs={len(langs)}; wrote stats-{{dark,light}}.svg")


if __name__ == "__main__":
    main()
