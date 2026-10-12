---
name: pitch-notes-publish
description: Build the Pitch Notes dashboard from scripts/content.html and deploy it to the live host. Only the user runs this, by typing /pitch-notes-publish.
disable-model-invocation: true
---

The pipeline (build, stage, deploy) already ran when the user typed this
command. Claude did not run it and must not. This is its output:

```!
python3 scripts/run_pipeline.py
```

Do not run any command. Tell the user what the output above says, in one or
two lines. If it says deployed, give the URL: https://divbox.ai/premier-league/

If the pipeline fails, Claude Code stops before this text loads and shows the
error to the user directly. A refusal that says "edition N is already live"
means `scripts/content.html` still has an old date: run `pitch-notes-content`.
