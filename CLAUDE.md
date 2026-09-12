# Pitch Notes — Project Instructions

## What this is
A weekly, self-hosted Premier League dashboard: a single HTML file, built
for Divbox (an Arsenal fan who also follows Manchester United, his father's
team) and shared with UK friends who are also Arsenal fans. Tone is
informative and cheeky, not corporate. This is a fun personal project, not
a critical app — proportionate effort, not enterprise rigor, except where
noted below.

## Working with Claude
General preferences for how to work on this project, not just what to
build.

- Think before acting: state assumptions, surface multiple
  interpretations instead of picking one silently, and stop to ask when
  something's genuinely unclear.
- Simplicity first: minimum code that solves the problem, no speculative
  abstractions or unrequested flexibility. This is a personal project,
  not production — proportionate effort applies here too.
- Surgical changes: touch only what the task requires. Don't refactor or
  restyle adjacent code, and match existing style even if you'd do it
  differently. Clean up orphans your own change creates (unused
  imports/vars); leave pre-existing dead code alone but mention it.
- Goal-driven execution: for multi-step work, state a brief plan and how
  you'll verify it worked before starting.
- Communication: direct and concise, prose over bullets in conversation,
  minimal headers and bold. Act on clear requests without asking first;
  raise a real risk of building the wrong thing before starting, not
  after. Don't pad with reflexive caveats, and say when uncertain rather
  than guessing. Match Divbox's casual tone.
- Technical context: 25 years in software, self-taught; last 15 as a
  director of technology, not hands-on day-to-day. Can read code and
  follow technical reasoning, but treat this knowledge as dated by
  default, including anything stated with confidence.
- Secrets: read `.env` values only by letting a script load them at
  runtime, never by cat/Read-ing the file or typing a key's actual
  value into a command, file, or chat message. A script reading its
  own config is normal; a secret passing through Claude's own output
  is not — it's now in the transcript and has to be treated as
  exposed.

## Session endings
At the end of a working session, write `NEXT-SESSION.md` in the project
root (overwritten each session; git history keeps old ones). Trigger:
Claude asks if the session feels like it's winding down, or Divbox
signals he's stepping away (e.g. "have to go walk the dog") — treat that
as the cue and write it without being asked. Include what got done this
session, key decisions and the brief reasoning behind them, what's next,
open questions, and files created or modified. Keep it a handoff note,
not a recap essay.

## Output format
- The deliverable is a single self-contained HTML file per week: no
  external JS dependencies beyond Google Fonts, all CSS/JS inline. A
  local Python pipeline generates it (see Pipeline below) — "no build
  step" means the browser needs none, not that nothing runs locally.
- Visual design (theme, palette, fonts, dashboard component styles): see
  DESIGN.md. That file is the source of truth for tokens — don't
  redefine colors or fonts here.
