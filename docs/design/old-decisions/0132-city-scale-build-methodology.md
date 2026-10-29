<!-- imported unchanged from elder-souls-argonia docs/decisions/0132-city-scale-build-methodology.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0132: City-scale build methodology: worklist waves, scale rules, process rules

Cities are designed by district in the 3D scene, not emitted
([0133](0133-cities-are-hand-built.md)); this record holds the generator
contract for any other generated place and the process rules for every city.
Binding for every city and every other generated place; it sharpens 0128 and
the builder-parts rule of 0106/0118.

**Owner's words:** "Make sure the lessons learned get applied persistently for
future cities, not just small specific items but big picture and
process/procedure/methodology too." **Evidence:** a 41-district city with gates
needs wave state on disk, one-cause briefs and tools proven at city scale:
`tooling/.reports/helstrom/DIAGNOSIS-part3.md` (rulings 1 to 22) and the process
review in `tooling/.reports/16k/walk12/inbox-2026-10-10-evening.md`.

## What the rules prevent

A different city on every run, a scene drifting from its blueprint and hand
edits lost on regeneration. Under them lie wave state held only in agent
memory, briefs that span several causes, tools never run at city scale and a
deploy that shares a branch with the build. None is a design question; each is
a rule below.

## A. The generator contract (any place whose layout is generated)

2. **Ground siting goes through the siting function** (`site_poses` and
   `apply_sited` in the siting module), never plan coordinates. Cost: a
   city on the wrong ground, and a siting call that took 1268 s until a scan bug was
   fixed (6 s after the fix, Q11).
3. **Run-twice idempotence.** Every generator stage, the street router included, has
   a test that runs it twice and compares the output. Cost: part 3 stopped on a
   non-idempotent orient solve (a2aa0d7d1); `street_router --apply` re-routed lanes
   differently on a second run (ruling 7, determinism standard).
4. **Post-apply drift check.** After apply, the scene-exported blueprint is compared
   with the tree blueprint and any drift fails (ruling 16). Cost: `apply_sited`
   ignored four uid prefixes, so the scene and the tree disagreed for two waves (Q4).
6. **Every stage that can orphan something falls back, never drops.** A home socket
   with no tier-A claim falls back to the doorstep (ruling 19); a door path whose
   target moves is re-derived, not dropped. Cost: 4 orphan home sockets after one
   shell swap; 5 door paths dropped in an experiment.

## B. The wave methodology

7. **ONE survey, a persistent worklist, then waves.** `wb.py survey` merges every
   failure into `tooling/.reports/places/<place>/worklist.json` (R158). The lead
   triages the whole set to causes once. Cost: 19 of 41 gates red, 2060 failures in
   52 classes, 11 causes.
8. **One cause per child, briefed from a pinned line map.** A child's brief names its
   worklist ids, the file:line map of the code involved and one `Acceptance:` line;
   it never spans causes. Cost: five deliver agents spent their whole context reading
   code from multi-cause briefs (parts 5 and 6).
9. **Verify per uid and tick.** A child ticks its rows with its commit sha; the
   builder verifies the touched uids with `wb.py <scene> check --uids <..>
   --tick-worklist` (seconds). Gate and compile rows stay open for the next survey.
10. **A confirming survey runs only when no row is open** (or a whole-layout
    regeneration changed everything). A partial wave, and a successor builder, resume
    from `wb.py worklist <place> --summary`. Cost: each resurvey was 5 to 10 minutes and
    5 to 7 GiB, and parts 5 to 7 each paid one to learn where the last part stopped.
11. **A part stops at a green step or at 150k context** with its note naming the
    worklist, the live children's report files and the next command (0118).

## C. Scale rules

12. **Tool targets scale with op count** (`tool_targets.json`, a6e5432); a city's
    apply is not judged against a village's. A job past 2x its target is diagnosed
    from `<log>.overrun`, never waited on or retried.
13. **Every heavy tool carries a measured peak** beside its time target, read from its
    job-guard log. A peak over a few GiB on one item is the defect (A x B hotspot).
    Cost: apply 578 to 611 s at 6.5 GiB and `export_interior_bundle` 1014 s before
    ruling 17; apply 3.99 GiB after.
14. **`wb.py apply --cache` is the default**; `--full` only right before publish.
    Cost: a 578 s `--full` had no headroom (ruling 9).
15. **Dressing and variety are budgeted by the generator per district**: at most 8%
    of a district's pieces from one asset, and a dressing budget by role (ruling 20).
    Cost: 100 pitchforks in one quarter, 9 pieces in a market.

## D. Process rules

16. **A deploy is a serial barrier on the branch.** "Deploy, then start Y" means Y
    edits nothing tracked until the push lands. Cost: the build shared the branch
    with the deploy against the owner's order, then a 70-minute hold.
17. **`lane_resume.py` runs before any relaunch.** Cost: duplicate children after a
    session restart (part 5).
18. **A builder never hands back with a live child.** It ends its turn with one
    `waiting:` line, or blocks on the child's report file with `lane_wait.py --files`.
    A lead or builder may wait on report files. Cost: parts 4 and 5 stopped with
    fx-mem still running, and nothing from apply onward had run.
19. **A rule change lands before the confirming survey** and a late one reopens the
    set (walk 11: 80 minutes, 10 places).

## E. The model note

20. Sonnet delivery stays. On specified jobs it was sound and cheap. The stalls
    came from broad briefs. On Opus the same work would have cost four times as much. A lead
    or place-builder may spawn an Opus investigator (`investigate` with
    `model: opus`) only for a cross-system cause that a Sonnet attempt has not pinned.
    Cost: "a different city every run" took one Sonnet agent two attempts and about
    300k tokens for three causes.

## How it is enforced

A record is only useful if it is read, so tools make the rules unskippable:

2. **`wb.py survey --whole-layout REASON`**: with open worklist rows and no flag,
   `survey` exits with the open count and prints `wb.py worklist <place> --summary`, and does not
   resurvey (pure `worklist.survey_refusal(doc, whole_layout)`, tested; every place).
3. **`references/part-brief-template.md`** carries the worklist ids and the pinned
   line map in every part brief by default, so every launch starts from the same
   rules.

## Where it lives

Skills: `place-build` § Builder parts (detail in `references/builder-parts.md`) and §
Cities, `place-edit` steps 2 and 5, `references/part-brief-template.md`.
Agents: `lead.md`, `place-builder.md` (Spawns gains `investigate`; deploy barrier;
`lane_resume.py` before a relaunch; no hand-back with a live child). Hooks:
`docs/standards/hooks.md` (the guards above, and the fourth-part diagnosis, which points
at the worklist). Phase doc: `16k-place-loop.md` (the city).
