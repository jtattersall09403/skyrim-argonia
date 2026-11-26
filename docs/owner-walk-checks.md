# Owner walk checks owed

These checks of the mod stack are walked in the new world; each phase's own walk is in its phase file (`docs/phases/`, status in [PROGRESS](PROGRESS.md)).

The one list of in-game checks the owner owes. The owner ticks a box when a check has been done and the owner is satisfied with the result, owner will write in claude code session if any issues. Agents: read this before posting a walk,
add a check here when you build something only the owner can see in game. Add the smallest number of checks that proves what needs to be proven. Do not move ticked checks, we keep them here as a record. A check that passed is never re-asked.

**Start a new game for this walk.** Several fixes only take on a new character (the HUD defaults, no health
regeneration, the Levitate spell).

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

## 5. Walk 3's fixes (built and deployed 2026-11-08)

**Start a new game**: the game now opens in the barge hold, and the HUD defaults take only on a new character.

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
- [ ] **5.5 Block Test, the end in the journal** (it had no objective, and the journal lists quests by their objectives).
      Console `startquest ARG_BlockTest`, `setstage ARG_BlockTest 90`: both "Block Test" and "Block Test, the end" are in
      the journal's completed quests.

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

## Done

- Climbing works (Phase 1 walk, 2026-11-06).
- Your ticks of 2026-11-08 for the 2026-11-07 walk: Mark and Recall; the standing backstep (since shortened at your
  ruling, so re-checked above); the attack queued after a roll (our plugin); parry and riposte; poise staggers; the
  TrueHUD player bars.
- Walk of 2026-11-07: New Game shows the race menu with a bare face; you start on Lilmoth's dock in third person, in
  roughspun, with a journal line; the Imperial sword, shield and Morrowind spells are in the inventory; a moving dodge
  rolls that way and holding it sprints; guard counter; lock-on, sprint and climbing on the Mac keyboard.
- TrueHUD bars show when set to Dynamic (2026-11-07, set by hand in the menu; now the default, check above).
