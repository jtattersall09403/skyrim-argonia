<!-- imported unchanged from elder-souls-argonia docs/decisions/0079-cheap-hands-expensive-head-agent-cost-controls.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0079 — Agent policy: who does what, when to delegate, what it costs

**Status:** accepted; rewritten in place 2026-10-14 as the current policy
(owner). History is in git; the evidence is
[the 2026-10-14 review](../research/archive/agent-process-reviews/instruction-and-agent-tree-review-2026-10-14.md).

## What the bill is

Prices per million tokens (`agent_models.py`): input/output Fable 10/50 $,
Opus 4/20, Sonnet 2/10, Haiku 1/5; cache read Fable 0.25, Opus 0.20, Sonnet
0.20, Haiku 0.10; a cache write is 1.25× input at the 5-minute TTL and 2×
at the 1-hour TTL.

Measured over a fortnight of planner and subagent transcripts: cache reads
are 95 % of tokens but about 46 % of dollars, cache writes about 48 %,
output about 7 %. Opus carries 68 % of the spend. A write share near 5 % of
tokens is the normal per-turn append ratio, not churn.

The rule: everything that lands in an agent's context is paid once at write
price, then at read price on every later turn of that agent. So:

- **Keep output out of context.** A long result read once costs its write
  and then a read on every turn after it; `find`, `run` and `check` exist to
  keep that output in a short-lived child and return only the verdict.
- **Model choice scales cost linearly.** Every class (write, read, output)
  is priced per model, so the same work on Opus costs twice Sonnet and four
  times Haiku. Put each job on the cheapest tier that does it right.

A spawn costs the child's cold start (a cache write of its system prompt,
agent file and brief), the parent's brief (output), and a wake of the
parent for the report. Delegation pays when it keeps long output or many
turns out of a long-lived context, or runs beside other work. It loses when
the job is one or two steps the parent can take, or when the parent needs
the exact lines: a paraphrase that misleads costs a round of rework.
`session_tokens.py` prices every token by its model.

## The tree

- **Planner** (Fable): scopes, writes briefs, reviews plans and diffs,
  judges, and owns decisions and records. It launches lane owners directly
  and absorbs their wakes; a Fable wake costs about what an Opus wake does.
- **`place-builder`**: one place per agent, end to end, designing in the
  wb.py session.
- **`deliver`**: a large, clearly briefed packet carried to completion. It
  may split bulk output into `deliver-small` children.
- **`deliver-small`**: bounded work whose acceptance can be written before
  the cause is known: bulk edits, and diagnoses confined to the named files.
  It returns when a finding would change the brief's scope, and spawns a
  `reader` for its own text review rather than deferring it to the planner.
- **Leaf agents**: `find` (wide searches), `run` (long jobs whose verdict is
  all that matters), `check` (the batch gate and review,
  [0131](0131-one-check-gate.md)), `research` (sourcing, audits, mining),
  `reader` (checklist sweeps, independent visual judgement and the prose
  pass of text-review), `voice-reader` (one Sonnet lens on one dialogue
  batch, run as a panel) and `corpus-reader` (one long-context read of a
  whole dialogue corpus; [0139](0139-cultures-down-to-the-person-facts-once-opinions-each.md)). Root cause of a class spanning systems is a
  read-only `deliver` brief with `Mode: diagnose`.

Owner ruling 2026-10-18: dialogue writing and reviewing run on Sonnet (`dialogue-lane`, `dialogue-writer`, `voice-reader`, `corpus-reader`); Opus is overkill there.

There is no lead tier: a lead added a hop, a cold start per relaunch and a
paraphrase of intent, and saved no price on wakes.

**Model and effort live only in each agent's frontmatter.** Opus, Fable and Haiku
agents and the review gate run at low effort; Sonnet agents may run at
medium; quality comes from a plan-first
step that the planner reviews and from checks built into the tools, never
from raising effort. Hand-off marker:
Haiku at 100k context, every other agent at 300k (never the planner, 0083). Every
`deliver` and `deliver-small` brief carries an `Acceptance:` line
(`agent_guard.py` refuses the spawn without it).

## When to delegate, when not

- **The size rule.** Type a look-up yourself when its output is small
  (under roughly 1k tokens or 60 lines). Delegate to `find` or `run` when
  the raw output or the reading behind the answer is larger, because a
  result in your context is re-read on every later turn. This holds for the
  planner and workers alike; `shell_guard.py` enforces it for the planner.
- **Workers** (deliver, place-builder, research) read, search
  and run their own tests and publishes when they need the exact lines to
  decide; the size rule still sends a bulky trawl to `find`.
- **Images**: a designer looks at its own design-loop renders.
  `reader` takes the checklist sweeps and independent judgement such
  as a blind feel check. The planner never ingests images.
- **Batch**: several questions in one area are one agent. Two or more leaf
  agents with nothing to do between them run as one `Workflow` (the owner's
  standing opt-in). An agent that spawns agents launches with the Agent
  tool.
- **Waiting**: the planner (an hour's cache) ends its turn with
  `waiting: <labels>` and is woken by each child's report; it never polls.
  A subagent's cache lives 5 minutes, and a lapse re-writes its whole
  context (about $0.75 at 150k on Opus; 502 lapses in one week): it waits
  in calls under 270 s, `job_guard.sh --wait <lane>` on a backgrounded job
  and `job_guard.sh --warm` on children, each one cache read (about $0.03).
- **Never reply to a non-actionable wake.**

## Sessions and reports

- One phase per planner session, run to its deploy; it never hands off for
  cost ([0083](0083-session-switch-advice.md)).
- Reports are written for re-reading: outcome first, each fact once,
  evidence as file:line or a number, at most 25 lines returned, and raw
  output in a file under `tooling/.reports/`.

## Enforcement

- `shell_guard.py`, `agent_guard.py` and `role_guard.py`; see
  [hooks.md](../standards/hooks.md).
- rtk filters shell output (the owner's global hook); `rtk recall <id>` gives
  the full text.
- The `cost-review` skill runs `session_tokens.py` about weekly.
- The batch code review runs once per batch through `check`
  ([0131](0131-one-check-gate.md)). The planner finds the shared cause behind
  CONFIRMED items and treats PLAUSIBLE ones as questions.
