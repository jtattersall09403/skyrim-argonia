<!-- imported unchanged from elder-souls-argonia docs/research/archive/place-decision-rounds/0106-as-recorded.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0106 — How we work: fix at source in minutes, one preflight per batch, scoped for real, review code only, incremental mining, measured throttles, rulings as rows

Evidence: decision 0106 as it stood before it was rewritten as one current document; the record itself is [0106](../../../old-decisions/0106-how-we-work-fix-at-source-one-preflight-per-batch-scoped-for-real.md).

**Date:** 2026-09-28. **Owner's words:** "we are in a pickle: too slow,
overcautious; every VM minute and token costs me; make the improvements
definitely taken forward and obeyed by all agents and subagents from now on,
so the slower ways never creep back in: golden rules, hooks, whatever it
takes." **Evidence:** the workflow cost review
[`docs/research/process/workflow-cost-review-2026-09-28.md`](../agent-process-reviews/workflow-cost-review-2026-09-28.md)
(session 925af94b, 16k walk 3). **Supersedes:** 0079 rule 8's "the first
preflight on an unreviewed diff triggers a review" for non-code diffs and
its 20 min fix window; 0087 §3 "a lane preflights its own files" and "no
lane cap"; the preflight lines of 0099 and 0102; 0102's "everything a tool
can measure is a check rule" where the check would cost 5 s or more;
the addenda of 0105 (now rows of the rulings table).

## The numbers (one specimen day, 07:47–15:29)

- 22 deliver lanes carried 545 M of the session's ~680 M tokens (96 %
  cache reads); orientation alone was ~75k tokens per lane, re-read on
  every turn (~160 M tokens).
- Preflight ran 16 times for 7 commits; all 16 ended red on the same two
  tests red on HEAD; 60 min of summed wall. Placement ran 168 of 168 test
  files in 8 of 16 "scoped" runs (a README in the suite folder selected the
  whole suite; a kit or record change selected ~90 %).
- The code review ran 13 times (36.5 M tokens), docs-only diffs included.
- One Riften stable set off an 83 min abuts full run and a 17.8 min mounts
  full run.
- Process lanes (rules, method, docs) took 14 % of deliver time and 17 % of
  its tokens; 0105 grew 50 rulings and 4 addenda in two days.

## Decisions

1. **Fix at source, in minutes.** A new gate or check is added only when it
   costs under 5 s per run and the same failure class has already occurred
   twice; otherwise a unit test sits beside the fix.
2. **Red on HEAD blocks.** A test red on HEAD is fixed at source by whoever
   meets it, never labelled and tolerated.
3. **One check per commit batch.** The planner's `check` agent runs
   `npm run check` once per batch; the gate, its contents and its budget are
   [0131](../../../old-decisions/0131-one-check-gate.md).
4. **Lanes run only the tests beside their change.**
5. **The code review reads code only** (`.py .ts .tsx .mjs .js` under
   packages/, apps/, tooling/), once per batch (60 min fix window).
   Text-review runs once per batch, listed only in the place-build skill's
   batch step.
6. **Miners merge per asset.** `mine_abuts`, `mine_mounts` and
   `mine_designed_sink` take `--assets <ids> --merge` (abuts: the pieces'
   families, rows keyed by (parent, child), lists re-derived from the
   merged rows; 13.7 s for a wall family, identical rows to the full run).
   A full run is for a miner rule change only and carries `--rule-change`;
   the hook refuses it otherwise. `build_kit` re-derives the abuts lists
   that depend on the kits after every build (`--refresh-derived`, 0.5 s).
7. **Chunk, monitor, split by context; a Budget line is optional** (owner
   2026-10-04: "the only valid throttles are CPU limits and memory limits,
   measured properly, never arbitrary job or agent cap numbers"). Each
   brief is one deliverable for one context (0118); the planner watches
   elapsed against expected and splits a lane past 300k context from its
   note. A brief may carry `Budget: <N> min` when the planner wants a
   checkpoint note, and `job_guard.sh <lane> --budget <N>` may stop a job
   with a checkpoint line; neither is required. How many lanes run at once
   is decided by the measured memory and CPU checks (decision 18), never a
   count.
8. **No rulings store.** A place lesson becomes a tool default, a check or
   a lint rule first; only otherwise does it become an in-place edit of the
   place-build skill, made by the planner at slice close. A decision record
   is written only when a contract or architecture changes.
9. **Gates that never go:** site-refs, bundle-load, the repo standards
   (0104 ids, credits), typecheck, the place's own gates, and `npm run check`
   before a merge to main.
10. **Drift is measured weekly** by the `cost-review` skill's § Workflow
    drift, each measure with a red threshold.

### Addendum 2026-09-28 (owner, after walk 4: "it might be fine now, but own this problem")

11. **Fix the recipe, never append history** (owner 2026-10-14). A defect
    whose root cause is agent behaviour is fixed first in the tool, check
    or default that would have prevented it. Prose changes only when no
    tool can carry the fix, and then it edits the recipe in place: skills,
    agent files and CLAUDE.md state the current recipe, generalised to the
    class of problem and the approach that gets it right first time; the
    new line replaces or merges the nearest one and deletes what it
    supersedes. They carry no incident names, walk numbers or dates; the
    why lives in the commit message. Word budgets on these files are a
    gate. Every fix round names, per defect, the tool or recipe line that
    changed; a test beside it is welcome, a test instead of it is a
    plaster.
12. **A batch is a fix round or a delivered chunk**, never a lane, a commit
    or a file. In 16k: all the lanes' work between one owner walk and the
    next packet. One check, one review, one text-review per batch.
13. **The review runs once, exhaustively, never in rounds.** Low effort,
    a "this is the only pass" prompt with a coverage line, findings under
    `tooling/.reports/review/` (never under `.claude/`), and the stamp
    holds until the planner closes the batch (`review_gate.py --close`, at
    the packet): the round's later commits and fixes are not re-reviewed;
    the next round gets its own review.
14. **A stop (a split, an optional budget) is a diagnosis, never a result.** The planner reads the
    stop note, finds the cause of the overrun (walk 3's causes: a survey
    and scan pass re-run per round, 22–44 min a place; orient 12–17 min a
    place; a stable sited by hand for 45 min; 3 preflights at 5 min), fixes
    it in minutes, relaunches from the note. Work cut by a budget is never
    handed to the owner as a gap.
15. **Direct Blender for placement.** When the workbench lacks a placement
    ability, the deliver agent runs its own script against the loaded scene
    (`wb.py bpy`) and adds the command in the same lane; "needs a new
    tool" is never a hand-off line (0079 rule 19 widened).
17. **The review's limits.** The review's diff cap is a fix round's code diff (1.2 MB), measured on
    code files only. The reviewer's turn cap is 80 (walk 9: the 40-turn cap
    ended the first review unfinished, the retry took 46).
