<!-- imported unchanged from elder-souls-argonia docs/phases/2-slice/2.10-loops/walk.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Loop survey: walk integration (2.10 § crime, lane 2.10-w)

Rule (decisions 0092, 0142 § 3, 0151; lanes/2.10/briefs/rules.md): every
placed person in the walk is a notice observer on the player (the `person`
detection profile, one book per observer, never shared); a crime is filed
only when seen (0039); a zone entered while private and seen by a person
inside it is trespass, once per entry; a watch person engaged on the player
while the region's Owing is open walks up and opens the guard stop; resist
provokes the watch through answered violence and the walk's people driver
fights them; pay or serve clears the place. Faction standing saves in its
own family; regions carry a player-facing name. Eyes: none (headless).

Measures:

- `cd packages/scene && npx vitest run src/interact/walk-crime-session.test.ts`
- `cd packages/save && npx vitest run src/families/standing.test.ts`
- `cd tooling/world-generation && python3 -m worldgen.stealth_views --check && python3 -m worldgen.place_text --check`

| Measurement | Bar | Result | Elapsed | Capture |
|---|---|---|---|---|
| A Greenspring townsperson within sight sees an owned item taken; theft filed with that person as witness | filed, witness the townsperson | filed: spring-keeper witness, victim, region hist-heartland | 8 ms | `walk-crime-session.test.ts` |
| An owned lock opened in sight files theft with the townsperson witness | filed | witness list is `observersEngaged`, which holds the engaged townsperson; the lock filing itself is locks-session.test | 8 ms | `walk-crime-session.test.ts` |
| A person inside their own zone out of hours sees the player: trespass filed once per entry (two frames inside = one entry; leave and re-enter = two) | 1 then 2 | 1 then 2; none in hours | 2 ms | `walk-crime-session.test.ts` |
| The watch walks to the player and the guard stop opens without the player talking | stop opened, distance ≤ talk reach | stop opened unasked at ≤ 2.5 m, watch standing | 6 ms | `walk-crime-session.test.ts` |
| Resist: answered violence provokes the watch; a kitless person is the people driver's (draw, then fight intents), a watch person the combat runtime's (w2 rows) | provoked, driven or handed | provoked; the watch handed to the runtime (w2) | 6 ms | `walk-crime-session.test.ts` |
| Pay or serve later: the place stands down, the driver releases the watch | not provoked, released | not provoked, released, driven null | 6 ms | `walk-crime-session.test.ts` |
| Faction standing round-trips through `faction-standing` | equal after save, load | equal | 2 ms | `standing.test.ts`, `walk-crime-session.test.ts` |
| Every region has a player-facing name in the records; the Owing sheet names the region | 8 of 8 | 8 of 8; sheet shows Middle Argonia | 1 ms | `stealth_views --check`, `walk-crime-session.test.ts` |
| Per-frame cost of townsfolk notice on the largest slice roster | < 0.5 ms per frame on the test runner | 0.043 ms per frame (Riverwalk, 10 persons, the largest roster; whole people step) | 27 ms | `walk-crime-session.test.ts` |
| w2: every slice watch person carries the guard profile (fight 30, flee 0, alarm 100) and a kit; the integrity gate reds a watch with no person, a watch person with no loadout or off the profile | 5 of 5 watches, 0 reds; the gate's three reds fire on purpose | 5 of 5 (Riverwalk 3, Broke Column 6 hostile, Work Camp 2, Teeth 7 hostile, Flotilla 3); 0 reds; 3 of 3 reds fire | 46 tests, 2.9 s | `test_stealth_views.py`, `test_hostile_loadout.py`, `hostile_loadout --check` |
| w2: resist hands the watch person to the combat runtime as a hostile spawn; the runtime's registration takes it; its light blow lands on the player's health | handed, registered, health lower | handed (`recordEnemies` record = the toll-holder), blow kind hit, health below 100 | 5 ms | `walk-crime-session.test.ts` (3, 4) |
| w2: pay or serve later hands the watch back to its day | not handed, released | both: handed [], released, driven null | 5 ms, 2 ms | `walk-crime-session.test.ts` (3, 4), (3b) |
| w2: townsfolk read the runtime's light, loudness and boots (`CombatHudState.detection.target`) | dark, still, sneaking noticed later than lit and running | lit and running engaged after 0.3 s; dark, still, sneaking not engaged in 30 s | 2 ms | `walk-crime-session.test.ts` (3c) |
