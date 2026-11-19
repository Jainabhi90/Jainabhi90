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
