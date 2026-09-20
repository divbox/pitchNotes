"""Build the Pitch Notes HTML dashboard for one edition.

Pulls live data via fetch_data.py, bakes it together with this edition's
hand-written editorial content (Hero, Club News, Transfer Wire, Divbox 101),
and writes editions/pitch-notes-<build-date>.html.

Usage:
  python3 build.py            # build the edition dated in content.html
  python3 build.py --force    # rebuild an edition older than the live one
"""
import datetime
import html
import json
import os
import re
import sys
from html.parser import HTMLParser

import fetch_data as fd
import fetch_fpl as ffpl
import fetch_openfootball as fof

EDITIONS_DIR = "editions"
MANIFEST = "manifest.json"
HISTORY = "standings-history.json"
CONTENT_PATH = os.path.join(os.path.dirname(__file__), "content.html")


def load_history():
    if os.path.exists(HISTORY):
        with open(HISTORY) as f:
            return json.load(f)
    return {}


def record_positions(history, date, full_table):
    """Snapshot this edition's full table, keyed by build date.

    Keyed by date rather than appended, so rebuilding the same edition
    replaces its own entry instead of inventing a move against itself.
    """
    history[date] = {r["team"]["tla"]: r["position"] for r in full_table}
    with open(HISTORY, "w") as f:
        json.dump(history, f, indent=2, sort_keys=True)


def previous_positions(history, date):
    earlier = [d for d in history if d < date]
    return history[max(earlier)] if earlier else None


def check_not_stale(build_date, force=False):
    """Refuse to rebuild an edition older than the one currently live.

    Rebuilding today's edition is normal -- that's iterating before publish,
    and overwriting is the point. Building a date *earlier* than the live
    edition means content.html wasn't refreshed first, and writing it would
    clobber an already-published edition (which is exactly how the 10 Sept
    edition got overwritten with 19 Sept data).
    """
    if force or not os.path.exists(MANIFEST):
        return
    with open(MANIFEST) as f:
        current = json.load(f).get("current_date")
    if current and build_date < current:
        raise SystemExit(
            f"refusing to build {build_date}: edition {current} is already live, and "
            f"this would overwrite it.\nRefresh content.html's data-build-date "
            f"(pitch-notes-content), or pass --force if you really mean it."
        )

# Editorial content lives in content.html as prose + data-* attributes, not in
# a .py file: a typo there can't break this build script. Each block is one
# top-level element tagged with data-slot; prose is its inner HTML, typed
# fields are its data-* attributes.
class _ContentParser(HTMLParser):
    """Pull the data-slot blocks out of content.html.

    Uses a real parser rather than a regex because a regex match for the
    closing tag stops at the *first* one, so a nested <div> inside a block
    silently truncated it and the rest of that section vanished from the page
    with no error. Depth is tracked per block instead.
    """

    def __init__(self):
        super().__init__(convert_charrefs=False)  # keep &rarr; etc. verbatim in prose
        self.blocks = []
        self._slot = None
        self._tag = None
        self._depth = 0
        self._attrs = {}
        self._buf = []

    def handle_starttag(self, tag, attrs):
        if self._slot is None:
            d = dict(attrs)
            if "data-slot" in d:
                self._slot = d["data-slot"]
                self._tag = tag
                self._depth = 1
                # attribute values arrive already unescaped; re-escape so a bare
                # & in a headline can't land in the output as stray markup
                self._attrs = {
                    k[len("data-"):]: html.escape(v or "", quote=False)
                    for k, v in d.items()
                    if k.startswith("data-") and k != "data-slot"
                }
                self._buf = []
            return
        if tag == self._tag:
            self._depth += 1
        self._buf.append(self.get_starttag_text())

    def handle_startendtag(self, tag, attrs):
        if self._slot is not None:
            self._buf.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if self._slot is None:
            return
        if tag == self._tag:
            self._depth -= 1
            if self._depth == 0:
                self.blocks.append((self._slot, self._attrs, "".join(self._buf)))
                self._slot = self._tag = None
                self._buf = []
                return
        self._buf.append(f"</{tag}>")

    def handle_data(self, data):
        if self._slot is not None:
            self._buf.append(data)

    def handle_entityref(self, name):
        if self._slot is not None:
            self._buf.append(f"&{name};")

    def handle_charref(self, name):
        if self._slot is not None:
            self._buf.append(f"&#{name};")


