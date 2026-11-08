# Owner walk checks owed

The one list of in-game checks the owner owes. The owner ticks a box when a check has been done and the owner is satisfied with the result, owner will write in claude code session if any issues. Agents: read this before posting a walk,
add a check here when you build something only the owner can see in game. Add the smallest number of checks that proves what needs to be proven. Do not move ticked checks, we keep them here as a record. A check that passed is never re-asked.


**Start a new game for this walk.** Several fixes only take on a new character (the HUD defaults, no health
regeneration, the Levitate spell, the renamed people), and your old save has the Block Test used up.

## 1. The stack: HUD, movement, magic and combat (Phase 1, issue #49)

Fixed after your walk of 2026-11-07 (feedback in `tmp/walk-2-feedback.md`).

- [ ] (superseded by 5.2) **TrueHUD bars**, on the dock straight after the new game, without opening any menu: your health, magicka and
      stamina bars sit at the top left, a little in from the corner, and show when they change (sprint a few
      seconds: the stamina bar shows, then fades once full). The vanilla bars at the bottom never show. In Esc, Mod
      Configuration, TrueHUD, Player Widget you should see your settings already there: Dynamic for all three bars,
      width 150, minimum 50, maximum 500, scale bars ticked, anchor X 0.045, Y 0.105. (Our earlier setting used the
      wrong number: 2 is "In combat", Dynamic is 1.)
- [x] **No health regeneration.** In the console type `player.damageav health 30`, close it and wait 30 seconds
      out of combat: health stays down. `player.damageav magicka 30` and `player.damageav stamina 30`: both refill on
      their own. A healing spell or potion still heals (`player.restoreav health 30` puts it back).
- [x] **The compass** is back at the top of the screen outside. Quest markers stay off, as before; say if you want
      them on too.
- [x] **Running with a weapon drawn.** Draw the sword and move forward without sprinting: you run as fast as with
      it sheathed, not a fast walk. (The faster Arena Movement variant only ran at about half speed; our plugin now
      sets the drawn-weapon run to the same speed as the sheathed run.)