- No real team crests or logos anywhere — they're trademarked. Use flat
  color chips (each club's actual kit color) with 2–3 letter initials
  instead. This is a hard rule, not a placeholder to revisit.
- Week numbering tracks the PL matchday just played, not an edition
  count. This runs Monday nights as a recap of the weekend's games plus
  a look ahead — so "Week 3" means matchday 3 just happened, not that
  it's the third time this has run.
- File naming: pitch-notes-W<N>.html, same on disk locally
  (weeklies/W<N>) and once archived on the host (archive/W<N>) — one
  naming scheme everywhere, since the raw filename is the only label a
  visitor to the archive sees (see Pipeline).

## Pipeline
The weekly run is two skills, deliberately split because one needs
judgment and the other doesn't:

- **pitch-notes-content** (research + writing, human/agent in the loop).
  Gathers this week's Hero/Schedule Watch/Club News/Transfer
  Wire/Divbox 101 material and writes it into `content.py`. Never
  touches `build.py`. A subprocess can't invoke a skill — there's no
  LLM in a script — so this step can't be folded into the mechanical
  wrapper below; it only runs when someone (or an agent) is actually
  doing the work.
- **pitch-notes-weekly** (mechanical, no judgment). Runs
  `scripts/run_weekly.py`, which chains `build.py` (renders `content.py` +
  live standings/fixtures into HTML) → `publish.py` (promotes the
  newest `weeklies/` file to `dist/index.html`, archives the outgoing
  week into `dist/archive/` under its original filename, tracks state
  in `manifest.json`) → `deploy.py` (rsyncs `dist/` to the Linode
  host). Stops at the first failing step, logs every run to
  `logs/pitch-notes.log`, never retries or improvises around a failure —
  report it and wait.

All pipeline scripts live in `scripts/` (`fetch_data.py`,
`content.py`, `build.py`, `publish.py`, `deploy.py`,
`run_weekly.py`, `fetch_odds.py`); `fetch_data.py` is imported by
`build.py`, not run standalone. Every script uses paths relative to
the project root (`.env`, `weeklies/`, `dist/`, `manifest.json`,
`logs/pitch-notes.log`), so always run them from the repo root, e.g.
`python3 scripts/run_weekly.py`.

`.env` keys (local, for this repo's pipeline): `FOOTBALL_DATA_API_KEY`,
`LINODE_HOST`, `LINODE_USER`, `LINODE_PORT`, `LINODE_WWW_PATH`. Linode
connects over SSH on a non-standard port with key-based auth already
in place — deploy.py reads all of this, never prompts for credentials.

### The Odds section — a separate, independent pipeline
Odds is the one part of the page that's genuinely dynamic client-side
JS, not baked in at build time, and it's deliberately decoupled from
everything else above:

- `fetch_odds.py` pulls average h2h odds (The Odds API,
  `soccer_epl` + `soccer_uefa_champs_league`, whichever is each
  followed club's actual next fixture) and writes `odds.json`.
- It runs via **cron directly on the Linode host**
  (`/home/divbox/pitch-notes-odds/`, outside the web root), not from
  this repo's weekly pipeline — because the API key must never reach
  the browser, and the freshness the odds deserve (a few times a day)
  is a different cadence than the weekly rebuild. Its own `.env`
  there holds `ODDS_API_KEY` and `ODDS_OUTPUT_PATH` (mode 600),
  entirely separate from this repo's `.env`.
- Cron fires at 1am/6am/9am server time (America/New_York) ≈ 6am
  UK/ET/PT. Drifts by up to an hour for a few weeks each autumn since
  UK and US DST changes land on different dates — known, not a bug.
  Output logs to `fetch_odds.log` next to the script.
- The page's inline `<script>` does a same-origin `fetch('odds.json')`
  on load — no CORS issue (same origin), no key exposure (the file
  has none), and a plain fallback message if the file's missing or
  the fetch fails, so a hiccup here never breaks the rest of the page.
- Local `.env` also has `ODDS_API_KEY` for testing `fetch_odds.py`
  before pushing changes to the remote copy by hand (there's no
  automated deploy step for this piece, unlike the rest of the site).

The archive is a bare Apache directory listing on the host, not a
generated index page. Decided deliberately: full filenames
(pitch-notes-W<N>.html) make the raw listing self-explanatory, and a
fancier generated page isn't worth building for what this is.

## Section order
1. Masthead — week number, date, followed clubs.
2. Hero / Today — the day's headline story.
3. Schedule Watch — call out any week where the normal Saturday/Sunday
   rhythm is interrupted (European competition matchday, international
   break, domestic cup round) and explain why. This section exists
   specifically so a fixture gap is never left unexplained.
4. The Table — top 6 plus Arsenal and Man United rows, highlighted.
5. Golden Boot Watch — league-wide top 5 scorers and top 5 assists,
   side by side. Followed-club players highlighted same as The Table.
   The assists list is drawn from the same scorers dataset (see Data
   rules), so it only covers players who've also scored — say so on
   the page, don't present it as a full assists leaderboard.
6. Early Risers & Strugglers — movers. Once two consecutive editions
   exist, show real week-over-week position change; until then, form
   only (and say so).
7. Club News — Arsenal and Man United, paraphrased from real sources,
   never reproduced verbatim beyond a short attributed phrase.
8. The Transfer Wire — rumors graded Confirmed / Likely / Speculative.
   Explicitly note when the transfer window is closed rather than
   manufacturing urgency that isn't there.
9. Divbox 101 — one teaching topic per week, tied to that week's biggest
   storyline (not a random rule pulled from a fixed list).
10. Next Up — next fixtures for Arsenal and Man United specifically.
11. The Odds — bookmaker-average odds for each followed club's next
    fixture. Loaded client-side from odds.json (see Pipeline), not
    baked in at build time, so it's the one section that can show
    "unavailable" if that file's missing or stale. Always paired with
    a plain note that it's a snapshot for fun, not financial advice.
12. Footer — build date and a one-line data-provenance note. No build
    process commentary, no references to prior chat discussion — the
    people reading this don't need to know what we debated to get here.

## Data rules — non-negotiable
This is the part to get right without exception. Schedules, scores, and
standings get zero guessing, zero "plausible" filler, and zero inference
from a paraphrased article when a structured source exists.

- Standings and scores: use the football-data.org API (v4,
  `https://api.football-data.org/v4`), competition code `PL`. Auth via
  `X-Auth-Token` header, key stored in `.env` (`FOOTBALL_DATA_API_KEY`),
  free tier (10 calls/min, delayed scores — fine for a weekly job).
  `/competitions/PL/standings` for the table, `/competitions/PL/matches`
  for fixtures/scores. Before writing any sentence describing a match,
  check its `status` field. Free tier scores are delayed, not live, so
  a game that isn't finished never gets described as a finished result.
- Continental fixtures (Champions League, etc.): same API, competition
  code `CL`, also in the free tier's 12 included competitions. Don't
  reconstruct a schedule from a news article summary if the structured
  API covers it.
- Player goals/assists (Golden Boot Watch): same API,
  `/competitions/PL/scorers`. This is the only player-stats resource
  the free tier exposes — it lists players with at least one PL goal
  this season, each with a `goals` and `assists` count. There's no
  separate assists-only leaderboard, so ranking by `assists` from this
  same list only covers players who've also scored; the page says so.
- Fetch via a small Python script (per DESIGN.md: heavy lifting happens
  in Python, baked into the HTML, not fetched client-side) — CORS isn't
  confirmed for football-data.org and the token can't sit in a page
  anyone can view-source anyway.
- Any week with no Premier League fixture for a followed club: figure
  out why (European matchday, international break, cup round) and say
  so in Schedule Watch, sourced from official calendars (club sites,
  Premier League, UEFA) — not generic web search, which is frequently
  outdated or templated SEO content for exactly this kind of fixture
  question.
- Odds: The Odds API (see Pipeline), averaged across whatever
  bookmakers it returns for that fixture. Never estimate or guess an
  odds figure — if the file's missing or a club has no upcoming
  fixture in either competition, show the unavailable state, don't
  fill in a plausible-looking number.
- If a schedule, score, or standings fact can't be verified with
  confidence, stop and ask rather than filling the gap with a guess.
  This standard applies strictly to schedules/scores/standings. The
  Transfer Wire and Divbox 101 sections can be more conversational and
  don't need the same rigor — hedged, speculative framing is fine there
  when that's genuinely the state of things.

## Style rules
- No meta-commentary about the build process, prior chat exchanges, or
  internal reasoning in anything a reader sees — that includes captions,
  footnotes, and footer text.
- Paraphrase news and rumors in your own words; name the source; never
  quote more than a short attributed phrase.
- Club News / Transfer Wire sourcing: check these first, in order —
  Arsenal.com/news, ManUtd.com/news, PremierLeague.com/news, BBC Sport
  Football, Sky Sports Transfer Centre, then a tabloid (The Sun or
  Daily Star football) for the edgier/earlier rumors. General web
  search fills gaps, especially for transfer rumors with no single
  official source. Grading calibration: Fabrizio Romano, David
  Ornstein (The Athletic), or multiple outlets corroborating something
  means at least "Likely" — a single tabloid mention stays
  "Speculative."
- Section tags (`.sec-head .tag`) use `--color-accent` (Arsenal red, see
  DESIGN.md).
- Tone is cheeky but clean — Divbox 101's framing and the masthead
  kicker are the calibration point for how far to push it.
- Run reader-facing prose (Hero, Club News, Transfer Wire, Divbox 101)
  through the `unslop` skill before finalizing — AI writing tells,
  including em dash overuse, are handled there, not duplicated here.

## Open items
- Scheduling: pitch-notes-weekly (the mechanical half) is safe to fire
  on a schedule since it has no judgment calls. pitch-notes-content
  isn't — it's a research/writing task requiring an agent in the loop,
  so full unattended automation would silently republish stale prose
  with refreshed numbers. Not scheduling either skill automatically
  until content generation is reliable enough to trust unattended.
- The current `ODDS_API_KEY` value was typed into a chat transcript
  during setup (2026-09-07). Divbox chose not to rotate it at the
  time ("just a sports odds key, I'll rotate if it's ever misused") —
  not a to-do, just a fact worth knowing if odds ever behave oddly.
