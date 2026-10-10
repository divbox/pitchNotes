# PITCH NOTES CONSTRAINTS

## 🚨 MANDATORY EXECUTION CONSTRAINTS (STOP & ASK)
- **Bugs & Failures:** Never execute a bug fix or attempt to bypass a script failure autonomously. Report the error/bug clearly and wait for instructions.
- **Surgical Changes:** Touch only the exact code required. Do not refactor adjacent code or format untouched lines. Remove dead code in the code you're changing. Flag dead code elsewhere; don't remove it on the side.
- **Strict Compliance:** Do not invent data, filler text, or API structures. If data is missing or mismatched, log it and ask.
- **Minimal Code:** Minimum code that solves the problem. Nothing speculative. No abstractions for single-use code, no "flexibility" that wasn't requested. If a bigger change seems warranted, name it and ask — don't just include it. Current work isn't production/consumer-facing — don't over-engineer edge cases.
- **Prose Quality:** You must invoke your `unslop` skill/routine for ALL user-facing content (README, project docs, web content, shared markdown) to eliminate AI jargon.
- **Worth It First:** This is a private app with one viewer, not production. The first line of every proposal (fix, feature, doc change, backlog item) answers "Worth it for a one-viewer app? Yes/no, because…". If the answer is no, say "drop it" in one line and stop. Generic best practice (security hardening, privacy scrubs of things nobody sees, docs polish) is not a reason on its own.

## 📋 CONTEXT ROUTING
Do not guess the architecture, data rules, section orders, or deployment commands. You must read the source of truth files before acting:
- **For Visual Design, Themes, and Stylesheets:** Read `DESIGN.md`.
- **For APIs, Data Rules, Pipelines, and Section Orders:** Read `PROJECT.md`.
