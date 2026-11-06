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

From any save or a new game on the Argonia card, about ten minutes, all on Lilmoth's dock. Open the console (`~`) and
type `startquest ARG_BlockTest`. After each step, `sqs ARG_BlockTest` in the console shows the stages done. Reply on the
issue with the number of any step that did not happen as written (and the game hour for step 13).

- [ ] 1. Anywhere: type `startquest ARG_BlockTest`. You are moved onto Lilmoth's fishing dock, 3 m west of the Dock
      Keeper; the journal has "Block Test" with "Speak to the Dock Keeper"; no Naga anywhere on the dock.
- [ ] 2. Talk to the keeper, pick "I am ready for the test.". "Ship Door Key" is in your inventory; a wooden bowl,
      "Test Token", is now on the planks about 5 m south of him; click him in the console, type
      `getrelationshiprank player`: it says 1.
- [ ] 3. Pick up the Test Token. The objective becomes "Bring the token to the Dock Keeper";
      `getglobalvalue ARG_BT_Global` says 1.
- [ ] 4. Talk to the keeper, pick "Here is the token.". The token leaves your inventory;
      `player.getinfaction ARG_BT_Faction` says 1.
- [ ] 5. Talk to the keeper again. "Talk me into it." shows, "Talk me into it, master." does not. Pick the first: the
      Dock Walker appears 2 m north of the keeper and the two speak two lines each (subtitles, no voice).
- [ ] 6. Watch. When the talk ends the walker walks south-east down the dock toward the ship and stops where the
      dock's walkable ground ends (about 7 m from the keeper); a mudcrab appears about 15 m south-east and comes for
      you; the walker may flee it but goes back to her walk, she does not stand still.
- [ ] 7. While she walks: crouch out of her sight behind the dock clutter and type
      `player.getdetected ARG_BT_WalkerRef` (says 0), then stand in her view and type it again (says 1).
- [ ] 8. Save, then load that save. The walker carries on to her spot, the crab is still there, the journal as before.
- [ ] 9. Kill the mudcrab. The objective becomes "Walk to the ship door"; click the crab's body, type `getlevel`: 4.
- [ ] 10. Walk east to the ship's door (the hatch about 20 m east of the keeper) and stand beside it. `sqs
      ARG_BlockTest` shows exactly one of 71 or 72 done, never both, and 75 done; objective "Open the ship door".
- [ ] 11. Save, load, walk away from the door and back. Still exactly one of 71 or 72.
- [ ] 12. Open the ship door. It opens with the key (no lockpicking) and you are inside "Test Ship" (the name on the
      loading screen and the map); objective "Tell the Dock Keeper".
- [ ] 13. Go back out, talk to the keeper, pick "The crab is dead.". Between 6 in the morning and 8 at night he says
      "By day, too. Done.", otherwise "At this hour. Done." (tell us the hour); 10 gold in your inventory; "Block Test"
      shows complete and a second entry, "Block Test, the end": "The second quest started from the first."

## Later (not yet buildable)

- The in-game world map is still Skyrim's, and BM&V labels Lilmoth "Lolmoth" (docs/phases/5-scale.md).
- Phase 4: play the first story slice from a new game.

## Done

- Climbing works (Phase 1 walk, 2026-11-06).
