"""Build the weekly Pitch Notes HTML dashboard.

Pulls live data via fetch_data.py, bakes it together with this week's
hand-written editorial content (Hero, Club News, Transfer Wire, Divbox 101),
and writes a self-contained HTML file.

Usage: python3 build.py
"""
import datetime
import os
import re
import sys
import fetch_data as fd
import fetch_fpl as ffpl
import fetch_openfootball as fof

WEEKLIES_DIR = "weeklies"
CONTENT_PATH = os.path.join(os.path.dirname(__file__), "content.html")

# Editorial content lives in content.html as prose + data-* attributes, not in
# a .py file: a typo there can't break this build script. Each block is one
# flat top-level element tagged with data-slot; prose is its inner HTML, typed
# fields are its data-* attributes.
_BLOCK_RE = re.compile(
    r'<(section|article|div)\b([^>]*)\bdata-slot="([^"]+)"([^>]*)>(.*?)</\1>',
    re.DOTALL,
)
_ATTR_RE = re.compile(r'data-([\w-]+)="([^"]*)"')


def load_content(path=CONTENT_PATH):
    with open(path) as f:
        raw = f.read()
    content = {"club_news": [], "transfer": {"window_note": "", "items": []}}
    for tag, pre, slot, post, inner in _BLOCK_RE.findall(raw):
        attrs = dict(_ATTR_RE.findall(pre + post))
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


def render_movers(full_table, followed, n=4):
    def row(r):
        tla = r["team"]["tla"]
        note = f"{r['won']}W-{r['draw']}D-{r['lost']}L"
        cls = " class=\"followed\"" if tla in followed else ""
        return f'<div class="mover-row{cls}"><span>{chip(tla)} {r["team"]["shortName"]}</span><span class="note">{note}</span></div>'
    top_html = "".join(row(r) for r in full_table[:n])
    bottom_html = "".join(row(r) for r in full_table[-n:])
    return top_html, bottom_html


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


def build_html(data, content):
    followed = {"ARS", "MUN"}
    table_html = render_table(data["table"], followed)
    movers_up, movers_down = render_movers(data["full_table"], followed)

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

    ars_next = fd.next_fixtures(TOKEN, fd.ARSENAL_ID, n=2)
    mun_next = fd.next_fixtures(TOKEN, fd.MAN_UTD_ID, n=2)
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
        movers_up=movers_up,
        movers_down=movers_down,
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
<style>
@import url('https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;700;800&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {{
  --font-display: 'Big Shoulders Display', system-ui, sans-serif;
  --font-serif:   'Source Serif 4', Georgia, serif;
  --font-mono:    'IBM Plex Mono', 'Courier New', monospace;

  --color-accent:        #ef0107;
  --color-accent-bg:     #2a0a08;
  --color-accent-text:   #ff4d43;
  --color-gold:          #d4a94e;

  --surface-page:        #060d18;
  --surface-card:        #0a1628;
  --surface-subtle:      #101f36;

  --text-primary:        #f1ede2;
  --text-secondary:      #b8b2a3;
  --text-muted:          #7a7568;

  --border:              #1c2d47;
  --border-strong:       #2a3f5c;

  --color-success:       #16a34a;
  --color-success-bg:    #0d2618;
  --color-success-text:  #4ade80;

  --color-warning:       #ea580c;
  --color-warning-bg:    #2b1608;
  --color-warning-text:  #fb923c;

  --color-danger:        #dc2626;
  --color-danger-bg:     #2a0d0d;
  --color-danger-text:   #f87171;

  --text-xs:   11px;
  --text-sm:   13px;
  --text-base: 16px;
  --text-lg:   18px;
  --text-xl:   22px;

  --radius:    8px;
  --radius-lg: 12px;
}}

* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--surface-page);
  color: var(--text-primary);
  font-family: var(--font-serif);
  font-size: var(--text-base);
  line-height: 1.55;
}}
.wrap {{ max-width: 960px; margin: 0 auto; padding: 24px 20px 60px; }}

