"""Cross-check the current PL matchday against openfootball/england's
plain-text season schedule (public domain, no key -- confirmed reachable
without auth). A second, independent source so fetch_fpl.py's gameweek
number is never trusted alone for something CLAUDE.md's data rules treat
as a schedule fact.

Format reference (one block per matchday, exactly 2-space-indented date
lines, year only stated where it changes -- confirmed against the live
2026-27 file):

    ▪ Matchday 1
      Fri Aug 21 2026
        20:00  Arsenal FC v Coventry City FC  3-0 (2-0)
      Sat Aug 22
        ...

Usage: python3 fetch_openfootball.py [YYYY-MM-DD]  (defaults to today)
"""
import datetime
import re
import sys
import urllib.error
import urllib.request

RAW_BASE = "https://raw.githubusercontent.com/openfootball/england/master"
MATCHDAY_RE = re.compile(r"^▪ Matchday (\d+)\s*$")
DAY_RE = re.compile(r"^  (\w{3} \w{3} \d{1,2})(?: (\d{4}))?\s*$")
SEASON_START_MONTH = 6  # PL season runs Aug-May; anything before June still belongs to the prior season


def season_start_year(d):
    return d.year if d.month >= SEASON_START_MONTH else d.year - 1


def fetch_season_text(start_year):
    season = f"{start_year}-{str(start_year + 1)[-2:]}"
    url = f"{RAW_BASE}/{season}/1-premierleague.txt"
    # Browser UA instead of urllib's default -- insurance against UA filtering
    # on a public endpoint; no recorded failure behind it (default UA worked
    # when checked 2026-09-20).
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as r:
        return r.read().decode()


def matchday_for_date(text, target_date, initial_year):
    """Most recently *started* matchday as of target_date -- matches FPL's
    is_current semantics, which flips at the round's first kickoff, not
    once every fixture in it has finished."""
    matchday = None
    year = initial_year
    best = None
    for line in text.splitlines():
        md = MATCHDAY_RE.match(line)
        if md:
            matchday = int(md.group(1))
            continue
        day = DAY_RE.match(line)
        if not day:
            continue
        if day.group(2):
            year = int(day.group(2))
        day_date = datetime.datetime.strptime(f"{day.group(1)} {year}", "%a %b %d %Y").date()
        if day_date <= target_date:
            best = matchday
        else:
            break
    return best


def current_matchday(target_date):
    start_year = season_start_year(target_date)
    try:
        text = fetch_season_text(start_year)
    except (urllib.error.URLError, OSError, UnicodeDecodeError):
        return None
    return matchday_for_date(text, target_date, start_year)


def demo():
    """Parse the real file, check known matchday boundaries."""
    text = fetch_season_text(2026)
    assert matchday_for_date(text, datetime.date(2026, 8, 21), 2026) == 1, \
        "season opener should be Matchday 1"
    assert matchday_for_date(text, datetime.date(2027, 1, 1), 2026) == 19, \
        "New Year's Day fixture should be Matchday 19 (tests the year-rollover parse)"
    assert matchday_for_date(text, datetime.date(2027, 5, 30), 2026) == 38, \
        "season finale should be Matchday 38"
    print("demo OK", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        target = (
            datetime.date.fromisoformat(sys.argv[1])
            if len(sys.argv) > 1
            else datetime.date.today()
        )
        print(current_matchday(target))