- [x] **Levitate** (Magistrate's Levitate, new in the stack): the Magic menu, Alteration, lists "Levitate". Equip
      it and hold cast: you rise and float; look up or down to steer; let go of cast to come down.
- [ ] (superseded by 5.1) **Dodge, standing still** (changed 2026-11-08, your ruling): stand still, hold no direction, tap Alt (pad: B).
      You now take one short hop back, about 2 metres (the first of Dynamic Dodge's two pushes; it went about 5.4 m).
      Say whether it looks right, whether the feet slide during the second half of the move (the clip keeps its full
      length), and whether the distance is too short: the fallback is Skyrim's own hop-back, about 3 metres. (A dodge
      tapped mid-attack still plays the mod's back roll; that is unchanged.)
- [x] **Parry window** (you passed parry and riposte on 2026-11-07; the window is now wider as you asked, half a
      second, was 0.3): against a bandit, say whether landing a parry is now hard but possible, too easy, or still too
      hard.
- [ ] (superseded by 5.3) **Backstab**. Behind a bandit who has not seen you, about a sword's length away, facing the way
      he faces, locked on (F; pad: right stick click): hold block and tap attack (keyboard: right mouse, left mouse; pad:
      hold LB, tap RB). He lurches into a big stagger; attack again for the execution.
- [ ] **Pad layout** (GameSir X2): RB light attack, RT heavy (power) attack in one press, LB block, LT shout, d-pad
      left or right opens the Tween menu (skills, items, map, magic).
- [ ] **Lock-on, sprint and climbing on the pad** (lock-on: right stick click).

## 2. Lilmoth: windows

- [x] Walk up from the dock to the tall stone-and-timber houses behind it (the ones in your screenshot of
      7 November). The arched windows on all five houses, the half-ruined one too, show leaded glass (it glows
      faintly at night), not flat pale-blue panes.

## 3. The world map (new, 2026-11-08)

Pressing M in Black Marsh showed Skyrim's map. Our plugin now gives BM&V's four worlds the map area they lacked, and
the game now gets the terrain-detail settings files BM&V left out (made on the play machine from your copy of BM&V).
The marker "Lolmoth" now reads "Lilmoth", and "Southern Morowind Pass" reads "Southern Morrowind Pass".

- [x] **Lilmoth:** on the dock (the new game puts you there), press M: Black Marsh's own land, not Skyrim's; you can
      pan and zoom; Lilmoth's walled town marker reads "Lilmoth".
- [x] **Thorn:** console `cow BlackMarshNorth -6 5`, close the console, press M: Thorn's land, pan and zoom.
- [x] **Valenwood:** console `cow Valenwood 17 27` (Arenthi), press M: Valenwood's land, pan and zoom.
      If a map shows only cloud or only part of the land, say which world and whether you could pan to the edges.

## 4. The building blocks: only what is still unproved (Phase 3)

Steps 1 to 6, 8, 9, 12 and the keeper's reply in 13 passed on 2026-11-07 and are not asked again. Each check below
starts the test quest and jumps straight to the stage it needs, so there is no replay. Reply with the letter of any
check that did not happen as written.

- [x] **A. The token on the planks** (a new, more precise way of placing things: we now read the shape of the dock
      planks themselves, not just the walkable ground). Console: `startquest ARG_BlockTest`, then `setstage
      ARG_BlockTest 20`. A wooden bowl, "Test Token", appears on the wooden dock planks about 3 m east of the Dock
      Keeper, not on the ground beside you, and you can pick it up there. (Last time it was placed on land: the spot
      we picked from the walkable ground was land, not the planks.)
- [x] **B. Does the walker see you** (step 7). Same game: `setstage ARG_BlockTest 50`. The Dock Walker appears and
      talks with the keeper, then walks toward the ship (a mudcrab appears south-east; ignore it or kill it). While she
      walks, crouch out of her sight behind the crates and type `ARG_BT_WalkerRef.getdetected player`, then stand in
      front of her and type it again. Pass: hidden it prints 0, in view 1. (Last time the line was the wrong way round:
      `player.getdetected ...` asks whether you see her, hence the -1000.) If the console refuses it, click her and
      type `getdetected player`.
- [x] **C. Two trigger boxes, one result** (steps 10 and 11). A new game (the boxes are used up once fired):
      `startquest ARG_BlockTest`, then `setstage ARG_BlockTest 65`. Walk east to the ship's door (the hatch about
      20 m east of the keeper) and stand beside it. Type `sqs ARG_BlockTest`, `getglobalvalue ARG_BT_RaceRuns` and
      `getglobalvalue ARG_BT_RaceHits`. Pass: stages 71 and 75 are done (there is no 72 any more), RaceRuns says 1,
      the objective reads "Open the ship door". Tell us RaceHits (2 means both boxes fired at once and the guard
      held; 1 means one box fired first). [owner answer: 1]. Then save, load, walk away from the door and back, and type the two
      `getglobalvalue` lines again: the same numbers. (Last time both 71 and 72 were done: both boxes fire in the same
      instant, so the quest now has both set one stage that guards itself, as Skyrim's own quests do.)
- [x] **D. The finished quests in the journal** (step 13). Any game: `startquest ARG_BlockTest`, then `setstage
      ARG_BlockTest 90`. You get 10 gold. Open the journal (J). Pass: "Block Test" ("I passed the block test.") and
      "Block Test, the end" ("The second quest started from the first." and "The second quest ended with the
      first.") are listed as completed. Then the Stats page (Quests section): "Side Quests Completed" has gone up by 2
      (in a new game: 2), one for each test quest, as Skyrim's own side quests add it in their last stage; tell us
      what "Quests Completed" says too (we expect the game to add those itself, but have no proof). (They were Misc
      quests, which Skyrim drops from the journal when done, and nothing added to the stats.)
- [ ] (superseded by section 6) Speak to various people, are you happy with their names, topics and talking style?


## 5. Walk 3's fixes (built and deployed 2026-11-08)

**Start a new game**: the game now opens in the barge hold (section 7), and the HUD defaults take only on a new character.

- [ ] **5.1 (superseded by 8.1) Standing backstep.** The clip itself now ends at the end of its first push (0.33 s, about 2 m); before, it kept
      playing after the push. Stand still, hold no direction, tap dodge (Alt; pad B): one short hop back that ends at once,
      with no sliding or stepping after it.
- [ ] **5.2 (superseded by 8.2) HUD from TrueHUD's Combined preset**, with your tweaks on top (Dynamic, width 150, max 500, anchor X 0.045,
      Y 0.105). New game: health, magicka and stamina show as one combined block at the top left, appear when they
      change and fade when full; the vanilla bars never show.
- [ ] **5.3 (superseded by 8.3) Backstab like Dark Souls** (our plugin does it on a normal attack: no block, no lock-on, no stamina, one press
      gives the stagger and the execution). Console `player.placeatme 3decb` (a vanilla bandit, a test target only), walk up
      behind him a sword's length away facing his way, tap attack once: big stagger, then the execution by itself. From the
      front one tap is a normal swing. Say whether your own swing also hit him first.
- [ ] **5.4 Music.** BM&V's worlds had none; they now have Skyrim's own (marsh exploration in Black Marsh, pine forest in
      Valenwood). Outside for a minute: music plays; in a fight: the battle music.
- [ ] **5.5 Block Test, the end in the journal** (it had no objective, and the journal lists quests by their objectives).
      Console `startquest ARG_BlockTest`, `setstage ARG_BlockTest 90`: both "Block Test" and "Block Test, the end" are in
      the journal's completed quests.

## 6. Talk: everyone in the act's places (recipe v2)

119 people now have their own name, temperament and topics: Lilmoth, Hereguard and Soulrest's dock (30, redone), Low-Reed
Village east of Lilmoth (6), Helstrom (7) and its river landing (5), Thorn, the coast ship's stop in Black Marsh North (33),
and Blackrose (38). Directions are routes of two to four steps that end at things you can see; first words are cool to a
stranger and warmer only for someone who likes you; facts are checked against BM&V's world; names follow the old naming
rules.

- [ ] **6.1 Directions.** In Lilmoth ask Deep-In-His-Cups (shore track south-west of Lilmoth Dock) "Directions" and walk
      his route to Flaa Heet's village; in Blackrose ask the guard Tzeel-Vaa by the west gate's marker post the way to the
      jail and walk it. Name any step whose landmark you could not find.
- [ ] **6.2 Voices.** Talk to anyone you meet on the act's way (Thorn: try Quill-Teeth, a Tax Heel soldier by the house on
      the east side). Say whether names, topics and manner sit right, any two who sound alike, and any "my friend" from a
      stranger.

- [ ] **6.3 Rumours.** Before taking a side quest, ask a local "Latest rumours" (Bejeen-Ul in Helstrom's street for LQ30;
      in Blackrose, Talks-To-Water for BC01). They name the quest giver and where to find them; once the quest has
      started they no longer offer it.

## 7. The first story slice (Phase 4): play it from a new game

All 11 quests are built and every stage reads back from the plugin; none has run in game. Reply with the step where any
quest broke or stopped making sense. Positions marked * were picked from navmesh and never walked: say if anyone floats,
sinks or stands in a wall.

- [ ] (superseded by 9.2 and 9.3) **7.1 The opening (MQ01).** The race menu opens in a barge hold at Lilmoth's dock; you wear a tunic and footwraps.
      Ask Wuleen-Sei "Why am I here?" and answer; leave by the hold's door and follow the gang along the shore to the
      camp's fire at the edge of Hereguard Plantation. The attack: Mee-Tuja is killed and the huts burn; run to the shed
      or into the water under the huts, then south to the shore; the one you saved follows.
- [ ] **7.2 The Veiled Reed (MQ03).** On the shore: taste the spilled sap in the shed or dive for the brass tag in the
      sunk fish-trap; "I am ready to go". In the house in Lilmoth*: tell Nesh-Deeka what you saw, get Ties to talk, answer
      "I will serve the Reed" or "Not yet"; the dream in the hold, then back in the house.
- [ ] **7.3 MQ04 and MQ05.** Low-Reed Village's Hist (dead tree while it is turned, a living one after: does it look
      right?), Pays-Late's gum pot lifted after dark; then the coast ship to Helstrom's river landing, using the new door
      between the ship's two halves both ways (a new building block), and on to Helstrom.