16. **Reports live in `tooling/.reports/`** (per run, per area), never in
    `.claude/`, the repo root or a docs folder; `.claude/` holds only
    settings, agents and skills.

### Addendum 2026-09-30 (owner, walk-6 process audit, tooling/.reports/16k/walk6/process-audit.md)

18. **Agents and jobs are admitted on measured memory and CPU only**
    (owner 2026-10-01, made exclusive 2026-10-04: no count, no fixed
    minute number). `job_guard.sh` admits a job when machine unreclaimable
    memory + its declared `--mem` cap + the other live guarded jobs'
    unreached caps stays under the memwatch ceiling; `agent_cap.py --check`
    (run before a big fan-out) answers `wait` when unreclaimable memory + a
    per-agent reserve + those unreached caps reaches the ceiling, or when
    the 1-min load reaches nproc × 3 while unreclaimable memory is above
    half the ceiling (load alone never waits: it only slows jobs). Why:
    walk 5's two OOM kills cost 504 min; memory was the cause, so it is the
    gate.
19. **One review per round**: the batch spans the round's pathspec commits
    until `review_gate.py --close` (walk 5's close ran four reviews in 40
    min); inside the open batch a re-run fires no reviewer and preflight
    re-runs only the gates red last time (decision 0118).
20. **No polling waits**: a job runs in the foreground with a timeout up
    to 600 s, in chunks if longer (decision 0118 d6); the shell guard refuses `tail -f`, `tail --pid`, `until` and busy loops,
    and pgrep loops, python sleep one-liners, waiting while-loops and
    `date; grep` ticks (decision 0118).
21. **A lean close, closed before its preflight**: review items go to one
    lane, crash and infra fixes to a side lane; each lane runs
    `select_tests.py` on its diff before returning; job logs carry a 1-min
    load-average sample. Nothing lands in a core module after the round's
    survey; a late change goes to the next round. Before the batch
    preflight, `tooling/repo-standards/batch_close.py` runs (under 60 s)
    and must be green. It checks three things. No file under world/,
    apps/world-studio/public or packages/*/data is uncommitted or
    untracked. Every shipped file with an "is current" test, and every
    place changed since `--base`, matches its generator. No test reads
    gitignored data a clean clone lacks without a skip guard or a
    `# clean-clone:` line. The preflight runs once, after close is green
    (walk 11: 20 preflights; three re-runs came from a stale reseat file,
    tests reading unbuilt raw kits and an uncommitted bundle).
22. **Measure-diagnose-fix loops: one measure, one diagnosis of every
    cause, one fix wave, re-measure** (owner 2026-10-02). Evidence:
    `tooling/.reports/16k/walk10/monitor-fixbatch.md`: fix agents spent
    60-80 % of wall time waiting on the pod, both GPU lanes drifted to
    find-one-fix-one, and causes visible in an earlier measure were fixed
    2 h later. The rules (one measure job per round, one diagnosis report
    listing every cause, one parallel fix wave that never touches the pod,
    one re-measure, pod owned by the measure job) live in
    [`tooling/gpu-lane/measure-loop.md`](../../../../tooling/gpu-lane/measure-loop.md). The same holds
    for every survey, compile and publish: all findings in one fan-out, one
    consistent fix set (CLAUDE.md golden rule "Find everything in one go,
    then fix it once", owner 2026-10-04).

## Where each lives

- `tooling/repo-standards/check.mjs`, `review_gate.py`, `batch_close.py`,
  `job_guard.sh`; the hooks are listed in
  [`docs/standards/hooks.md`](../../../standards/hooks.md).
- `tooling/world-generation/scripts/select_tests.py`;
  `worldgen/mine_abuts.py` (`merge_scope`, `near_scope`, `merge_abuts`);
  `pipeline/build_kit.py` (`refresh_abuts_derived`).
- CLAUDE.md § How we work; the `place-build`, `kit-mining`,
  `modular-runs` and `cost-review` skills; `docs/standards/engineering.md`.
