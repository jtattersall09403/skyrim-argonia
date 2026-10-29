<!-- imported unchanged from elder-souls-argonia docs/decisions/0151-stealth-crime-and-locks-ship-whole-pickpocket-is-the-one-gamble.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0151 Stealth, crime and locks ship whole; pickpocketing is the one gamble

**Decision (owner, 2.10 plan review).**

1. **The full detection model, per observer.** Light on the player, noise
   by gait, armour weight and surface, the view cone, line of sight,
   distance, scent and hearing from the creature records, the player's
   Sneak and Agility against the observer's spot score, all as data rows
   on the existing notice service. Every observer keeps its own state
   (decision 0092's unaware, suspicious, engaged); nothing is shared, and
   an alarm call within a radius is how one observer's finding reaches
   the rest (the Skyrim rule, lore `topics/skyrim-sneak-detection.md`).
   The eye shows the worst state across observers as hidden, caution,
   danger, detected. A searching observer walks to where it last knew the
   player, gives up on a data timeout and returns to its post.
   A sneak blow never auto-kills (owner ruling, 2.10b): it deals the
   Sneak-band multiplier (world/76 §121.5, melee and bow columns) times
   its damage on a target of any band, withheld only from an aware, boss
   or warded target (`detection.json` `sneakAttack.withheldWhen`); there
   is no one-shot rule and no band cap. Only when that damage is lethal
   does the paired kill play (the dagger's vanilla sneak kill crouched),
   otherwise the blow lands as a hit.
2. **The Owing is the sentence, paid in coin or time, or resisted.** A
   crime exists only when seen and is an entry on the regional ledger.
   A guard stop offers three resolutions: pay the assessment in gold,
   serve it as custody that advances the clock and costs pending skill
   progress, or resist, which makes the watch hostile through the
   answered-violence runtime and adds assault until the Owing is
   cleared. Where no watch keeps a place, its people keep it (owner
   ruling, 2.10b): the nearest person who witnessed a crime there walks
   up and challenges as a guard would, with two resolutions: pay the
   place's assessment in gold, handing back what a caught theft took, or
   resist, answered by that witness and its kin. There is no custody
   without a watch. Audit, buy out and burn are the Owing as the quest
   lines use it (the Chainbreakers' bookkeeping), never a guard-stop verb.
3. **Trespass is a zone with hours; a lock is a weight on top.** A place
   record marks its private volumes with who may be there and when;
   being inside out of hours or without standing is trespass once seen,
   lock or no lock. Opening a locked thing you do not own is a
   theft-grade act in its own right.
4. **Pickpocketing is in, and it is the one roll.** A visible percent on
   the sheet, resolved by a seeded roll per attempt: the one verb that
   breaks the no-dice rule, because the gamble is the point of it.
   Anything carried can be taken, weapons harder by weight class; worn
   armour never. Gold is an item, so a person's purse is a row with its
   own roll, the whole purse lifted at once and priced by its amount.
5. **Traps are a whole system, thinly placed.** Trap kinds and their
   effects are data (a spell effect from the 2.9 catalogue fired from
   the lock, with its visual family and a hit reaction); probes disarm
   and wear; one or two slice locks carry one. The bar is the
   Skyrim-quality rendering of what Morrowind does.
6. **Loops with eyes, five journeys.** One small loop per subset and per
   seam, each with its own stills or strips and a reader; the trap loop
   reads temporal strips. Five player journeys as data on real slice
   places (the burglary, the hunter, the archer, the pickpocket, the
   trapped and unpickable lock), scripted as short as proves the step,
   run on both headless runners and one pod strip each.

**Why.** The owner wants sneaking to feel like a game rather than a
threshold, and the record already designs that model; a per-observer rule
is what makes a crowd readable; the Owing replaces Morrowind's prison and
must offer the player the same choice Morrowind did, plus the fight the
owner expects; pickpocketing as a gamble is a Bethesda moment worth one
exception; a probe with nothing to probe, or a trap with no effect, would
be a half-done thing the player meets.
