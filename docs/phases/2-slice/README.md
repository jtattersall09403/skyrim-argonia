# Part 2: The slice, in two tracks

**Goal.** By the end of this part:
- the whole worldspace exists in Skyrim;
- the slice places are ported and populated;
- every system the final game will have is real, in its scaled shape, on its final interface, with exactly as
  much content as the slice touches and nothing half-done inside it.

The owner plays the slice in the studio (2.17).

**What the slice is.** The places the old project built and walked, fully populated: every `npc`, `idle`,
`container`, `item`, `encounter`, `fauna` and `ambience` socket filled; every placed NPC with their whole
dialogue and services; every placed item usable. The quests are the imported staged quests those places hold.
The wild between them gets its encounters. The places:

| Wave | Places | Why in this wave |
|---|---|---|
| Part 1 | Claywater Station (road-station village) | the first place |
| 1 | Greenspring (Hist village), The Broke Column (hideout with interiors), Riverwalk (boardwalk village), Lighter Flotilla (houseboat flotilla), the two routes (border road to Greenspring's crossings; Archon to Gideon by the Mere Neck) | the owner-accepted places first, plus one of each type that is riskiest on this host (stilts over water, hulls on water, interiors behind load doors) |
| 2 | Jungle Root Hollow, Rose-Bone Waystation, Bog-Iron Workings, Upriver Hist Village, Naga Highway Camp, Pearl Lots, The Wamasu Shrine, Chasepoint, Teeth of Sithis, Voriplasm Vault, the Opening Work Camp | the rest, with the wave-1-proved recipe; the Opening Work Camp is ported here and made the opening with the owner in 3.3 |

Helstrom (the old project paused it) and the cities wait for 4.1. The two studio fixtures (the proving ground and
the booth) come from 0.3 and 0.4.

## The two tracks

The tracks run side by side because they load different machines, and the world track starts first (after 0.4,
beside Part 1), because the world is the first priority and the longest track (decision 0027). The systems track
runs in the order of the priorities: people, dialogue and quests first, then the sheet and items they need whole,
then combat's map, progression, the UI's second stage, and the rest. The **world track** (2.W) is mostly generators
and L1 checks on the build VM. The **systems track** (2.1–2.17) is mostly L2 and L4 work on the GPU box. They
meet at the places: the systems that need people (2.4 onwards) wait for wave 1, and 2.17 waits for wave 2.

**How a systems brief is written.**
- It fixes the **data shape at Morrowind scale first**: the record, its home table, its ids, and its joins to the
  world record set.
- Then the rules (on the 1.1 §a host), then the game adapter, then the view, then the slice content.
- Then the gate that proves every slice instance is complete.
- Each deepens the first rung Part 1 built. Anything the final game needs that is not in a brief is missing from
  the plan, not deferred: add it to the nearest brief and tell the planner.

## Reading order for a fresh agent
1. [../README.md](../README.md) and [../../loops.md](../../loops.md).
2. This file, then your brief in full, then the Part 1 brief it deepens (its Outcome).
3. The decisions your brief names, and [inherited-rulings.md](../../inherited-rulings.md) for any old record it
   cites.
4. The imported design module it names (`docs/design/...`), at the sections it names.

## Chunk table

| Id | Chunk | Depends on | Lane-able beside |
|---|---|---|---|
| 2.W1 | [Terrain, apron and edges](2.W1-terrain.md) | 0.4 and 0.5 (it starts beside Part 1; decision 0027 §2) | Part 1, systems track |
| 2.W2 | [Water](2.W2-water.md) | 2.W1 | systems track |
| 2.W3 | [Regions, weather, light, roads and the route graph](2.W3-regions-roads.md) | 2.W1 | 2.W2 |
| 2.W4 | [Vegetation, navmesh and LOD](2.W4-vegetation-navmesh-lod.md) | 2.W2, 2.W3 | systems track |
| 2.W5 | [The slice places, in two waves](2.W5-slice-places.md) | 2.W1–2.W4 (navmesh at least, for wave 1) | systems track |
| 2.W6 | [Performance and the world walk](2.W6-performance-walk.md) | 2.W5 wave 2 | systems track |
| 2.4 | [People](2.4-people.md) | Part 1 exit, 2.W5 wave 1 | 2.1, 2.3 |
| 2.5 | [Dialogue](2.5-dialogue.md) | 2.4 | 2.3 |
| 2.12 | [Quests, journal and maps](2.12-quests-journal-map.md) | 2.5, 2.W3 (the route graph) | 2.6, 2.7 |
| 2.1 | [The sheet whole: races, birthsigns, classes, effects, perks](2.1-the-sheet.md) | Part 1 exit | world track |
| 2.3 | [Items](2.3-items.md) | 2.1 | 2.4 |
| 2.6 | [Trade, services and travel](2.6-trade-and-services.md) | 2.5, 2.3 | 2.7 |
| 2.7 | [Combat: the map, DSR measured, timing, the built rows, encounters](2.7-combat.md) | 2.3 (2.4 for encounters) | 2.5, 2.6, 2.12 |
| 2.8 | [Progression, rest and death](2.8-progression.md) | 2.7 | 2.9 |
| 2.2 | [The UI, stage two: the design system, the windows, the HUD, every screen](2.2-ui-whole.md) | Part 1 exit (the 1.2 §d rounds) | every systems chunk (it owns the components; each system wires its screen) |
| 2.9 | [Magic](2.9-magic.md) | 2.8 | 2.11 |
| 2.10 | [Crafting](2.10-crafting.md) | 2.9, 2.W5 wave 2 | 2.11 |
| 2.11 | [Stealth, crime, locks and the Owing](2.11-stealth-crime.md) | 2.6, 2.7, 2.W5 wave 2 | 2.9 |
| 2.13 | [Swim and climb](2.13-swim-and-climb.md) | 2.W4, 2.7 | 2.12 |
| 2.14 | [Marsh specials: hazards, effect arrows, harvests, materials](2.14-marsh-specials.md) | 2.9, 2.10, 2.13, 2.W5 wave 2 | — |
| 2.15 | [Boats](2.15-boats.md) | 2.13, 2.6 | 2.16 prep |
| 2.16 | [Sound and music](2.16-sound-and-music.md) | 2.15 | — |
| 2.17 | [Persistence, the immersion gate and the playthrough](2.17-playthrough.md) | all above | — |

Sub-chunks (`2.7a` and so on) are the lettered sections of a brief. The planner may run one as its own session.

## Part 2 exit (the owner signs)
- **The coverage gate (2.17) is green.** Every system row has its plugin or DLL, a journey, a save
  round trip, and a slice place where the owner met it.
- **Immersion:** zero reachable `unreviewed` immersion rows. The full vanilla quarantine journey is green.
- **The owner's playthrough found no blocker.** Every finding is a `P1`, `P2` or `P3` row with its tag justified.
- **The world track's walk closed.** The owner can say "the world is leg-work".
- **Part 3's Starting state** is written from the 2.17 ledger, and the planner re-estimates Parts 3–4.
