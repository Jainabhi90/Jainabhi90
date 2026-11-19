#!/usr/bin/env python3
"""
KICK.EXE - "The season so far" timeline generator
==================================================
Static, content-maintained timeline SVG (no network). Milestones are reviewed
by the owner; the last node is explicitly labeled as plans, not results.

Usage: python3 generate_timeline.py --out-dir assets/graphs
"""
import argparse

W, H = 730, 218
THEMES = {
    "dark":  {"bg": "#0D1117", "panel": "#10151C", "text": "#F5F5F5", "muted": "#8B949E",
              "line": "#1E2630", "accent": "#E5252A", "mark": "#FFD338"},
    "light": {"bg": "#F5F5F5", "panel": "#FFFFFF", "text": "#0D1117", "muted": "#5b6470",
              "line": "#e3ddd2", "accent": "#E5252A", "mark": "#B8860B"},
}
MONO = "ui-monospace,Menlo,Consolas,monospace"

NODES = [
    ("2025", "FIRST LAP", "#E5252A", [
        "Started B.Tech CSE (AI & ML)",
        "at Vedam, Pune",
        "Joined GitHub, first repos shipped"]),
    ("2026", "FULL THROTTLE", "#E5252A", [
        "NioLearn live - co-founder & CTO",
        "EduOS multi-tenant school OS",
        "Fnatics - 24h hackathon build",
        "Wrote NOESIS 2.0 offline marketing strategy"]),
    ("NEXT", "PLANS, NOT RESULTS", "#FFD338", [
        "First paid NioLearn cohort",
        "NOESIS 2.0 fest - Jan 29-30",
        "Keep shipping in public"]),
]


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(t):
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
         f'aria-label="Timeline: 2025 first lap, 2026 full throttle, and what is planned next.">']
    p.append('<title>KICK.EXE - the season so far</title>')
    p.append(f'<rect width="{W}" height="{H}" fill="{t["bg"]}" rx="10"/>')
    p.append(f'<rect x="10" y="10" width="{W-20}" height="{H-20}" fill="none" stroke="{t["line"]}" stroke-width="1.5" rx="8"/>')
    p.append(f'<rect x="10" y="10" width="52" height="4" fill="{t["accent"]}" rx="2"/>')
    p.append(f'<text x="30" y="40" fill="{t["text"]}" font-family="{MONO}" font-size="15" font-weight="700" letter-spacing="2">THE SEASON SO FAR</text>')
    rail_y = 66
    p.append(f'<line x1="40" y1="{rail_y}" x2="{W-40}" y2="{rail_y}" stroke="{t["accent"]}" stroke-width="3" stroke-linecap="round"/>')
    seg = (W - 80) / len(NODES)
    for i, (year, tag, color, lines) in enumerate(NODES):
        cx = 40 + seg * i + seg / 2
        dashed = ' stroke-dasharray="4 4"' if year == "NEXT" else ""
        p.append(f'<circle cx="{cx:.0f}" cy="{rail_y}" r="7" fill="{t["bg"]}" stroke="{color}" stroke-width="2.5"{dashed}/>')
        p.append(f'<text x="{cx:.0f}" y="{rail_y+30}" text-anchor="middle" fill="{color}" font-family="{MONO}" font-size="17" font-weight="700">{year}</text>')
        bw = 8 + len(tag) * 6.4
        p.append(f'<rect x="{cx-bw/2:.0f}" y="{rail_y+40}" width="{bw:.0f}" height="15" rx="7.5" fill="none" stroke="{color}" stroke-width="1"/>')
        p.append(f'<text x="{cx:.0f}" y="{rail_y+51}" text-anchor="middle" fill="{color}" font-family="{MONO}" font-size="7.5" letter-spacing="1">{tag}</text>')
        y = rail_y + 76
        for line in lines:
            p.append(f'<text x="{cx:.0f}" y="{y}" text-anchor="middle" fill="{t["muted"]}" font-family="{MONO}" font-size="9.5">{esc(line)}</text>')
            y += 15
    p.append('</svg>')
    return "\n".join(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    for name, theme in THEMES.items():
        with open(f"{args.out_dir}/timeline-{name}.svg", "w") as f:
            f.write(svg(theme))
    print("wrote timeline-{dark,light}.svg")


if __name__ == "__main__":
    main()
