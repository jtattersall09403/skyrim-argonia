# Owner walk checks owed

The one list of in-game checks the owner owes. Owner: tick a box (edit this file on GitHub, or reply on the issue
named) when you have done it; write a line under it if something was wrong. Agents: read this before posting a walk,
add a check here when you build something only the owner can see in game, and move a ticked check to "Done" in the
commit that acts on it. A check that passed is never re-asked.

How to play: the Argonia card on Moonlight starts the game (the play machine starts on demand and stops itself after
15 minutes idle). Console: the `~` key (on a Mac keyboard over Moonlight, the key left of `1`).

**Start a new game for this walk.** Several fixes only take on a new character (the HUD defaults, no health
regeneration, the Levitate spell, the renamed people), and your old save has the Block Test used up.

## 1. The stack: HUD, movement, magic and combat (Phase 1, issue #49)

Fixed after your walk of 2026-11-07 (feedback in `tmp/walk-2-feedback.md`).

- [ ] **TrueHUD bars**, on the dock straight after the new game, without opening any menu: your health, magicka and
      stamina bars sit at the top left, a little in from the corner, and show when they change (sprint a few
      seconds: the stamina bar shows, then fades once full). The vanilla bars at the bottom never show. In Esc, Mod
      Configuration, TrueHUD, Player Widget you should see your settings already there: Dynamic for all three bars,
      width 150, minimum 50, maximum 500, scale bars ticked, anchor X 0.045, Y 0.105. (Our earlier setting used the
      wrong number: 2 is "In combat", Dynamic is 1.)
- [ ] **No health regeneration.** In the console type `player.damageav health 30`, close it and wait 30 seconds
      out of combat: health stays down. `player.damageav magicka 30` and `player.damageav stamina 30`: both refill on
      their own. A healing spell or potion still heals (`player.restoreav health 30` puts it back).
- [ ] **The compass** is back at the top of the screen outside. Quest markers stay off, as before; say if you want
      them on too.
- [ ] **Running with a weapon drawn.** Draw the sword and move forward without sprinting: you run as fast as with
      it sheathed, not a fast walk. (The faster Arena Movement variant only ran at about half speed; our plugin now
      sets the drawn-weapon run to the same speed as the sheathed run.)