def parse_blocks(raw):
    parser = _ContentParser()
    parser.feed(raw)
    parser.close()
    return parser.blocks


def load_content(path=CONTENT_PATH):
    with open(path) as f:
        raw = f.read()
    content = {"club_news": [], "transfer": {"window_note": "", "items": []}}
    for slot, attrs, inner in parse_blocks(raw):
        inner = re.sub(r">\s+<", "><", inner.strip())
        if slot == "edition":
            content["build_date"] = attrs["build-date"]
        elif slot == "hero":
            content["hero"] = {"headline": attrs["headline"], "body": inner}
        elif slot == "schedule":
            content["schedule"] = {"heading": attrs["heading"], "icon": attrs["icon"], "text": inner}
        elif slot == "club-news":
            content["club_news"].append({"tla": attrs["tla"], "name": attrs["name"], "text": inner})
        elif slot == "transfer-window":
            content["transfer"]["window_note"] = attrs["note"]
        elif slot == "transfer":
            content["transfer"]["items"].append(
                {"headline": attrs["headline"], "text": inner, "grade": attrs["grade"]}
            )
        elif slot == "divbox":
            content["divbox"] = {"heading": attrs["heading"], "html": inner}
    missing = [k for k in ("build_date", "hero", "schedule", "divbox") if k not in content]
    if missing:
        raise SystemExit(f"{path}: missing required block(s): {', '.join(missing)}")
    return content

# 2-3 letter chip color per club, approximating real kit colors (no crests/logos).
KIT_COLORS = {
    "MCI": "#6CABDD", "ARS": "#EF0107", "HUL": "#F5A623", "CHE": "#034694",
    "BRE": "#E30613", "LIV": "#C8102E", "MUN": "#DA291C", "NAP": "#12A0D7",
    "SAB": "#1B5E20", "SUN": "#EB172F",
}
DARK_TEXT_TLAS = {"HUL"}  # amber chip needs dark text for contrast


def chip(tla):
    color = KIT_COLORS.get(tla, "#4a5568")
    text = "#0a1628" if tla in DARK_TEXT_TLAS else "#f1ede2"
    return f'<span class="chip" style="background:{color};color:{text}">{tla}</span>'


def fmt_kickoff(utc_iso):
    dt = datetime.datetime.fromisoformat(utc_iso.replace("Z", "+00:00"))
    return dt.strftime("%a %-d %b, %H:%M UTC")


def render_table(rows, followed):
    out = []
    for row in rows:
        tla = row["team"]["tla"]
        cls = " class=\"followed\"" if tla in followed else ""
        out.append(f"""
        <tr{cls}>
          <td>{row['position']}</td>
          <td>{chip(tla)} {row['team']['shortName']}</td>
          <td>{row['playedGames']}</td>
          <td>{row['won']}-{row['draw']}-{row['lost']}</td>
          <td>{row['goalDifference']:+d}</td>
          <td><strong>{row['points']}</strong></td>
        </tr>""")
    return "".join(out)


def mover_row(r, note, followed):
    tla = r["team"]["tla"]
    cls = " class=\"followed\"" if tla in followed else ""
    return (
        f'<div class="mover-row{cls}"><span>{chip(tla)} {r["team"]["shortName"]}</span>'
        f'<span class="note">{note}</span></div>'
    )


