---
name: pitch-notes-publish
description: Rebuild the Pitch Notes dashboard from whatever content currently lives in content.html and stage it in dist/, then deploy it to the live host as a separate, explicitly confirmed step (standings/fixtures refresh automatically from the API; Hero/Club News/Transfer Wire/Divbox 101 do not — that's pitch-notes-content's job). Use when the user asks to run, publish, or push a Pitch Notes update.
---

Run the mechanical pipeline for Pitch Notes. It is two commands, on purpose.

## Step 1 — build and stage (local, reversible)

`python3 scripts/run_pipeline.py` from the project root.

Builds the HTML from `content.html` plus live standings/fixtures, promotes it
to `dist/index.html`, and archives the outgoing edition. Stops at the first
failure. Nothing is live at the end of this.

## Step 2 — deploy (live, needs a go-ahead)

`python3 scripts/deploy.py` from the project root. `--dry-run` shows what would
change without touching the host.

This is the step that publishes to https://divbox.ai/premier-league/. It is
separate from step 1 so the built page can be looked at first.

## Rules

- Run the commands. Do not re-implement, re-order, or "improve" the steps inline.
- **Never run step 2 without an explicit go-ahead in the moment.** Don't infer
  yes from an ambiguous or unrelated reply, and don't carry over approval from
  an earlier deploy. If in doubt, run `--dry-run` and ask.
- If either command exits non-zero: stop immediately. Show the user the exact
  stderr output and the relevant line(s) from `logs/pitch-notes.log`. Do not
  retry, do not attempt a fix, do not fall back to a different approach. Report
  the failure and wait for instructions.
- Before step 1: check `content.html`'s build date (the `data-build-date` on the
  edition block) and prose against what date it actually is. If it looks like
  it's still the last edition's content, say so and suggest running
  `pitch-notes-content` first rather than publishing stale news.
- If the build refuses with "edition N is already live", that's the stale-date
  guard doing its job: `content.html` wasn't refreshed. Run `pitch-notes-content`
  rather than reaching for `--force`.
- After step 2 exits 0: tell the user it's live and give the URL.
