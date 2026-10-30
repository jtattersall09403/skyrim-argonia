# Ways of working

How the planner and its agents build Argonia. Inherited from elder-souls-argonia's doctrine, kept lean
([decision 0011](decisions/0011-ways-of-working-are-inherited-lean.md)).

## 1. Roles

- **The owner** decides the vision, rules on hard-to-reverse calls (the open calls in
  [decisions/README.md](decisions/README.md)), plays packets, and reports what feels wrong. The owner never
  checks anything an agent can measure.
- **The planner** (the main Claude Code session, on whatever model the owner starts it with) plans, briefs,
  judges results and talks to the owner. It builds directly when delegation would cost more than the work
  (tooling, docs, a bounded fix) and delegates volume and parallel lanes: looking-around to `find`, long jobs to
  `run`, judgement of images and prose to `reader`, builds to `deliver` and `deliver-small`. It reads reports,
  never image dumps.
- **Agents** (in `.claude/agents/`, model and effort set only in their frontmatter): `deliver` (Opus, builds a
  packet from a brief), `deliver-small` (Sonnet, a bounded change with a quick acceptance), `world-builder`
  (from 2.W5), `find`, `run`, `check` (Haiku), `research`, `reader` (Sonnet), the writing agents
  `dialogue-writer` (Sonnet), `quest-reviewer` (Opus), `corpus-find` (Haiku).

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

## 3. Loops, the ladder and the studio (decisions 0021, 0022; full text in [loops.md](loops.md))

Work is checked by **fast focused loops with eyes**. The lane that builds a feature subset tests the subset and
its joins to what is already built in the same loop; each block at the cheapest level that reliably proves it,
composed once:

| Level | What | Where | Example |
|---|---|---|---|
| L1 data | schemas, integrity, generated-record checks, Spriggit round trip, direction validator, CK load log | build VM | every NPC has a home cell |
| L2 logic | unit tests of the rules and tools | build VM | a formula over five builds; a condition evaluator case |
| L3 still (off-game) | PrismaUI views in headless Chrome against mock JSON; readers on stills | build VM | dialogue view shows hyperlinks at every viewport |
| L4 in game, from a scene | a scene applied on the base save; the journey runner's state reads, event timestamps and a still per step; fixed-vantage stills read by readers | game machine | roll i-frames within ±1 frame; a place's vantage stills |
| L5 short clip | a 3–8 s clip (or side by side with DSR), read frame by frame, **only with a stated reason** | GPU box | a transition's feel |
| L6 owner | the owner plays from a scene (Parts 0–2) or the real game (Parts 3–4) through the stream | owner | the slice playthrough |

**The studio** (0022) is the dev profile of the real game booted into any place from the base save by a scene
(a console batch file, `bat <id>`); our dev-only bridge (`ArgoniaBridge` through `tools/bridge.py`) and the console are the hands for agents and the owner alike, and
there is no panel of ours. Every L4 check and every owner check starts there; nothing is tested through the
new-game flow. **Journeys read state and keep stills** (0021 §3): one script, one runner, state and events decide,
a still per step as evidence, teleport between short steps, no agent playing by looking.

Rules (old 0149/0155/0156 and universal-modder's oracle rules): test the shipped path (no debug mode stands in
for a game action); the running game is the oracle for behaviour; prove the screenshot oracle is live (two
frames differ); stop after 3 identical failures and diagnose; never let the thing under test own the test; a
crash is a failure, never "still running"; a check that cannot change a decision is not run.

