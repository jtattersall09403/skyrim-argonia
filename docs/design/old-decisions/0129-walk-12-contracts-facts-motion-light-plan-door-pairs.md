<!-- imported unchanged from elder-souls-argonia docs/decisions/0129-walk-12-contracts-facts-motion-light-plan-door-pairs.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0129 — Walk 12 contracts: place facts with carriers, a published-socket gate, water motion (bundle schema 6) and the lanes still to be recorded

Date: 2026-10-09 (16k walk 12, part 2 lanes B1 to B3). Supersedes nothing; replaces the W1d `discovery` rows.

## Context

Walk 12 found claims in place records that nothing in the built place carried (a "service hub" with no sign, a strongroom with no loot table), published sockets missing the fields the runtime needs (item kind, sign purpose, npc schedule), and boats placed on water with no motion contract. Each was a check that could not fail or a field with no home. This record fixes the contracts for facts, sockets and water motion; the other lanes' contracts follow in the last section.

## Decision

### Facts (lane B1)
1. Home table: `world/sources/placement/facts/<placeId>.json`, `schemaVersion` 1: `{placeId, facts[{id fact.<slug>.<tail>, claim, sourceField, tag?, provision?, kind feature|activity|service|cache|history, carrier}]}`. The carrier is `{built:{uid,type}}`, `{queued:{type,ref}}` or null. It replaces the catalogue and ledger `discovery` rows, which are deleted along with their code in `promise_gate.py` and `blueprint_promises.py`.
2. Built carrier types: sign, readable, visual-cue, npc, container, piece-set. A service rests on a sign with `signPurpose` or an npc; a cache is a container with a `lootTable`; a piece-set uid is a placement-id prefix.
3. Queued carrier refs: npc-topic names an id in `registries/npcs.json` or `rumour-pools.json`; book names an id in `registries/items.json`; quest-beat names an id in `registries/quests.json`.
4. Gate `facts` (`place_gates.py`, after `record`): every purpose and reward tag has a fact; a null carrier fails; a built uid must be in the bundle with a matching kind; a queued ref must be a registry row; every quest provision and catalogue socket is kept by a published filling socket or by a fact `provision` with a carrier (an `unfilled` excuse does not keep it).
5. `python3 -m worldgen.place_facts --table` is the place skill's first step (before layout), `--check` grades a place, `--write` merges the extractor's output without overwriting existing facts or carriers.
6. Rule R128: a claim with no carrier is built, or removed from the record through text-review; never left open. The 18 published places are in `PENDING` in `test_place_facts.py`; the list only shrinks, a place leaves it when it passes after republish.

### Published sockets (lane B2)
7. Gate `sockets.published` (`place_gates.py`): every socket row in a shipped bundle passes `sockets.socket_shape_errors`. `test_published_sockets.py` holds a `PENDING` list (7 places) that only shrinks.
8. Item sockets name `itemKind`, a key of the vocabulary's `itemClasses[itemClass].kinds`. Sign sockets name `signPurpose` from `signPurposes`; a waymark carries `pointsTo`, any other purpose a `textKey` `text.sign.<place>.<socket>` whose home table is `world/sources/placement/sign-text.json` (`schemaVersion` 1), emitted by `place_text --emit-text`. Npc sockets carry `rosterSlotId` and a non-empty `schedule[]`.
9. When `PENDING` is empty, `itemKind` and `signPurpose` become required in `sockets.ts` and `types.ts` and the `PENDING` machinery is deleted.

### Water motion and bundle schema 6 (lane B3)
10. `SettlementPlacement.motion?: {kind:'static'} | {kind:'buoyant', massKg, draughtM, linDamp, angDamp, hullPoints?, tether?:{to: uid|'seabed', lengthM}}`; absent means static. The settlement bundle is `schemaVersion` 6, additive: versions 3 to 5 still read, their placements as static.
11. Class defaults (rowboat, barge, keg-buoy, ferry-raft, moored-hull, gangplank) live in `world/sources/placement/water-motion-classes.json`, keyed by kit piece id. `wb.py place --wet` over drawn water writes the default; `--tether UID` and `--moored` override it.
12. Gate `water.motion` (`place_gates.py`, `water_motion.py`): a craft-class piece not beached, or a rigid plank placed wet, with no motion fails; a tether to a missing uid fails; a rigid gangplank within 0.3 m of a buoyant piece fails.
13. `tether.to` is the layout uid; the runtime (lane S2) maps it to the placement id (`<bp>.<parcel>.building`, `<bp>.<landmark>`, `<bp>.<parcel>.assembly.<slug(uid)>`). The runtime stays static until S2's `BuoyantBody`; `SettlementLayer` is untouched.

### Ground overlay precedence (ruling 52, Helstrom p16)
14. Where ground overlays overlap, the smaller polygon applies later and wins. `apply_order` (`pad_overlay.py`) and `applyOrder` (`heightOverlays.ts`) apply run pads and pools first in id order, then building pads and mounds with the larger summed piece area first (area rounded to 1e-6 m2), ties in id order; a mound never yields inside a building pad. The shared fixture `packages/game-core/src/terrain/__fixtures__/ground-overlays-precedence.json` (a terrace mound and a smaller door-bank mound whose id sorts first) is read by `test_pad_overlay.py` and `heightOverlays.test.ts`, which assert the same heights.

## Other lanes' contracts (closed at the Phase 16 close, [0135](0135-phase-16-closes-the-world-is-leg-work-now.md))

- Facts (1-6): done; `test_place_facts.py` `PENDING` is empty.
- Published sockets (7-8): done; `test_published_sockets.py` `PENDING` is empty. Item 9 (make `itemKind` and `signPurpose` required in `sockets.ts`, delete the `PENDING` machinery) moved to `P1` in the polish backlog.
- Water motion (10-13): done; the runtime `BuoyantBody` and tethers landed in 16x (`water.record`, `water.buoyantFit` gates).
- Ground overlay precedence (14): done.
- Light plan: done, the per-cell `lightPlan` in `interiorWindows.json` read by `interiors.dark` (c70950cf1, night plans for all cells c16ad233f).
- Door pairs: done, the interior claim's door pairing (`blueprint_interiors.py`, "door pairing refused", c98f2c0d6).
- Sign host: done, rule R127 `snap.sign_host_kind` / `sign_host_refusal` (009fe3dd9).
- `doors.open`: done (c70950cf1).
- `interiors.dark`: done (c70950cf1).
- Helstrom ([0133](0133-cities-are-hand-built.md)): moved to Part 4 chunk 4.1b by [0134](0134-four-parts-de-risk-first.md); its three houses failing `pathReach` are in 4.1's Starting state.

## Consequences

Wave-2 place builders clear each place's backlog in `tooling/.reports/16k/walk12/part2/lanes/B-backfill.md` and remove the place from both `PENDING` lists on republish. A fact dropped from prose is deleted from its facts file in the same change.
