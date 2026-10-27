# Ways of working

How the planner and its agents build Argonia. Inherited from elder-souls-argonia's doctrine, kept lean
([decision 0011](decisions/0011-ways-of-working-are-inherited-lean.md)).

## 1. Roles

- **The owner** decides the vision, rules on hard-to-reverse calls (the open calls in
  [decisions/README.md](decisions/README.md)), plays packets, and reports what feels wrong. The owner never
  checks anything an agent can measure.
- **The planner** (the main Claude Code session, Opus) plans, briefs, judges results and talks to the owner.
  It reads plans, decisions and reports, not code dumps or images; it delegates looking-around to `find`, long
  jobs to `run`, judgement of images and prose to `reader`.
- **Agents** (in `.claude/agents/`, model and effort set only in their frontmatter): `deliver` (Opus, builds a
  packet from a brief), `deliver-small` (Sonnet, a bounded change with a quick acceptance), `world-builder`
  (from P3), `find`, `run`, `check` (Haiku), `research`, `reader` (Sonnet), the dialogue agents (Sonnet).

## 2. Briefs

Every build brief is written with `tooling/brief_template.py --write` and has: **Lane** (id), **Paths** (what
the lane owns; others avoid them), **Acceptance** (a runnable command or a measured number, never "looks
good"), **Report path**, **Test level** (the lowest sufficient), the **reuse route** chosen (decision 0010)
with why higher routes were not enough, and **Prior art** (decision 0020: which universal-modder field notes and
skills, mod sources and open reimplementations were searched and what was reused). One deliverable per context; at the context marker (**300k tokens of
context; 100k for Haiku agents**) an agent commits what is green and writes a hand-off note (done, commits, next
steps with file:line, reds). A lane whose diff passes **1,500 changed lines** runs one code review (a `reader` or
`deliver` in review mode) over its commits before reporting.

Agents return at most 25 lines (outcome, changes, measurements, failures, recommendations); the full report
goes to the report path.

## 3. Testing levels (cheapest sufficient level wins; compose once)

| Level | What | Where | Example |
|---|---|---|---|
| L1 | Data and records: schemas, integrity, generated-record checks, Spriggit round trip, direction validator | build VM | every NPC has a home cell |
| L2 | Unit: Python tools, the pure C++ core (formulas, timing windows, condition evaluator) | build VM | stamina formula; parry window maths |
| L3 | UI harness: PrismaUI views in headless Chrome against mock JSON; screenshots | build VM | dialogue view shows hyperlinks |
| L4 | In game, scripted through ArgoniaBridge on the GPU box: state reads, event timestamps, screenshots | GPU box | roll i-frames within ±1 frame |
| L5 | Recorded clip for a feel judgement by reader agents; **only with a stated reason** a lower level cannot answer | GPU box | hit feel vs DSR footage |
| L6 | The owner plays a packet through the stream | owner | slice playthrough |

Rules (old 0149/0155/0156 and universal-modder's oracle rules): test the shipped path (no debug mode stands in
for a game action); the running game is the oracle for behaviour; prove the screenshot oracle is live (two
frames differ); stop after 3 identical failures and diagnose; never let the thing under test own the test; a
crash is a failure, never "still running"; a check that cannot change a decision is not run.

GPU-box time is the bottleneck: batch L4 checks per lane, start the box once per batch, stop it after. **Only
one lane drives the game at a time** (universal-modder's one-game-worker rule): `job_guard.sh --gpu` takes a lock
on the GPU box; other lanes queue. Each port (combat, climbing, boats, dialogue) keeps a journal file
`docs/research/journals/<port>.md` (universal-modder's MODLOG): what was tried, measured and learned, so nothing
is lost at a context hand-off.

## 4. The gate

`make check` (≤ 3 minutes, one command, every red in one summary) is the only gate; CI runs the same command.
It contains the no-assets guard, lint and unit tests, UI harness tests, schema/integrity checks, Spriggit round
trip, regenerate-twice-no-diff, the immersion coverage check (from P7), link checks and the CLAUDE.md word
budget. A new check earns its place by catching a real defect, and is made to fail on purpose once. Stale
generated data is the commonest red: regenerate, never hand-edit generated files.

## 5. Owner check-ins

`tooling/owner_inbox.py --post` opens a GitHub issue labelled `owner-check-in`: plain English, one check per
bullet, what to try and where (a save on the GPU box, a start link), how to reply (comment on the issue; the
owner may also reply in a Claude chat), the open owner calls, and the week's costs (AWS month-to-date, Claude
usage). Nothing measurable is sent to the owner.

**Blocker vs polish** (old rule): a blocker is something the player cannot do (stuck, falls through, crash,
lost save, unreachable control) or sees at the normal play camera in normal play (floating, a limb through a
wall, a visible pop, a Nordic element). Everything else is polish: one quick fix, then the backlog
(`docs/phases/backlog.md`, created in P0-WP0.1), never a relaunch.

**The repo is public, so check-in issues are too.** Issues carry no secrets, no start links, no stream URLs, no IP
addresses and no Lambda or console links; those reach the owner privately (a secret gist via `gh gist create` without
`--public`, referred to in the issue only by its title, which the owner finds in their own gist list; or the
owner's AWS console). Costs may be summarised.

## 6. Cost controls (old 0079, 0083, 0118)

- Cheapest model that does the job; the planner on Opus; looking around on Haiku; prose and dialogue on Sonnet.
- Keep output out of long-lived contexts: reports to disk, short returns, `find` for trawls, `run` for long
  jobs' verdicts.
- No `sleep`, no polling loops (the shell guard refuses them); long jobs run under `job_guard.sh` in the
  background, and waits return within 270 s so the prompt cache does not lapse (lapses were ~$0.75 each in the
  old project, 500 in one week).
- The planner never hands off for cost; parallel lanes are worth more than fresh contexts.
- Weekly `cost-review` skill run; costs in every check-in; machines stop when idle.

## 7. Git

Work on `main` with small commits (`git commit -- <paths>`, never an empty pathspec); every commit passes the
pre-commit no-assets guard; the planner pushes after a green gate. Commit messages end with the attribution
lines Claude Code is configured to add. Never rewrite pushed history.

## 8. Docs

The repo holds the current state, git the history: rewrite in place, delete the superseded, no `v1`/`legacy`
twins. Decisions hold the why; phase files hold the work; PROGRESS holds status; research holds evidence.
CLAUDE.md holds only binding one-line rules under its word budget.

## 9. Lessons from the old project to keep in mind

- Swarms of agents on one artefact (34 agents on one city) cost a fortune and converge slowly: one builder per
  place or district.
- Twelve filming passes that found almost nothing: "we build the game, not the tools".
- A gate that keeps growing and re-runs on already-red heads: run only what the change can reach.
- Rules accreting in CLAUDE.md produced contradictions agents resolved by coin flip: one recipe, fixed at the
  tool or default that would have prevented the defect.
- Estimating instead of measuring (phone fps from ratios): measure on the real target, the GPU box.
- Hand-built environments get lost: every machine is rebuilt from a script in `infra/`.
