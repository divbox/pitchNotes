# Next session

## What got done
- Built the full data layer: `fetch_data.py` pulls PL standings and
  Arsenal/Man Utd fixtures from football-data.org (free tier).
- Built and shipped the first real edition (Week 3) end to end:
  `content.py` (editorial prose) → `build.py` (renders HTML) →
  `publish.py` (promotes to `dist/`, archives outgoing week, tracks
  state in `manifest.json`) → `deploy.py` (rsyncs to Linode) →
  `run_weekly.py` (chains the last three, stops and logs on first
  failure).
- Iterated the visual design against an earlier reference file
  Divbox provided — adopted its masthead/hero/section-header styling,
  kept this session's Club News (API-verified) and Transfer Wire
  content.
- Split the weekly work into two project skills:
  `.claude/skills/pitch-notes-content` (research + writing, human/
  agent in the loop, can't be scripted since it needs judgment) and
  `.claude/skills/pitch-notes-weekly` (mechanical rebuild + publish,
  no judgment, stops and reports on any failure).
- Added a live Odds section: `fetch_odds.py` (The Odds API, averaged
  across bookmakers) runs via cron directly on the Linode host
  (outside the web root, own `.env`), and the page fetches
  `odds.json` client-side (same-origin, no key ever reaches the
  browser).
- Updated CLAUDE.md throughout to match what actually got built —
  it's current, not aspirational.

## Key decisions and why
- Week numbering tracks the PL matchday just played (this runs Monday
  nights as a recap), not an edition count — so this was Week 3, not
  Week 1.
- Archive is a bare Apache directory listing, not a generated index
  page — deliberate, full filenames make the raw listing
  self-explanatory and a fancier page isn't worth it here.
- Content generation stays a human/agent-invoked skill, not something
  folded into the automated wrapper — it requires research and
  judgment (source selection, fact verification, rumor grading,
  unslop pass), which a subprocess can't do.
- Odds run on a completely separate pipeline (cron on the Linode box)
  rather than through this repo's weekly deploy, because the API key
  can never reach the browser and the odds deserve fresher-than-weekly
  updates.

## Open questions / not yet done
- Scheduling pitch-notes-weekly itself (cron or a scheduled task) is
  still open — deliberately not automated yet, since content
  generation isn't automated either and scheduling only the mechanical
  half would silently republish stale prose with fresh numbers.
- `ODDS_API_KEY`'s value was typed into the chat transcript during
  setup (a mistake, corrected for going forward — see CLAUDE.md's new
  "Secrets" rule). Divbox opted not to rotate it. Worth rotating if
  odds ever look tampered with or usage spikes unexpectedly.
- Root folder cleanup: move the scripts (`fetch_data.py`,
  `fetch_odds.py`, `content.py`, `build.py`, `publish.py`, `deploy.py`,
  `run_weekly.py`) into a `scripts/` folder so the project root isn't
  a flat pile of Python files next to CLAUDE.md/DESIGN.md. Will need
  updating the imports between them (`content`/`fetch_data` imports in
  `build.py`), the `.claude/skills/*` instructions that reference
  script paths, `.claude/launch.json`, and CLAUDE.md's Pipeline
  section. Divbox wants this next session, not now.

## Files created or modified this session
`fetch_data.py`, `fetch_odds.py`, `content.py`, `build.py`,
`publish.py`, `deploy.py`, `run_weekly.py`, `.env` (new keys),
`.claude/skills/pitch-notes-content/SKILL.md`,
`.claude/skills/pitch-notes-weekly/SKILL.md`, `.claude/launch.json`
(local test server config), `CLAUDE.md` (substantial update),
`weeklies/pitch-notes-W3.html`, `dist/` (index.html + archive/),
`manifest.json`, `pitch-notes.log`. Remote: `/home/divbox/pitch-notes-odds/`
(script + `.env`) and a new crontab entry on the Linode host.
