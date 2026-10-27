# 0011: Ways of working are inherited from elder-souls-argonia, lean

**Status:** decided 2026-10-27. Detail in [ways-of-working.md](../ways-of-working.md).

## Context

The old project developed a strong agent doctrine (decisions 0079, 0083, 0106, 0118, 0131, 0154, 0155, 0156
there) and also suffered from its excess: 950-turn sessions, a planner exploring with bash, hundreds of
sleeps, twelve filming passes that found almost nothing ("we build the game, not the tools"), a gate that kept
growing, rule accretion in CLAUDE.md producing contradictory rules agents resolved by coin flip, a swarm of
~34 agents on one city.

## Decision

1. **Carry over the doctrine:** cheap hands and an expensive head (model per agent in frontmatter, lowest tier
   that does the job, reports to disk with a short return); one deliverable per context with a hand-off note;
   every build brief has Lane, Paths, Acceptance (a runnable command or a measured number) and a report path;
   the testing ladder (cheapest sufficient level, compose once); one gate; decision records for the why;
   PROGRESS rows; fix forward; owner check-ins in plain English.
2. **Start lean.** P0 copies the *ideas* and only the few tools that pay for themselves at once (brief
   template, shell guard against sleeps/polls and destructive git, job guard for long jobs, the no-assets
   guard, session token report, owner inbox). Every further hook or gate is added only after a measured
   incident it would have prevented, with a test that makes it fail on purpose. CLAUDE.md stays under a word
   budget enforced by a test.
3. **No swarms on one artefact.** One builder per place, per plugin module, per UI view at a time.
4. **No test tooling for its own sake.** A harness feature is built only when a gameplay check needs it next.
5. **Owner time is the scarcest resource.** Nothing measurable goes to the owner; the owner plays packets and
   rules on hard-to-reverse calls.
