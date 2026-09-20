# Pick 'Em

Source of truth for the Pick 'Em feature. Parked as of 2026-09-20, to be
picked up after the main dashboard work. Phase 1 (link + modal) exists;
phase 2 (actual picks and storage) is unstarted.

## Where the code lives

`pickem/`, `assets/js/pickem.js`, `scripts/local_pickem_server.py`,
`scripts/submit_picks.py` are all committed but the feature isn't finished.
`git stash list` also has one entry, `pickem-wip`, holding paused Pick 'Em
and odds work from before 2026-09-16.

## Phase 1: what's built

A "Pick Em" link in the masthead that opens a modal over the page.

- The link sits top-right of the masthead kicker line, in Arsenal red.
- The modal shows a static "Standings" table: photo, name, a red vertical
  divider, and an example win/loss figure (e.g. "7W - 3L"), hardcoded for
  the four people in `images/` (`divs.jpg`, `cheeky.jpg`, `ll.jpg`,
  `ldog.jpg`).
- Sizing went through several rounds: photos ended around 200x140, the name
  column fixed at 100px so the divider lines up across rows regardless of
  name length, win/loss text enlarged, red, and centered (tabular-nums so 1-
  vs 2-digit counts don't shift the center point).

Known open issue: with photos this size, four rows can require scrolling
inside the modal. The plan is to ship as-is and get real feedback rather
than keep guessing at sizing.

## Not yet ported into the build

The link and modal were built directly into the old
`weeklies/pitch-notes-W3.html` so the design could be iterated on fast.
They've never been ported into `build.py`'s HTML template, so they don't
survive a rebuild. Once the design is settled, that port needs doing, with
the standings table becoming data-driven. Note the file and directory have
both since been renamed (`weeklies/` is now `editions/`), so the original
prototype lives in git history rather than at that path.

## Phase 2: open questions

Deferred until phase 1's design is settled. Rough ideas going in:

- How to display 10 fixtures a week without the page getting unwieldy. A
  compact per-fixture home/away toggle was suggested instead of rows of
  radio buttons.
- How a user gets selected to enter picks (name dropdown, tabs?).
- Storage: a small script on the Linode host responding to an AJAX call
  from the page, most likely a flat JSON file in the style of `odds.json`,
  not a database.

Still unresolved: pick locking at kickoff, who scores results and how
(manual vs. pulled from football-data.org), and any lightweight auth so one
person can't overwrite another's picks.

## Decisions already made

- Images are referenced as plain files in `images/`, not base64-embedded.
  This breaks DESIGN.md's "self-contained single file" rule on purpose;
  Divbox said to ignore it here.
- `images/` is tracked in git (Divbox's call) even though nothing in the
  pipeline references it yet outside this modal.
