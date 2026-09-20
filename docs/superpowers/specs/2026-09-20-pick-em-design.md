# Pick 'Em design

Date: 2026-09-20
Status: approved in brainstorming, not yet planned or built

Replaces the Pick 'Em prototype described in `pick-em.md`. That prototype is
deployed by hand to the live host and works end to end, but nothing in it is
load-bearing here: where this design and the existing code disagree, this
design wins. `pick-em.md` stays as the record of what's there now.

## What we're building

A Pick 'Em game for four friends, running alongside the Pitch Notes
dashboard. Each Premier League matchday, each player picks a winner for all
ten fixtures before the deadline. A correct pick scores one point. A wrong
pick scores nothing, and so does a draw. A season table ranks the four
players by total points, and ties are displayed as ties.

## Decisions taken, with reasons

**Split deployment.** The page, its styling and its JavaScript ship through
the existing pipeline into `dist/`. The data it displays is fetched
client-side from JSON files that host-side cron jobs refresh. This is the
pattern the odds card already uses, and it means the deployable parts stay
under `publish.py`/`deploy.py` while the time-sensitive parts move at their
own cadence.

**Automatic scoring that never invents a result.** A host cron scores each
matchday. Only matches football-data.org reports as `FINISHED` are scored.
Anything else is left unscored and shows as pending on the page, so a
postponed fixture never quietly counts as a miss for everyone.

**One deadline per matchday, enforced server-side.** `submit_picks.py`
refuses any submission after the deadline. Resubmitting before the deadline
is allowed and overwrites, so people can change their minds all week. The
deadline is FPL's own gameweek deadline, which is set before the first
kickoff of the round and which `fetch_fpl.py` already returns and currently
discards.

**No auth.** Four friends on the honor system, as now. The deadline removes
the only cheat that distorts the table, which is submitting once results are
known. The remaining risk is impersonation between friends in a game with no
stakes, and that is a social problem, not a software one.

**Picks move outside the web root.** Unrelated to auth. `submit_picks.py`
currently derives its picks directory from its own location, which on the
host resolves inside the web root and would let anyone read everyone's picks
at a guessable URL before the deadline. That defeats the game with no bad
intent required.

**Two-way picks.** Home or away. The draw price is displayed as information
but is not selectable, and a drawn match scores nothing for anyone. Points
are flat: no weighting by odds. Roughly a quarter of Premier League matches
draw, so a meaningful share of fixtures will score nothing for anyone. That
is understood and accepted.

**Current matchday only, with a running season total.** Past matchdays
persist as files on the host but are not browsable. The season total in the
standings rows is the accumulating part.

**Reached by a link from the edition masthead.** A standalone page rather
than a section inside an edition: an edition is a dated snapshot that gets
archived, and embedding a live, deadline-bound form in one would leave every
archived edition carrying a dead picks form. `.pickem-link` is already in the
stylesheet for exactly this and is currently orphaned.

## Data sources

Fixtures and results both come from football-data.org, competition `PL`,
via `/competitions/PL/matches?matchday=N`. Verified on 2026-09-20 that the
free tier honours the `matchday` filter on this endpoint, returning exactly
that round's ten matches. This differs from `/competitions/PL/standings`,
where the same filter is silently ignored.

Using one source for both fixtures and results means a stable
football-data.org match id flows through the whole system: it identifies a
fixture on the page, it is what a pick refers to, and it is what the scoring
job looks up. No component ever matches a team name to score a pick.

FPL supplies the current gameweek number and the deadline, which it is
authoritative on.

FPL's `/api/fixtures/` was evaluated as an alternative for fixtures and
results and rejected on one specific ground: it splits completion across
`finished` and `finished_provisional`, flipping `finished` only once bonus
points are confirmed, which can lag a day. At the time of evaluation nine
fixtures were provisional-only. football-data.org's single `FINISHED` status
has no such ambiguity.

football-data.org's `matchday` and FPL's `event` could disagree for a
rescheduled fixture, putting a match in one bucket for the deadline and
another for the slate. Log the mismatch and continue, matching how `build.py`
already handles a matchday disagreement.

The Odds API remains the only source of prices. It knows nothing of
football-data.org's ids and uses full club names, so joining prices onto
fixtures needs a 20-entry club-name-to-TLA table, refreshed when clubs are
promoted or relegated. This join is decoration only: if it fails or a price
is missing, the fixture still renders and the pick still scores.

## Components

Three host-side cron jobs, one page, one endpoint.

**Fixtures job.** Asks football-data.org for the current matchday's ten
matches and writes `feeds/fixtures.json`.

**Odds job.** Today's `fetch_odds.py`, extended to join prices onto those
fixtures by TLA and write `feeds/pickem-odds.json`. Continues to write
`feeds/odds.json` for the dashboard as it does now.

**Scoring job.** Reads every stored pick file plus finished matches, and
writes `feeds/pickem-standings.json`. Recomputes from scratch each run rather
than accumulating, so it is idempotent and an upstream correction self-heals.

**The page.** `build.py` grows a Pick 'Em template and writes
`pickem/index.html` the way it writes an edition. `publish.py` stages it into
`dist/` along with `cgi-bin/`. The page is a shell: fixtures, prices and
standings are all fetched client-side, so it stays current between builds.

**The endpoint.** `submit_picks.py`, keeping its current shape, with three
changes: it enforces the deadline read from `feeds/fixtures.json`, it stores
picks as a match id plus `HOME`/`AWAY` rather than a scraped display name,
and its picks directory moves outside the web root.

## File layout

