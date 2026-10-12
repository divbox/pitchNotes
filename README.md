# Pitch Notes

A Premier League dashboard. See [PROJECT.md](PROJECT.md) for data sources and
things to watch out for, and [DESIGN.md](DESIGN.md) for the visual design system.

## Layout

```
scripts/     pipeline scripts (see below)
editions/    generated edition HTML files (pitch-notes-YYYY-MM-DD.html)
dist/        the promoted "live" site (index.html + archive/), rsynced to the host
logs/        pipeline run log
data/        pipeline state (manifest.json = which edition is live;
             standings-history.json = each edition's table, for Early Risers
             & Strugglers; picks/ = Pick 'Em, gitignored)
odds.json    local test output of fetch_odds.py (the real one runs on the host,
             and the page fetches it from the web root, so it stays put)
```

## Pipeline

Two steps, run from the project root:

1. **Write this edition's content.** Hand-edit `scripts/content.html` or run the
   `pitch-notes-content` skill. Research and judgment live here.
2. **Build, stage and deploy.** Type `/pitch-notes-publish` in Claude Code, or
   run it by hand:
   ```bash
   python3 scripts/run_pipeline.py
   ```
   Runs `build.py`, `publish.py`, then `deploy.py`. `build.py` renders
   `content.html` plus live data into `editions/`. `publish.py` promotes the
   newest edition to `dist/index.html` and archives the outgoing one.
   `deploy.py` pushes `dist/` to the Linode host, so the edition is live when
   the run ends. The run stops at the first failing step and logs to
   `logs/pitch-notes.log`.

   `build.py` refuses to build an edition dated earlier than the one already
   live, since that would overwrite a published edition. If you hit that, it
   means `content.html` wasn't refreshed. `--force` overrides it.

   To see what a deploy would change without pushing anything:
   ```bash
   python3 scripts/deploy.py --dry-run
   ```

### Odds

`scripts/fetch_odds.py` is a separate pipeline. The real one runs on a cron job
on the Linode host, not from this repo.

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

`ODDS_OUTPUT_PATH` is optional. `fetch_odds.py` writes to it if set, and to
`./odds.json` if not.
