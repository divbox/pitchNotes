# Next session

## What got done
- Cleaned up the project layout and got it into git: pipeline scripts
  moved into `scripts/`, the run log into `logs/`, added `.gitignore`
  (`.env`, `__pycache__/`, `dist/`, `logs/*.log`, `.claude/settings.local.json`,
  `.DS_Store`) and a `README.md`. Verified `run_weekly.py --demo` and
  `publish.py`'s self-check still pass after the move. Made the initial
  commit (`cd40c03`).
- CLAUDE.md updated to match the new `scripts/`/`logs/` layout, along
  with both `.claude/skills/pitch-notes-*/SKILL.md` files.
- Started the "Pick Em" feature, phase 1 only: a link in the masthead
  and a modal that opens over it. Built directly in `weeklies/pitch-notes-W3.html`
  (not yet ported into `build.py` — see below) so we could iterate on
  design fast.
  - "Pick Em" link sits top-right of the masthead kicker line, in
    Arsenal red.
  - Modal shows a static "Standings" table: photo, name, a red vertical
    divider, and an example win/loss figure (e.g. "7W – 3L"),
    hardcoded for the four people in `images/` (`divs.jpg`,
    `cheeky.jpg`, `ll.jpg`, `ldog.jpg`).
  - Went through several rounds of sizing: photos ended around 200x140,
    name column fixed at 100px so the divider lines up across rows
    regardless of name length, win/loss text enlarged, red, and
    centered (using tabular-nums so 1- vs 2-digit counts don't jitter
    the center point).
  - Known open issue: with photos this large, 4 rows can require
    scrolling inside the modal. Divbox's plan is to ship this as-is and
    get real feedback rather than keep guessing at sizing.

## Key decisions and why
- Images are referenced as plain files in `images/` (`../images/divs.jpg`
  from `weeklies/`), not base64-embedded. This breaks DESIGN.md's
  "self-contained single file" rule on purpose — Divbox said to ignore
  it here.
- JSON state files (`manifest.json`, `odds.json`) stay at the project
  root rather than moving into a `data/` folder — kept simple since
  scripts already read/write them with plain relative paths.
- `images/` is tracked in git (Divbox's call) even though nothing in
  the pipeline references it yet outside this modal.

## Open questions / not yet done (Phase 2 — picks + storage)
Explicitly deferred until phase 1's design is settled. Divbox's rough
ideas going in, to revisit:
- Display for 10 fixtures/week without the page getting unwieldy — a
  compact per-fixture home/away toggle was suggested as an alternative
  to rows of radio buttons.
- How a user is selected to enter picks (name dropdown/tabs?).
- Storage: a small script on the Linode host, written to respond to an
  AJAX call from the page — likely a flat JSON file in the style of
  `odds.json`, not a database.
- Still unresolved: pick locking at kickoff, who/how results get
  scored (manual vs. pulled from football-data.org), any lightweight
  auth so one person can't overwrite another's picks.

## Also not yet done
- The Pick Em link + modal only exist in `weeklies/pitch-notes-W3.html`
  right now. Once the design is settled, it needs porting into
  `build.py`'s HTML template (with the standings table becoming
  data-driven) so it survives the next weekly rebuild.

## Files created or modified this session
`scripts/` (new — moved `build.py`, `content.py`, `deploy.py`,
`fetch_data.py`, `fetch_odds.py`, `publish.py`, `run_weekly.py` into
it), `logs/pitch-notes.log` (moved), `.gitignore` (new), `README.md`
(new), `CLAUDE.md` (Pipeline section), both
`.claude/skills/pitch-notes-*/SKILL.md`, `weeklies/pitch-notes-W3.html`
(Pick Em link + modal), `images/` (tracked in git).
