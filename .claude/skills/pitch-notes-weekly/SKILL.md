---
name: pitch-notes-weekly
description: Rebuild and republish the Pitch Notes dashboard from whatever content currently lives in content.py (standings/fixtures refresh automatically from the API; Hero/Club News/Transfer Wire/Divbox 101 do not — that's pitch-notes-content's job). Use when the user asks to run, publish, or push this week's Pitch Notes update.
---

Run the mechanical pipeline for Pitch Notes: `python3 scripts/run_weekly.py` from the project root.

This does three things in order and stops at the first failure: build the HTML from `content.py` plus live standings/fixtures, promote it to `dist/`, archive the outgoing week, and rsync `dist/` to the Linode host.

## Rules

- Run the command. Do not re-implement, re-order, or "improve" the steps inline.
- If it exits non-zero: stop immediately. Show the user the exact stderr output and the relevant line(s) from `logs/pitch-notes.log`. Do not retry, do not attempt a fix, do not fall back to a different approach. Report the failure and wait for instructions.
- If it exits 0: tell the user it published and give the live URL (https://divbox.ai/premier-league/).
- Before running: check `content.py`'s `BUILD_DATE` and prose against what week it actually is. If it looks like it's still last week's content, say so and suggest running `pitch-notes-content` first rather than publishing stale news — this script has no way to detect that itself.
