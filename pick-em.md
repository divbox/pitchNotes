# Pick 'Em inventory

What exists as of 2026-09-20, read from the code rather than from notes.
This is an inventory, not a design. Everything here is prototype unless the
"Environment facts" section says otherwise, and none of it constrains what we
build next.

An earlier version of this file described Pick 'Em as an unstarted phase 2
with a standings modal. That came from `NEXT-SESSION.md` and was wrong. If
this file and the code ever disagree again, the code wins.

## Status: live, by hand, and stale

`https://divbox.ai/premier-league/pickem/pick-em.html` returns 200. It was
deployed by hand to validate the Apache CGI setup and to show a friend, who
liked it. It has never gone through `publish.py`/`deploy.py`: nothing stages
`pickem/` or `cgi-bin/` into `dist/`, and `dist/` holds only `index.html`,
`assets/` and `archive/`. So the live copy and the repo copy can drift with
nothing to catch it, and the page currently shows Week 4 and 12-14 September
fixtures.

`/premier-league/cgi-bin/submit-picks.py` returns 500 on a GET. That's the
script behaving correctly, not a fault: `run_cgi()` reads a `CONTENT_LENGTH`
of 0, `json.loads("")` raises, and the catch-all returns 500. A 404 would
have meant CGI wasn't wired at all. Whether the web user can actually write
to the picks directory is untested.

## What exists

`pickem/pick-em.html` (225 lines, hand-written, not generated). A standalone
page, not part of any edition. Masthead reads "Week 4", "RESULTS.", and 10
September 2026. Four user rows with photos from `images/` and hardcoded W-L
records. Ten fixture cards, each with two radio buttons sharing a `name` like
`fx-mun-mci`, a kit-color chip, and a hardcoded decimal price, plus a draw
price that isn't selectable. `data-week="4"` on the grid. Links the shared
stylesheet and `pickem.js` by absolute path. No favicon link, unlike the
edition template.

`assets/js/pickem.js` (111 lines). Identity is a name in `localStorage` under
`pickem_user`, chosen by clicking a row. Lock-in requires all ten fixtures
picked, then POSTs `{user, week, picks}` to the CGI endpoint. `collectPicks()`
reads each checked radio and records the team's display name as the pick.
`locked` is a plain JS variable, so a reload clears it.

`scripts/submit_picks.py` (78 lines). Validates and writes one file per user
per matchday to `data/picks/W<week>/<user>.json`, with a `locked_at` UTC
timestamp. Four users hardcoded in a `USERS` set. Runs as Apache CGI in
production and is imported directly by the local test server. Its own
docstring is explicit that there's no auth and a resubmit just overwrites,
which is fine for friends on the honor system.

`scripts/local_pickem_server.py` (69 lines). Serves the project root under
`/premier-league/` and handles the POST the same way Apache does, so the flow
can be tested end to end locally. Dev tool only, never runs on the host.

Styling lives in `assets/css/styles.css:148-181`.

## What's faked

The W-L records on the page are invented. Nothing reads `data/picks/` back,
nothing compares a pick to a result, and no score is ever computed. The odds
prices are baked into the HTML by hand.

## Paused work in the stash

`stash@{0}` (`pickem-wip`) extends `fetch_odds.py` with `build_matchday()`,
writing a `matchday.json` of the full 10-fixture slate with averaged odds
from the same API call the newsletter odds already make. That's close to the
feed a generated picks page would need.

It also carries a finding worth keeping whatever we decide: taking the
soonest 10 fixtures breaks once a matchday is partway through. Confirmed
live, it returned 3 leftovers from the ending round plus 7 from the next and
showed three clubs twice. The stashed code clusters fixtures by gap between
kickoffs instead. The stash also modifies `NEXT-SESSION.md`, which no longer
exists, so popping it needs that resolved.

## Environment facts (fixed, not up for redesign)

- The app lives at `/premier-league/` under the shared divbox.ai vhost, not
  at a domain root. Asset links are site-absolute because of this and because
  archived editions sit a directory deeper (DESIGN.md).
- Apache on the host runs CGI at `/premier-league/cgi-bin/`.
- `deploy.py` rsyncs `dist/` and nothing else, so anything the site needs has
  to be staged into `dist/` first.
- Host-side files outside `dist/` (the odds cron and its own separate config)
  are updated by hand. There's no automated path for them.
- DESIGN.md's rules hold: dark-only, no crests or logos, shared stylesheet
  rather than inlined CSS.

## Prototype choices (all open)

Radio buttons per fixture. `localStorage` for identity with no auth. Four
users hardcoded in Python. One JSON file per user per matchday. Locking that
only exists in the browser. `week` numbering, while the rest of the project
moved to matchday. A standalone page rather than a section of the edition.
Odds shown on the picks page at all. The draw being displayed but unpickable.

## Known debt

- `.fixture-card` and `.fixture-time` are each defined for two different
  things: Next Up cards on the dashboard and fixture cards on the picks page.
  `.fixture-time` is declared twice (`styles.css:133` and `:166`) with
  different colors, so the picks-page rule silently wins on the dashboard.
- `.pickem-link` (`styles.css:68-69`) styles a masthead link that no longer
  exists in `build.py`'s template or any edition. Orphaned.
- `submit_picks.py` and `local_pickem_server.py` have no `--demo` self-check.
  Every other script in `scripts/` does.
- `submit_picks.py` derives its picks directory from its own location's
  grandparent. On the host that resolves inside the web root, which would
  make submitted picks publicly readable. Unverified, worth checking before
  this goes any further.
- Pick 'Em is documented nowhere: not in CLAUDE.md, README.md, DESIGN.md, or
  either skill. Only `data/picks/` in `.gitignore` hints at it.
