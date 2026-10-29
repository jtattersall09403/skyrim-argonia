<!-- imported unchanged from elder-souls-argonia docs/decisions/0133-cities-are-hand-built.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0133: Cities are designed by district in the 3D scene, not emitted by a generator

**Evidence:** `tooling/.reports/helstrom/COST-AUDIT-2026-10-11.md`
(sections 1 to 4). **Supersedes:** the generator contract of 0132 (section A: rules 2, 3, 4 and 6, the siting function, run-twice idempotence, the post-apply drift check and the orphan fallback).
The rest of 0132 (survey once, scale rules, process rules) stands.

## Why

Helstrom (71 parcels) cost 13 builder parts, about 34 agents past 150k context,
30.5 VM-hours of guarded jobs (484 applies, 564 min; 29 surveys, 84 min; 37 street
router runs, 6694 s) and 13 whole-city re-emits (975k lines of churn). Rows recurred on the worklist. The cause is the architecture: the
layout was a function output, so any fix to the function re-emitted 2800 places and
a hand fix lived in a side file the next re-emit dropped. The designer debugged a
4195-line compiler and never stood in the scene.

## Rules

1. **The place-builder is the designer.** It places, looks and adjusts in the real
   3D scene from the blueprint; scripts are its tools, never its product. Cost: the
   Helstrom builder spent its contexts reading `helstrom_layout_gen.py` (238 kB).
2. **The layout file is the source of truth and is edited through `wb.py` ops**
   (`wb.py edit`, place, move, mount, snap, swap). It is never re-emitted from a
   blueprint, and carries no `generatedFrom` stamp. Cost: 13 re-emits, 74k deletions
   in one commit, hand fixes undone (DIAGNOSIS-part3.md:23).
3. **The blueprint is the district plan** (streets, plot lines, purpose, density), written
   by hand. It is not compiled into a layout.
4. **One builder per district of 8 to 12 buildings, one context.** Cost: 34 children
   re-orienting on a file too big for one context.
5. **Every change is scoped to the district.** `wb.py apply --district <id>`,
   `apply --uids <..>`, `check --uids` and `survey --district <id>` are the defaults.
   Cost: apply 484 runs at 5 to 19 min whole-city; a hand place applies with
   `--cache` in 31 to 44 s.
6. **A whole-place apply or survey is refused** unless it carries `--whole-place
   --reason "<why>"`; the reason goes in the commit. Cost: resurveys at 5 to 10 min
   and 14 GiB, repeated across parts 2, 5, 6, 9.
7. **Scripts are small, deterministic tools called on a chosen area.** They take uids
   or an area in, write poses into the layout and never re-emit it: seat a row of
   stilts, lay a street or boardwalk run through `modular-runs`, hang lamps along a
   run, seat doors, stairs and lamps on a shell's final pose (`wb.py seat-on-shell`),
   build a terrace on a slope. Each has a unit test and a `place-scope.json` row
   (standard 19). Kept from Helstrom: the street router (6 s form), final-position
   (POSTLIFT) seating, the terrace rule, the ring threshold at parcel scale, the
   building-family kits and the cached apply.
8. **Thrown away:** the layout emitter, the blueprint-to-layout derive chain, the
   edits fragment and the `generatedFrom` stamp. Helstrom stays as built; its
   remaining rows close by place-edit on its layout and its generator is frozen.
9. **`agent_guard.py` requires a district id and a uid scope** in a city `place-builder`
   brief (replacing the 0132 `worklist` plus `0132` naming
   check), and refuses a brief that names a file over 1,500 lines for editing
   unless it splits the file first. Cost: three delivers burnt 150k each editing the
   generator in part 4.
10. **Survey once per district** as confirmation and once for the city at close. A
    partial wave resumes from `wb.py worklist <place> --summary`.
11. **Place cost is recorded at close-out.** `tooling/repo-standards/place_cost.py`
    writes the place's job minutes, peak memory and agent tokens per building into
    the lessons file in the closing step, so the next comparison is exact (the audit
    had to approximate).

## Expected cost of the next city

About 7 districts at one builder context each (about 120k) plus a few small
children. Apply with the cache is under a minute and a district takes 5 to 10
applies, so job time is 4 to 6 VM-hours against Helstrom's 30.5. Tokens run at a
fifth to a tenth of Helstrom's: no 150k relaunch chains, no regeneration to
reconcile, no generator to read.

## Where it lives

Skills: the `place` skill (one builder per place or district) and its
`references/edit.md`. 0132 keeps its survey, scale and process rules.