- [ ] **7.4 Helstrom's locals.** LQ30: Haj-Wan inside the basin gate, the viper among the roots, Sei-Wan. LQ25 (after MQ05
      reaches its basin warning): Okan-Zish by the landing's houses, the crocodile under the plank walk, the Bait Bucket.
- [ ] **7.5 Night-Reed (TG01, TG02).** At Soulrest's house on the dock, Tilts-The-Jug's test and the thief Keeps-What-Floats;
      the trapdoor north of Pusbottom, Bent-Spine, the lockbox in the deep water (does the horker-tusk "Worn Bone Figurine"
      pass as a bone trinket?).
- [ ] **7.6 Chainbreakers (BC01 to BC03).** In Blackrose, Never-Sold sends you to the estate landing* north of town;
      Rows-For-Another down the channel at night; then the fire in the old stone house* on the shore at Blackrose's east
      edge, its two gate-keepers outside its west wall (BC02); then Heavy-Rope and Ussa-Rekh on Soulrest's open dock (BC03).
- [ ] **7.7 Warmth and afterwards.** A quest person you have helped greets you more warmly than a stranger does. After
      BC01 ends, speak to Rows-For-Another: a short greeting about being out of the estate's hands (say the line, or
      "silent").
- [ ] (superseded: all eleven now proven on a real floor or moved onto one) **7.8 Eleven spots the off-game check could not prove** (the navmesh is there, but no visible floor under it): say
      if anyone floats or stands in nothing at MQ04's camp by Low-Reed Village (the likeliest problem), BC02's keep and
      gate, LQ30's Sei-Wan and the viper, MQ05's second wasp, and MQ01's Ri-Sakka and Never-Sold.

