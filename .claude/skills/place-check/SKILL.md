---
name: place-check
description: Verify a drafted place once at the end - draft check, the seat check, the build with the carried walking mesh, the seventeen checks with their accepted findings, truth, units and joints, probe --all and --mesh, the playwalk tour, the survey and the owner captures - each heavy step run under job_guard and the machine-wide lock. Use before hand-over and when a check fails, to find which skill owns the failure.
---

# Verify once

Step 11 of the place path ([place-system](../place-system/SKILL.md)). The inner loop is the look tool
(`place-look`); these steps run once, when the adaptation is done, and again only for what a mend touched.

## Heavy steps

`draft check`, the build and `check` take minutes each and queue on the machine-wide lock
(`tools/places/heavy_lock.py`):

1. Commit the place files by path.
2. Run it under `tooling/job_guard.sh run <name> -- <cmd>` in the background, then `tooling/job_guard.sh wait
   <name>`.
3. Touch nothing of the place until it ends.

## The steps, in order

1. `python3 -m tools.places draft check <place_id>` PASS: every draft rule, then the draft built and every build
   check run.
2. `python3 -m tools.places seat <place_id>`: 0 refs moved.
3. Correct the record's radius to what was built: `place.json` `radius_m` into the research record's
   `footprint_radius_m`, then `python3 -m tools.newworld.refresh`: the tables, the story digest and the story explorer, in order; it says
   what changed (commit it by path) and whether the story explorer or the Atlas needs republishing.
4. `python3 -m tools.places build <place_id> --plan` (lists every problem), then the build: the place layer plugin
   and its navmesh, the source's own mesh carried where `wholesale.navmesh` is `"source"`. It stamps the world records
   it stands on; a stale place is refused by `infra/gpu-box/places_deploy.sh`. A `plugin` failure naming records of
   our own plugin means it was written by an older build: build again with this tree's tool.
5. `python3 -m tools.places check <place_id>`: the seventeen checks green (`plugin`, `seat`, `overlap`, `doors`,
   `people`, `navmesh`, `streets`, `land`, `clear`, `services`, `nordic`, `rooms`, `levelled`, `jail`, `primitives`,
   `stock`, `promises`).
6. `python3 -m tools.places navexport <place_id>`: the walking mesh the studio draws.
7. `look truth <place_id> --sample 40`: the pictures hold against the numbers for this place.
8. `units <place_id>` and `units <place_id> --joints`: every flag mended or accepted.
9. `look <place> probe --all` and `probe --mesh`: nothing open; no door or street point off the main network.
10. The walk-through, required of every place, run as a loop that runs down:
    a. One FULL walk: `look <place> playwalk` (one tour past every door, stall, station, Hist and quest spot) and
       `playwalk --rooms` (entering views). Read the table's faults first, then every strip and the map; open a
       look at full size only where a strip or the table shows something doubtful, and at each door, stair, bridge
       end and quest spot. Write every issue down in `STATE.md`: what, where, the look that shows it.
    b. Fix the issues. Then recapture ONLY the views that showed them: `playwalk --changed` (the stations near what
       changed since the last walk), or `playwalk <from> <to>` for one leg, or `at --stand` for one view. Read
       those. Still wrong: fix and recapture those views again. Repeat until the list is empty.
    c. One more FULL walk, to see that no fix broke something else. New issues: back to b.
    d. Done when a full walk is clean. An issue that has not moved after several rounds is not chased further: it
       goes under "For the owner" in `STATE.md` in plain English, with where it stands and the look that shows it.
    Then `look <place> survey` and
    `survey <unit>` for every structure, each tile read; the owner captures (`place-look`, the hand-over look).
11. The promises check is green: `python -m tools.places promises <place_id> --check` passes (the build's `promises`
    check runs the same): every gathered sentence of the record, its people and its quests has a row, every built row
    its evidence in the place files, every quest state its `states.jsonl` row with its key refs. Look at each state
    once (`look <place> at <its key ref> --state <state>`). For each quest need at the place, write down in `STATE.md`
    how the player is told: the objective's text and target, a map marker, or the line that names it.
12. A place on a source an earlier place uses: `look <place> versus <other>`, the sheet read whole; say what tells
    the two apart.
13. Commit `newworld/places/<place_id>/` and the record change by path. The final build and check come after the
    LAST edit of any kind to the place's files: `check` ends with whether the built check is current against them,
    and `python3 -m tools.places handover <place_id>` says it again before returning (exit 1 when not, and the
    consistency stage would refuse the landing). For a stocked place, `handover` also needs `python -m tools.places
    stock reach <place_id>` to flag no row (material reach, region, place class, trade kit; `place-stock`, section 4).
    The place goes to `place-people`.

## Accepted findings

A finding that is right as built after looking is accepted with what was seen (a reason of at least a sentence),
shown apart and never failing; an entry that no longer matches a finding fails as stale and is deleted:

- a build check's (`overlap`, `doors`, `clear`, `nordic`): `place.json` `draft.accepted_checks` `[{check, ids, why}]`;
- a unit's flag: `draft.accepted` `[{unit, flag, why}]` (`place-site`);
- a probe fault (`draft check` reads the same rows): `draft.accepted_faults` `[{id, fault, why}]` (`place-look`).

## A failure

Each failure's full list is in `out/places/shards/<place_id>/check_failures/<check>.txt`; `check <place_id> --reach
[person]` says what is cut off from what. Mend it at its cause, by the skill that owns it:

| Failure | Skill |
|---|---|
| `plan` faults | `place-plan` |
| `seat`, `land`, `clear`, `nordic`, `levelled`, floating or buried pieces, unit flags | `place-site` (and `place-look`) |
| `overlap` with something added, moved or pruned | `place-adapt` |
| `streets`, `doors`, `navmesh`, reach | `place-streets` |
| `rooms`, room names | `place-rooms` |
| `people`, `services`, `jail` | `place-routines` |
| lights, lanterns, sap, stations, `primitives` | `place-dressing` |
| `promises`, needs | `place-story`, or `place-stock` for a promise of what the place holds |
| `stock`, `stock reach` | `place-stock` |

A finding beyond the checks is weighed by what the player would notice.
