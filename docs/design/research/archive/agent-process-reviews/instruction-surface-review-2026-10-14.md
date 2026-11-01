<!-- imported unchanged from elder-souls-argonia docs/research/archive/agent-process-reviews/instruction-surface-review-2026-10-14.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Instruction surface review (2026-10-14)

Owner asked for a critical review of CLAUDE.md, agent definitions, skills,
standards, decisions, hooks and the workbench: waste, duplication, conflict,
cost and wall-time traps. Five research agents measured and read each area;
their full reports are in `tooling/.reports/instruction-review/` (gitignored):
`agents.md`, `place-skills.md`, `docs-rules.md`, `hooks-tooling.md`,
`workbench.md`. This file holds the conclusions and the staged plan.

## What the numbers say

| Surface | Words now | Target |
|---|---|---|
| CLAUDE.md (loaded by every agent without `omitClaudeMd`) | 6,158 | ~2,000 |
| Planner session-start read list (CLAUDE.md steps 1-2b) | ~29,000 | ~8,000 |
| `.claude/skills/` total | 116,036 | ~35,000-40,000 |
| Place-builder read path before its first edit | ~79,000 | ~17,000 |
| `rulings.md` | 12,659 (184 rows) | ~2,500 |
| Lessons store | ~28,900 | ~6,000 |
| `placement-workbench/SKILL.md` | 10,399 | ~1,200 |
| MEMORY.md index (every session) | 1,876 | ~500 |
| lead.md | 3,913 | 2,678 after stage 1 |

Spend, last 7 days, in session_tokens cost units: deliver 82.8,
place-builder 49.3, deliver-small 34.9, find 32.5, lead 18.0, run 6.3. One
place (Helstrom) took about half of all units. Agent results are 53 % of the
planner's carried context.

## Conclusions

1. **The largest cost is rework from the tools fighting each other, not
   instruction size.** In Helstrom about 12 of 13 open worklist rows were
   tool against tool (the stair tool sinks bases 0.39-0.48 m, the burial
   rule allows 0.28 m). Each such row costs an Opus builder round. Fixing
   the shared cause (one seat/sink module that both the seating tools and
   the checks call, with a fixture test composing them) is worth more than
   any text cut.
2. **The text regrows because the process writes prose for every defect.**
   "Fix at source" became "write a lesson row", so rulings and lessons grew
   to 41k words of incident history ("walk 11", "Nine Bends w3f"). A rule a
   tool or gate enforces needs no prose beyond its id; a judgement no tool
   can check gets one line, replacing an older line where it can. Word
   budgets on the always-loaded files (a gate, like the download budget)
   stop the regrowth; the 450-line skill cap was met by moving text into
   files every builder is told to read anyway.
3. **Handing off a quick look-up costs more than it saves.** With prompt
   caching, carried context costs about a tenth of fresh input, so a 1 kB
   grep result in an Opus context is cheap. A find spawn costs 20-90 s of
   wall time, two parent wakes and a full turn; builders logged 243 min of
   waits on 298 finds in one walk. The planner shell guard refuses `head`,
   `tail` and `git log --oneline -5` while letting `rtk proxy grep` through.
   A rule on output size (refuse a command whose output would exceed N
   lines, which `rtk` already condenses) protects context without forcing
   a spawn. `find` stays the tool for multi-file sweeps and docs crawls.
4. **The delegation tree is one level too deep for most work.** Planner,
   lead, place-builder, deliver and deliver-small means four briefs and four
   report hops for one change. A lead only pays when two or more large lanes
   run in parallel (its own description says so). A place-builder or
   deliver writing a short tool change itself is cheaper than briefing a
   child, reviewing its plan and reading its diff.
5. **Model moves change the economics.** `deliver` was already the largest
   spender on Sonnet; on Opus it costs more per token and must earn it by
   less rework. `deliver-small` on Sonnet is now the cheap implementer. Re-run
   `session_tokens.py` after a week of the new tiers before judging.
6. **Most session-start reading is planner lookup, not every-session
   reading.** Only CLAUDE.md and PROGRESS.md are needed every session; the
   phases README (10.6k), decisions index (4.4k) and buildout README are
   looked up when a task touches them. `docs/world/00-core.md` is needed for
   tasks that decide world content.
7. **Direct Blender is possible but is not the bottleneck yet.** Blender
   3.2.2 runs headless; `wb.py bpy` already loads the whole placed scene but
   is read-only. A `bpy-session` plus `bpy-commit` pair, where the commit
   diffs transforms into the existing layout-edit vocabulary, keeps stable
   uids, the frozen ground and every check. It must refuse moves of snapped
   or mounted pieces, which carry mined joint evidence. It helps multi-object
   design work, and it does nothing about rules that contradict each other.

## Stage 1, done 2026-10-14

- CLAUDE.md: model-policy bullet no longer restates tiers (frontmatter is the
  one source); "Don't over-validate" names `npm run check` (0131); step 3
  reads the injected git status instead of a refused `git log`.
