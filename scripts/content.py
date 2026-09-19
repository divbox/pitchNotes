"""This week's editorial content for Pitch Notes.

Rewritten each week by the pitch-notes-content skill (research + writing).
build.py only reads these values -- it never generates prose itself, and a
short list here (one Club News item, zero Transfer Wire items) is a normal
editorial outcome, not something build.py should treat as an error.
"""

BUILD_DATE = "2026-09-10"  # ISO date

HERO = {
    "headline": "Both clubs win in Europe",
    "paragraphs": [
        "Arsenal opened their Champions League campaign with a 1-0 win at Napoli on Wednesday, Martin Odegaard settling it with a low finish from the edge of the box after a quick one-two with substitute Christos Tzolis. It was his fourth goal in five games, and Arsenal fired 26 shots at goal, their most in a single Champions League match since 2003-04, though a tidier side would have won by more.",
        "Man United's return to the competition went even better. Goals from Matheus Cunha, Bruno Fernandes and Benjamin Sesko inside the first 45 minutes put Sabah FK away before Lisandro Martinez added a fourth after the break, a 4-0 win in Michael Carrick's first Champions League game in charge. It's over 1,000 days since United last played in this competition.",
    ],
}

SCHEDULE_WATCH = {
    "heading": "Normal service resumes this weekend",
    "icon": "PL",
    "text": "No fixture gap to explain this time. After Champions League commitments in midweek, both clubs are back to the regular Saturday/Sunday rhythm: Sunderland host Arsenal on the 12th, and Manchester United welcome Manchester City to Old Trafford on the 13th.",
}

# One entry per club with real news this week -- can be 1 or 2, not always both.
CLUB_NEWS = [
    {
        "tla": "ARS",
        "name": "Arsenal",
        "text": "A professional away win at Napoli, even if the scoreline undersold the dominance. Odegaard's strike was the difference, and Arteta's side fired more shots than in any Champions League game in over two decades. The finishing needs work before the knockout rounds matter, but three points on the road in Europe is three points on the road in Europe.",
    },
    {
        "tla": "MUN",
        "name": "Man United",
        "text": "A statement return to the Champions League. Cunha, Fernandes and Sesko did the damage inside the first half, Martinez added a fourth, and Carrick got his European bow at Old Trafford out of the way in style. Now it's straight back to league business against the club at the top of the table.",
    },
]

TRANSFER_WIRE = {
    "window_note": "Summer window closed 23:00 BST, 1 September. Everything below is January-window chatter, so treat it accordingly.",
    # Can be an empty list some weeks -- that's a quiet transfer week, not an error.
    "items": [
        {
            "headline": "Arsenal &rarr; Andria Bartishvili (unattached Georgian midfielder)",
            "text": "Fabrizio Romano reports Arsenal are set to sign the teenage midfielder, which puts this a notch above the usual January noise.",
            "grade": "likely",
        },
        {
            "headline": "Arsenal &amp; Man United &rarr; Pio Esposito (Inter Milan)",
            "text": "Both clubs are credited with interest in the Inter striker, valued at around £73m. Nothing here yet beyond shared interest, and a straight run at each other for the same player rarely resolves quickly.",
            "grade": "speculative",
        },
        {
            "headline": "Man United &rarr; Lewis Hall (Newcastle)",
            "text": "United have made an approach after failing to get him out of Newcastle before. An inquiry is a step up from pure speculation, but it's not a here-we-go yet.",
            "grade": "speculative",
        },
    ],
}

DIVBOX_101 = {
    "heading": "Why an away goal isn't worth extra anymore",
    "html": """
    <p>Older fans will remember the away goals rule: if a two-legged tie finished level on aggregate, the team that scored more goals away from home went through, sometimes even after extra time. UEFA scrapped it in 2021, reasoning that the pitch and travel disadvantages it was designed to offset had mostly disappeared.</p>
    <p>So Arsenal's 1-0 at Napoli is worth exactly what it looks like: three points and a goal, nothing more, nothing tactically encoded into it the way it would have been a few years ago. Under the current Champions League league-phase format there's no two-legged tie to speak of anyway until the knockout rounds start in 2027, so the rule wouldn't apply here regardless. Still worth knowing before someone at the pub tells you an away win in Europe "counts double."</p>
    """,
}