def render_movers(full_table, followed, previous=None, n=4):
    """Real position change against the previous edition, where there is one.

    Until a previous edition exists there's nothing to compare against, so
    fall back to current record and say so on the page rather than dressing
    up the top and bottom of the table as movement (CLAUDE.md section 6).
    """
    if not previous:
        return {
            "up": "".join(mover_row(r, f"{r['won']}W-{r['draw']}D-{r['lost']}L", followed)
                          for r in full_table[:n]),
            "down": "".join(mover_row(r, f"{r['won']}W-{r['draw']}D-{r['lost']}L", followed)
                            for r in full_table[-n:]),
            "up_heading": "&uarr; Best start",
            "down_heading": "&darr; Toughest start",
            "tag": "Form, not rank",
            "note": "No previous edition to compare against yet, so this is ranked on "
                    "current record rather than movement. From the next edition on it "
                    "shows real position change.",
        }

    moves = []
    for r in full_table:
        tla = r["team"]["tla"]
        if tla in previous:
            moves.append((previous[tla] - r["position"], r))
    moves.sort(key=lambda m: m[0], reverse=True)

    def side(entries):
        return "".join(
            mover_row(r, f"{previous[r['team']['tla']]} &rarr; {r['position']} ({d:+d})", followed)
            for d, r in entries
        )

    risers = [m for m in moves if m[0] > 0][:n]
    fallers = [m for m in moves if m[0] < 0][-n:]
    empty = '<div class="mover-row"><span class="note">Nobody moved.</span></div>'
    return {
        "up": side(risers) or empty,
        "down": side(reversed(fallers)) or empty,
        "up_heading": "&uarr; Climbing",
        "down_heading": "&darr; Sliding",
        "tag": "Since last edition",
        "note": "Places gained or lost against the previous edition's table.",
    }


def render_scorer_list(scorers, stat_key, followed, n=5):
    ranked = sorted(scorers, key=lambda s: s.get(stat_key) or 0, reverse=True)[:n]
    out = []
    for i, s in enumerate(ranked, 1):
        tla = s["team"]["tla"]
        cls = " followed" if tla in followed else ""
        out.append(
            f'<div class="stat-row{cls}"><span>{i}. {chip(tla)} {s["player"]["name"]}</span>'
            f'<span class="note">{s.get(stat_key) or 0}</span></div>'
        )
    return "".join(out)


def render_hero(hero):
    return f'<p class="headline">{hero["headline"]}</p>{hero["body"]}'


def render_club_news(items):
    blocks = []
    for item in items:
        blocks.append(f"""
    <div class="club-block">
      <h3>{chip(item['tla'])} {item['name']}</h3>
      <p>{item['text']}</p>
    </div>""")
    return "".join(blocks)


def render_transfer_wire(wire):
    if not wire["items"]:
        return '<p style="margin:0; color: var(--text-secondary);">Quiet week on the wire. Nothing worth reporting.</p>'
    items = []
    for item in wire["items"]:
        items.append(f"""
    <div class="wire-item">
      <div><strong>{item['headline']}</strong><p>{item['text']}</p></div>
      <span class="grade {item['grade']}">{item['grade'].capitalize()}</span>
    </div>""")
    return "".join(items)


def render_fixture(m, for_team_tla):
    home, away = m["homeTeam"]["tla"], m["awayTeam"]["tla"]
    venue = "H" if home == for_team_tla else "A"
    opp = away if home == for_team_tla else home
    opp_name = m["awayTeam"]["shortName"] if home == for_team_tla else m["homeTeam"]["shortName"]
    comp = m["competition"]["name"]
    return f"""
    <div class="stat-card fixture-card">
      <div class="stat-label">{comp} &middot; {venue}</div>
      <div class="stat-value">{chip(opp)} {opp_name}</div>
      <div class="fixture-time">{fmt_kickoff(m['utcDate'])}</div>
    </div>"""


