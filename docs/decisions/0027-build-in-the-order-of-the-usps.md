# 0027: Build in the order of what makes Argonia worth playing: the world and its places, then the story and its people; combat rides the tuned mod stack until its map; the UI in two stages; tools just in time

**Status:** decided 2026-10-29. The owner, opening the 0.1 session, ranked what the game is for, "in descending
order of importance":

1. the world and the places;
2. quests, storyline, people;
3. combat, a closer reproduction of DS1;
4. the stats and progression model, a blend of Morrowind and Souls;
5. UI and dialogue, inspired by Morrowind, uniquely Argonia.

"If we only delivered the first two to high quality, with combat based on the souls-like mod stack, that
wouldn't be a bad achievement." The owner also asked the planner to think critically about the plan as written
(by another agent, "probably not perfect yet"), about which of the old project's ways of working to adopt (the
old project "burned through tokens like crazy"; the 0.0 session was "much cheaper"), and whether the build order
should follow that ranking or whether some low-ranked systems (vastei, the UI) must come first because they are
"much harder to build late".

## What the plan as written got wrong

The plan of 2026-10-28 ([0023](0023-five-parts-de-risk-first.md)) ordered Part 1 by **host risk**: a thread
through dialogue interception, the UI takeover, DS1 combat through the stream, the Souls death loop on the
co-save, and climbing, swimming and boats; quests and barter were left out as "well-trodden". Four things have
changed or were wrong:

1. **0.0 retired most of the combat risk.** The owner played the stock souls-like stack through the stream on
   2026-10-29: "definitely playable", combat "felt reasonably good". What is left (stagger, riposte, backstab
   on one press, kicks and running attacks) is tuning and the combat map ([0019](0019-combat-maps-each-ds1-behaviour-to-a-tuned-mod-or-our-own-ds1-build.md)),
   not a host question. A thread that spends a chunk on it before the world exists is weighted to the owner's
   third priority.
2. **Traversal is not a priority at all.** Climbing, swimming and boats are three dependency mods (route 2).
   Proving they load and run belongs in the stack smoke test (0.2 G3), not in a core-loop chunk.
3. **The world is no longer "mostly data conversion".** [0026](0026-everything-is-built-natively-the-skyrim-way.md)
   made every place a native rebuild from its design with a look loop. That is the longest and most important
   track, with a cost history (Helstrom: 34 agents). 0023's reason for putting the world after the thread
   ("on Skyrim the engine renders, so the world is mostly data conversion") no longer holds. The world track
   must start as soon as G4 proves the recipe and run continuously beside everything else.
4. **The bootstrap built tools first.** 0.1 installed Ghidra with two MCP servers, soulstruct, Paramdex, UXM,
   DSAnimStudio, JPEXS, OpenMW's source, two Wines, msvc-wine, a cross-compile triplet, twelve vendored skills
   and a CLI, then reviewed 78 old test files and triaged 470 old polish rows, before a single record existed.
   That contradicts [0011](0011-ways-of-working-are-inherited-lean.md) §2 (a tool is added after the need it
   meets) and the old project's own lesson ("we build the game, not the tools"). It was also stale: the game
   machine became Windows on 2026-10-28, so Wine and Proton have no job here.

## What must come first anyway (the "harder late" question)

Some things are foundations because every piece of content is written against them. These stay at the front
whatever their rank:

- **The record pipeline and the data shapes** (0.5; one home table per type, stable ids, the FormID allocator):
  everything is generated from them.
- **The sheet** (seven attributes, 27 skills, the formulas; 1.3 §a): every NPC, weapon, perk entry and formula
  reads it. Adding Medium Armor or Spear after a thousand records exist is a migration.
- **The dialogue model** (topics, hyperlinked keywords, learned topics, conditions, disposition; G5 and 1.3 §b):
  every line is written to it, so its shape, not its look, is fixed first.
- **The quest model and the journal as the only quest surface** (no markers, directions; 1.4): every quest is
  written to it.
- **The vanilla quarantine** (0.5 §b) and the **save contract** (1.1): rest as the only save and the death loop
  are additive once the co-save families and the suspend save exist from day one.
- **The game-state seam** (1.1): the typed message schema and the menu router let the UI be replaced later
  without touching a rule.

The rest is additive. **Vastei, the sitting and the death pile** are one chunk on top of the sheet and the save
contract; they should land before quest content scales (rewards and trainers follow their rules), which 1.5 does,
but they do not gate the world. **The UI's look** is a layer over the seam; what is fixed early is the dialogue
window and the journal, because they are the surfaces the content is written for.

## Decision

1. **The order of the parts follows the ranking, after the foundations.** Part 1 is no longer "the host-risky
   systems"; it is **the first place, complete**: Claywater Station with people who talk, a quest that runs
   through the journal, the sheet, carrying, rest, death and saving, with combat on the tuned stack. Part 2
   builds the world and the slice places first in its systems order: places, people, dialogue, quests, then
   combat's map, progression, the rest.
