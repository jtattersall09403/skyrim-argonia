# Owner walk checks owed

The one list of in-game checks the owner owes. Owner: tick a box (edit this file on GitHub, or reply on the issue
named) when you have done it; write a line under it if something was wrong. Agents: read this before posting a walk,
add a check here when you build something only the owner can see in game, and move a ticked check to "Done" in the
commit that acts on it. A check that passed is never re-asked.

How to play: the Argonia card on Moonlight starts the game (the play machine starts on demand and stops itself after
15 minutes idle). Console: the `~` key (on a Mac keyboard over Moonlight, the key left of `1`).

## Next walk: the stack in BM&V, again (Phase 1, issue #49)

From a new game on the Argonia card.

- [x] New Game shows the race menu with the character's face bare (no helmet, no armour).
- [x] After the race menu you stand on a wooden dock with lanterns, at the "Lilmoth Dock" map marker (not Hereguard
      Plantation), in third person, in roughspun clothes, with a journal line.
- [X] The inventory holds an Imperial sword and an Imperial light shield; the Magic menu lists Morrowind spells
      (Mark, Recall, Jump, Slowfall, Water Walking, Fire Touch, Force, Burden, Teleport and others; Magic Expanded has
      no Levitate, so Jump and Slowfall stand in).
- [ ] Cast Mark, walk away, cast Recall: you return to where you cast Mark. A new character cannot afford them
      (they are Expert Alteration spells and the test kit gives them early on purpose), so first type in the console
      `player.setav alteration 100` then `player.setav magicka 600`, and wait a few seconds for magicka to fill.
- [x] With a weapon drawn you can run (Arena Movement's faster variant, owner #53).
- [ ] Dodge (issue #51): standing still with no direction held, tap Alt (pad: B) for under half a second: you take a
      quick backstep (a hop back), not a roll. Fixed 2026-11-07: the standing tap played Dynamic Dodge's back roll; it now
      plays the same mod's backstep clip whenever no direction key is held.
- [x] Dodge (issue #51): tap Alt (pad: B) for under half a second. moving you roll in
      that direction. Holding it sprints.
- [ ] Queue attack during roll, our plugin: press attack during a roll, does it execute after roll completes?
      Fixed 2026-11-07: our plugin (ArgoniaDodgeBuffer) could not watch the dodge after a New Game until the next
      save was loaded; it now hooks in on your first key press. Test from a New Game: roll, press attack mid-roll, and
      the swing should come straight out of the roll.
- [ ] Pad layout (issue #51, GameSir X2): RB light attack, RT heavy (power) attack in one press, LB block, LT shout,
      d-pad left or right opens the Tween menu (skills, items, map, magic).
- [ ] Parry and riposte (issue #51): lock on to a bandit, hold LB (keyboard: right mouse) and tap RB (left click)
      just as their blow lands. They stagger and kneel; press RB (left click) again for the riposte.
      2026-11-07: the mods were loaded, but none of your 37 parry attempts landed inside the parry window, so the
      window is widened to Elden Parry's own setting (0.3 seconds, was 0.2). Start the bash a fraction before the blow
      lands, not as it lands. Fighting bandit, in the console: `player.placeatme 00039CF6`, then click him and type
      `additem 00012EB7 1` and `equipitem 00012EB7` (a level 1 Imperial bandit with an iron sword, who fights back).
- [ ] Backstab - block+attack from behind, then attack. Lock on (F, or right stick click), stand behind them, hold
      block and tap attack (a light bash): they are knocked down; then attack for the execution. A bandit who stands
      still: `player.placeatme 00039CF6`, click him, `setav aggression 0` (he stays where he is and does not turn to
      you until you hit him). If he still attacks, click him and type `tai` instead (his AI is off; type `tai` again
      to turn it back on). Say which of the two you used and whether the knockdown played.
- [x] Guard counter (issue #51): block a hit, then power attack (RT, or hold left click) within 1.5 seconds.
- [ ] Combat - enemies stagger per poise system. 2026-11-07: our stack had no poise mod; Chocolate Poise is added (why
      not the two you named: issue #54; reply there). Hit a bandit with light attacks: after several hits he staggers; a
      power attack staggers sooner. Bandits hitting you stagger you the same way.
- [ ] Lock-on (pad: right stick click), sprint and climbing, on the GameSir X2.
- [x] Lock-on (keyboard: tap F), sprint and climbing, on the Mac keyboard.
- [ ] The HUD shows TrueHUD's player bars (health, magicka, stamina), not vanilla Skyrim's, all the time, even at
      full health. (Your walk of 2026-11-07 saw none: TrueHUD hides each bar while it is full, and hides vanilla's; now
      they always show. There is no compass on purpose.)

## Phase 3 walk: the building blocks test quest

From any save or a new game on the Argonia card, about ten minutes, all on Lilmoth's dock. Open the console (`~`) and
type `startquest ARG_BlockTest`. After each step, `sqs ARG_BlockTest` in the console shows the stages done. Reply on the
issue with the number of any step that did not happen as written (and the game hour for step 13).

- [ ] Talk (W-talk). Stand on Lilmoth's dock (`coc` is not needed: the opening puts you there) and walk about
      200 m south-west to a small village on the marsh. Talk to Flaa Heet (the headman, beside a food barrel) and the
      villager standing a few metres west of him: each opens a menu with topics such as "Yourself", "Directions",
      "Latest rumours", "Plants and ingredients"; each answer shows as a subtitle. Check one answer is true: the
      villager says wild leeks grow just east of the village (go and pick one), or Flaa Heet says three dead Dunmer
      lie at the east end of the dock (go and look). Also try the three Argonian sellswords and the drunk
      Deep-In-His-Cups on the shore south-west of the dock. Reply with anyone who still opens nothing.
- [x] 1. Anywhere: type `startquest ARG_BlockTest`. You are moved onto Lilmoth's fishing dock, 3 m west of the Dock
      Keeper; the journal has "Block Test" with "Speak to the Dock Keeper"; no Naga anywhere on the dock.
- [x] 2a. Talk to the keeper, pick "I am ready for the test.". "Ship Door Key" is in your inventory;
- [ ] 2b. a wooden bowl, "Test Token", is now on the planks between where you started and the keeper, about 1.5 m
      from him (moved after your walk of 2026-11-07: it had been placed inside the planks and fell through). In the
      console type `ARG_BT_KeeperRef.getrelationshiprank player` (no clicking needed): it says
      "GetRelationshipRank >> 1.00".
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
