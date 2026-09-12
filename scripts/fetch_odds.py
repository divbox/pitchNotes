"""Pull average h2h odds for Arsenal/Man Utd's next fixture from The Odds API.

Checks both soccer_epl and soccer_uefa_champs_league so this lines up with
whichever competition a club's next match actually is (matches
fetch_data.py's next_fixtures logic, which isn't PL-only either).

Usage: python3 fetch_odds.py

Requires ODDS_API_KEY in .env. Writes to ODDS_OUTPUT_PATH if set in .env,
else ./odds.json. This is the script meant to run via cron on the Linode
host, independent of the weekly build/publish/deploy pipeline -- see
CLAUDE.md's Pipeline section.
"""
import json
import os
import sys
import urllib.request

FOLLOWED = {"Arsenal": "ARS", "Manchester United": "MUN"}
SPORTS = ["soccer_epl", "soccer_uefa_champs_league"]
BASE = "https://api.the-odds-api.com/v4"


def load_key(env_path=".env"):
    with open(env_path) as f:
        for line in f:
            if line.startswith("ODDS_API_KEY="):
                return line.strip().split("=", 1)[1]
    raise RuntimeError(f"ODDS_API_KEY not found in {env_path}")


def load_output_path(env_path=".env"):
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("ODDS_OUTPUT_PATH="):
                    return line.strip().split("=", 1)[1]
    return "odds.json"


def get(key, sport):
    url = f"{BASE}/sports/{sport}/odds/?apiKey={key}&regions=uk&markets=h2h&oddsFormat=decimal"
    with urllib.request.urlopen(urllib.request.Request(url)) as r:
        return json.load(r)


def average_odds(event):
    sums, counts = {}, {}
    for bm in event["bookmakers"]:
        for market in bm["markets"]:
            if market["key"] != "h2h":
                continue
            for outcome in market["outcomes"]:
                sums[outcome["name"]] = sums.get(outcome["name"], 0) + outcome["price"]
                counts[outcome["name"]] = counts.get(outcome["name"], 0) + 1
    return {name: round(sums[name] / counts[name], 2) for name in sums}


def find_next_event(events, team_name):
    matches = [e for e in events if team_name in (e["home_team"], e["away_team"])]
    return min(matches, key=lambda e: e["commence_time"]) if matches else None


def build(key):
    events_by_sport = {sport: get(key, sport) for sport in SPORTS}
    result = {}
    for team_name, tla in FOLLOWED.items():
        candidates = [
            find_next_event(events, team_name)
            for events in events_by_sport.values()
        ]
        candidates = [e for e in candidates if e is not None]
        if not candidates:
            result[tla] = None
            continue
        event = min(candidates, key=lambda e: e["commence_time"])
        result[tla] = {
            "commence_time": event["commence_time"],
            "home_team": event["home_team"],
            "away_team": event["away_team"],
            "bookmaker_count": len(event["bookmakers"]),
            "odds": average_odds(event),
        }
    return result


def demo():
    """ponytail: self-check against the real API -- free tier, 2 calls, negligible cost."""
    key = load_key()
    result = build(key)
    for tla in ("ARS", "MUN"):
        assert tla in result, f"{tla} missing from result"
        if result[tla] is not None:
            assert result[tla]["odds"], f"{tla} has an event but no odds"
    print("demo OK", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        result = build(load_key())
        output_path = load_output_path()
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"wrote {output_path}")