.masthead {{ padding: 8px 0 24px; border-bottom: 3px solid var(--color-accent); margin-bottom: 32px; }}
.masthead .kicker {{ font-family: var(--font-mono); font-size: var(--text-xs); color: var(--color-gold); letter-spacing: 0.1em; text-transform: uppercase; margin: 0 0 10px; }}
.masthead h1 {{ font-family: var(--font-display); font-weight: 800; font-size: clamp(38px, 9vw, 56px); line-height: 0.95; margin: 0 0 12px; letter-spacing: 0.01em; }}
.masthead h1 span {{ color: var(--color-accent); }}
.masthead .meta {{ display: flex; flex-wrap: wrap; gap: 6px 16px; font-family: var(--font-mono); font-size: var(--text-sm); color: var(--text-secondary); }}
.masthead .meta strong {{ color: var(--text-primary); font-weight: 600; }}
.masthead .archive-link {{ color: var(--color-accent-text); text-decoration: none; }}
.masthead .archive-link:hover {{ text-decoration: underline; }}

.sec-head {{ display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin: 40px 0 14px; border-bottom: 1px solid var(--border); padding-bottom: 10px; }}
.sec-head .tag {{ font-family: var(--font-mono); font-size: var(--text-xs); font-weight: 500; color: var(--color-accent); letter-spacing: 0.06em; text-transform: uppercase; white-space: nowrap; }}
.sec-head h2 {{ font-family: var(--font-display); font-weight: 700; font-size: var(--text-xl); margin: 0; color: var(--text-primary); }}

.card {{ background: var(--surface-card); border: 0.5px solid var(--border); border-radius: var(--radius-lg); padding: 18px 20px; }}

.hero {{ border-left: 4px solid var(--color-accent); }}
.hero .headline {{ font-family: var(--font-display); font-weight: 700; font-size: 22px; margin: 0 0 8px; }}
.hero p {{ margin: 0 0 8px; color: var(--text-secondary); }}
.hero p:last-child {{ margin-bottom: 0; }}

.schedule-note {{ display: flex; gap: 12px; align-items: flex-start; }}
.schedule-note .icon {{ font-family: var(--font-mono); color: var(--color-warning-text); background: var(--color-warning-bg); border-radius: 4px; padding: 2px 6px; font-size: var(--text-xs); flex-shrink: 0; }}

table {{ width: 100%; border-collapse: collapse; font-family: var(--font-mono); font-size: var(--text-sm); font-variant-numeric: tabular-nums; }}
thead th {{ text-align: left; color: var(--text-muted); font-weight: 500; font-size: var(--text-xs); text-transform: uppercase; letter-spacing: 0.05em; padding: 0 8px 8px; border-bottom: 1px solid var(--border-strong); }}
tbody td {{ padding: 9px 8px; border-bottom: 0.5px solid var(--border); }}
tbody tr.followed {{ background: var(--surface-subtle); }}
tbody tr.followed td:first-child {{ box-shadow: inset 3px 0 0 var(--color-accent); }}
.chip {{ display: inline-block; font-family: var(--font-mono); font-size: 10px; font-weight: 500; padding: 2px 5px; border-radius: 4px; margin-right: 4px; }}

.stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
.stat-col {{ background: var(--surface-card); border: 0.5px solid var(--border); border-radius: var(--radius-lg); padding: 16px 18px 6px; }}
.stat-col h3 {{ font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.06em; text-transform: uppercase; margin: 0 0 12px; color: var(--color-gold); }}
.stat-row {{ display: flex; justify-content: space-between; align-items: baseline; padding: 8px 0; border-top: 0.5px solid var(--border); font-size: var(--text-sm); }}
.stat-row:first-of-type {{ border-top: none; }}
.stat-row.followed {{ box-shadow: inset 3px 0 0 var(--color-accent); padding-left: 6px; }}
.stat-row .note {{ font-family: var(--font-mono); font-size: var(--text-xs); color: var(--text-muted); font-variant-numeric: tabular-nums; }}
@media (max-width: 480px) {{ .stats-grid {{ grid-template-columns: 1fr; }} }}

.movers-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
.mover-col {{ background: var(--surface-card); border: 0.5px solid var(--border); border-radius: var(--radius-lg); padding: 16px 18px 6px; }}
.mover-col h3 {{ font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.06em; text-transform: uppercase; margin: 0 0 12px; }}
.mover-col.up h3 {{ color: var(--color-success-text); }}
.mover-col.down h3 {{ color: var(--color-danger-text); }}
.mover-row {{ display: flex; justify-content: space-between; align-items: baseline; padding: 8px 0; border-top: 0.5px solid var(--border); font-size: var(--text-sm); }}
.mover-row:first-of-type {{ border-top: none; }}
.mover-row.followed {{ box-shadow: inset 3px 0 0 var(--color-accent); padding-left: 6px; }}
.mover-row .note {{ font-family: var(--font-mono); font-size: var(--text-xs); color: var(--text-muted); }}
.movers-note {{ color: var(--text-secondary); font-size: var(--text-sm); margin-top: 12px; }}
@media (max-width: 480px) {{ .movers-grid {{ grid-template-columns: 1fr; }} }}

