<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.10-loops/traps.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: traps (2.10 § Loops, lane 2.10-d)

Rule (lanes/2.10/briefs/rules.md trap rows; world/76 §128.2; decision 0151
item 5): a probe at probe score ≥ probeThreshold finds and disarms the trap
(state "disarmed", saved) and wears like a pick; below it reports nothing
found. An unprobed trapped pick or open fires the trap's effect at the
player through the 2.9 effect stack with its visual family and a hit
reaction, then resets or not per the row. Eyes: trap strips are lane j's
pod (journey step named in lanes/2.10/d-report.md).

Measures:

- `cd packages/game-core && npx vitest run src/interaction/locks.test.ts`
- `cd packages/scene && npx vitest run src/interact/locks-session.test.ts`

| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| Probe at threshold finds and disarms; one below reports nothing found | both edges | both edges green | 4.8 s (game-core run) | `locks.test.ts` |
| Probe wear by the pick rule | green | green | (same run) | `locks.test.ts` |
| An unprobed trapped pick or open fires: stack entry, visual family, hit-reaction flag | green | green; the flag plays the player's light flinch (`playerFlinch` queue on the magic binding, read by `CombatRuntime`) | 5.7 s session; 6.4 s studio host | `locks-session.test.ts`, `studioLocks.test.ts`, `playerFlinch.test.ts` |
| Every trap kind in traps.json fires in a test | every row | every row green | (game-core run) | `locks.test.ts` |
| Resets per the row (resets true stays armed; false is spent) | both | both green | (game-core run) | `locks.test.ts` |
| Disarmed state saves | green | green | 0.7 s | `locks.test.ts` (save) |