def build_html(token, data, content):
    followed = {"ARS", "MUN"}
    table_html = render_table(data["table"], followed)

    history = load_history()
    movers = render_movers(
        data["full_table"], followed, previous_positions(history, content["build_date"])
    )
    record_positions(history, content["build_date"], data["full_table"])

    build_date_obj = datetime.date.fromisoformat(content["build_date"])
    fpl_data = ffpl.build()
    matchday = fpl_data["gameweek"]
    # Cross-check FPL's current matchday against openfootball as of the run
    # date, not the edition's build date -- both sources answer "what's the
    # matchday now", and the build date can be days old.
    today = datetime.date.today()
    cross_check = fof.current_matchday(today)
    if cross_check is not None and cross_check != matchday:
        print(
            f"MISMATCH matchday: FPL={matchday} openfootball={cross_check} "
            f"as of {today} -- using FPL, flag for review",
            file=sys.stderr,
        )
    elif cross_check is None:
        print(
            f"warning: could not cross-check matchday against openfootball as of {today}",
            file=sys.stderr,
        )

    top_scorers_html = render_scorer_list(fpl_data["scorers"], "goals", followed)
    top_assists_html = render_scorer_list(fpl_data["scorers"], "assists", followed)

    ars_next = fd.next_fixtures(token, fd.ARSENAL_ID, n=2)
    mun_next = fd.next_fixtures(token, fd.MAN_UTD_ID, n=2)
    next_up_html = "".join(
        render_fixture(m, "ARS") for m in ars_next
    ) + "".join(
        render_fixture(m, "MUN") for m in mun_next
    )

    build_date = build_date_obj.strftime("%-d %B %Y")

    return TEMPLATE.format(
        matchday=matchday,
        build_date=build_date,
        hero=render_hero(content["hero"]),
        schedule_heading=content["schedule"]["heading"],
        schedule_icon=content["schedule"]["icon"],
        schedule_text=content["schedule"]["text"],
        table_rows=table_html,
        top_scorers=top_scorers_html,
        top_assists=top_assists_html,
        movers_up=movers["up"],
        movers_down=movers["down"],
        movers_up_heading=movers["up_heading"],
        movers_down_heading=movers["down_heading"],
        movers_tag=movers["tag"],
        movers_note=movers["note"],
        club_news=render_club_news(content["club_news"]),
        window_note=content["transfer"]["window_note"],
        transfer_wire=render_transfer_wire(content["transfer"]),
        divbox_heading=content["divbox"]["heading"],
        divbox_html=content["divbox"]["html"],
        next_up=next_up_html,
    )


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pitch Notes — Matchday {matchday}</title>
<link rel="icon" type="image/svg+xml" href="/premier-league/assets/favicon.svg">
<link rel="stylesheet" href="/premier-league/assets/css/styles.css">
</head>
<body>
<div class="wrap">

  <header class="masthead">
    <p class="kicker">Matchday {matchday} &middot; Premier League 2026/27</p>
    <h1>PITCH NOTES<span>.</span></h1>
    <div class="meta">
      <span>{build_date}</span>
      <span>&middot;</span>
      <span>Following <strong>Arsenal</strong> &amp; <strong>Man United</strong></span>
      <span>&middot;</span>
      <a class="archive-link" href="archive/">Archive</a>
    </div>
  </header>

  <section class="hero card">
    {hero}
  </section>

  <div class="sec-head"><h2>{schedule_heading}</h2><span class="tag">Schedule Watch</span></div>
  <div class="card schedule-note">
    <span class="icon">{schedule_icon}</span>
    <p style="margin:0; color: var(--text-secondary);">{schedule_text}</p>
  </div>

  <div class="sec-head"><h2>Top six, plus the ones we actually care about</h2><span class="tag">The Table</span></div>
  <table>
    <thead><tr><th>Pos</th><th>Club</th><th>P</th><th>W-D-L</th><th>GD</th><th>Pts</th></tr></thead>
    <tbody>{table_rows}
    </tbody>
  </table>

  <div class="sec-head"><h2>Who's doing the business</h2><span class="tag">Golden Boot Watch</span></div>
  <div class="stats-grid">
    <div class="stat-col">
      <h3>Top scorers</h3>
      {top_scorers}
    </div>
    <div class="stat-col">
      <h3>Top assists</h3>
      {top_assists}
    </div>
  </div>
  <p class="movers-note">Every player carries a real goals/assists count via the Fantasy Premier League API, so a pure creator with zero goals still shows up in the assists list.</p>

  <div class="sec-head"><h2>Early Risers &amp; Strugglers</h2><span class="tag">{movers_tag}</span></div>
  <div class="movers-grid">
    <div class="mover-col up">
      <h3>{movers_up_heading}</h3>
      {movers_up}
    </div>
    <div class="mover-col down">
      <h3>{movers_down_heading}</h3>
      {movers_down}
    </div>
  </div>
  <p class="movers-note">{movers_note} Arsenal and Man United only show up here when they're actually among the biggest movers. Otherwise, check The Table above for where they sit.</p>

  <div class="sec-head"><h2>Arsenal &amp; Man United</h2><span class="tag">Club News</span></div>
  <div class="card club-news">{club_news}
  </div>

  <div class="sec-head"><h2>The rumour mill</h2><span class="tag">Transfer Wire</span></div>
  <p class="window-note">{window_note}</p>
  <div class="card">{transfer_wire}
  </div>

  <div class="sec-head"><h2>{divbox_heading}</h2><span class="tag">Divbox 101</span></div>
  <div class="card divbox101">{divbox_html}
  </div>

  <div class="sec-head"><h2>What's coming</h2><span class="tag">Next Up</span></div>
  <div class="next-up-grid">{next_up}
  </div>

  <div class="sec-head"><h2>Who the bookies fancy</h2><span class="tag">The Odds</span></div>
  <div class="card" id="odds-card">
    <p style="margin:0; color: var(--text-muted); font-size: var(--text-sm);">Loading odds&hellip;</p>
  </div>
  <p class="odds-note">Bookmaker average, refreshed a few times a day. Not live, so lines will have moved by kickoff, and it's for fun, not financial advice. <a href="https://www.begambleaware.org" target="_blank" rel="noopener">BeGambleAware.org</a></p>
  <script>
  (function() {{
    var el = document.getElementById('odds-card');
    fetch('odds.json').then(function(r) {{
      if (!r.ok) throw new Error('no odds file');
      return r.json();
    }}).then(function(data) {{
      var order = ['ARS', 'MUN'];
      var html = '';
      order.forEach(function(tla) {{
        var d = data[tla];
        if (!d) return;
        var prices = Object.keys(d.odds).map(function(name) {{
          return name + ' ' + d.odds[name].toFixed(2);
        }}).join(' &middot; ');
        html += '<div class="odds-row"><div class="odds-match">' +
          d.home_team + ' vs ' + d.away_team + '</div><div class="odds-prices">' +
          prices + '</div></div>';
      }});
      el.innerHTML = html || '<p style="margin:0; color: var(--text-muted); font-size: var(--text-sm);">No odds available this week.</p>';
    }}).catch(function() {{
      el.innerHTML = '<p style="margin:0; color: var(--text-muted); font-size: var(--text-sm);">Odds unavailable right now.</p>';
    }});
  }})();
  </script>

  <footer>
    Built {build_date}. Standings and fixtures via football-data.org (free tier, delayed); matchday number and Golden Boot Watch via the Fantasy Premier League API, cross-checked against openfootball. Everything else is Divbox's own reporting and paraphrasing of public sources.
  </footer>

