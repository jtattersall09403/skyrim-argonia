# Owner walk checks owed

The one list of in-game checks the owner owes. The owner ticks a box when a check has been done and the owner is satisfied with the result, owner will write in claude code session if any issues. Agents: read this before posting a walk,
add a check here when you build something only the owner can see in game. Add the smallest number of checks that proves what needs to be proven. Do not move ticked checks, we keep them here as a record. A check that passed is never re-asked.


**Start a new game for this walk.** Several fixes only take on a new character (the HUD defaults, no health
regeneration, the Levitate spell, the renamed people).

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

- [x] **8.1 Standing backstep, Skyrim's own.** Stand still, hold no direction, tap dodge (Alt; pad B): one hop back of
      about 3 metres in a single movement, the hop Skyrim's own characters use, with no second push. Holding a
      direction and tapping dodge still rolls that way.
- [x] **8.2 HUD from TrueHUD's Combined preset**, with your tweaks (Dynamic, width 150, max 500, anchor X 0.045,
      Y 0.105). New game: health, magicka and stamina are one combined block at the top left; take a hit or sprint and
      it shows, then fades when full; Skyrim's own three bars never show.
- [ ] **8.3 Backstab, one press.** Console `player.placeatme 3decb` (a vanilla bandit, a test target only), walk up
      behind him a sword's length away facing his way, tap attack once: he staggers with the red light, your swing
      finishes, then you play the execution and he takes its big damage, all from that one tap. Wait 10 seconds and do
      it again on a second bandit. From the front one tap is a normal swing. Say if the execution did not play.

## 9. Walk 4's quest fixes (built and deployed 2026-11-08)

**Start a new game** for all of these (several fixes only take on a new game).

- [x] **9.1 Everyone talks again.** On Lilmoth's dock, talk to three of the people who were silent on walk 4 (anyone
      near the pier, for example Deep-In-His-Cups on the shore track south-west of the dock). Each has topics. The cause
      was a missing file the game reads to start our quests on a new game; it is now sent with the plugin.
