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
    """Standings only. Fixtures are fetched separately by whoever needs them
    (build.py asks for 2 per club), so this doesn't spend API calls on a
    next-fixture lookup its caller is going to redo anyway."""
    standings = get(token, "/competitions/PL/standings")
    table = standings["standings"][0]["table"]
    return {
        "table": top6_plus_followed(table),
        "full_table": table,
    }


def demo():
    """Self-check against the real API — free tier, a few calls, negligible cost."""
    token = load_token()
    result = build(token)
    assert 6 <= len(result["table"]) <= 8, "expected top 6 plus up to 2 followed clubs"
    tlas = [row["team"]["tla"] for row in result["table"]]
    assert "ARS" in tlas and "MUN" in tlas, "Arsenal/Man Utd must appear even outside top 6"
    for club, team_id in (("ARS", ARSENAL_ID), ("MUN", MAN_UTD_ID)):
        for fixture in next_fixtures(token, team_id, n=2):
            assert fixture["status"] not in ("FINISHED", "CANCELLED", "POSTPONED"), f"{club} next fixture must be unplayed"
    print("demo OK", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        print(json.dumps(build(load_token()), indent=2))