</div>
</body>
</html>
"""

def demo():
    """Self-check the parser, the ranking/highlight logic, and the stale-edition guard."""
    # a nested <div> inside a block used to truncate it silently
    nested = (
        '<section data-slot="divbox" data-heading="Nested">'
        '<p>before</p><div class="x"><p>inside</p></div><p>after &amp; done</p>'
        "</section>"
    )
    blocks = parse_blocks(nested)
    assert len(blocks) == 1, "expected exactly one block"
    slot, attrs, inner = blocks[0]
    assert slot == "divbox" and attrs["heading"] == "Nested"
    assert "after &amp; done" in inner, "content after a nested element must survive"
    assert inner.count("<div") == 1 and inner.count("</div>") == 1, "nested markup must round-trip"

    # movers: real position change when there's a previous edition, form when there isn't
    fake_table = [
        {"position": i, "team": {"tla": tla, "shortName": tla}, "won": 0, "draw": 0, "lost": 0}
        for i, tla in enumerate(["MCI", "ARS", "BHA", "BRE", "EVE", "LEE", "MUN", "FUL"], 1)
    ]
    first = render_movers(fake_table, {"ARS", "MUN"}, previous=None)
    assert "No previous edition" in first["note"], "first edition must say it's form, not movement"
    assert "Best start" in first["up_heading"]

    # MUN was 2nd and is now 7th (-5); BHA was 8th and is now 3rd (+5)
    prev = {"MCI": 1, "MUN": 2, "ARS": 3, "BRE": 4, "EVE": 5, "LEE": 6, "FUL": 7, "BHA": 8}
    moved = render_movers(fake_table, {"ARS", "MUN"}, previous=prev)
    assert "Since last edition" == moved["tag"]
    assert "8 &rarr; 3 (+5)" in moved["up"], "biggest riser should lead the up column"
    assert "2 &rarr; 7 (-5)" in moved["down"], "biggest faller should lead the down column"
    assert moved["up"].index("BHA") < moved["up"].index("ARS"), "risers sort by size of gain"
    assert 'class="followed"' in moved["down"], "followed clubs stay highlighted"

    # a rebuild of the same date must not produce a move against itself
    hist = {"2026-09-19": {r["team"]["tla"]: r["position"] for r in fake_table}}
    assert previous_positions(hist, "2026-09-19") is None, "same-date rebuild has no earlier edition"
    assert previous_positions(hist, "2026-09-26") == hist["2026-09-19"]

    fake_scorers = [
        {"player": {"name": "Striker"}, "team": {"tla": "ARS"}, "goals": 3, "assists": 1},
        {"player": {"name": "Poacher"}, "team": {"tla": "MCI"}, "goals": 7, "assists": 0},
        {"player": {"name": "Creator"}, "team": {"tla": "MUN"}, "goals": 1, "assists": 5},
    ]
    followed = {"ARS", "MUN"}
    goals_html = render_scorer_list(fake_scorers, "goals", followed, n=2)
    assert goals_html.index("Poacher") < goals_html.index("Striker"), "top scorer should rank first"
    assert 'class="stat-row followed"' in goals_html, "followed club row should be flagged"
    assists_html = render_scorer_list(fake_scorers, "assists", followed, n=2)
    assert assists_html.index("Creator") < assists_html.index("Striker"), "top assist should rank first"

    # the stale-edition guard, against a scratch manifest rather than the real one
    import tempfile

    global MANIFEST
    orig_manifest = MANIFEST
    with tempfile.TemporaryDirectory() as tmp:
        MANIFEST = os.path.join(tmp, "manifest.json")
        with open(MANIFEST, "w") as f:
            json.dump({"current_date": "2026-09-19"}, f)
        check_not_stale("2026-09-19")  # same date: rebuilding the live edition is fine
        check_not_stale("2026-09-26")  # newer date: fine
        check_not_stale("2026-09-10", force=True)  # older, but forced
        try:
            check_not_stale("2026-09-10")
        except SystemExit:
            pass
        else:
            raise AssertionError("should refuse to rebuild an edition older than the live one")
    MANIFEST = orig_manifest
    print("demo OK", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        content = load_content()
        check_not_stale(content["build_date"], force="--force" in sys.argv)
        token = fd.load_token()
        data = fd.build(token)
        out = build_html(token, data, content)
        os.makedirs(EDITIONS_DIR, exist_ok=True)
        filename = os.path.join(EDITIONS_DIR, f"pitch-notes-{content['build_date']}.html")
        with open(filename, "w") as f:
            f.write(out)
        print(f"wrote {filename}")
