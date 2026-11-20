---
name: place-check
description: Prove a drafted place - draft check, the seat check, the build of the place layer plugin with its navmesh, the build's seventeen checks and the walking mesh the studio draws, each heavy step run once at a milestone under job_guard and the machine-wide lock. Use at a draft's milestones, before hand-over and when a check fails, to find which skill owns the failure.
---

# Build and check

Step 10 of the place path ([place-system](../place-system/SKILL.md)).

## Heavy steps at milestones

`draft check`, a whole draft, a `streets` run and the build each take 10 to 40 minutes and queue on the
machine-wide lock (`tools/places/heavy_lock.py`). They are never the inner loop: iterate with `look probe`,
`look section` and the one stage that owns a change (`place-look`). Run each heavy step once at a milestone:

1. Commit the place files by path.
2. Run it under `tooling/job_guard.sh run <name> -- <cmd>` in the background, then `tooling/job_guard.sh wait
   <name>`.
3. Touch nothing of the place (look session, quest spots, place files) until it ends.

## The checks, in order

1. `python3 -m tools.places draft check <place_id>` PASS. It proves the place files against every draft rule (each
   skill names the ones it owns), then builds the draft and runs every build check, so a draft that passes here
   passes there. Its `measures` line gives the patched cells and the streets' length.
2. `python3 -m tools.places seat <place_id>` reports 0 refs moved.
3. Correct the record's radius to what was built: `place.json` `radius_m` into the research record's
   `footprint_radius_m`, then `python3 -m tools.newworld.build_db`.
4. `python3 -m tools.places build <place_id> --plan` (lists every problem), then the build under job_guard. It builds
   the place layer plugin and its navmesh, meeting the world's navmesh edge for edge; the world file, its refs shards
   and its navmesh must be of one build. The build stamps the world records it stands on
   (`out/places/shards/<place_id>/world.json`); a stale place is refused by `infra/gpu-box/places_deploy.sh`.
5. `python3 -m tools.places check <place_id>`: all seventeen checks green (`plugin`, `seat`, `overlap`, `doors`,
   `people`, `navmesh`, `streets`, `land`, `clear`, `services`, `nordic`, `rooms`, `levelled`, `jail`,
   `primitives`, `stock`, `promises`). A place that fines passes `jail` with a note saying why.
6. `python3 -m tools.places navexport <place_id>` writes the walking mesh the studio draws routes on.
7. Commit `newworld/places/<place_id>/` and the record change by path. The place goes to `place-people`.

## A failure

Each failure's full list is in `out/places/shards/<place_id>/check_failures/<check>.txt`; `check <place_id> --reach
[person]` says what is cut off from what. Mend it at its cause, by the skill that owns it:

| Failure | Skill |
|---|---|
| `plan` faults, a structure dropped with a piece standing | `place-plan` |
| `seat`, `overlap`, `land`, `clear`, `nordic`, `levelled`, floating or buried pieces | `place-site` (and `place-look`) |
| `streets`, `doors`, `navmesh`, reach | `place-streets` |
| `rooms`, room names | `place-rooms` |
| `people`, `services`, `jail` | `place-routines` |
| lights, lanterns, sap, stations, `primitives` | `place-dressing` |
| `promises`, needs | `place-story`, or `place-stock` for a promise of what the place holds |
| `stock` | `place-stock` |

A finding beyond the checks is weighed by what the player would notice (skill `world-build`).
