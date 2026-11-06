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
- [ ] Dodge (issue #51): tap Alt (pad: B) for under half a second. Standing still you backstep; moving you roll in
      that direction. Holding it sprints.
- [ ] Pad layout (issue #51, GameSir X2): RB light attack, RT heavy (power) attack in one press, LB block, LT shout,
      d-pad left or right opens the Tween menu (skills, items, map, magic).
- [ ] Parry and riposte (issue #51): lock on to a bandit, hold LB (keyboard: right mouse) and tap RB (left click)
      just as their blow lands. They stagger and kneel; press RB (left click) again for the riposte.
- [ ] Guard counter (issue #51): block a hit, then power attack (RT, or hold left click) within 1.5 seconds.
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
