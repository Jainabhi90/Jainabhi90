# Maintenance

- Regenerate locally: `python3 scripts/generate_stunt_track.py --user Jainabhi90 --out-dir assets/graphs`
- Offline re-render from the cached snapshot: add `--from-json data/contributions.json`
- Static (no motion) variants are written alongside the animated ones as
  `stunt-track-<theme>-static.svg`; use them for reduced-motion contexts.
- Rider art: the art owner replaces ONLY the `<g id="rider">` group in the
  generated SVG (marked RIDER-ART). Geometry, path, and timing are
  data-driven; do not edit them by hand. Better: edit the `rider` template
  in the generator so workflow regeneration keeps the art.
- Dark/light: reference the pair with <picture> + prefers-color-scheme
  srcset; never embed SVGs as base64 data URIs (they do not animate in
  Firefox on GitHub; see github/markup#1864).
- If the public page layout changes, the parser fails loudly (no cells or
  non-consecutive dates) instead of emitting wrong data.
- Failure semantics: a fetch/network failure writes nothing (last good
  assets stay live) AND exits nonzero with a ::warning:: annotation, so the
  workflow run is visibly marked failed instead of silently green. A page
  layout change fails the same way before any write.
- Velocity chart window: shows every month the rolling year touches,
  including both partial ends; bars sum to the same total as the calendar.

## 2026-11-19 revision (visual pass 2)

- Hero: skater motion path confined to the red rail (ends x~786, clear of the
  poster at x=918) with fade-in/out at the loop ends; poster art unchanged.
- New generators: `generate_stats.py` (pit-wall numbers, streaks, language
  byte share, monthly velocity; public data only), `generate_cards.py`
  (featured mission cards, static content, no network), `generate_timeline.py`
  (season timeline, static; last node labeled plans-not-results).
- Cards are dark-styled on both color schemes by design.
- `generate_telemetry.py` and its SVGs are superseded by the stats deck and
  no longer referenced in the README; kept in repo.
- Daily workflow now also regenerates stats, cards and timeline.
- GitHub's native pinned-repos grid cannot be repositioned by the README; the
  clickable mission cards directly under the hero carry that role.
- Stats generator: fails loudly if any repo language fetch fails (a partial
  aggregate would commit a wrong language bar) and supports offline re-render
  via --from-json (assets/data/contributions.json + assets/data/stats-snapshot.json).
- Cards/timeline/stats generators XML-escape all text (& < >). Raw "&" is
  well-formed in no XML context: SVGs served as images must parse as strict XML.

## 2026-11-19 revision (visual pass 3)

- Owner asked for larger fonts, boxes and graphs throughout: cards 320x188 ->
  440x258 (README display width 290 -> 430, two per row), stunt-track cells
  12.4 -> 13.2px with a taller lane and larger labels, stats panel 348 -> 410px
  tall with larger tiles and charts, timeline 244 -> 300px with larger nodes.
- New 7th card: Portfolio (abhirajjain.me), linking the public
  Abhiraj-portfolio repo; every public project card is link-wrapped in the
  README. EduOS stays unlinked (private repo, case-study card only).
- Pinned-repos note still applies: the native pinned/popular section cannot be
  removed by the README; pins are curated to match the featured missions.

## 2026-11-19 revision (visual pass 4)

- Owner asked for still bigger graphs and details, smaller tech logos in a
  floating hexagon section (honeycomb reference), and a 3D activity graph
  (profile-3d-contrib style reference).
- Stunt track: grid now renders the last 40 weeks at 18px cells (was 53 at
  13.2px) so the graph and its labels read ~35% larger on the profile;
  header/stats/month fonts enlarged; full-year totals kept in the stats
  strip and header ("last 40 weeks shown" is labeled on the asset).
- New `generate_activity_3d.py`: isometric 3D bar city from the cached
  contributions.json (run after the stunt track, which refreshes that
  file). New `generate_tech_deck.py`: offline, icon art embedded in the
  generator; SMIL float animation survives camo.
- Tech Deck section: skillicons.dev image rows replaced by the generated
  floating hexagon deck (dark/light pair).
- Stats panel: bigger tiles/numbers/legend; velocity chart shows the last
  10 months with taller bars. Timeline: bigger nodes and text.
- Workflow now also regenerates activity-3d and tech-deck assets.
