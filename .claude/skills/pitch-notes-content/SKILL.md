---
name: pitch-notes-content
description: Research and write this week's Pitch Notes editorial content (Hero, Schedule Watch, Club News, Transfer Wire, Divbox 101) into content.html. Use when the user asks to write, research, or update this week's Pitch Notes content, before running pitch-notes-weekly.
---

Write this week's `content.html` for the Pitch Notes dashboard. This is a research-and-writing task, not a script to run — do the work directly.

## Sources

Check these first, in this order:

1. [Arsenal.com/news](https://www.arsenal.com/news) — official Arsenal
2. [ManUtd.com/news](https://www.manutd.com/en/news) — official Man Utd
3. [PremierLeague.com/news](https://www.premierleague.com/news) — official league storylines
4. [BBC Sport Football](https://www.bbc.com/sport/football) — mainstream, includes their gossip column
5. [Sky Sports Transfer Centre](https://www.skysports.com/transfer-centre) — mainstream transfer specifics
6. The Sun or Daily Star football sections — tabloid tier, for the edgier/earlier rumors

Use general web search too, especially for transfer rumors that don't have one official source. For grading a rumor's reliability: if Fabrizio Romano, David Ornstein (The Athletic), or multiple outlets corroborate it, it's at least "Likely." A single tabloid mention stays "Speculative."

## Non-negotiable: verify against the data, not the article

Before writing any sentence about a score, fixture, or standings position, check it against `scripts/fetch_data.py`'s output (run `python3 -c "import sys; sys.path.insert(0, 'scripts'); import fetch_data as fd; import json; print(json.dumps(fd.build(fd.load_token()), indent=2))"` or similar, from the project root). Search results and news articles are frequently stale on scores — never state a result or standing that contradicts the API. If something can't be verified this way and it's a schedule/score/standings claim, stop and ask rather than guessing (this is CLAUDE.md's non-negotiable rule, not a suggestion).

## Thin results are fine

If research only turns up one Club News story, or zero genuine Transfer Wire items, write with what's actually there. `content.html` takes any number of club-news and transfer blocks, including one or none. Do not pad with filler or manufacture a second story to fill space — that's worse than running one real story.

## Writing

- Follow CLAUDE.md's section rules (paraphrase news in your own words, never quote more than a short attributed phrase, grade transfer rumors, note explicitly when the transfer window is closed).
- Match `content.html`'s existing structure: one block per section tagged with `data-slot` (edition, hero, schedule, club-news, transfer-window, transfer, divbox). Prose goes in the block's inner HTML; the typed fields (build date, club TLA, rumour grade, schedule icon) are `data-*` attributes. Follow the blocks already in the file.
- Divbox 101's topic should tie to this week's actual biggest storyline, not a rule pulled from a fixed list.
- Run the finished prose through the `unslop` skill before considering it done.

## Scope

Only touch `content.html`. Never edit `build.py`'s HTML/CSS/structure as part of this skill — that's a separate concern. When done, tell the user what changed and that `pitch-notes-weekly` is the next step whenever they're ready to publish; don't run it yourself as part of this skill.
