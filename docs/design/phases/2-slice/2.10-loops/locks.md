<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.10-loops/locks.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: locks (2.10 § Loops, lane 2.10-d)

Rule (world/76 §118 Security row, §120.2; decisions 0151 items 3 and 5,
0144 item 5, 0114; lanes/2.10/briefs/rules.md): a lock opens iff
(Security + Agility/5) × quality ≥ level on effective values
(`compileCharacter`); a key and Open (magnitude ≥ level) always open a
pickable lock; unpickable-key opens to its key or spellKey only;
quest-sealed refuses everything. A pick wears level / score condition per
attempt and breaks at 0. Lock states save in the `locks` family. Eyes: one
`look` of a locked door and the lock screen on three viewports (ui-lab),
read by a `reader` child.

Measures:

- `cd packages/game-core && npx vitest run src/interaction/locks.test.ts`
- `cd packages/scene && npx vitest run src/interact/locks-session.test.ts`
- `cd packages/save && npx vitest run src/families/locks.test.ts`

| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| Every lock class at its threshold (none, simple, hard, unpickable-key, quest-sealed) | 5 of 5 | 5 of 5 green | 4.8 s (game-core: locks, dayLocks, interior; 112 tests) | `locks.test.ts` |
| Key always opens a pickable lock; Open at magnitude ≥ level opens, below refuses | green | green | (same run) | `locks.test.ts` |
| Unpickable-key: key or spellKey only, the screen line says so; quest-sealed refuses and says so | green | green; lines `text.system.lock.needs-key`, `.sealed` in the catalogue | (same run) | `locks.test.ts` |
| Pick wear = level / score at three levels; a pick at 0 breaks and is consumed | 3 levels + break | 3 levels + break green | (same run) | `locks.test.ts` |
| A Security use report on every worthy success (§120.2); failure earns no more than success | green | green on success; a failure reports nothing (§120.2 has no failed-attempt value: owner call) | (same run) | `locks.test.ts` |
| Day locks: createDayLocks yields the contract shape; keyHeld and pick reach doorTransition from both hosts | 2 hosts | 2 hosts green (game 6 tests, studio 3) | 8.1 s game, 6.4 s studio | `dayLocks.test.ts`, `apps/game/src/gameDoors.test.ts`, `apps/world-studio/src/character/studioLocks.test.ts` |
| The verb: a locked door or lid opens the lock screen through session state; pick and probe resolve through locks.ts; success opens it; a theft-grade open files theft | green | 12 of 12 green | 5.7 s | `locks-session.test.ts` |
| The locks family round-trips every lock state | 3 states | green | 0.7 s | `locks.test.ts` (save) |
| Look of a locked door, the lock screen on three viewports, read by a reader | reader green | see `lanes/2.10/d-reader.md` | look 41 s | `lanes/2.10/d-reader.md` |
