# Owner rulings that still bind

The owner's rulings from 2026-10-27 to 2026-11-05 that survive the pivot ([0038](decisions/0038-the-pivot-bmv-is-the-world.md)),
in the owner's terms. Everything else the owner said before the pivot is in git history
(`docs/owner-brief.md`, `docs/inherited-rulings.md` before this commit) and no longer binds. New rulings are
added here the day they are made, with the date and the issue.

## The goal (2026-11-05)

- Vanilla Skyrim + Black Marsh & Valenwood + the collection xyf1u3 for soulslike combat, out of the box +
  FreeClimb + Morrowind magic (Magic Expanded). BM&V is the default world: a start mod puts the player in Black
  Marsh; the main quest, dragon attacks, the civil war, the Thieves Guild couriers and Skyrim's radiant quests are
  stopped.
- A new game takes the player straight into our own authored opening, nothing via Helgen and no alternate-start
  menu, as Enderal does it (2026-11-05).
- No owner test in Phase 0; the first walk is after Phase 1, with a Vanilla Skyrim card and the Argonia card
  on the play page to try both at once (2026-11-05).
- Agents verify by reading the files the game will consume (the ESP, the scripts, the DLLs, the profile) and
  loop until that read meets the bar; they never run the game themselves (2026-11-05).
- The BM&V census into the relational story data runs in Phase 1, beside the stack (2026-11-05).
- Write and review the first act before building any block, so the blocks are the ones the story needs; aim for
  a small set of blocks that combine into many quest dynamics, so proving each once (and their connectors once)
  proves every quest built from them, like a proof by induction; if a block is too hard, re-author the quests
  around the blocks that work (2026-11-05).
- An offline interactive 2D map of BM&V's world, linked to the mined place records, for the owner and agents
  (2026-11-05).
- Decided by the agents under the owner's hand-over (2026-11-05, "gate nothing on me; full permission"): the four
  free Creation Club files' self-starting quests are stopped like vanilla's; our plugin ships `Argonia.ini` to blank
  the race-menu bound-hands pose, as Live Another Life does; the opening marker stands on Lilmoth's pier, a dock
  arrival; the Creation Kit EULA was accepted with the owner's OK.
- Phase 2 adapts the entire quest system and every faction line to BM&V's world (minor world edits allowed), keeping
  each line's spirit, designed once as a consistent whole with no clashes; minor lines adapted or dropped; a wider
  minor-quest build-out is a Phase 5 placeholder (2026-11-05).
- BM&V is used whole, all four plugins and every file of both ModDB parts; all of it goes through the census and the
  map (2026-11-05).
- Then our storyline, quests and factions on top of BM&V's world, with minimal tweaks (NPCs, items, bosses,
  creatures added, removed, changed). This is the main work, in phases.
- Process as light as possible. Agents avoid in-game testing if at all possible; the owner tests. Test a small
  number of building blocks once, then build everything from them.
- Delete as much as possible; this was a throwaway repo. Keep the build machine and the Paris g6.xlarge play
  machine; keep the rule that build-machine agents assume frequent interruption.

## Machines and money

- AWS London; the $100 a month cap is for AWS infrastructure only and binds from November 2026.
- The build VM is on demand (the owner's change, 2026-11-05) and runs only about 8 to 10 hours a day; the play
  machine stays spot. Every job resumes from where it got to after an interruption (decision 0037).
- Agents may always start and stop the game machines; a stop is never a reason to wait (2026-10-30).
- The game machine runs Windows (the licence cost is approved); the build VM stays Linux.
- Tidy up: delete temporary files, captures and anything we will never need, on the VM and in the bucket; never
  archive rubbish "to be safe" (2026-11-02). Claude usage is reported as a percentage of the weekly allowance
  (about 1% per $19), never in dollars.
- Stale machine images are deleted (2026-11-02, "explicit permission"); the owner deleted the last ones and the
  play machine itself on 2026-11-05.
- The play machine must not be interrupted often; the owner will pay a bit more, but not on-demand (2026-10-31).
  A g6.xlarge is comfortably strong enough; use whichever region is expected to interrupt less at a similar
  price (2026-11-05); Paris has been the machine since 2026-10-31.
- Changes to the owner's live services (the play-switch Worker, the play page, the stream config) get an owner
  call first (2026-10-30).

## Playing

- The owner plays entirely in third person (2026-10-29).
- Controls: keyboard and mouse on the Mac; on the phone the GameSir X2s or on-screen touch; the whole game must
  be playable by touch (2026-10-28). Moonlight's Android app is an option.
- The gamepad follows DS1 Remastered on Switch by button position: roll on the right button, R1/R2 light and
  heavy, L1 block, L2 parry (2026-10-29). The collection's own bindings are the starting point now.
- Latency and stream health are logged automatically; the owner never records anything by hand (2026-10-28).
- Cheats and shortcuts (god mode, item grants, teleports, setstage) are allowed whenever they make something
  easier to test (2026-10-28).

## Working with the owner

- One GitHub issue per owner check or owner call (`tooling/owner_inbox.py`), assigned to the owner, closed when
  answered; an owner comment wakes the build VM (wake.yml). Only the owner's own GitHub text counts; the repo
  is public (2026-10-31).
- Owner check-ins are plain English: one check per bullet, places named, how to reply, costs.
- Hand over nothing partially finished; "known issues" only for what truly cannot be fixed, each with why
  (2026-10-30, 2026-11-03, 2026-11-04).
- Method changes are applied and recorded without asking; a goal change is an owner call (2026-10-28).
- The owner judges look; agents check for Nordic tells, never feel (2026-10-30, #43).
- Agents stop only when the work is complete, a blocker needs the owner, or at a handover the owner asked for.

## The game

- Set in Argonia (Black Marsh), 4E 201; no Nordic element reaches the player through what we add (0006);
  Skyrim's own voiced barks stay, filtered of lines naming Skyrim places, people or events (2026-10-31, #22).
- Dialogue is unvoiced text, Morrowind-like in structure and style; the writing rules live in the
  `dialogue-write` skill and `story/design/text/` (2026-10-27, 0024).
- Nothing is ever levelled against the player: creatures, enemies, loot, chests; danger bands are fixed and the
  player grows into them (2026-11-01, 0035).
- Quests have "action" (the player's skills used, varied), no talk-to-X-then-Y quests; the old main quest,
  factions and quest designs are the foundation, improved not replaced (2026-10-28).
- A detectives' faction, rival to the assassins and thieves (0025).
- A creature from a mod is used as its mod designed it (2026-10-30).
- Magic is mostly covered by Magic Expanded; reuse it rather than build magic (2026-10-30).
- Interiors may look Nordic where a borrowed interior is all there is (2026-10-30); exteriors are BM&V's.
- Armour pieces stay as base Skyrim has them (2026-10-31, #21).
- Climb anything big enough, Breath of the Wild style, through FreeClimb (2026-11-01).
- Parry, riposte and backstab are what the owner called souls-like (2026-10-29); the collection is used out of
  the box first, and that ruling is revisited only if the owner misses them.

## Writing

- Lines read as if they were Morrowind's, adapted to Black Marsh; the old written lines are not models.
- No personification, no verbless fragments, no dangling modifiers, nothing opaque to the player; British
  punctuation; held-back information says so; banned constructions live in `dialogue-write/bans.yaml`.
- Speakers and players may be any of the ten races; address and manner vary by player race, faction and rank.
- Quests, places, dialogue, characters and facts are consistent first time, by how they are written.
- Every world, people and quest call cites the lore dossiers (`story/lore/`) or the extrapolation (0032).
