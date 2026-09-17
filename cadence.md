# Cadence

Working notes for making the build/publish pipeline cadence-agnostic. The
site used to run weekly. Cadence is now TBD, and the goal is code that
doesn't care how often it runs. This doc drives the code changes; once
those land, CLAUDE.md and README get updated to match. Not a permanent doc.

## Decision: date-based file key (option C)

An edition is identified by its build date, not a week number.

- Files become `weeklies/pitch-notes-YYYY-MM-DD.html`.
- `manifest.json` and `publish.py` key off that date instead of `W<N>`.

Why: a date is unique and meaningful at any cadence, needs no hand-maintained
counter, and sorts chronologically on its own. It also splits two jobs that
`WEEK_NUMBER` currently does at once: naming the file, and labelling the
edition for the reader. This decision only covers the file/manifest key. The
reader-facing label is a separate decision (see Open items).

## What's cadence-coupled today

The code is not hard-coded to *run* weekly. Nothing schedules it, checks for
Monday, or blocks a different interval. The coupling is in how an edition is
named and in a bit of hard-coded copy.

1. Edition identity is a week number (the real coupling).
   - `content.py` — `WEEK_NUMBER`, hand-maintained; comment says "this runs
     Monday nights."
   - `build.py` — feeds `WEEK_NUMBER` into the `<title>`/masthead "Week {N}"
     label and the output filename `weeklies/pitch-notes-W{N}.html`.
   - `publish.py` — `latest_week()` parses `W(\d+)` and promotes the max;
     `manifest.json` stores `current_week`/`current_file`.
   - The promote-newest / archive-previous logic only needs a monotonic key.
     It works unchanged with a date key.

2. Hard-coded weekly copy in the HTML.
   - `build.py` masthead sub-line: "recap of the weekend just played" (assumes
     a weekend just happened).
   - `build.py` movers note: "week-over-week movement"; CLAUDE.md's Early
     Risers section is defined as week-over-week. With irregular cadence this
     becomes edition-over-edition. Low urgency (form-only today).

3. Cosmetic naming only.
   - `run_weekly.py` (filename + "Weekly run complete"), `build.py`/
     `content.py` docstrings, `WEEKLIES_DIR = "weeklies"`.

Not cadence-aware, leave alone: `deploy.py`, and `fetch_data.py` (it already
reads `currentMatchday` from the API, a football concept independent of how
often we publish).

## Code changes to implement C

Core (the file/manifest key):

- `build.py` — build the output filename from `content.py`'s `BUILD_DATE`
  (`pitch-notes-{BUILD_DATE}.html`) instead of `WEEK_NUMBER`.
- `publish.py` — find the newest edition by date (ISO date filenames sort
  chronologically, so max-by-filename still works, or parse the date out);
  archive the previous one under its date filename; store the date (and file)
  in `manifest.json` instead of `current_week`.
- `manifest.json` — `current_week` → the build date (plus `current_file`).
- `content.py` — drop the "runs Monday nights" cadence assumption from the
  `WEEK_NUMBER` comment. Keep `WEEK_NUMBER` for now only as the masthead label
  input; it stops being the file key here and gets resolved in the label work.

Left as-is for now (belongs to the label decision, not this one):

- `build.py` "Week {N}" in `<title>` and masthead kicker — still driven by
  `WEEK_NUMBER` until the label source is chosen.

Cosmetic renames (optional, do with the docs cleanup, not required for C):

- `run_weekly.py` name + "Weekly run complete" string, docstrings,
  `WEEKLIES_DIR = "weeklies"`, and the `pitch-notes-weekly` skill name.

## Open items (later, not this pass)

- Reader-facing label: what number the masthead shows once it isn't a week.
  Two candidate sources for "current matchday," to choose from when we do the
  label work:
  - football-data.org's `currentMatchday`, already fetched in `fetch_data.py`
    (live, but an opaque single number).
  - The openfootball season schedule, resolved by comparing the run date
    against the fixture list (inspectable, static file, covers more than the
    single current number). Premier League file:
    https://github.com/openfootball/england/blob/master/2026-27/1-premierleague.txt
    Reportedly the same repo carries Champions League too; format and CL
    coverage to be evaluated during the label work. It updates through the
    season, so if we go this way we need a refresh mechanism — candidate:
    pull it as a submodule (daily, or at run time). To decide with the source.
  - `repos.txt` collects further candidate schedule repos to weigh against
    the API (or some combination of the two) when we pick.
- Early Risers movers: "week-over-week" becomes "edition-over-edition" once
  cadence is irregular.
- Docs cleanup: fold the settled cadence model into CLAUDE.md and README, and
  strip the remaining "weekly" language there.
- Minor: two editions built on the same date would collide on the date key.
  Unlikely at any real cadence; note only.
