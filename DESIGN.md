# Design preferences

Design system for Pitch Notes.

## Philosophy

- CSS custom properties (root variables) for everything — no hardcoded colors scattered through stylesheets
- Dark-only. Stadium-navy background, no light mode toggle — this is a fixed design decision, not a default awaiting an override.
- No real team crests or logos anywhere — they're trademarked. Use flat color chips (each club's actual kit color) with 2–3 letter initials instead.
- Status colors (green/orange/red) are semantic and fixed. Don't reassign them.

## Fonts

Three fonts, each with a job, from Google Fonts (allowed in this project):

- Big Shoulders Display — headlines and scoreboard numerals
- Source Serif 4 — editorial body copy
- IBM Plex Mono — data, labels, tags

## Color palette — Stadium Navy

Arsenal red accent, gold trim, warm off-white ink on a dark navy ground.

- Accent is Arsenal red. Gold is trim and highlights only, not a second accent.
- Status colors are semantic and fixed: green for good, orange for warning (orange, not yellow, so it stays distinct on a dashboard), red for danger. Each has a matching background and text shade for status cells.
- Surfaces run dark navy from the page ground up through cards and subtle panels; text runs warm off-white down through secondary and muted.

## Dashboard conventions

Stat cards pair a small muted label with a larger primary value, in tabular numerals so columns of figures line up.

Status cells use the semantic color pair: `--color-{status}-bg` for background, `--color-{status}-text` for text and label. Never mix status colors across palettes.

## Asset system

The app uses shared CSS and JS as needed. Pages pull their styling from `assets/css` and their behavior from `assets/js` rather than inlining it. The specific files in those folders can change, and nothing here pins them.
