<!-- imported unchanged from elder-souls-argonia docs/decisions/0142-combat-is-met-everywhere-hostile-places-roaming-bands-and-answered-violence.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0142 Combat is met everywhere: hostile places attack on sight, roaming bands come from the region's danger, and violence is answered by its victims

**Decision (owner).** Three rulings fix what the player fights in the
slice and in the province, and where the combat phase ends and the crime
phase begins.

1. **Hostile places attack on sight.** A living thing whose record says
   `hostility: hostile` draws and comes when it notices the player, and
   its alarm pulls in its band or household. The three slice places that
   hold hostile people (the Broke Column, the Teeth of Sithis, the Naga
   highway camp) and every hostile creature socket are fights, not
   scenery. Every hostile record carries a filled `statblock.loadout`;
   `null` is a gate failure.

2. **Roaming bands from the region's danger.** Wild humanoid encounters
   are not places. A per-region table names which territory-holders roam
   there (tribeless Naga, Sul-Xan raiders, pirates on the coast: the
   lore's rule that no bandit is anonymous,
   [ecology-encounters-loot](../../../world/sources/lore/topics/ecology-encounters-loot.md) § territory-holders),
   with what frequency, at what danger band, and from which spots: a spot
   is eligible by geometry and record (on the baked nav, off any place by
   a clearance, a sightline and a retreat route by the road-approach rule
   in [quests/20](../quests/20-world-provisions.md)), never by a fixed
   marker. Each band is authored for variety (composition, gear, headcount,
   a leader or none) so no two reads as clones. Frequency and band follow
   the region, never the player: this is fixed regional danger
   ([0004](0004-fixed-difficulty-constraint.md)) applied to the wild, and
   it is the same table every Part 4 packet fills for its region.

3. **Violence is answered by its victims; the ledger is 2.10's.** Striking
   anyone makes them fight or flee by their own `fightFleeAlarm`; their
   alarm brings their band or household; a place with no watch judges by
   the crime's weight (a blow is answered by the victim and their kin, a
   killing turns the whole place hostile until amends). Combat (2.7) owns
   every reaction to violence and emits typed witnessed-attack and
   witnessed-kill events. Stealth and crime (2.10) owns the bookkeeping:
   crime typing from those events, the Owing ledger, guards where a watch
   exists, fines, and how a hostile place is made peaceful again.

**The 2.7 and 2.8 seam.** Enemy numbers come from the danger band through
the stats package (`packages/game-core/src/stats`): band in, health, hit
and armour out, by the band table of [world/76](../world/76-stats-progression.md)
§128. The player keeps the sandbox's calibrated values until 2.8, which
swaps only the player's side onto compiled stats through the same
API and re-runs the balance sweep. Nothing in 2.7 computes a number 2.8
will replace.

**Why.** The slice already holds 79 hostile living things across twelve
places; building two or three archetypes beside them would have left the
placed world inert. A fixed camp per band would cost a place build each
and still leave the roads empty; a per-region table scales to the
province and keeps the lore's attribution rule. Fighting back is combat
behaviour and belongs with the fighting brain; the ledger is bookkeeping
that theft needs anyway.
