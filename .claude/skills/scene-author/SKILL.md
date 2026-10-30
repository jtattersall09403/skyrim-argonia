---
name: scene-author
description: Write an Argonia scene (tests/scenes/<id>.txt, a console batch file) or a runnable journey (tests/journeys/<id>.yaml for tools/run_journey.py) that can fail. Use before any L4 check in game, and to turn a draft journey into steps.
---

# Scene author

Decisions 0021 and 0022; chunk 0.3 §c and §d. A check in game starts from the base save (`argoniabase`, written by
`make deploy`), applies a scene, then plays short steps judged on state and events, with a still at each step.

## A scene: `tests/scenes/<id>.txt`

- One console line per line, CRLF, applied with `bat <id>` from the base save. The runner sends the file to the game's
  folder before it applies it; `make deploy` sends them all. The owner types the same `bat <id>` on the stream.
- It **stages**: the place (`coc <cell>`, or `cow <world> <x> <y>`, `player.moveto <marker>`) as the file's **last line**: a line after it runs during the cell load, and a `setpos` or `fw` there crashed the game twice (game-6, 2026-10-30); a point inside the cell, or anything placed by the player, is the journey's first step (`teleport pos x y z`), the hour
  (`set gamehour to 12`), the weather (`fw <hex id>`), the kit (`player.additem`, `player.equipitem`), who stands
  where (`player.placeatme`), quest stages, and the sheet (`player.setav`) until 1.3's setters exist.
- It **never sets what the check tests** (loops rule 4): a roll check never sets the player's speed, a quest check never
  sets the stage it reads, a combat check never kills the target.
- Cheats are for setup only (god mode, items, stages); the action under test goes through the real game path: the pad,
  real keys, an activation.
- Name the place by what it is (`plain-armed`, `argonia-water`). Prefer an open floor where movement is measured:
  QASmoke's pillars stopped rolls at 2 to 80 units (2026-10-30).

## A journey: `tests/journeys/<id>.yaml`

```yaml
id: smoke
runner: 1                 # runnable; a file without it is a draft (prose)
scene: plain-armed
steps:
  - name: roll
    do: [{pad: "+LX=0,LY=1:500 B:100 wait:600 -:1200"}]
    expect: [{event: {kind: anim, match: TKDR_DodgeStart}}, {moved: {gt: 300}}]
```

- **Actions:** `pad`, `key "<K> <ms>"`, `console`, `teleport`, `wait` (at most 10 s), `game_hours`, `call`. Each input
  is at most 3 s. Between distant steps, teleport; never walk far.
- **Expectations:** `read` (any bridge read and a path), `console` (contains or not), `event` (anim, menu, hit, quest since
  the step began), `moved` (ground distance), `quests_running`. Each is polled until `within` seconds (default 5).
- **Judge by state and events, never by pixels.** A still is evidence; only a brief that names an L5 reason judges one.
- **Make it able to fail.** Before trusting a new check, run it once on a case that must fail (a step with no input,
  a wrong expected value) and see the reason it prints.
- Keep steps short and named by what they do; one behaviour per step.

## Running

`tooling/job_guard.sh run --gpu <name> -- python3 tools/run_journey.py tests/journeys/<id>.yaml [--runs 2]`, then
`job_guard.sh wait <name>`. Out: `out/runs/<id>/<stamp>/report.json`, a still per step, and for a failed step
`failure.json` (the step, its expectation, its still): hand that to a `reader` with the expectation. Three identical
failures stop the batch: diagnose before running again. A crash is a failure (exit 2).

The play camera is third person: the runner checks `IsPC1stPerson` after the load and toggles it (setup only). In first
person TDM's directional movement is off, and every roll reads as a strafe.
