<!-- imported unchanged from elder-souls-argonia docs/decisions/0106-how-we-work-fix-at-source-one-preflight-per-batch-scoped-for-real.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0106 — How we work: fix at source in minutes, one check per batch, review code only, incremental mining, measured throttles, rulings as rows

**Status:** accepted; superseded in part by [0131](0131-one-check-gate.md)
(the gate replaces the preflight; decisions 3 and 9 name it). **Owner's
words:** "too slow, overcautious; every VM
minute and token costs me; make the improvements definitely taken forward
and obeyed by all agents and subagents, so the slower ways never creep back
in." **Supersedes:** the review trigger for non-code diffs;
[0087](0087-opus-decides-when-delegated-no-lane-cap-review-by-pathspec.md)
§ 3's per-lane preflight and "no lane cap"; the preflight lines of 0099 and
0102; the addenda of 0105 (now rows of its rulings table). The gate itself
is [0131](0131-one-check-gate.md); context and look-ups are
[0118](0118-agents-are-capped-by-context-leads-only-plan-look-ups-are-batched-by-hook.md).
**Evidence:** [workflow cost review](../research/archive/agent-process-reviews/workflow-cost-review-2026-09-28.md).

## Decisions

1. **Fix at source, in minutes.** A new gate or check is added only when it
   costs under 5 s a run and the same failure class has occurred twice;
   otherwise a unit test sits beside the fix.
2. **Red on HEAD blocks.** A test red on HEAD is fixed at source by whoever
   meets it, never labelled and tolerated.
3. **One check per commit batch:** `npm run check`, once, as 0131 defines.
4. **Lanes run only the tests beside their change.**
5. **The code review reads code only** (`.py .ts .tsx .mjs .js` under
   packages/, apps/, tooling/), once per batch. Text-review runs once per
   batch.
6. **Miners merge per asset.** `mine_abuts`, `mine_mounts` and
   `mine_designed_sink` take `--assets <ids> --merge` (abuts: rows keyed by
   parent and child, lists re-derived from the merged rows, identical to a
   full run). A full run is for a miner rule change only and carries
   `--rule-change`; the hook refuses it otherwise. `build_kit
   --refresh-derived` re-derives the abuts lists that depend on the kits
   after every build.
7. **Chunk, monitor, split by context.** Each brief is one deliverable for
   one context (0118); the planner watches elapsed against expected and
   splits a lane past its context threshold from its note. A brief may carry
   `Budget: <N> min` and `job_guard.sh <lane> --budget <N>` may stop a job
   with a checkpoint line; neither is required. How many lanes run at once is
   decided by measured memory and CPU (decision 18), never a count.
8. **No rulings store.** A place lesson becomes a tool default, a check or a
   lint rule first; only otherwise an in-place edit of the `place` skill. A
   decision record is written only when a contract or architecture changes.
9. **Gates that never go:** site-refs, bundle-load, the repo standards (ids,
   credits), typecheck, the place's own gates, and `npm run check` before a
   merge to main.
10. **Drift is measured** by the `cost-review` skill's § Workflow drift, each
    measure with a red threshold.
11. **Fix the recipe, never append history.** A defect whose root cause is
    agent behaviour is fixed first in the tool, check or default that would
    have prevented it. Prose changes only when no tool can carry the fix, and
    then it edits the recipe in place: skills, agent files and CLAUDE.md state
    the current recipe, generalised to the class of problem; the new line
    replaces or merges the nearest one and deletes what it supersedes. No
    incident names, walk numbers or dates; the why lives in the commit. Word
    budgets on these files are a gate. A test beside the fix is welcome; a
    test instead of it is a plaster.
12. **A batch is a fix round or a delivered chunk**, never a lane, a commit
    or a file: one check, one review, one text-review per batch.
13. **The review runs once, exhaustively, never in rounds**: a "this is the
    only pass" prompt with a coverage line, findings under
    `tooling/.reports/review/`, and the stamp holds until the planner closes
    the batch (`review_gate.py --close`). The batch's later commits are not
    re-reviewed.
14. **A stop is a diagnosis, never a result.** The planner reads the stop
    note, finds the cause of the overrun, fixes it in minutes and relaunches
    from the note. Work cut by a budget is never handed to the owner as a gap.
15. **Direct Blender for placement.** When the workbench lacks an ability,
    the agent scripts the loaded scene (`wb.py session run`) and adds the
    verb in the same lane; "needs a new tool" is never a hand-off line.
16. **Reports live in `tooling/.reports/`** or the lane's own report path,
    never in `.claude/`; `.claude/` holds only settings, agents and skills.
17. **The review's limits.** The diff cap is a fix round's code diff
    (1.2 MB, code files only); the reviewer's turn cap is 80.
18. **Agents and jobs are admitted on measured memory and CPU only.**
    `job_guard.sh` admits a job when unreclaimable memory, its declared
    `--mem` cap and the other live jobs' unreached caps stay under the
    memwatch ceiling; `agent_cap.py --check` answers `wait` when
    unreclaimable memory plus a per-agent reserve plus those caps reaches the
    ceiling, or when the 1-minute load reaches nproc × 3 while memory is above
    half the ceiling. Memory caused the out-of-memory kills, so memory is the
    gate.
19. **One review per round**: the batch spans the round's pathspec commits
    until `review_gate.py --close`.
20. **No polling waits.** A job runs in the foreground with a timeout up to
    600 s, in parts if longer; the shell guard refuses `tail -f`, `until`,
    sleep and busy loops (0118).
21. **A lean close.** Review items go to one lane, crash and infra fixes to a
    side lane; nothing lands in a core module after the round's survey.
    Before the batch check, `tooling/repo-standards/batch_close.py` (under
    60 s) must be green: nothing under world/, apps/world-studio/public or
    packages/*/data uncommitted; every shipped file with an "is current" test
    and every changed place matches its generator; no test reads gitignored
    data a clean clone lacks without a skip guard.
22. **Measure, diagnose, fix, re-measure: one of each per round.** One
    measure job, one diagnosis listing every cause, one parallel fix wave
    that never touches the pod, one re-measure
    ([`tooling/gpu-lane/measure-loop.md`](../../tooling/gpu-lane/measure-loop.md),
    [loops.md](../phases/loops.md)). The same holds for every survey,
    compile and publish: all findings in one fan-out, one fix set.

## Why

One measured day showed the cost: orientation re-read every turn, a
preflight run sixteen times for seven commits on the same two red tests,
the review run thirteen times on docs-only diffs, a full miner run for one
stable, and process lanes taking a sixth of the delivery tokens. Each rule
above removes one of those costs at its source.

## Where each lives

`tooling/repo-standards/check.mjs`, `review_gate.py`, `batch_close.py`,
`job_guard.sh`, `agent_cap.py`; the hooks in
[`docs/standards/hooks.md`](../standards/hooks.md);
`tooling/world-generation/scripts/select_tests.py`; `worldgen/mine_abuts.py`;
`pipeline/build_kit.py`; CLAUDE.md § How we work; the `place`, `kit-mining`,
`modular-runs` and `cost-review` skills. The numbers and the earlier
wording: [place-decision-rounds/0106](../research/archive/place-decision-rounds/0106-as-recorded.md).
