#!/usr/bin/env python3
"""
KICK.EXE - Featured mission cards generator
============================================
Renders the "featured missions" project cards shown directly under the hero.
Static content (project facts maintained here, reviewed by the owner); no
network calls. One dark Kick-styled SVG per project; the README wraps each
in its own link, because an SVG embedded via <img> cannot carry per-card links.

Card content rules:
  - private repos (NioLearn, EduOS) are described, never linked; NioLearn's
    card links to the live product instead
  - plans are labeled as plans, never as results

Usage: python3 generate_cards.py --out-dir ../assets/cards
"""
import argparse, os

CW, CH = 440, 258
C = {"bg": "#10151C", "border": "#1E2630", "text": "#F5F5F5", "muted": "#8B949E",
     "red": "#E5252A", "yellow": "#FFD338", "chip_bg": "#161B22", "chip_line": "#2A3440"}
MONO = "ui-monospace,Menlo,Consolas,monospace"

# (slug, name, status, status_color, description lines, tech chips, link)
PROJECTS = [
    ("niolearn", "NioLearn", "LIVE PRODUCT", C["red"],
     "Admissions platform for Indian students, live and taking users: timed assessments, Razorpay checkout. Co-founder & CTO.",
     ["Next.js", "Supabase", "Razorpay", "Turborepo"], "https://niolearn.com/"),
    ("eduos", "EduOS", "CASE STUDY", C["yellow"],
     "Multi-tenant K-12 school operating system. Modular monolith, strict tenant isolation with Postgres RLS.",
     ["Turborepo", "PostgreSQL", "RLS", "ADR-driven"], None),
    ("github-analyser", "GitHub Analyser", "SHIPPED", C["red"],
     "Turns any GitHub profile into charts and a score: languages, top repos, 12-month heatmap.",
     ["React", "Chart.js", "GraphQL", "Serverless"], "https://github.com/Jainabhi90/GitHub-Analyser"),
    ("fnatics", "Fnatics", "24H HACKATHON", C["yellow"],
     "AI-assisted DSA practice: topic mastery, streaks, live leaderboard. Built at Vedam's 24h hackathon, which I co-organized.",
     ["React", "Firebase", "Tailwind", "Recharts"], "https://github.com/Jainabhi90/Fnatics-project-"),
    ("insta-crm", "Insta-CRM", "PUBLIC REPO", C["red"],
     "Instagram CRM concept: multi-account management, automated DM workflows, lead tracking.",
     ["JavaScript", "OAuth 2.0", "Analytics"], "https://github.com/Jainabhi90/Insta-CRM"),
    ("arbdetector", "ArbDetector", "PUBLIC REPO", C["yellow"],
     "Matches equivalent markets across Kalshi and Polymarket; fee-adjusted arbitrage alerts.",
     ["JavaScript", "Dashboard", "Telegram"], "https://github.com/Jainabhi90/Arbitrage"),
    ("portfolio", "Portfolio", "PUBLIC REPO", C["red"],
     "This portfolio: abhirajjain.me, designed and built from scratch, deployed on Vercel.",
     ["Next.js", "TypeScript", "Tailwind", "Vercel"], "https://github.com/Jainabhi90/Abhiraj-portfolio"),
]


def wrap(text, width=52):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur.strip())
            cur = w + " "
        else:
            cur += w + " "
    lines.append(cur.strip())
    return lines[:4]


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def card(slug, name, status, status_color, desc, chips, link):
    name, status, desc = esc(name), esc(status), esc(desc)
    chips = [esc(c) for c in chips]
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CW} {CH}" width="{CW}" height="{CH}" role="img" aria-label="{name} project card: {desc}">']
    p.append(f'<title>{name} - {status.lower()}</title>')
    p.append(f'<rect width="{CW}" height="{CH}" fill="{C["bg"]}" rx="12"/>')
    p.append(f'<rect x="0.75" y="0.75" width="{CW-1.5}" height="{CH-1.5}" fill="none" stroke="{C["border"]}" stroke-width="1.5" rx="11.25"/>')
    p.append(f'<rect x="0" y="0" width="84" height="6" fill="{C["red"]}" rx="3"/>')  # kick stripe
    # status badge
    bw = 10 + len(status) * 9.2
    p.append(f'<rect x="{CW-14-bw:.0f}" y="18" width="{bw:.0f}" height="22" rx="11" fill="none" stroke="{status_color}" stroke-width="1.2"/>')
    p.append(f'<text x="{CW-14-bw/2:.0f}" y="33.5" text-anchor="middle" fill="{status_color}" font-family="{MONO}" font-size="11.5" letter-spacing="1">{status}</text>')
    p.append(f'<text x="18" y="46" fill="{C["text"]}" font-family="{MONO}" font-size="22" font-weight="700">{name}</text>')
    y = 82
    for line in wrap(desc):
        p.append(f'<text x="18" y="{y}" fill="{C["muted"]}" font-family="{MONO}" font-size="13.5">{line}</text>')
        y += 22
    # tech chips; leave the bottom-right corner clear for the link / privacy tag
    x = 18
    x_max = CW - 84 if link else CW - 112
    for chip in chips[:4]:
        wpx = 12 + len(chip) * 7.8
        if x + wpx > x_max:
            break
        p.append(f'<rect x="{x:.0f}" y="{CH-38}" width="{wpx:.0f}" height="22" rx="11" fill="{C["chip_bg"]}" stroke="{C["chip_line"]}" stroke-width="1"/>')
        p.append(f'<text x="{x+wpx/2:.0f}" y="{CH-22.5}" text-anchor="middle" fill="{C["text"]}" font-family="{MONO}" font-size="11">{chip}</text>')
        x += wpx + 8
    if link:
        p.append(f'<text x="{CW-16}" y="{CH-18}" text-anchor="end" fill="{C["yellow"]}" font-family="{MONO}" font-size="13">OPEN -&gt;</text>')
    else:
        p.append(f'<text x="{CW-16}" y="{CH-18}" text-anchor="end" fill="{C["muted"]}" font-family="{MONO}" font-size="11">PRIVATE REPO</text>')
    p.append('</svg>')
    return "\n".join(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    for proj in PROJECTS:
        with open(f"{args.out_dir}/card-{proj[0]}.svg", "w") as f:
            f.write(card(*proj))
    print(f"wrote {len(PROJECTS)} cards to {args.out_dir}")


if __name__ == "__main__":
    main()
