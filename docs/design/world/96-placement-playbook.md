<!-- imported unchanged from elder-souls-argonia docs/world/96-placement-playbook.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Module 96 — The placement loop and its records

> Places are built in the place loop (decision 0099) with the `place` skill
> (decision 0100): its [SKILL.md](../../.claude/skills/place/SKILL.md) holds
> the judgement, `wb.py next` runs the mechanical steps, and
> `references/types/` holds the per-type sheets. The binding rules the steps
> apply are [97-placement-principles.md](97-placement-principles.md). This
> module states the loop in outline, the two plot rules, the standing
> placement rules, the automation-readiness checklist and where each record
> lives. Owner steers on taste go to 0041's Taste ledger. The playbook this
> replaced is provenance in
> [the archive](../research/archive/phase11-rounds/96-placement-playbook-history.md).

## 1. The loop, per place

The steps are `place` §0–8: the site dossier, the design brief, the layout
file and `wb.py apply`, the plan read, the render rounds, export and publish
per place, the walk packet, the fix round, the slice close. A place's
promise ledger (`python3 -m worldgen.blueprint_promises --id <place-id>`) is
its list of layout requirements: every service, NPC role, travel
destination, provision and socket in it is a thing the layout builds.

**The seed rule.** The committed plot is the seed of the plot solve, not a
by-product of it. `macro_plot` reads every record's committed `positionM` and
keeps it; it re-sites only the records whose committed cell is no longer
valid under the current fields — water depth at the dot (a submerged record
needs real depth; a dry record must not stand in open water), a danger or
region raster that has moved under the dot, a sightline the terrain blocks.
Crowding, score and the old fit are never re-judged, because the scorer is
globally sensitive (a 0.55 m median terrain edit moves hundreds of records in
a from-scratch solve). Records pinned by a blueprint siting are never
re-judged (`pin_overrides` owns those dots). Every run reports what it
re-sited and why (`macro-plot.json` → `seeding`). A province-wide re-plot is
the owner's call: `python3 -m worldgen.macro_plot --resolve-all`
(decision 0041). A seeded run fails on any record left homeless, except the
owner-accepted rows in `world/sources/sites/plot-homeless-accepted.json`.

**The write-back rule.** A place moved after the plot is not moved until the
write-back has run (`apply_sitings`, then the chain's tail by dependency,
decision 0080). The blueprint's chosen siting is the source of truth for the
position; `apply_sitings` is the only writer of `macro-plot-overrides.json`;
major-city anchors keep their owner-approved dot and the geometry sits
around it. A tie to water, a point or a sightline is written in
`sitingPrefs` (`nearWater`, `minDepthM`, `nearPoint`, `boundTo`,
`sightlineTo`), never as prose.

## 2. Standing placement rules

- **Compile last.** Every build step stamps its output with the hash of what
  it read; a hand edit after a step invalidates that step's receipt and the
  exporter refuses. Fix, then run the chain.
- **Derived geometry is regenerated, never hand-corrected.** Routes,
  boardwalks, canals, footprints, districts and doors derive from placed
  pieces and the shipped rasters; when the ground moves the chain's
  `rederive_blueprints` and `rederive_terminals` stages, `street_router
  --apply` and `blueprint_footprints --apply` re-derive them.
- **A structure no piece fits is not published.** It stays in
  `world/sources/routes/route-structures.json` (the debt is real and the
  grader needs its window) and out of the studio bundle; the count prints
  every run, and a growing count means the family needs a shorter piece,
  never a looser gate.
- **The kit interiors library is a tracked record.** `<kit>.interiors.json`
  ships at `world/sources/placement/kit-interiors/`; `blueprint.py` and
  `blueprint_interiors.py` merge it with the local build, tracked winning,
  and a kit missing from both fails validation.
- **A walk in progress publishes with a policy fit and a receipt.** Under
  `wb.py publish --accept-open`, a piece whose authored `groundFit`
  contradicts its asset's manifest policy exports with the policy's fit and
  is listed in `acceptance.walkInProgress.bundleGates.groundFitFallbacks`;
  otherwise the export refuses.
- **Sockets hold their things by id.** Every container, item and plant socket
  of a published place is frozen by `worldgen.loot_fill` and checked by
  `sockets.fill_errors`; reach is checked by `workbench.socket_reach
  --place`; climb, swim, dive and magic caches are gated by
  `worldgen.exploration_rewards --place`.
- **A spot a person lives at stands clear of solids.** The `spots.solids`
  place gate (and `layer_publish`) runs `spot_solids.mjs` on the published
  bundle: a home, bed, work or shell-hosted spot inside a solid is red; move
  the socket in the layout and layer-patch. A layer publish diffs against the
  last publish's layout, so only the changed ops republish.
- **A parcel promises only services in the service-kind table.** A
  parcel's `services` and the promise ledger use the kinds in
  `packages/economy/src/data/service-kinds.json` (decision 0141);
  a building's use that no one sells (a stable, a boat shed) stays a parcel
  use, never a service. `derive_services`, `blueprint_promises` and the
  promise classes keep their own service words, so a kind dropped from the
  table drops from them and from every blueprint that names it in the same
  change.
- **A ladder is seated by its top.** `wb.py mount --ladder <child> <deck>`
  (`snap.ladder_mount`) leans a `climbSurface: ladder` piece on its host
  deck's edge, its spare length under the ground by design. `burialRule`
  judges it by `seat_rules.ladder_top`: the mesh top 0 to 0.15 m over the
  deck it serves, and the foot at most the `ladder` class's `floatMaxM`
  (`workbench/seat.py`) over the ground.
- **New lessons go into the `place` skill**, edited in place as the current
  recipe. Engineering standard 13 fails when a blueprint, design record,
  placement tool, the workbench or the place skill changes without the skill,
  world 97, this module or decision 0041 changing too.

## 3. Automation-readiness checklist (per place type and per interior family)

A place type may be rolled out without an owner round when all of these hold:

- [ ] the exit bar of the place loop (0099 decision 2): two fresh places of the type in a row pass unattended with no defect from the owner's walk; city and early-game types exit by owner acceptance instead;
- [ ] every steer from its rounds is a rule in the Taste ledger or a compiler check, none is a one-off edit;
- [ ] the type's accepted places rebuild clean from their layout files alone (`wb.py apply`, then export and compile) and their acceptance receipts in `accepted-places.json` hold (0100 decisions 2 and 6); the yards are the regression fixture (0099 decision 5);
- [ ] the type's siting grammar (which candidates, how measured, what wins) is written in the type sheet (`place/references/types/<n>-<type>.md`), which reproduces the accepted places' choices;
- [ ] the agent-as-reviewer experiment (0041) has matched the owner's verdict on one non-city instance of the type;
- [ ] no open row in the sourcing-gap register for a piece the type needs.

**Major cities and the opening-scene places (the prisoner tutorial in the
marsh near Stormhold and Alten Corimont, quests 00) never leave the owner's
hands** (0041): no skill runs unattended on them; the packet brief plans
their owner rounds. Interior families join this checklist the same way,
gated by size band.

## 4. Records and routing

- Procedure and lessons → the `place` skill (`SKILL.md`, `references/`) ·
  taste steers → 0041 Taste ledger · per-place reasoning →
  `world/sources/blueprints/<place>.design.md` and the layout
  `<place>.layout.json` (0100 decision 2) · acceptance →
  `world/sources/placement/accepted-places.json` · lessons that are really
  *rules* → world 97, a gate or a `check` rule, with a skill line naming it.
- Router rows: [docs/README.md](../README.md) "Siting, laying out or
  building a place"; [world/README.md](README.md) module table.