.club-news h3 {{ font-family: var(--font-display); font-size: var(--text-lg); margin: 0 0 6px; }}
.club-news p {{ color: var(--text-secondary); margin: 0 0 14px; }}
.club-news .club-block:last-child p {{ margin-bottom: 0; }}

.wire-item {{ display: flex; justify-content: space-between; gap: 12px; padding: 12px 0; border-bottom: 0.5px solid var(--border); }}
.wire-item:last-child {{ border-bottom: none; padding-bottom: 0; }}
.wire-item p {{ margin: 4px 0 0; color: var(--text-secondary); font-size: var(--text-sm); }}
.grade {{ font-family: var(--font-mono); font-size: var(--text-xs); font-weight: 500; padding: 2px 8px; border-radius: 4px; white-space: nowrap; height: fit-content; }}
.grade.speculative {{ color: var(--text-muted); border: 1px solid var(--border-strong); }}
.grade.likely {{ color: var(--color-warning-text); background: var(--color-warning-bg); }}
.grade.confirmed {{ color: var(--color-success-text); background: var(--color-success-bg); }}
.window-note {{ font-family: var(--font-mono); font-size: var(--text-xs); color: var(--text-muted); margin: 0 0 16px; }}

.divbox101 p {{ color: var(--text-secondary); }}
.divbox101 ul {{ color: var(--text-secondary); padding-left: 20px; }}

.next-up-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
.stat-card {{ background: var(--surface-card); border: 0.5px solid var(--border); border-radius: var(--radius); padding: 0.75rem 1rem; }}
.stat-label {{ font-size: var(--text-xs); color: var(--text-muted); font-weight: 500; margin-bottom: 4px; font-family: var(--font-mono); }}
.stat-value {{ font-size: var(--text-base); font-weight: 500; color: var(--text-primary); }}
.fixture-time {{ font-family: var(--font-mono); font-size: var(--text-xs); color: var(--text-secondary); margin-top: 4px; }}

.odds-row {{ padding: 10px 0; border-top: 0.5px solid var(--border); }}
.odds-row:first-child {{ border-top: none; padding-top: 0; }}
.odds-match {{ font-size: var(--text-sm); color: var(--text-primary); margin-bottom: 4px; }}
.odds-prices {{ font-family: var(--font-mono); font-size: var(--text-sm); color: var(--text-secondary); font-variant-numeric: tabular-nums; }}
.odds-note {{ font-size: var(--text-xs); color: var(--text-muted); margin: 10px 0 0; }}
.odds-note a {{ color: var(--text-muted); }}

footer {{ margin-top: 48px; padding-top: 16px; border-top: 1px solid var(--border); font-family: var(--font-mono); font-size: var(--text-xs); color: var(--text-muted); }}

@media (max-width: 480px) {{
  .next-up-grid {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<div class="wrap">

  <header class="masthead">
    <p class="kicker">Matchday {matchday} &middot; Premier League 2026/27</p>
    <h1>PITCH NOTES<span>.</span></h1>
    <div class="meta">
      <span>{build_date} &middot; recap of the weekend just played</span>
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

  <div class="sec-head"><h2>Early Risers &amp; Strugglers</h2><span class="tag">Form, not rank</span></div>
  <div class="movers-grid">
    <div class="mover-col up">
      <h3>&uarr; Best start</h3>
      {movers_up}
    </div>
    <div class="mover-col down">
      <h3>&darr; Toughest start</h3>
      {movers_down}
    </div>
  </div>
  <p class="movers-note">Ranked on current record, not week-over-week movement. Arsenal and Man United only show up here when their form actually puts them in the top or bottom four. Otherwise, check The Table above for where they sit.</p>

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

TOKEN = None


def demo():
    """ponytail: self-check the ranking/highlight logic against fake scorer data."""
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
    print("demo OK", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        TOKEN = fd.load_token()
        content = load_content()
        data = fd.build(TOKEN)
        out = build_html(data, content)
        os.makedirs(WEEKLIES_DIR, exist_ok=True)
        filename = os.path.join(WEEKLIES_DIR, f"pitch-notes-{content['build_date']}.html")
        with open(filename, "w") as f:
            f.write(out)
        print(f"wrote {filename}")
