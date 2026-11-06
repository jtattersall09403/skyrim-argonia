# Owner walk checks owed

The one list of in-game checks the owner owes. Owner: tick a box (edit this file on GitHub, or reply on the issue
named) when you have done it; write a line under it if something was wrong. Agents: read this before posting a walk,
add a check here when you build something only the owner can see in game, and move a ticked check to "Done" in the
commit that acts on it. A check that passed is never re-asked.

How to play: the Argonia card on Moonlight starts the game (the play machine starts on demand and stops itself after
15 minutes idle). Console: the `~` key (on a Mac keyboard over Moonlight, the key left of `1`).

## Next walk: the stack in BM&V, again (Phase 1, issue #49)

From a new game on the Argonia card.

- [ ] New Game shows the race menu with the character's face bare (no helmet, no armour).
- [ ] After the race menu you stand on a wooden dock with lanterns, at the "Lilmoth Dock" map marker (not Hereguard
      Plantation), in third person, in roughspun clothes, with a journal line.
- [ ] The inventory holds an Imperial sword and an Imperial light shield; the Magic menu lists Morrowind spells
      (Mark, Recall, Jump, Slowfall, Water Walking, Fire Touch, Force, Burden, Teleport and others; Magic Expanded has
      no Levitate, so Jump and Slowfall stand in).
- [ ] Cast Mark, walk away, cast Recall: you return to where you cast Mark.
- [ ] Weapon drawn: you walk or sprint but do not run. This is Arena Movement's design ("you can walk, you can
      sprint, you just can't run around"). Reply "keep" or "faster": the faster variant runs at about twice walking pace.
- [ ] Dodge (issue #51): tap Alt (pad: LB) for under half a second. Standing still you backstep; moving you roll in
      that direction. Holding it sprints.
- [ ] Guard counter (issue #51): block an enemy's hit, then power attack within 1.5 seconds. There is no timed
      parry in the collection; #51 asks whether to add one.
- [ ] Lock-on (pad: right stick click; keyboard: tap F), sprint and climbing, on the Mac keyboard and on the GameSir X2.
- [ ] The HUD shows TrueHUD's player bars, not vanilla Skyrim's.

## Phase 3 walk: the building blocks test quest

Posted when built (docs/phases/3-building-blocks.md). One console command, about ten minutes.

- [ ] Every step of `ARG_BlockTest` happens as the issue says (list any step that did not).

## Later (not yet buildable)

- The in-game world map is still Skyrim's, and BM&V labels Lilmoth "Lolmoth" (docs/phases/5-scale.md).
- Phase 4: play the first story slice from a new game.

## Done

- Climbing works (Phase 1 walk, 2026-11-06).
