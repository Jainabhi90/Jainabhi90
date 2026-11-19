#!/usr/bin/env python3
"""
KICK.EXE - Engineering telemetry generator
==========================================
Static SVG panel from PUBLIC, unauthenticated GitHub data only:
  A. Contribution velocity  - monthly totals from the public contributions page
  B. Public repo activity   - most recently pushed PUBLIC repos (api.github.com)
  C. Languages              - bytes aggregated across PUBLIC repos only

Hard rules baked into the output:
  - private repos (NioLearn, EduOS, ...) are never touched or named
  - language bars are labeled as bytes of code, never as skill percentages
  - network failure keeps last good assets (exit 0, no writes)

Usage: python3 generate_telemetry.py --user Jainabhi90 --out-dir assets/graphs
"""
import json, re, sys, urllib.request
from datetime import date

W, H = 730, 322
THEMES = {
    "dark":  {"bg": "#0D1117", "panel": "#161B22", "text": "#F5F5F5", "muted": "#8B949E",
              "line": "#1c232d", "accent": "#E5252A", "mark": "#FFD338", "bar": "#8f2327"},
    "light": {"bg": "#F5F5F5", "panel": "#FFFFFF", "text": "#0D1117", "muted": "#5b6470",
              "line": "#e3ddd2", "accent": "#E5252A", "mark": "#B8860B", "bar": "#e0676b"},
}
MONO = "ui-monospace,Menlo,Consolas,monospace"
MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]


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
    repos = json.loads(get(f"https://api.github.com/users/{user}/repos?per_page=100&sort=pushed&type=owner"))
    return [r for r in repos if not r.get("private") and not r.get("fork")]


def language_bytes(user, repos):
    agg = {}
    for r in repos:
        try:
            for lang, b in json.loads(get(r["url"] + "/languages")).items():
                agg[lang] = agg.get(lang, 0) + b
        except Exception:
            continue
    return sorted(agg.items(), key=lambda kv: -kv[1])


def monthly_velocity(days):
    """Every month the data window touches, including both partial ends.
    Dropping the leading partial month would undercount vs the 583 total,
    so the window is shown in full and labeled."""
    per = {}
    for d in days:
        key = d["date"][:7]
        per[key] = per.get(key, 0) + d["count"]
    return sorted(per.items())


def svg(t, months, repos, langs, user):
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="Engineering telemetry for {user}: monthly contribution velocity, public repository activity, and language bytes across public repositories only.">']
    p.append(f'<title>KICK.EXE engineering telemetry (public data)</title>')
    p.append(f'<rect width="{W}" height="{H}" fill="{t["bg"]}" rx="10"/>')
    p.append(f'<rect x="10" y="10" width="{W-20}" height="{H-20}" fill="none" stroke="{t["line"]}" stroke-width="1.5" rx="8"/>')
    p.append(f'<text x="30" y="36" fill="{t["text"]}" font-family="{MONO}" font-size="15" font-weight="700" letter-spacing="2">ENGINEERING TELEMETRY</text>')
    p.append(f'<text x="{W-24}" y="36" text-anchor="end" fill="{t["muted"]}" font-family="{MONO}" font-size="9">PUBLIC DATA ONLY - NO PRIVATE REPOS</text>')

    # A: velocity bars
    p.append(f'<text x="30" y="66" fill="{t["muted"]}" font-family="{MONO}" font-size="9" letter-spacing="1">CONTRIBUTION VELOCITY (MONTHLY, REAL COUNTS)</text>')
    peak = max(v for _, v in months) or 1
    bw, gap, x0, base = 20, 7, 34, 196
    first_ym, last_ym = months[0][0], months[-1][0]
    for i, (ym, v) in enumerate(months):
        h = max(2, int(v / peak * 110))
        x = x0 + i * (bw + gap)
        cur = ym == date.today().strftime("%Y-%m")
        label = MONTHS[int(ym[5:7]) - 1]
        if ym in (first_ym, last_ym) or (i > 0 and ym[:4] != months[i-1][0][:4] and label == MONTHS[int(first_ym[5:7])-1]):
            label += "'" + ym[2:4]
        p.append(f'<rect x="{x}" y="{base-h}" width="{bw}" height="{h}" rx="2" fill="{t["accent"] if cur else t["bar"]}">'
                 f'<title>{v} contributions in {ym}</title></rect>')
        p.append(f'<text x="{x + bw/2}" y="{base + 12}" text-anchor="middle" fill="{t["muted"]}" font-family="{MONO}" font-size="8">{label}</text>')
        p.append(f'<text x="{x + bw/2}" y="{base - h - 4}" text-anchor="middle" fill="{t["text"]}" font-family="{MONO}" font-size="8">{v}</text>')
    p.append(f'<text x="30" y="{base + 28}" fill="{t["muted"]}" font-family="{MONO}" font-size="8">'
             f'FIRST BAR = PARTIAL {first_ym} (WINDOW START); RED BAR = CURRENT MONTH, STILL RUNNING</text>')

    # B: recent public repo activity
    rx = 430
    p.append(f'<text x="{rx}" y="66" fill="{t["muted"]}" font-family="{MONO}" font-size="9" letter-spacing="1">RECENT PUBLIC REPO ACTIVITY</text>')
    y = 86
    for r in repos[:6]:
        name = r["name"][:26]
        pushed = r["pushed_at"][:10]
        p.append(f'<text x="{rx}" y="{y}" fill="{t["text"]}" font-family="{MONO}" font-size="10">{name}</text>')
        p.append(f'<text x="{W-24}" y="{y}" text-anchor="end" fill="{t["muted"]}" font-family="{MONO}" font-size="9">{pushed}</text>')
        y += 18

    # C: language bytes
    ly = 220
    p.append(f'<text x="{rx}" y="{ly}" fill="{t["muted"]}" font-family="{MONO}" font-size="9" letter-spacing="1">LANGUAGES - BYTE SHARE, {len(repos)} PUBLIC REPOS</text>')
    total = sum(b for _, b in langs) or 1
    y = ly + 18
    for lang, b in langs[:4]:
        wpx = int(b / total * 200)
        p.append(f'<text x="{rx}" y="{y}" fill="{t["text"]}" font-family="{MONO}" font-size="9">{lang}</text>')
        p.append(f'<rect x="{rx + 110}" y="{y - 8}" width="{max(2,wpx)}" height="9" rx="2" fill="{t["mark"]}"/>')
        p.append(f'<text x="{rx + 116 + max(2,wpx)}" y="{y}" fill="{t["muted"]}" font-family="{MONO}" font-size="8">{round(100*b/total)}%</text>')
        y += 17
    p.append(f'<text x="{rx}" y="{y + 2}" fill="{t["muted"]}" font-family="{MONO}" font-size="7">SHARE OF CODE BYTES, NOT A SKILL RATING</text>')
    p.append('</svg>')
    return "\n".join(p)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="Jainabhi90")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    try:
        days = contribution_days(args.user)
        repos = public_repos(args.user)
        langs = language_bytes(args.user, repos)
    except SystemExit:
        raise
    except Exception as e:
        print(f"::warning::KICK.EXE telemetry fetch failed: {e}. "
              f"Kept last good assets; investigate the data source.", file=sys.stderr)
        sys.exit(1)
    months = monthly_velocity(days)
    for name, theme in THEMES.items():
        with open(f"{args.out_dir}/telemetry-{name}.svg", "w") as f:
            f.write(svg(theme, months, repos, langs, args.user))
    print(f"months={len(months)} public_repos={len(repos)} languages={len(langs)}; wrote telemetry-{{dark,light}}.svg")


if __name__ == "__main__":
    main()
