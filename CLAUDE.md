# Pitch Notes — Project Instructions

Pitch Notes is a Premier League dashboard covering the whole
league. Two clubs, Divbox's favorites, get special focus throughout:
Arsenal and Manchester United.

If doing the right thing, or a change Divbox is asking for, goes against
what a rule in these docs says, ask Divbox rather than deciding it
yourself or overriding the rule quietly. And don't invent reasons for a
rule that was never actually justified that way — if you don't have a
real reason, say so instead of making one up.

## Working with Claude
General preferences for how to work on this project, not just what to
build.

### Think Before Acting
Before implementing anything:
- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask as many questions as the ambiguity needs, not ones you could answer yourself.

### Simplicity First
Minimum code that solves the problem. Nothing speculative.
- No abstractions for single-use code, no "flexibility" that wasn't requested.
- If a bigger change seems warranted, name it and ask — don't just include it.
- If you write 200 lines and it could be 50, rewrite it.
- Current work isn't production/consumer-facing — don't over-engineer edge cases.

### Surgical Changes
Touch only what you must.
- Don't "improve" adjacent code, comments, or formatting. Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- When your changes create orphans (unused imports, variables, functions): remove them.
- Pre-existing dead code: mention it, don't touch it.
- When editing the user's text or code, make targeted changes — don't rewrite everything unless asked.

### Goal-Driven Execution
Do it directly when the request is unambiguous and the change is small and mechanical, with no real judgment call about what to do or how. When there's a genuine decision about what to build or how to do it, or the work is multi-step, plan first and get input before starting. If there's a real chance of building the wrong thing, raise it before starting instead of after.
- State a brief plan: `1. [step] → verify: [check]`
- Weak criteria ("make it work") need to be made concrete before starting.

### Bugs
Reproduce and diagnose first, then explain the bug clearly and ask how to
proceed. Never fix a bug on your own, even one you introduced. Bugs need
Divbox's input.

### Communication style
Be direct and concise. Skip preamble, affirmations, and filler — get to the point.

Default to prose over bullet points unless structure genuinely helps. Avoid unnecessary headers and bold text.

Don't pad with reflexive caveats.

Match the user's tone — casual and conversational unless the task calls for something more formal.

## Output format
- Assets and visual design (shared stylesheet + JS, theme, palette,
  fonts, dashboard component styles): see DESIGN.md, the source of
  truth. Don't redefine colors, fonts, or the asset system here.
- The masthead's edition number reflects the PL matchday just played,
  not how many times this has run. How that number is derived, and its
  wording, is being reworked — see cadence.md.

## Pipeline
The run is two skills, deliberately split because one needs
judgment and the other doesn't:

- **pitch-notes-content** (research + writing, human/agent in the loop).
  Gathers this edition's Hero/Schedule Watch/Club News/Transfer
  Wire/Divbox 101 material and writes it into `content.py`. Never
  touches `build.py`. A subprocess can't invoke a skill — there's no
  LLM in a script — so this step can't be folded into the mechanical
  wrapper below; it only runs when someone (or an agent) is actually
  doing the work.
- **pitch-notes-weekly** (mechanical, no judgment). Runs
  `scripts/run_weekly.py`, which chains `build.py` (renders `content.py` +
  live standings/fixtures into HTML) → `publish.py` (promotes the
  newest `weeklies/` file to `dist/index.html`, archives the outgoing
  edition into `dist/archive/` under its original filename, tracks state
  in `manifest.json`) → `deploy.py` (rsyncs `dist/` to the Linode
  host). Stops at the first failing step, logs every run to
  `logs/pitch-notes.log`, never retries or improvises around a failure —
  report it and wait.

Pipeline scripts live in `scripts/` and use paths relative to the
project root, so always run them from there, e.g.
`python3 scripts/run_weekly.py`.

`.env` keys (local, for this repo's pipeline): `FOOTBALL_DATA_API_KEY`,
`LINODE_HOST`, `LINODE_USER`, `LINODE_PORT`, `LINODE_WWW_PATH`. Linode
connects over SSH on a non-standard port with key-based auth already
in place — deploy.py reads all of this, never prompts for credentials.

### The Odds section — a separate, independent pipeline
Odds is the one section loaded client-side rather than baked into the
HTML at build time. It runs on the Linode host via cron, not from this
repo's pipeline, for two reasons: the API key must never reach the
browser, and odds want a fresher cadence (a few times a day) than the
main build.

- `fetch_odds.py` pulls average h2h odds from The Odds API for each
  followed club's actual next fixture (Premier League or Champions
  League) and writes `odds.json`.
- It runs on the host, outside the web root, with its own `.env`
  holding `ODDS_API_KEY`, separate from this repo's `.env`. No
  automated deploy for this piece: the remote copy is updated by hand.
- The page reads `odds.json` same-origin, so no key is exposed; if the
  file's missing or the fetch fails, it shows a fallback and the rest
  of the page is unaffected.
- The local `.env` also has `ODDS_API_KEY` for testing `fetch_odds.py`
  before pushing.

The archive is a bare Apache directory listing on the host, not a
generated index page. Decided deliberately: full filenames
(pitch-notes-YYYY-MM-DD.html) make the raw listing self-explanatory, and a
fancier generated page isn't worth building for what this is.

## Section order
1. Masthead — edition number, date, followed clubs.
2. Hero / Today — the day's headline story.
3. Schedule Watch — flag any week where the normal Saturday/Sunday
   rhythm is interrupted and explain why, so a fixture gap is never
   left unexplained.
4. The Table — top 6 plus Arsenal and Man United rows, highlighted.
5. Golden Boot Watch — league-wide top 5 scorers and top 5 assists,
   side by side. Followed-club players highlighted same as The Table.
6. Early Risers & Strugglers — movers. Once two consecutive editions
   exist, show real position change between them; until then, form
   only (and say so).
7. Club News — Arsenal and Man United.
8. The Transfer Wire — transfer rumors about the two clubs, graded
   (see Content rules).
9. Divbox 101 — one teaching topic per edition, tied to that edition's biggest
   storyline (not a random rule pulled from a fixed list).
10. Next Up — next fixtures for Arsenal and Man United specifically.
11. The Odds — bookmaker-average odds for each followed club's next
    fixture, loaded client-side (see Pipeline).
12. Footer — build date and a one-line data-provenance note.

## Data rules — non-negotiable
This is the part to get right without exception. Schedules, scores, and
standings get zero guessing, zero "plausible" filler, and zero inference
from a paraphrased article when a structured source exists.

- Standings and scores: use the football-data.org API (v4,
  `https://api.football-data.org/v4`), competition code `PL`. Auth via
  `X-Auth-Token` header, key stored in `.env` (`FOOTBALL_DATA_API_KEY`),
  free tier (10 calls/min, delayed scores — fine for an infrequent job).
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
- Any edition where a followed club has no Premier League fixture: figure
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

## Content rules
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
  official source. Grade rumors Confirmed / Likely / Speculative.
  Calibration: Fabrizio Romano, David Ornstein (The Athletic), or
  multiple outlets corroborating something means at least "Likely"; a
  single tabloid mention stays "Speculative." Note explicitly when the
  transfer window is closed rather than manufacturing urgency that
  isn't there.
- Tone is cheeky — Divbox 101's framing and the masthead
  kicker are the calibration point for how far to push it.
- Run reader-facing prose (Hero, Club News, Transfer Wire, Divbox 101)
  through the `unslop` skill before finalizing — AI writing tells,
  including em dash overuse, are handled there, not duplicated here.
