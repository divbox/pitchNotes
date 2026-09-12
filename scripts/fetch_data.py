"""Pull PL standings + Arsenal/Man Utd next fixtures from football-data.org.

Usage: python3 fetch_data.py > data.json
Requires FOOTBALL_DATA_API_KEY in .env (see CLAUDE.md Data rules).
"""
import json
import sys
import urllib.request

ARSENAL_ID = 57
MAN_UTD_ID = 66
FOLLOWED_TLAS = {"ARS", "MUN"}
BASE = "https://api.football-data.org/v4"


def load_token(env_path=".env"):
    with open(env_path) as f:
        for line in f:
            if line.startswith("FOOTBALL_DATA_API_KEY="):
                return line.strip().split("=", 1)[1]
    raise RuntimeError(f"FOOTBALL_DATA_API_KEY not found in {env_path}")


def get(token, path):
    req = urllib.request.Request(BASE + path, headers={"X-Auth-Token": token})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def top6_plus_followed(table):
    rows = table[:6]
    seen = {row["team"]["tla"] for row in rows}
    for row in table[6:]:
        if row["team"]["tla"] in FOLLOWED_TLAS and row["team"]["tla"] not in seen:
            rows.append(row)
            seen.add(row["team"]["tla"])
    return rows


def top_scorers(token, limit=25):
    """Players with at least one PL goal this season, each with goals/assists/
    penalties. This is the only player-stats resource the free tier offers --
    there's no separate assists leaderboard, so an "assists" ranking drawn
    from this list only covers players who've also scored."""
    data = get(token, f"/competitions/PL/scorers?limit={limit}")
    return data["scorers"]


def next_fixtures(token, team_id, n=1):
    """Matches come back date-ascending with no filter; the API's own status
    filter doesn't reliably match its real status values (TIMED/SCHEDULED),
    so filter client-side instead."""
    data = get(token, f"/teams/{team_id}/matches")
    upcoming = [m for m in data["matches"] if m["status"] not in ("FINISHED", "CANCELLED", "POSTPONED")]
    return upcoming[:n]


def next_fixture(token, team_id):
    fixtures = next_fixtures(token, team_id, n=1)
    return fixtures[0] if fixtures else None


def build(token):
    standings = get(token, "/competitions/PL/standings")
    table = standings["standings"][0]["table"]
    return {
        "matchday": standings["season"]["currentMatchday"],
        "table": top6_plus_followed(table),
        "full_table": table,
        "scorers": top_scorers(token),
        "next_fixtures": {
            "ARS": next_fixture(token, ARSENAL_ID),
            "MUN": next_fixture(token, MAN_UTD_ID),
        },
    }


def demo():
    """ponytail: self-check against real API — free tier, one call, negligible cost."""
    token = load_token()
    result = build(token)
    assert 6 <= len(result["table"]) <= 8, "expected top 6 plus up to 2 followed clubs"
    tlas = [row["team"]["tla"] for row in result["table"]]
    assert "ARS" in tlas and "MUN" in tlas, "Arsenal/Man Utd must appear even outside top 6"
    for club, fixture in result["next_fixtures"].items():
        assert fixture is None or fixture["status"] not in ("FINISHED", "CANCELLED", "POSTPONED"), f"{club} next fixture must be unplayed"
    assert result["scorers"], "expected at least one scorer"
    assert all("goals" in s and "player" in s and "team" in s for s in result["scorers"]), "scorer rows missing expected fields"
    print("demo OK", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        print(json.dumps(build(load_token()), indent=2))