Published feeds live in one directory in the web root, reached by absolute
path: `/premier-league/feeds/`. Absolute rather than relative so they resolve
identically from the live index and from the archive, which matches
DESIGN.md's rule for assets. `odds.json` moves here too, which as a side
effect fixes the archive's odds card: archived editions currently fetch a
relative `odds.json` that resolves under `archive/` and 404s, so they have
always shown "Odds unavailable right now."

The deployed feeds directory is deliberately not called `data/`. The repo
already has a `data/` holding local pipeline state (`manifest.json`,
`standings-history.json`) that must never ship, and two directories with the
same name and opposite rules about what belongs in them is an easy mistake to
make in `publish.py`.

Picks are stored outside the web root, one file per player per matchday.

`feeds/fixtures.json` carries the matchday number, its deadline, when it was
generated, and the ten matches: football-data id, kickoff, both TLAs, both
display names, status.

`feeds/pickem-odds.json` is keyed by match id, with home, draw and away
prices. Separate from `odds.json` so a failed odds run costs prices on the
picks page and nothing else.

`feeds/pickem-standings.json` carries, per player, a season total and a
per-matchday breakdown, plus a list of match ids it deliberately did not
score.

A pick record is `{user, matchday, picks: [{match, side}], locked_at}`.
Directory naming moves from the prototype's `W4` to the matchday, matching
the rest of the project. Nothing has been scored yet, so there is no
migration.

## Page states

Four, explicitly, where the prototype really has one.

Before the deadline, fixtures are pickable and resubmission is unlimited.
After locking in but before the deadline, the card shows locked with a way
back. After the deadline but before results, picks show read-only and the
page says it is waiting on results. Once scored, each pick shows right or
wrong, the matchday total appears, and the standings rows show real season
points rather than the prototype's invented W-L figures.

## Failure behaviour

Every job writes to a temp file and renames into place. The page and the
endpoint both read these files, and a half-written file read mid-write
presents as a bug somewhere else entirely.

If the fixtures job fails, the previous file stays, which is the dangerous
case: a stale file would show a finished matchday as pickable. The page
treats a passed deadline with no newer file as "picks are closed, waiting on
the next matchday" rather than rendering a form. A missing file means the
page says so and offers nothing to click.

If the odds job fails, prices disappear and picking continues. A match id
absent from the odds file renders without a price rather than with a guess.

If the scoring job fails, the previous standings stay up, stamped with when
they were last updated, so a stale table is visibly stale rather than quietly
wrong.

The endpoint fails closed. If `feeds/fixtures.json` is missing or unreadable,
a submission is rejected rather than accepted without a deadline check. Past
the deadline, rejected. A match id outside the current matchday, rejected.
Accepting an unverifiable pick is the one failure that corrupts the game.

One prototype bug this design must not inherit: `pickem.js` sets `locked` and
disables the inputs before the POST resolves, and leaves them locked if it
fails, telling the player their picks are in when nothing was saved. Nothing
locks until the server confirms the picks were stored.

## CSS

The picks page's classes get namespaced; `.fixture-card` and `.fixture-time`
keep meaning Next Up on the dashboard. The reason is the archive: every past
edition links the shared stylesheet, so changing what `.fixture-*` means
would restyle pages that exist as a record of what was published. The
duplicate `.fixture-time` declaration at `styles.css:166` goes, and
`.pickem-link` stops being orphaned once the masthead link exists.

## Testing

Every new or changed script gets a `--demo` self-check, matching the
convention every script in `scripts/` follows except `submit_picks.py` and
`local_pickem_server.py`, which currently have none and will gain them.

Scoring is a pure function from picks plus results to standings. Its demo
covers a correct pick, a wrong pick, a draw, an unfinished match, a missing
pick file, and a resubmission, with fabricated data and no network. Deadline
enforcement is likewise a pure function of the current time and the deadline,
tested on both sides of the line. The fixtures job's demo hits the real API
and asserts ten matches from a single matchday, as the existing fetchers do.

`local_pickem_server.py` gains the ability to serve a local `feeds/`
directory, which makes every page state reachable by hand: a fabricated
fixtures file with a future deadline to test picking, the same file with a
past deadline to watch the endpoint refuse, a fabricated standings file to
see the scored view. No waiting for a matchday, no touching the host.

Two captured API responses are tracked in git, in a folder off the root,
trimmed to a single matchday rather than whole-season dumps. A finished
matchday from football-data.org, because scoring cannot be tested at all
without finished matches and waiting a week is the only alternative. And an
Odds API response, because that API is quota-limited and a demo that burns
requests every run is one people stop running. FPL and the upcoming-fixtures
call are deliberately not captured: both are free and unmetered, the existing
fetchers already self-check against them live, and a recorded schedule goes
stale in a way that misleads.

No test harness, no mocking framework. Files the demos read when handed a
path.

## Deliberately not in scope

An automated test runner. Browsable pick history. Odds-weighted scoring.
Tiebreak rules beyond displaying ties as ties. Per-fixture locking. Any form
of authentication.

## Open items for after the build

CLAUDE.md, README.md and DESIGN.md say nothing about Pick 'Em. They need a
pass once this exists rather than before, which is how the previous Pick 'Em
notes drifted from the code in the first place.

The `pickem-wip` stash can be dropped once this lands. Its `build_matchday()`
solved picking the current matchday's ten fixtures without a matchday source,
and the verified `matchday` filter removes the need. Its warning still holds
for anything inferring a round from kickoff times, which nothing here does.
The stash also modifies the now-deleted `NEXT-SESSION.md`, so popping it
needs that resolved.