## 8. Walk 4's fixes (built and deployed 2026-11-08)

Walk 3's backstep and HUD never reached the game: a second job, run minutes later from an older copy of our settings,
put the old ones back. That can no longer happen (the install now refuses an out-of-date copy). **Start a new game.**

- [ ] **8.1 Standing backstep, Skyrim's own.** Stand still, hold no direction, tap dodge (Alt; pad B): one hop back of
      about 3 metres in a single movement, the hop Skyrim's own characters use, with no second push. Holding a
      direction and tapping dodge still rolls that way.
- [ ] **8.2 HUD from TrueHUD's Combined preset**, with your tweaks (Dynamic, width 150, max 500, anchor X 0.045,
      Y 0.105). New game: health, magicka and stamina are one combined block at the top left; take a hit or sprint and
      it shows, then fades when full; Skyrim's own three bars never show.
- [ ] **8.3 Backstab, one press.** Console `player.placeatme 3decb` (a vanilla bandit, a test target only), walk up
      behind him a sword's length away facing his way, tap attack once: he staggers with the red light, your swing
      finishes, then you play the execution and he takes its big damage, all from that one tap. Wait 10 seconds and do
      it again on a second bandit. From the front one tap is a normal swing. Say if the execution did not play.

## 9. Walk 4's quest fixes (built and deployed 2026-11-08)

**Start a new game** for all of these (several fixes only take on a new game).

- [ ] **9.1 Everyone talks again.** On Lilmoth's dock, talk to three of the people who were silent on walk 4 (anyone
      near the pier, for example Deep-In-His-Cups on the shore track south-west of the dock). Each has topics. The cause
      was a missing file the game reads to start our quests on a new game; it is now sent with the plugin.
- [ ] **9.2 The opening's steps.** In the barge hold the journal says to speak to Wuleen-Sei, with a marker on her.
      "Why am I here?" ends with her question, and the three answers follow at once. Before you answer, the door at the
      top of the stairs is locked; after you answer, the journal moves on to "Leave the barge's hold by the door at the
      top of the stairs" (marker on the door). Open it: you come out on the pier, the journal says to follow the gang
      (marker on the camp's fire), and the gang walks off along the dock. On the shore path they go ahead of you and
      are waiting at the fire when you reach the camp.
- [ ] **9.3 The hold's doors.** The stair door takes you to the pier, and the pier door brings you back to the top of
      the stairs. The other door (down in the hold and up the far stairs) now opens onto its room and does not move you.
- [ ] **9.4 Everyone in the opening has something to say.** In the hold, ask Ri'Sakka, Tsanji, Llarvi Maryon and
      Finds-The-Other-Bank "Who are you?"; on the pier, Mee-Tuja the courier; at the camp, Sal-Sei and Deesh-Duun.
- [ ] **9.5 Buys-The-Months on the pier** no longer asks you for something you cannot give: he tells you Wuleen-Sei
      asks the names, and after you have answered her, that it is written.
- [ ] **9.6 Heights.** Mee-Tuja on the pier, and Ties-The-Loose-Plank on the shore after the fire, stand as tall as the
      others (they were about twelve feet).

## Done

- Climbing works (Phase 1 walk, 2026-11-06).
- Your ticks of 2026-11-08 for the 2026-11-07 walk: Mark and Recall; the standing backstep (since shortened at your
  ruling, so re-checked above); the attack queued after a roll (our plugin); parry and riposte; poise staggers; the
  TrueHUD player bars; talk (W-talk) with Lilmoth's first 12.
- Walk of 2026-11-07: New Game shows the race menu with a bare face; you start on Lilmoth's dock in third person, in
  roughspun, with a journal line; the Imperial sword, shield and Morrowind spells are in the inventory; a moving dodge
  rolls that way and holding it sprints; guard counter; lock-on, sprint and climbing on the Mac keyboard.
- Block test, 2026-11-07: steps 1 to 6, 8, 9, 12 and the keeper's reply in 13 ("By day, too. Done." at 2:52 pm,
  10 gold). Talk: everyone in the first 12 opened topics.
- TrueHUD bars show when set to Dynamic (2026-11-07, set by hand in the menu; now the default, check above).