2. **The world track starts after G4 and never stops.** 2.W1–2.W4 (the whole worldspace: terrain, water, regions
   and roads, vegetation, navmesh, LOD) run as their own lane beside Part 1 on the build VM; 2.W5 (the slice
   places) starts as soon as navmesh holds. Part 1's exit does not wait for them; Part 2's does.
3. **Combat rides the tuned mod stack until its map.** The 0.0 stack, wired to the sheet (damage, stamina, carry
   and protection from the Morrowind-based numbers), with the DS1 gamepad layout, lock-on and one archetype at
   fixed danger, is Part 1's combat (1.6). The combat map, the measured DSR numbers (G6), runtime timing (G9) and
   the built rows are 2.7. 0019 is unchanged in substance: DS1's whole system stays the target and the map
   decides row by row; only when the map is made moves.
4. **Traversal is in the base stack from the start** (owner, 2026-10-29: FreeClimb 193552, Swimming Extensions
   189821, Sailable Ship VR and SE 72070 as the MVP boat): proved in the stack smoke test (0.2 G3: climb a wall,
   swim and dive, board and sail a boat), usable at the first place as installed, and built to our rules in 2.13
   and 2.15. 1.6 no longer exists as a traversal chunk.
5. **The UI is built in two stages** ([0017](0017-one-coherent-argonian-ui-approach-chosen-with-the-owner.md)
   stands; G11 still chooses the approach with the owner, with this as the recommendation):
   - **Stage one (1.2):** Pelagiad everywhere (the font library and `fontconfig.txt`); a paper theme over the
     vanilla and SkyUI menus from an existing permissive skin family where its permissions allow (the Dear Diary
     paper menus, their Wood and Paper skin and the Oblivion-like loading menu are the candidates the owner
     named; the owner confirmed on 2026-10-29 that Dear Diary's permissions allow it); the compass and quest
     markers gone; **our own dialogue window and journal** (content is written for them); and, by the owner's
     2026-10-29 reply, **our own HUD and the parchment chart** (a sketch of the province, its roads and seven cities
     always visible, detail revealed by exploring), in the chosen approach. Morrowind-style magic as a dependency (Magic Expanded, 133435) is checked here too.
   - **Stage two (2.2, 3.1, 3.2):** the whole design system, the Morrowind pause-menu windows (draggable,
     resizable, remembered), every remaining screen, chargen, the main menu; it opens with the OpenMW analysis
     (what to use or be inspired by), as the owner asked.
   The seam (1.1) makes stage two a replacement of views, never of rules. The soul contract's C10 and C11 are met
   at stage two.
6. **Quests enter the core loop.** 1.4 writes one Claywater quest through the writing skills, generates it into
   records, and runs it through the journal with directions and no markers. The owner's verdict in 1.7 is on
   the first two priorities: the place, the talk, the quest, and "is this the game".
7. **Tools arrive at first use.** 0.1 installs what Part 0 uses: Python, .NET with Mutagen and Spriggit, Node
   for the UI harness, rtk, the guards and the gate. Ghidra and its MCP servers, the Souls data tools,
   JPEXS, OpenMW's source, Blender and the universal-modder CLI are installed by the chunk that first needs
   them, with a lock entry. universal-modder's knowledge base and playbooks are referenced from the research
   index and read in place; its skills are vendored one at a time when a brief uses one.
8. **The three old-repo reviews are cut.** The old tests are not reviewed (0026 already says they are read for
   intent only; 2.5 and 2.12 write their tests from the design docs). The old polish backlog is not triaged
   (three.js polish). The goals list is a short index into the imported design docs, which are the goals.
9. **Ways of working stay lean, and the planner builds directly where delegation costs more than the work.**
   See [0011](0011-ways-of-working-are-inherited-lean.md) and ways-of-working §6: rtk in front of every shell
   command; no review gate, no lane watchers, no scheduled check-ins, no reader panels by default.

## Consequences

- 0023 is adapted: the five parts and the gates stay; Part 1's thread is re-cut and the world track starts in
  Part 1; its "what dominates total cost" paragraph still holds.
- 0019: the combat map moves from 1.4 to 2.7; 1.6 is the stack on the sheet.
- 0017: the two-stage recommendation goes into G11's study.
- The briefs: 0.1 rewritten (lean), 0.2 (Windows, G3 carries traversal, G7 joins 2.W2, G6 and G9 join 2.7, G10
  slimmed to the rows Part 1 needs), Part 1 (1.2 stage one, 1.4 quests, 1.6 fight on the stack, 1.7's verdict),
  Part 2 (dependency order; 2.2 stage two; 2.7 the map; 2.13 and 2.15 own traversal's first rung).
- PROGRESS, PLAN §4–5, phases/README and the owner brief are rewritten to match.