- [ ] **Levitate** (Magistrate's Levitate, new in the stack): the Magic menu, Alteration, lists "Levitate". Equip
      it and hold cast: you rise and float; look up or down to steer; let go of cast to come down.
- [ ] **Mark and Recall.** Cast Mark, walk away, cast Recall: you return to where you cast Mark. They are Expert
      spells, so first type `player.setav alteration 100` then `player.setav magicka 600` and wait a few seconds.
- [ ] **Dodge, standing still.** You asked us to check the double backstep: it is Dynamic Dodge's own backstep
      animation as the mod ships it (one clip, about 5 metres in two pushes, with two footsteps in it), not two
      dodges firing. Nothing changed. Tick this if that is fine, or say "cut it to one step" and we will look for a
      shorter clip.
- [ ] **Attack queued during a roll** (our own plugin): from the new game, roll and press attack mid-roll; the
      swing comes straight out of the roll.
- [ ] **Parry**, against a bandit (`player.placeatme 00039CF6`, click him, `additem 00012EB7 1`, `equipitem
      00012EB7`): hold block and tap attack just as his swing lands. The window is now half a second (it was 0.3),
      to allow for the stream's delay. He staggers and kneels; attack again for the riposte. Say if it is now too
      easy or still too hard.
- [ ] **Backstab.** It is Rim Parry's: the light bash (hold block, tap attack; pad: hold LB, tap RB) from straight
      behind the bandit (within about 30 degrees of directly behind; a little to one side fails). The bandit drops to
      his knees; attack again to execute. Try first on a bandit busy with something else (no `tai`); then click a
      bandit in the console, type `tai`, close the console and try again, so we learn whether a frozen bandit can be
      backstabbed. If nothing happens, say where you stood, whether lock-on (F) was on, and what animation played.
- [ ] **Poise.** Hit a bandit with light attacks: after several hits he staggers; a power attack staggers sooner.
      Bandits hitting you stagger you the same way.
- [ ] **Pad layout** (GameSir X2): RB light attack, RT heavy (power) attack in one press, LB block, LT shout, d-pad
      left or right opens the Tween menu (skills, items, map, magic).
- [ ] **Lock-on, sprint and climbing on the pad** (lock-on: right stick click).

## 2. Lilmoth: windows and walk-in houses (new)

- [ ] Walk up from the dock to the tall stone-and-timber houses behind it (the ones in your screenshot of
      7 November). The arched windows on all five houses, the half-ruined one too, show leaded glass (it glows
      faintly at night), not flat pale-blue panes. Cause: BM&V ships copies of those vanilla house meshes edited for
      a lighting mod (ELFX) whose textures it does not include; the stack now leaves those 62 copies out so the
      game's own meshes draw. If you pass a canvas army tent (Murkwood, the temples, Longmont), it should look like
      plain canvas too.
- [ ] **Walk-in houses** (new: a census of every BM&V settlement now lists 1,889 shell buildings, 86 of them
      walkable from the street with no loading door; quests and homes will use them as rooms). While at those houses,
      walk in through any open doorway of the five tall houses and of the ruined farmhouses just south-west of the dock.
      For each you try, say: can you walk in, is there a floor (not sunk into the ground or floating), and could a
      person live or a scene play there. No console needed.

## 3. The building blocks: only what is still unproved (Phase 3)

Steps 1 to 6, 8, 9, 12 and the keeper's reply in 13 passed on 2026-11-07 and are not asked again. Each check below
starts the test quest and jumps straight to the stage it needs, so there is no replay. Reply with the letter of any
check that did not happen as written.

- [ ] **A. The token on the planks** (a new, more precise way of placing things: we now read the shape of the dock
      planks themselves, not just the walkable ground). Console: `startquest ARG_BlockTest`, then `setstage
      ARG_BlockTest 20`. A wooden bowl, "Test Token", appears on the wooden dock planks about 3 m east of the Dock
      Keeper, not on the ground beside you, and you can pick it up there. (Last time it was placed on land: the spot
      we picked from the walkable ground was land, not the planks.)
- [ ] **B. Does the walker see you** (step 7). Same game: `setstage ARG_BlockTest 50`. The Dock Walker appears and
      talks with the keeper, then walks toward the ship (a mudcrab appears south-east; ignore it or kill it). While she
      walks, crouch out of her sight behind the crates and type `ARG_BT_WalkerRef.getdetected player`, then stand in
      front of her and type it again. Pass: hidden it prints 0, in view 1. (Last time the line was the wrong way round:
      `player.getdetected ...` asks whether you see her, hence the -1000.) If the console refuses it, click her and
      type `getdetected player`.
- [ ] **C. Two trigger boxes, one result** (steps 10 and 11). A new game (the boxes are used up once fired):
      `startquest ARG_BlockTest`, then `setstage ARG_BlockTest 65`. Walk east to the ship's door (the hatch about
      20 m east of the keeper) and stand beside it. Type `sqs ARG_BlockTest`, `getglobalvalue ARG_BT_RaceRuns` and
      `getglobalvalue ARG_BT_RaceHits`. Pass: stages 71 and 75 are done (there is no 72 any more), RaceRuns says 1,
      the objective reads "Open the ship door". Tell us RaceHits (2 means both boxes fired at once and the guard
      held; 1 means one box fired first). Then save, load, walk away from the door and back, and type the two
      `getglobalvalue` lines again: the same numbers. (Last time both 71 and 72 were done: both boxes fire in the same
      instant, so the quest now has both set one stage that guards itself, as Skyrim's own quests do.)
- [ ] **D. The finished quests in the journal** (step 13). Any game: `startquest ARG_BlockTest`, then `setstage
      ARG_BlockTest 90`. You get 10 gold. Open the journal (J). Pass: "Block Test" ("I passed the block test.") and
      "Block Test, the end" ("The second quest started from the first." and "The second quest ended with the
      first.") are listed as completed. Also tell us what the Stats page says for "Quests Completed" and "Side Quests
      Completed". (They were Misc quests, which Skyrim drops from the journal when done; they are now Side Quests that
      end the way Skyrim's do.)

## 4. Talk to Lilmoth's people (block W-talk, again)

Everyone in and around Lilmoth now opens a talk menu, shows their own name under the crosshair, and should sound
different from their neighbours: 30 people (12 before), each with their own temperament, wants, grudges and local
knowledge written for them, and not everyone knows the same facts. Talk to as many as you like; for each one you
try, ask the topic named and check the fact where it says. Reply with anyone who opens nothing or still shows an old
name ("Villager", "Argonian Boat Captain", "New Order Soldier"), any two who sound alike, and any fact that is not
true where it says. Walking time for all of them is about 40 minutes; nothing to type.

#### Flaa Heet's village (about 200 m south-west of Lilmoth Dock, where the opening puts you)

- [ ] **Flaa Heet**, headman of the marsh village south-west of Lilmoth Dock; stands beside the village cooking spit, the middle of his people. Ask "Directions" and check: Lilmoth Dock lies about 200 m north-east of here.
- [ ] **Peeks-Under-Boats**, a hatchling of Flaa Heet's village who runs errands and gets under feet; stands at the north edge of the village, where he can see the boats and the path to the fish barrels. Ask "Plants and ingredients" and check: Wild leeks grow about 45 m north-west of here, near the fish barrels.
- [ ] **Tseeta**, stall seller of food and small goods for the village; stands her stall on the north side of the village, the first stall anyone walking in from the dock meets. Ask "Directions" and check: The place the map calls the Docks lies about 380 m east-north-east of here, past Lilmoth Dock.
- [ ] **Hums-To-The-Rain**, net-mender and gatherer of the village; stands on the west side of the village, between the spit and the second hearth, where the nets dry. Ask "Plants and ingredients" and check: Gourds grow about 90 m north-north-east of here, and a swamp fungal pod about 100 m north-north-east.
- [ ] **Okeeh-Jas**, stall seller of food and small goods, south side of the village; stands her stall on the south side of the village, near the boat landing. Ask "Directions" and check: A rowboat is drawn up at the south landing about 15 m south of here.

#### The shore track south-west of the dock

- [ ] **Breaks-The-Oar**, sellsword and brawler, the fists of a band of three; stands the band's camp on the shore track south-west of Lilmoth Dock, by the bedrolls. Ask "Dangers nearby" and check: The dead walk outside Lilmoth's walls; there are Walking Dead about 100 m north-north-west of here.
- [ ] **Heem-Tsal**, battle-mage of fire, the band's spell and its scholar; stands a few paces from the band's bedrolls on the shore track, on the side away from the others. Ask "Directions" and check: A Dwemer ruin lies far to the east, about 435 m east of here.
- [ ] **Keeps-Both-Edges**, swordsman with two blades, the band's watch; stands beside Breaks-The-Oar at the band's camp, facing the track so nothing comes up it unseen. Ask "Dangers nearby" and check: More dead walk among the gravestones north of Lilmoth's walls, about 195 m north-west of here.
- [ ] **Deep-In-His-Cups**, drinker and talker, of no settled trade; sits out on the shore track south-west of Lilmoth Dock, where the guards do not bother him. Ask "Directions" and check: Flaa Heet's village lies on the marsh about 145 m south-west of here.
- [ ] **Sheeh-Vos**, thief and scavenger of the dock's edges; stands among the leeks on the shore north of the band's camp, close enough to the dock to watch it. Ask "Plants and ingredients" and check: Wild leeks grow right here, about 20 m west-south-west of him.
- [ ] **Waits-For-Lanterns**, thief who works the dark, a planner of small jobs; stands a few paces east of Sheeh-Vos among the leeks, nearest the dock. Ask "Dangers nearby" and check: Walking Dead wander outside the walls about 115 m north-west of here.

#### Below Lilmoth's walls, by the water

- [ ] **Uleesh**, fisher of the shallows below Lilmoth's walls; stands in the open water south of the walls, among the lily pads where the fish feed. Ask "Dangers nearby" and check: Slaughterfish swim in the water about 15 m north of here, and more about 10 m south-west.

#### Hereguard Plantation (west of Lilmoth; the map marks it)

- [ ] **Reads-The-Shallows**, boat captain who carries the plantation's rice to Lilmoth; stands the plantation's north-east edge by the goats, waiting for a load. Ask "Directions" and check: Lilmoth Dock lies about 365 m east of here.
- [ ] **Hurz-Weel**, plantation hand who keeps the house's yard and stores; stands in the yard by the plantation house on its west side, between the barrels and the benches. Ask "Directions" and check: The walled part of Lilmoth lies about 200 m east-north-east of here.
- [ ] **Lifts-The-Sacks**, plantation hand and loader; stands in the middle of the plantation among the goats and chickens, between the house and the workbenches. Ask "This place" and check: Goats and chickens keep the yard about 10 m west-north-west of here.
- [ ] **Salith**, street seller of food and small goods to the plantation's hands; stands on the plantation's east side near the cooking spit, where the hands eat. Ask "Plants and ingredients" and check: A gleamblossom grows about 60 m south of here.
- [ ] **Okan-Wul**, plantation hand who builds and mends the huts; stands near Salith on the east side of the plantation, by the huts he keeps standing. Ask "This place" and check: The hands' huts stand about 35 m west of here, and more about 40 m west-north-west.
- [ ] **Stares-At-Clouds**, plantation hand who watches the flood water and the paddies' far edge; stands the north-east edge of the plantation, beyond the huts, where the water comes in. Ask "Directions" and check: the walled part of Lilmoth lies about 110 m east of here.
- [ ] **Folds-The-Linen**, house servant at the plantation house; stands by the plantation house, near the bed and benches on its south side. Ask "Plants and ingredients" and check: Nightshade grows about 15 m east-north-east of here; keep it out of the kitchen.
- [ ] **Mazei-Tul**, house servant who keeps the plantation's horses; stands on the north side of the plantation house, close to the horses. Ask "Directions" and check: Lilmoth Dock lies about 405 m east of here.
- [ ] **Sees-No-Shade**, hired soldier who guards the plantation's south side; stands on the south side of the plantation by a bench, facing the water and the shore. Ask "Dangers nearby" and check: A giant crab, Old Salty, lives in the shallows about 45 m east-south-east of here.
- [ ] **Rakhee-Tul**, hired soldier who guards the plantation's south side with Sees-No-Shade; stands a few paces north of Sees-No-Shade on the plantation's south side, nearer the yard. Ask "Dangers nearby" and check: Fly amanita grows about 30 m west-south-west of here; do not eat it.
- [ ] **Looks-At-Books**, bookseller and seller of paper and writing things; stands by the tables on the west side of the plantation house, where she keeps her books out of the rain. Ask "Someone in particular" and check: Folds-The-Linen keeps the house about 15 m east of here.

#### The Docks (the map's "Docks", about 240 m east of Lilmoth Dock)

- [ ] **Seeks-The-Channel**, boat captain at the Docks east of Lilmoth Dock; stands the head of the Docks between the cooking spits and the north door, where boats tie up. Ask "Dangers nearby" and check: A bear and her cubs roam about 65 m south-south-east of here.
- [ ] **Ushaa-Mei**, seller of food and small goods at the Docks; stands the south-west side of the Docks near the houses, where people come out to buy. Ask "Plants and ingredients" and check: Gourds grow about 20 m north-north-west of here.
- [ ] **Little-Minnow**, a hatchling of the Docks; stands in the middle of the Docks between the chairs and the cooking fire, where the grown-ups talk. Ask "Plants and ingredients" and check: Deathbell, nightshade, jazbay and other flowers grow together about 50 m south-east of here.
- [ ] **Plaits-The-Reed**, reed-weaver of the Docks, maker of mats and baskets; stands on the south-west side of the Docks near the houses, at her weaving. Ask "Dangers nearby" and check: A dead Vale Deer lies about 45 m south-east of here; something killed it.
- [ ] **Chases-Cows**, a hatchling of the Docks; stands the north side of the Docks near the cooking spits, where he can reach the cows. Ask "Plants and ingredients" and check: Gourds grow about 15 m north-west of here.
- [ ] **Wades-Late**, dock hand who hauls and ties up for the boats; stands on the south-east side of the Docks by the benches, where cargo is set down. Ask "Directions" and check: Hereguard Plantation lies far to the west, about 640 m west of here.
- [ ] **Feldril Nethri**, Dunmer labourer at the Docks working off an owing of months; stands the north end of the Docks by the north door, kept apart from the families. Ask "This place" and check: The north door of the Docks is about 10 m west of here and another about 5 m east-south-east.

- [ ] **Looks-At-Books' shop** (Hereguard Plantation): pick the trade option. She sells only books, paper and writing things: the four volumes of The Argonian Account, The Lusty Argonian Maid 1 and 2, The Sultry Argonian Bard 1, Short History of Morrowind, Welcome to Black Marsh (two copies), five rolls of paper, two inkwells and three quills, with about 300 gold to buy from you. She now has topics too (Yourself, My trade, Services, Someone in particular, Black Marsh).

## Later (not yet buildable)

- The world map: in BM&V it still shows Skyrim's map. Investigated 2026-11-08 and planned as block W-wrld-map in
  docs/phases/4-first-act-built.md (the native map of BM&V's own land, with "Lolmoth" renamed "Lilmoth"); a
  parchment map only if you want it after seeing that.
- Phase 4: play the first story slice from a new game.

## Done

- Climbing works (Phase 1 walk, 2026-11-06).
- Walk of 2026-11-07: New Game shows the race menu with a bare face; you start on Lilmoth's dock in third person, in
  roughspun, with a journal line; the Imperial sword, shield and Morrowind spells are in the inventory; a moving dodge
  rolls that way and holding it sprints; guard counter; lock-on, sprint and climbing on the Mac keyboard.
- Block test, 2026-11-07: steps 1 to 6, 8, 9, 12 and the keeper's reply in 13 ("By day, too. Done." at 2:52 pm,
  10 gold). Talk: everyone in the first 12 opened topics.
- TrueHUD bars show when set to Dynamic (2026-11-07, set by hand in the menu; now the default, check above).
