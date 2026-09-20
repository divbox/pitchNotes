# Pitch Notes

A Premier League dashboard. See [CLAUDE.md](CLAUDE.md) for the full project
brief and [DESIGN.md](DESIGN.md) for the visual design system.

## Layout

```
scripts/     pipeline scripts (see below)
editions/    generated edition HTML files (pitch-notes-YYYY-MM-DD.html)
dist/        the promoted "live" site (index.html + archive/), rsynced to the host
logs/        pipeline run log
manifest.json  tracks which edition is currently live
standings-history.json  each edition's full table, for Early Risers & Strugglers
odds.json      local test output of fetch_odds.py (the real one runs on the host)
```

## Pipeline

Three steps, run from the project root:

1. **Write this edition's content** — hand-edit `scripts/content.html` (or run the
   `pitch-notes-content` skill). Research and judgment live here.
2. **Build and stage**:
   ```bash
   python3 scripts/run_pipeline.py
   ```
   Chains `build.py` (renders `content.html` + live standings/fixtures from
   football-data.org, matchday label + Golden Boot Watch from the Fantasy
   Premier League API cross-checked against openfootball, into HTML) →
   `publish.py` (promotes the newest `editions/` file to `dist/index.html`,
   archives the outgoing edition). Stops at the first failing step and logs to
   `logs/pitch-notes.log`. Nothing is live at the end of this.

   `build.py` refuses to build an edition dated earlier than the one already
   live, since that would overwrite a published edition. If you hit that, it
   means `content.html` wasn't refreshed. `--force` overrides it.
3. **Deploy** (the only step that touches the live site, so it's separate and
   deliberate):
   ```bash
   python3 scripts/deploy.py --dry-run   # see what would change
   python3 scripts/deploy.py             # push dist/ to the Linode host
   ```

All scripts read paths relative to the project root, so always run them from
there.

### Odds

`scripts/fetch_odds.py` is a separate, independent pipeline — the real one
runs on a cron job on the Linode host (not from this repo). See CLAUDE.md's
Pipeline section for details.

## Setup

Requires a `.env` file in the project root with:

```
FOOTBALL_DATA_API_KEY=
ODDS_API_KEY=
LINODE_HOST=
LINODE_USER=
LINODE_PORT=
LINODE_WWW_PATH=
```

## Claude Code

The maintainer's global Claude Code config (in `~/.claude`, not part of this
repo) has a `SessionStart` hook that injects a short, read-only summary of the
repo's current git state when a session starts here. It changes nothing, and it
won't fire for anyone who opens this repo without that config. Script:
`~/.claude/hooks/session_context.py`.
