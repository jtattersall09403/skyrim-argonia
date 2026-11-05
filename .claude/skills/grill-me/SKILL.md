---
name: grill-me
description: Grill the owner relentlessly about a plan, decision or idea until we share one understanding, answering everything the repo already knows first and asking one question at a time. Use when the owner says "grill me", asks to stress-test a plan, or uses any 'grill' phrase.
---

Adapted from Matt Pocock's `grill-me` / `grilling` skills (github.com/mattpocock/skills, MIT).

Interview the owner relentlessly until we reach a shared understanding. Map it as a **design tree**: every
decision branches into the decisions that hang off it. The **frontier** is every decision whose prerequisites
are already settled.

## 1. The repo answers first

Finding facts is our job, never the owner's. Before each question, look for the answer in the repo:

- `docs/owner-brief.md` and `docs/inherited-rulings.md`: rulings the owner has already made.
- `docs/decisions/README.md` and the decision records it indexes.
- `docs/research/`, `story/` (its README), other READMEs, and owner issues and replies (`tooling/owner_inbox.py`, `gh issue`).

For a wide sweep, dispatch a `find` or `research` agent with a fresh context and keep only its conclusion;
don't block on it: ask questions it can't affect while it runs. Then:

- If the repo settles a branch, mark it settled, cite the file (and line), and don't ask.
- If the repo gives a likely answer but it may be stale or ambiguous, ask as a confirmation, quoting the source.
- Ask only what is genuinely the owner's call: taste, priority, scope, cost, or a ruling nothing records.

## 2. One question at a time

Ask exactly **one** question per message, then stop and wait for the owner's answer. Never batch questions,
never ask a question whose answer depends on one still open. Pick the frontier question that unblocks the most.

```
❓ **<question title>**: <the question, with the choices if any, and what the repo already says (file:line)>

➡️ <your recommended answer and why, in a line or two>
```

Word the question so "yes" accepts your recommendation. Plain English, no jargon the owner must decode.

Each answer reshapes the tree: settled decisions push the frontier outward. Recompute it, check the repo
again for anything the answer newly makes findable, then ask the next single question.

## 3. Finish

The session is done when the frontier is empty: every branch visited, nothing silently assumed. Give a short
summary of what was settled (by the owner, or by the repo with its source) and ask the owner to confirm.
Do not act on it until they confirm. Once confirmed, record each ruling in `docs/owner-brief.md` and the
decision it belongs to, per CLAUDE.md.