- [ ] (superseded by 10.1; passed on 2026-11-10 up to leaving the hold, then the gang never moved) **9.2 The opening's steps.** In the barge hold the journal says to speak to Wuleen-Sei, with a marker on her.
      "Why am I here?" ends with her question, and the three answers follow at once. Before you answer, the door at the
      top of the stairs is locked; after you answer, the journal moves on to "Leave the barge's hold by the door at the
      top of the stairs" (marker on the door). Open it: you come out on the pier, the journal says to follow the gang
      (marker on the camp's fire), and the gang walks off along the dock. On the shore path they go ahead of you and
      are waiting at the fire when you reach the camp.
- [x] **9.3 The hold's doors.** The stair door takes you to the pier, and the pier door brings you back to the top of
      the stairs. The other door (down in the hold and up the far stairs) now opens onto its room and does not move you.
- [x] **9.4 Everyone in the opening has something to say.** In the hold, ask Ri'Sakka, Tsanji, Llarvi Maryon and
      Finds-The-Other-Bank "Who are you?"; on the pier, Mee-Tuja the courier; at the camp, Sal-Sei and Deesh-Duun.
      The block test's Dock Walker answers too (`startquest ARG_BlockTest`, `setstage ARG_BlockTest 50`, then ask him).
- [x] **9.5 Buys-The-Months on the pier** no longer asks you for something you cannot give: he tells you Wuleen-Sei
      asks the names, and after you have answered her, that it is written.
- [x] **9.6 Heights.** Mee-Tuja on the pier, and Ties-The-Loose-Plank on the shore after the fire, stand as tall as the
      others (they were about twelve feet).
- [x] **9.7 No things that act like people.** Every line we have was swept for objects, places and documents doing a
      person's act (it was "the roll adds more months", "the hold heard you"). Ask Wuleen-Sei "Why am I here?": she now
      says she adds the months to the roll herself, and that everyone in the hold heard you. Say if any line you meet
      still makes a thing do what only a person does.

## 10. Walk 5's quest fixes (built and deployed 2026-11-11)

**Start a new game.** The opening has moved: the families' camp is now where Lilmoth's dock meets the land, about
fifty paces from the barge, so the whole opening happens in one place and nobody has to find a camp far away.
Black Marsh & Valenwood's ground does not let people walk from one stretch of its walking mesh to the next, which is
why the gang could not march to the old camp; the new camp is on the same stretch as the pier.

- [ ] **10.1 The opening, start to end.** In the hold, speak to Wuleen-Sei and answer her. Leave by the door at the
      top of the stairs. On the pier the gang (Wuleen-Sei, Ux-Xeek, Dives-Without-A-Rope, Finds-The-Other-Bank and
      Mee-Tuja the courier) is standing at the foot of the plank and sets off a moment after you come out; the
      marker is on the camp's fire. Follow them along the dock to the fire. As they reach it the attack comes: a
      tall Argonian woman kills Mee-Tuja, the huts on the water catch fire, and Dives-Without-A-Rope shouts where
      Sal-Sei and Deesh-Duun are (you should hear or read it as a subtitle). Then either go to the hatching shed to
      the north-east for Sal-Sei, or to the burning huts on the water to the west and dive under the boards for
      Deesh-Duun, and bring the one you reached to the shore just west of the camp (marker). The quest ends there
      and the next one starts on that shore. Tell us the step where anything did not happen as written, and whether
      the gang walked all the way to the fire in front of you.
- [ ] **10.2 Nobody is in two places.** After you come out on the pier, go back down into the hold by the pier
      door: Wuleen-Sei, Ux-Xeek and the gang are no longer there.
- [ ] **10.3 People in one place no longer repeat each other.** In the hold and on the pier, talk to everyone. Only
      Wuleen-Sei explains that months are added for food; the others each say something of their own or send you to
      her. The same rule was applied to every place the first act's quests visit: say if you meet two people in one
      place telling you the same thing in nearly the same words.
- [ ] **10.4 The Reed's house, without the oath** (part of 7.2). In the house in Lilmoth answer "Not yet" instead of
      swearing. You can still leave the house and come back in, and Nesh-Deeka still gives you the next task. Before,
      the door was locked to a key only the oath gave, so this path could not continue.
- [ ] **10.5 Markers and plain steps in every quest** (as you play 7.2 to 7.7). Every objective now has a marker,
      every journal entry tells only the next step, and a person who has already given you a quest no longer offers
      it again once it is done. Say which quest and step if a marker is missing or points at nothing, or if someone
      offers a finished quest again.

## 11. Directions told the Morrowind way (built 2026-11-12)

People now give directions by landmarks and compass points, and say how far in words ("just", "a short way", "a fair
way", "a long walk") instead of counting paces.

- [ ] **Ask for directions.** In Black Rose, talk to Tzeel-Vaa (a guard at the west gate) and Sakeeth (who watches the
      south landing); in Lilmoth, talk to Uleesh (a fisher in the shallows below the walls). Ask each one for directions, and ask each
      about "someone". Each answer should name things you can see (a dock, a boat, a ruin, a tower) and compass
      directions, and should never give a number of paces or metres. Then follow one route from each person: you
      should arrive where they said. Reply here with any answer that sends you the wrong way or still gives a number.

## 12. Walk 6: our quests, played from a new game (built and deployed 2026-11-13; posted as issue #69)

Every quest of ours is now written as one short form and built into the game by one builder, and everything a quest
does (move to its next step, give or take gold and things, start the next quest, show a message) is carried out by
the same four shared scripts. No quest has a script of its own any more. The steps below are real quests, chosen so
that between them they make those shared scripts do every job any of our quests asks of them at least once (the
table at the end says which step proves which job). If these pass, every other quest runs on the same scripts, and
rests on the automatic checks the agents run on every build.

- **Start a new game.** Old saves do not work with this build.
- **Quest markers are back on.** Each step of a quest shows a marker on the compass at the top of the screen and on
  the map (M), and over the person or thing when you look at them.
- **Removed from the opening:** the extra dock and its rope fence, the hut that sat in the water, the burning huts,
  the gang's march, and every person placed for them. The journal no longer tells of a fire and a rescue you never
  saw: the burning of the gang's camp is now something people tell you about.
- **The "Block Test" is gone from your game.** It was a test quest that started at the first moment of every new
  game on Lilmoth's fishing dock; it is now a tool the agents build only for themselves, and no player sees it.
- **The console**, for the travel shortcuts below: press the ~ key (below Esc) to open it, type the command exactly
  as written, press Enter and press ~ again to close it.

Do 12.1 to 12.3 in one game, in order. 12.4 and 12.5 can follow in the same game or start from a new one; 12.6 is
optional. **How to reply:** on the walk's issue, give each check's number and either "passed" or what you saw
instead (the step, and the words, marker or message that was wrong or missing).

- [ ] **12.1 The opening: "No Name on the Work Roll"** (a new game, about twenty minutes). You make your character in
      the hold of a ship, as before. The journal (J) already shows "No Name on the Work Roll" with "I woke in the hold
      of a ship, moored below Hereguard Plantation, west of Lilmoth in Black Marsh...". Go up the stairs and through
      the door at the top onto the deck.
      1. Buys-The-Months, a broker (a man who hires out the work of people who owe him months of work), stands on the
         deck a step from the door, facing it, with a quest marker over him. He speaks first without being asked and
         without walking up (the deck has no ground he can walk on, so he stays where he stands). Pass: he begins "I
         am Buys-The-Months, a broker. This is my ship, moored below Hereguard Plantation." and ends "You are no
         affair of mine. Get off my ship." If he does not speak first, speak to him: asking "Who are you?" gives the
         same words. The objective is "Speak to Buys-The-Months on the deck of the ship."
      2. Ask him "Where can I find work, then?". Pass: the objective becomes "Find Nesh-Deeka in Salts-The-Catch's
         house, south of the second big ship, anchored off Lilmoth's own dock." with a marker on the compass and on
         the map. Follow it: east along the shore, past the old lighthouse, into Lilmoth. Salts-The-Catch's house
         stands south of the second big ship, beside a wooden walkway, and Nesh-Deeka stands upstairs in it.
      3. Say "Buys-The-Months says you pay for anyone off his ship." Pass: she tells you of the burnt camp and of the
         Veiled Reed (the quiet service of the state that rules Black Marsh), and the objective becomes "Hear Nesh-Deeka
         out, then give her an answer on the Veiled Reed's offer." Before saying yes, ask her the questions she now
         offers ("Who was the woman with the knotted cord?", "What is the Veiled Reed?", "Why would the Reed want
         me?", "What does the Reed pay?", "Who does the Reed answer to?", "Was the courier who died at the camp one
         of yours?", "What are you not telling me?"); each is answered and none moves the quest on. Then say "I will
         work for the Reed."
      Pass at the end: she gives you 50 gold, the journal lists the quest as completed with "I took work with the
      Veiled Reed, and Nesh-Deeka put fifty gold in my hand. She has told me the first work the Reed wants of me.",
      and a new quest, "The Cutters' Jar", appears with "Nesh-Deeka gave me the Veiled Reed's first work...".
- [ ] **12.2 Anyone can die** (straight after 12.1, in Nesh-Deeka's house). Save first. Kill Nesh-Deeka. Pass: one
      message box reads "With this death the root of what was to come is cut: the main story can no longer be
      finished. Load an earlier save to let it grow again, or go on in the marsh as it now is.", and the journal
      lists "The Cutters' Jar" as failed with "Nesh-Deeka is dead. I will not learn from her what the cutters wanted
      with the jar." The message shows once and not again. Then load the save you made.
- [ ] **12.3 The quest after it: "The Cutters' Jar"** (the same game, after loading). Dives-Without-A-Rope is one of
      the broker's gang; she carried a jar of sap off the burnt camp.
      1. The objective "Ask Dives-Without-A-Rope for the jar, in the ship's hold." marks her. Go back west to the ship
         you woke in and down into its hold. Say "Nesh-Deeka wants the jar you carried off the camp." Pass: she
         refuses ("No. That jar holds sap of Nine Bends, my own tree...") and offers three answers, each showing its
         label: "(Persuade) The one I work for means to find who cut your tree. We can learn it from the jar.", "I
         will give you twenty gold for the key. (20 gold)" and "Then I will take it."
      2. Pick the "(Persuade)" answer. A new character's Speech is below the 25 it needs, so it fails. Pass: she
         answers in her own words, "Words cost nothing. I have heard plenty in this hold, and none of them gave me
         back my tree. Pay me twenty gold, a month off my roll, and the key is yours...", and the quest does not move.
      3. Ask again and pick "I will give you twenty gold for the key. (20 gold)". Pass: 20 gold leaves you, you get
         "Key to Dives-Without-A-Rope's Lockbox", the journal says "I paid Dives-Without-A-Rope twenty gold. She gave
         me the key to her lockbox in the ship's hold. I'm to take the jar from the lockbox and bring it to
         Nesh-Deeka.", and the objective "Bring the jar from Dives-Without-A-Rope's lockbox to Nesh-Deeka." puts a
         marker over the lockbox ("Dives-Without-A-Rope's Lockbox", among the crates under the lanterns in the hold)
         and one on Nesh-Deeka. (The other ways, if you want to see them on a reload: pick the lockbox's Novice lock,
         or pick her pocket for the key.)
      4. Open the lockbox with the key and take the "Cutters' Jar of Sap". Pass: it is a plain take, not a theft
         (the prompt says "Take", not "Steal", and nobody reacts), because she gave you the key.
      5. Back in Salts-The-Catch's house, say "Here is the jar Dives-Without-A-Rope carried off the camp.", then
         "I will taste a drop." Pass: the jar leaves you; you get 25 gold and "Nesh-Deeka's Page"; the quest is
         completed with "I tasted the cutters' sap in Salts-The-Catch's house. Nesh-Deeka wrote down what I said
         under it..."; the page, read from your inventory, says "Under the sap you spoke of a ship's hold, empty,
         with roots grown up through its deck in a ring like trees..."; and the next quest, "The Tree That Turned
         Its Face", appears.
- [ ] **12.4 One faction quest: the Chainbreakers' first, "Four Months for a Boat", by the break-in** (the same game
      or a new one; about half an hour). The Chainbreakers are a small band in Blackrose, a walled town in the
      south-east of Black Marsh, who free people held by an Owing (years of work owed for a debt). Their leader,
      Never-Sold, an Argonian woman, stands inside the Chainbreakers' house on the north side of Blackrose. On foot:
      from Lilmoth go east past Soulrest, then south-east; Blackrose is named on the map (M). With the console: `coc
      HouseInt` puts you inside that house, a few steps from her. Each step below has a marker on the compass and
      on the map.
      1. Ask Never-Sold "What is the job?". Pass: she gives you "Never-Sold's Leaf" (a leaf in her own hand), five
         lockpicks and 100 gold; the journal shows "Four Months for a Boat" with "Never-Sold of the Chainbreakers
         asked me to end Rows-For-Another's Owing on the Tulm-Varo estate: eleven years for one holed boat..."; and
         the marker points to Rows-For-Another on the channel bank north of the farm, north of the town.
      2. Say to Rows-For-Another "Never-Sold sent me. Tell me how you are held." Pass: the journal names three ways
         (her leaf in the count-box, the keeper Hulm-Tei's word, and Brings-Them-Back, the fetcher on the channel),
         and the markers point at her leaf, Hulm-Tei, Brings-Them-Back and her.
      3. The break-in: Hulm-Tei stands in the big house on the Tulm-Varo farm, by the cattle, with his count-box
         ("Hulm-Tei's Count-Box", an Adept lock) a few steps from him. Lift "Hulm-Tei's Key" from him (Pickpocket),
         or pick the box's lock with him near (crouch to sneak: a theft that is seen is a crime). Take
         "Rows-For-Another's Leaf" from the box. Pass: Never-Sold's leaf leaves your inventory (you have left it in
         the box in place of hers), and the journal says "I took Rows-For-Another's leaf from the count-box and left
         Never-Sold's in its place. Under it lay the keeper's own leaf, with Hulm-Tei's name on it: whatever any leaf
         comes up short is written onto his. If I hand hers in, her eleven years fall on him..."
      4. Say to Never-Sold "I have Rows-For-Another's leaf." Pass: she takes it and gives you 100 gold and ten
         lockpicks, and the quest is completed with "I gave Never-Sold Rows-For-Another's leaf, and she will read it
         aloud and burn it. Rows-For-Another is free; her eleven years fall on Hulm-Tei's leaf..."
      5. The turn: ask her "You knew about the keeper's leaf." Pass: "Yes. I knew before I sent you..." Then ask "Is
         there more work?" Pass: the second quest, "One Out of the Smoke", starts with "Never-Sold sent me to the
         heirs' post on Blackrose's east shore...".
      Say also whether anyone saw you take the leaf.
- [ ] **12.5 One Night-Reed quest: "A Dry Hand in a Wet City", and one locked door** (the same game or a new one;
      about twenty minutes). The Night-Reed Chapter is a guild of careful thieves. Soulrest is the small dock town
      east of Lilmoth along the shore. With the console: `coc 01cabinintDUPLICATE001` puts you inside the dock house
      where Tilts-The-Jug stands; S'Tabi, the Khajiit trader, stands on the dock a few steps east of its door.
      1. Ask S'Tabi "Is there quiet work on this dock?" Pass: "A Dry Hand in a Wet City" starts and marks
         Tilts-The-Jug, inside the house just west of him.
      2. Ask Tilts-The-Jug "Is there work here for careful hands?" Pass: she gives you three lockpicks; the objective
         "Take the Blue Jasper Necklace from Keeps-What-Floats's strongbox, or get his key from him (Speech 35, or 60
         gold)." marks the necklace (still inside the strongbox) and Keeps-What-Floats, a thief on the shore near her
         door; and "Keeps-What-Floats's Strongbox" now stands by the houses at the water's edge.
      3. Pick the strongbox's Novice lock, or pay him sixty gold for the key ("I will pay you sixty gold for the key
         to your strongbox. (60 gold)"), and take the "Blue Jasper Necklace". Pass: the journal says "I took the Blue
         Jasper Necklace out of Keeps-What-Floats's strongbox..." and marks Tilts-The-Jug.
      4. Say to her "I have the necklace." Pass: she takes it and pays you 100 gold, and the objective marks the
         coast ship's door on Soulrest's dock, the trapdoor on the ruin east of Lilmoth, and Bent-Spine. (To see that
         the step also raised her regard for you: open the console, click her and type `getrelationshiprank player`;
         it shows 3.)
      5. Take the coast ship to Lilmoth and go down the trapdoor, or use the console: `coc 01LilmothDungeon` puts you
         in the Night-Reed Chapter under Lilmoth. Say to Bent-Spine, the Chapter's fence, "Tilts-The-Jug sent me."
         Pass: the quest is completed, and the Night-Reed's second quest, "The Drowned Lockbox", starts with
         "Bent-Spine, the Night-Reed Chapter's fence, has work for me now that I am a Lookout...".
      6. One locked door, while at Soulrest. The Chainbreakers' third quest has a doorkeeper, Feldril Nethri, who
         unbars the door of the Broker's house (the north one of the three houses by Soulrest's dock) when talked
         round. That quest comes after two others, so jump to that moment with the console: first try the door (it
         is locked), then type `setstage ARG_BC03 21`. Pass: the journal shows "The Broker's Mercy" with "I talked
         Feldril Nethri round. He unbarred the Broker's door for me...", and the door now opens without a key or a
         lockpick.
- [ ] **12.6 Optional, if you have time: one small local quest, "The River Monster"** (any game). Helstrom is the
      walled city in the north of Black Marsh, and the landing is on its river. With the console: `player.moveto
      0B08D5EE` puts you beside Okan-Zish, a rafter of the landing crew, who stands on the rock roots at the landing
      (0B is Black Marsh North's place in our load order).
      1. He greets you with his trouble ("I poled rafts at this landing before the beast came..."). Ask him "What
         lives in the water here?" Pass: "The River Monster" starts with the objective "Kill the crocodile in the
         shallows east of the scaffold at Helstrom's landing." and a marker on the crocodile, a short walk east
         through the shallows.
      2. Kill it. Pass: the objective becomes "Tell Okan-Zish on the rock roots at the landing that the crocodile is
         dead." and marks him. Say "The crocodile in the shallows by the scaffold is dead." Pass: he admits the crew's
         own bait drew it, and the objective marks the bait bucket (a wooden bucket in the shallows where the
         crocodile was), Sells-Dear the boat captain, and Wuleen-Taza.
      3. Take the "Bait Bucket" and show it to Sells-Dear ("I found this bucket in the shallows by the scaffold.").
         Pass: she keeps it and pays you 60 gold, and the quest is completed with "I showed Sells-Dear, the boat
         captain, the crew's bait bucket..."

**What each step proves.** Each job the shared scripts do, and the step that makes them do it. A job a check
proves without anything you can see (the start check finding a person alive, a faction rank) is proved by the step
running on to its next words and markers.

| Job of the shared scripts | Proved by |
|---|---|
| Set the quest's next stage from a line (SetStage) | 12.1 |
| Show an objective with its markers, complete one, make the quest the active one (ShowObjective, CompleteObjective, SetActive) | 12.1 |
| Close every open objective and stop the quest on its completed ending (CompleteAll, StopQuest) | 12.1 |
| The start check that fails a quest whose person is already dead (FailIfDead) | 12.1 (runs as the game starts) |
| Start the next quest at its first stage (StartOnStage) | 12.1, 12.3 |
| Give gold, set a stored number, set a faction rank (GiveGold, SetNumber, SetRank) | 12.1 |
| Switch a thing on away from the player (SwitchOn: the lockbox and the lockpicks in the hold) | 12.1, seen in 12.3 |
| A person speaks first (the quest's force-greet), and a line under the person's greeting | 12.1 |
| A death watched for the main story: quest still open, the message box, set the failed stage, close its objectives as failed (IfQuestOpen, ShowMessage, SetStageIfRunning, FailAll) | 12.2 |
| A line's results as it ends, an answer to a question, a check of skill and of gold with its fallback words (Speech 25, 20 gold) | 12.3 |
| Take gold, give an item, give a container to the player (TakeGold, GiveItem, GiveOwnership) | 12.3 |
| Take an item, switch a thing off (TakeItem, SwitchOff: the lockbox leaves the hold) | 12.3 |
| A line open only while an item is held | 12.3, 12.4 |
| A stage that checks what the player already holds (IfHolds) | 12.4 |
| A take that moves the quest only while its step is open (IfStageDone, IfStageAtMost, on a take) | 12.4 |
| A line open only while a person lives, and only once a stored number is set ("Is there more work?") | 12.4 |
| A line open only after the quest has ended | 12.4 |
| Count a side quest completed (IncSideQuests) | 12.4, 12.5 |
| A take that moves the quest (the game's own take script) | 12.5 |
| Change a person's regard for the player (ChangeRegard) | 12.5 |
| Start another quest from a stage (StartQuest) | 12.5 |
| Unlock a door (UnlockDoor) | 12.5 |
| A death that moves the quest (the game's own death script) | 12.6 (optional) |

Jobs the scripts can do that none of our quests uses, so they need no proof now: fail a single objective
(FailObjective), add to a stored number (AddNumber), join a faction on its own (JoinFaction: our quests join by
setting a rank), lock a door (LockDoor), the speaker attacking the player (SpeakerHostile), a quest moved by
another quest's stage, and lines that test the player's race, sex, faction or rank, a person's regard or whether
the two have spoken before. Three that our quests use are not walked: using or reading a thing to move a quest
(only in the main quest's fourth quest, through the game's own scripts), a line open once a stage has been done
(deep in the Chainbreakers' second and third quests), and a line open once a person is dead (on ways this walk does
not take); all three rest on the build's read-back and checks.

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
