"""Validate and persist a locked-in Pick Em submission.

One JSON file per user per week: data/picks/W<week>/<user>.json. Each
submission only ever touches its own file, so there's no read-modify-write
race between users locking in around the same time.

Runs as a CGI script under Apache in production (reads the POST body via
CONTENT_LENGTH, writes a CGI-style response). save_picks() is also imported
directly by scripts/local_pickem_server.py for local testing.

ponytail: no auth and resubmitting just overwrites the file -- fine for a
handful of friends on the honor system. Add real auth if this ever needs to
stop people editing each other's picks.
"""
import json
import os
import sys
from datetime import datetime, timezone

USERS = {"Divs", "Cheeky", "LL", "L-Dog"}
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "picks")


class ValidationError(Exception):
    pass


def validate(payload):
    user = payload.get("user")
    week = payload.get("week")
    picks = payload.get("picks")
    if user not in USERS:
        raise ValidationError(f"unknown user: {user!r}")
    if not isinstance(week, int):
        raise ValidationError(f"week must be an integer, got {week!r}")
    if not isinstance(picks, list) or not picks:
        raise ValidationError("picks must be a non-empty list")
    for p in picks:
        if not isinstance(p, dict) or not p.get("fixture") or not p.get("pick"):
            raise ValidationError(f"malformed pick: {p!r}")
    return user, week, picks


def save_picks(payload):
    user, week, picks = validate(payload)
    week_dir = os.path.join(DATA_DIR, f"W{week}")
    os.makedirs(week_dir, exist_ok=True)
    record = {
        "user": user,
        "week": week,
        "picks": picks,
        "locked_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(os.path.join(week_dir, f"{user}.json"), "w") as f:
        json.dump(record, f, indent=2)
    return record


def run_cgi():
    try:
        length = int(os.environ.get("CONTENT_LENGTH", 0))
        body = sys.stdin.read(length)
        payload = json.loads(body)
        record = save_picks(payload)
        status, result = "200 OK", {"ok": True, "saved": record}
    except ValidationError as e:
        status, result = "400 Bad Request", {"ok": False, "error": str(e)}
    except Exception:
        status, result = "500 Internal Server Error", {"ok": False, "error": "unexpected error"}
    print(f"Status: {status}")
    print("Content-Type: application/json")
    print()
    print(json.dumps(result))


if __name__ == "__main__":
    run_cgi()
