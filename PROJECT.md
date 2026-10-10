# Pitch Notes

Run every script from the project root.

## Data sources
- Standings, scores, fixtures: football-data.org v4 (`scripts/fetch_data.py`).
  A club's match list includes Champions League games.
- Goals, assists and the matchday number: Fantasy Premier League API
  (`scripts/fetch_fpl.py`). The matchday is cross-checked against openfootball.
- Odds: The Odds API (`scripts/fetch_odds.py`). Runs by cron on the Linode, not
  in the build. The page loads `odds.json` in the browser.

## Env keys
The key names are listed under Setup in `README.md`.

## Page
- Section order is the `TEMPLATE` in `scripts/build.py`.
- Schedule Watch flags any week where the usual Saturday/Sunday rhythm breaks,
  and says why.

## Watch out
- Building overwrites the edition for the date in `content.html`, and that
  date's entry in `data/standings-history.json`. Change the date first.
- A match in play counts as "upcoming" in Next Up.
