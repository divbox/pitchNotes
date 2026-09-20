"""Pull the current PL gameweek and every player's real goals/assists from
the free public Fantasy Premier League API (no key -- confirmed reachable
without auth: `curl fantasy.premierleague.com/api/bootstrap-static/`).

Two things come out of one call to bootstrap-static:
- events -> the gameweek flagged is_current (or is_next, between rounds),
  which drives the masthead "Matchday N" label (cross-checked against
  fetch_data.py).
- elements -> every player's goals_scored/assists, not just players who've
  scored -- this is what football-data.org's /scorers can't give you, see
  CLAUDE.md Data rules.

Usage: python3 fetch_fpl.py
"""
import json
import sys
import urllib.request

BASE = "https://fantasy.premierleague.com/api"


def get(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def current_event(events):
    for ev in events:
        if ev["is_current"]:
            return ev
    for ev in events:
        if ev["is_next"]:
            return ev
    raise RuntimeError("no current or next gameweek in FPL events")


def build_scorers(elements, teams):
    tla_by_team = {t["id"]: t["short_name"] for t in teams}
    return [
        {
            "player": {"name": e["web_name"]},
            "team": {"tla": tla_by_team[e["team"]]},
            "goals": e["goals_scored"],
            "assists": e["assists"],
        }
        for e in elements
    ]


def build():
    data = get("/bootstrap-static/")
    event = current_event(data["events"])
    return {
        "gameweek": event["id"],
        "deadline": event["deadline_time"],
        "scorers": build_scorers(data["elements"], data["teams"]),
    }


def demo():
    """Self-check against the real API -- free, no key, negligible cost."""
    result = build()
    assert 1 <= result["gameweek"] <= 38, "gameweek out of range"
    assert result["scorers"], "expected at least one player"
    assert all(
        "goals" in s and "assists" in s and "team" in s and "player" in s
        for s in result["scorers"]
    ), "scorer rows missing expected fields"
    print("demo OK", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        print(json.dumps(build(), indent=2))
