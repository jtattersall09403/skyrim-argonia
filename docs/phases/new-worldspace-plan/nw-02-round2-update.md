**Ready for your walk or fly: the new world is rebuilt with all of your 9 November feedback.** This is your first walk of it. Open the **"Argonia: New World"** card in Moonlight, start or load a game, open the console and type `coc ArgoniaNWStart`. The full check list, A to S, is in `docs/phases/new-worldspace-plan/nw-02-walk.md`. The four new checks are at the end (P to S) and are repeated below.

**What changed since the first post**

- **Water.** Your atlas edits are all kept, including your "Update-2026-11-09c" save. Your kind on a body is now final everywhere, so the Helstrom rule can no longer turn your river back into marsh or pond.
  - The northern streams that ran inland now run to the sea. They had drained north into the map's border band, which was being read as sea.
  - Every flowing stretch now flows along its own curving course toward the sea. It stops where it enters still water and starts again where water leaves.
  - 95 channels that do not reach the sea through water are now still water.
  - 208 small bits of stream on the edges of your swamps and marshes now take the kind of the body they touch.
  - Round Helstrom, the main rivers and a few tributaries stay flowing, and the rest is winding green marsh.
- **Water in the game.** All water is one surface at one level, with no gaps. Where two kinds meet, the colour now changes gradually over many cells instead of with a hard line.
  - The largest colour step between neighbouring cells fell from 130 to 14 on a 0–255 scale, and 99% of seams step by 9 or less.
- **Islets and the ground under places.** The terrain had never honoured what places ask of the ground. Places in lakes were drowned.
  - Now 361 of 368 of those needs pass. The other 7 are small: four flat building areas sit on a slope or a rise, one mine's pad has its entrance mound in it, Seafalls' rise stands on water, and Blackrose is drawn joined to the mainland.
- **Places** (all 258, shown on the atlas). Every place now lists what it gives the player, drawn from 47 kinds of thing Skyrim's own places give:
  - travel: fast travel
  - traders: general and specialist traders
  - crafting: forge, alchemy, enchanting, cooking
  - trainers
  - shrine blessings
  - rare ingredients and ores
  - treasure
  - fights, each paired with loot sized to the place's danger, not to your level

  The rest of the places work:
  - **Things Skyrim can't do** (currents, tides, floods and the like) are gone.
  - **Invented places:** none remain, down from 108. Each is re-derived from the lore, along one timeline that all places agree with. Wrecks now come from Senchal, Valenwood, Leyawiin and other neighbours, each with a reason.
  - **Ledgers, tallies and paperwork** are cut, and the document theme with them. Document hooks fell from 71 to 7, all of them an outsider's papers or canon.
  - **Lore check:** a reader who wrote none of it fixed about 300 contradictions with the lore, to zero.
- **Mods.** These are asset and source-place dependencies of the new world only, with their plugins off:
  - Dunmer Settlements of Solstheim
  - Project AHO
  - the Dunmer-style village (Solstheim Expansion, 180133)
  - Ashlander Camp New Zainab
  - Journey to Baan Malur and Morrowind
  - for Dawn of Grey Quarter, whose own file is only a patch: its two parent mods, Gray Quarter Overhaul and Dawn of Skyrim
- **Keys, on both cards.** Tap Space to dodge, hold Space to sprint, Left Shift jumps and climbs, and hold Option (Alt) to walk. The pad is unchanged.
- **The atlas** (https://claude.ai/artifact/HytwbVPXzurvxNZWfvzo6g, version 16) shows the new water and islets, each channel's flow along its curve, and each place's "What it gives the player".
- **Skills learn from your feedback** through one list, `docs/skill-fixes.md` (the rule is in CLAUDE.md). Each fault you report is recorded there at once. When your walk confirms the fix, the lesson goes into the skill as a clean recipe and the row is deleted.
- **Rebuilt and redeployed:** terrain, water, ground textures, plants and rocks, navmesh, the in-game map, and the far distance (LOD at Medium: land, trees, objects and water). The off-game read-back passes {VERIFY}.

**The new checks** (reply on this issue with the letter of any that looked wrong, and where):

- **P. Islets.** Luntoc (`cow ArgoniaBlackMarsh 14 -174`), Uzu-Tegh (`cow ArgoniaBlackMarsh 19 -170`) and Fort Gysilla (`cow ArgoniaBlackMarsh 20 -180`) in Lake Ulaish each stand on a small island with water all round.
- **Q. Helstrom's waters.** Round Helstrom (`cow ArgoniaBlackMarsh -8 -148`) and south-west of it (`cow ArgoniaBlackMarsh -21 -140`): a few main rivers that flow, a few streams, and winding arms of still green marsh.
- **R. Water seams.** Where two kinds of water meet (fly from the river at Q into the marsh): one surface at one level, no gaps, and the colour changes gradually with no straight line.
- **S. Keys.** Tap Space to dodge, hold Space to sprint, Left Shift to jump and climb, hold Option to walk.

**Cost.** The play machine costs about $0.80 an hour while you play and stops itself when idle. AWS is at ${AWS} this month as of 9 November, against the $100 budget. This month will go over unless the machines run less, and I'm keeping them stopped when idle. Claude usage was about {C1}% of the weekly allowance in the last 24 hours and about {C7}% over the last 7 days.