Game-machine time is the bottleneck: batch L4 checks per lane, start the machine once per batch, stop it after. **One
lane per game machine** (universal-modder's one-game-worker rule): `job_guard.sh --gpu[=NAME]` takes that machine's
lock; extra machines only for a substantial gain, created per job and stopped after (owner #13: up to three;
streaming stays on argonia-play, extra machines are headless; `infra/gpu-box/clone.sh`), within the quota and cost rules. Each port (combat, climbing, boats, dialogue) keeps a journal file
`docs/research/journals/<port>.md` (universal-modder's MODLOG): what was tried, measured and learned, so nothing
is lost at a context hand-off.
Game lanes `job_guard.sh reserve --gpu[=NAME] <lane>` at slot start and `release` at the end, and run jobs with `ARGONIA_LANE=<lane>`: the lock is per job, so without a slot another lane's job can take the machine between yours (a renamed DLL was left in place that way, 2026-10-30). A slot whose lane has no running job and finished its last job over 10 minutes ago yields automatically (`SLOT_IDLE`, default 600 s; `status` shows "yielding"), so coding gaps no longer block others; still release at the end of the slot, since a held slot starves other lanes' short jobs (2026-10-30, an owner-priority touch fix queued behind a 2-hour slot). Before writing a CommonLibSSE-NG call, grep the pinned source at `~/.argonia/commonlib` (v15.2.0; reclone with `git clone --depth 1 --branch v15.2.0 https://github.com/alandtse/CommonLibSSE-NG.git ~/.argonia/commonlib`) instead of guessing through remote compiles. Search the repo with `git grep` (tracked files), never `grep -r .` from the root: it walks out/ and the worktrees (GBs).

## 4. The gate

`make check` (≤ 3 minutes, one command, every red in one summary) is the only gate; CI runs the same command.
It contains the no-assets guard, lint and unit tests, UI harness tests, schema/integrity checks, Spriggit round
trip, regenerate-twice-no-diff, the immersion gate (binding from 2.17), link checks and the CLAUDE.md word
budget. A new check earns its place by catching a real defect, and is made to fail on purpose once. Stale
generated data is the commonest red: regenerate, never hand-edit generated files.

## 5. Owner check-ins

`tooling/owner_inbox.py --post` opens a GitHub issue labelled `owner-check-in`: plain English, one check per
bullet, what to try and where (a scene by `bat` name or a place by name), how to reply (comment on the issue; the
owner may also reply in a Claude chat), the open owner calls, and the week's costs (AWS month-to-date, Claude
usage). Nothing measurable is sent to the owner.

**Blocker vs polish** (old rule): a blocker is something the player cannot do (stuck, falls through, crash,
lost save, unreachable control) or sees at the normal play camera in normal play (floating, a limb through a
wall, a visible pop, a Nordic element). Everything else is polish: one quick fix, then the backlog
(`docs/phases/backlog.md`, tagged `P1 before-scale`, `P2 rolling` or `P3 final`; [phases/README.md](phases/README.md)), never
a relaunch.

**The repo is public, so check-in issues are too.** Issues carry no secrets, no start links, no stream URLs, no IP
addresses and no Lambda or console links; those reach the owner privately (a secret gist via `gh gist create` without
`--public`, referred to in the issue only by its title, which the owner finds in their own gist list; or the
owner's AWS console). Costs may be summarised.

## 6. Cost controls (old 0079, 0083, 0118; decision 0027 §9)

- **rtk in front of every shell command.** The `rtk hook claude` PreToolUse hook in `.claude/settings.json`
  rewrites Bash calls so git, test, grep and listing output reaches the model trimmed (rtk 1.1.0, pinned in
  `infra/build-vm/toolchain.lock`; Apache-2.0 CLI). `rtk gain` shows what it saved.
- **What is deliberately not here** (the old project's 18,000 lines of process tooling were most of its bill):
  no review gate (a lane past 1,500 changed lines runs `/code-review` once, by hand), no lane watchers, keepalives
  or memory watchdogs, no scheduled check-ins, no `Workflow` fan-outs by default, no reader panels (one `reader`
  per question; a second only when the first disagrees with the builder), no per-hunk commit tooling (one
  builder per path). Each returns only after an incident it would have prevented, with its test (0011 §2).
- Cheapest model that does the job; looking around on Haiku; prose and dialogue on Sonnet; the planner's model
  is the owner's choice at session start.
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
twins. Decisions hold the why; chunk briefs hold the work (written just in time, nothing dropped: 0023 §7); PROGRESS holds status; research holds evidence.
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