- Agent files: one hand-off line (Haiku 100k, all others 150k) in every
  body; `omitClaudeMd` on `run` and `check` (about 10k tokens per spawn);
  `run` gained the one job_guard line it needs; `investigate` description
  matches its medium effort; `research` and `investigate` hand-off notes no
  longer tell a read-only agent to commit; `reader` rtk line no longer
  sits under "Never" and its rows carry a suggested rewrite.
- lead.md: GPU measure-loop protocol moved to
  `tooling/gpu-lane/measure-loop.md`; deliver/deliver-small criteria point to
  the descriptions; plan-first applies to deliver and place-builder only;
  stale "investigate with model opus" line removed.
- Hooks: session-start token report parses only the files it reports; dead
  Agent-matcher miner hook removed; Haiku/Opus sets derived from frontmatter;
  the planner guard ignores quoted text (see the commit for what landed).
- Gate: the batch check refused at the review step on 11 findings, all in
  the 2026-10-12 perf round's unreviewed code (settlement far cells,
  gpu-lane harness, studio GL context), none in this batch. They are owed
  by that round's batch close (`tooling/.reports/review/review-findings.md`).
  This batch committed on its own guard tests (72 passed). The review gate
  being tree-wide rather than per batch is itself a wall-time trap: one
  open batch blocks every other lane's check. Stage 5 fixes that.

## Stages 2-5, done 2026-10-14 (one session, four parallel lanes)

- Workbench: one seat/sink module (`workbench/seat.py`) used by every placing
  tool and check, with a contract test; `apply` derives its scene; builders
  design in a persistent Blender session (`wb.py session`, warm round trip
  0.04 s) whose commit writes uid edits to the layout and checks them.
- Skills: 116k words to within the 40k budget; place-build SKILL 2,286 words
  plus one procedure file and one type sheet per place type; rulings.md and
  lessons/ deleted (246 rows carried by gates and `wb.py explain`, 142 folded
  into 14 class-level recipe lines, 75 dropped with reasons; mapping in
  `tooling/.reports/instruction-review/stage2/skills-mapping.csv`). Builder
  read path about 8.3k words. Word-budget gate `test_word_budget.py`.
- CLAUDE.md 2,096 words; 0079 is the current agent policy; memory 101 files
  to 38; every-session reading is CLAUDE.md and PROGRESS.md.
- Agent files within budget, shared rules once in CLAUDE.md; standards by
  task in `docs/standards/by-task.md`; review gate scoped per named batch;
  look-ups on a known file done directly, searches sent to `find`.

The plan as written before the work:

**Stage 2, workbench contradictions (highest value).** Shared seat/sink
module used by the seating tools and the burial/prop-seat rules, fixture test
composing them; `apply` derives the scene from the layout and refuses
`--scene`; build ledger writes one row per place close with correct units.
Every Helstrom open row classified tool-vs-tool or design first.

**Stage 3, place skills to ~35-40k words.** Word-budget gate on SKILL.md
files, agent files and CLAUDE.md first. Map each ruling and lesson row to the
gate or tool that enforces it (25-row sample with expected answers, then a
fresh batch, then all); rows with a gate shrink to `id | gate` and are served
by `wb.py explain`; the 85 unnumbered lesson rows are folded or deleted.
Merge the eight round/brief/packet process files into one `procedure.md`.
Cut `placement-workbench/SKILL.md` to a 1.2k command index over
`wb.py --help` and `explain`. `site_packet` serves the type sheet, design
index and rulings rows for the place's type. The close step requires a tool
or gate change per finding, prose only for what no tool can check.

**Stage 4, CLAUDE.md and memory.** CLAUDE.md to ~2k words in about 13
topics, each a one-line rule plus its decision link (outline in
`docs-rules.md`); one deploy bullet; the "How we work" bullet to four lines.
Decision 0079 rewritten as the current agent policy; `sonnet-5-5-task-fit.md`
tier tables deleted. MEMORY.md pruned to ~35 live entries; closed-round and
preflight-era memories deleted. Session-start list cut to CLAUDE.md and
PROGRESS.md, the rest routed by task. PROGRESS.md row 16 trimmed to state.

**Stage 5, agent bodies.** Shared blocks (report style, pathspec commits,
waiting line, rtk line) stated once in CLAUDE.md for agents that load it;
`omitClaudeMd` agents keep their short copy. One by-task standards digest
replaces the "find agent reads engineering.md in full for every brief" step.
`hooks.md` to one line per hook.

## Owner decisions (settled 2026-10-14: 1 look-up rule as described; 2 deliver stays Opus; 3 builders design in a persistent Blender session that commits through layout edits; 4 integrator abolished)

1. Replace the planner and lane shell-guard verb ban with an output-size
   rule (conclusion 3). Reverses part of 0079.
2. Keep `deliver` on Opus, or move it back to Sonnet after a week's
   measured cost (conclusion 5).
3. `place-builder.md` now invites builders to bypass `wb.py` for direct
   Blender, while the place-build skill makes the layout file the only
   source of truth. Proposed reading: free bpy to look, measure and try;
   every lasting change goes through layout edits, later through
   `bpy-commit`. Build `bpy-session`/`bpy-commit` now, or after stage 2.
4. Abolish the lesson "integrator" role: a lesson lands as a gate, a tool
   default or one replacing line, or not at all.
