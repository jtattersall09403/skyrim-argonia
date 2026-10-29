<!-- imported unchanged from elder-souls-argonia docs/decisions/0144-progression-ships-whole-one-stat-schema-compiled-for-every-actor.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0144 Progression ships whole: one stat schema compiled for every actor, birthsigns on the effect stack, crafting in the slice

**Decision (owner, 2.8 kickoff review).**

1. **One stat schema, compiled, for every actor.** The player and every
   placed person and creature in the slice run on the same attributes,
   skills, derived pools and formulas ([world/76](../world/76-stats-progression.md)
   §128, [0019](0019-stats-system-workstream-and-placement.md)). No actor's
   numbers are hand-written: a person's record names a class, a race, a
   band and a position (creatures a species statblock on the same ladder),
   and the compiler emits the absolutes. Retuning a table regenerates
   every actor; 2.8 ends with every living record in the slice compiled
   and the player on the same path.
2. **Rest is the one mechanic.** Rest saves, consolidates one pending
   level, opens the attribute purchase, restores pools and respawns
   `onRest` populations; wait passes time only; death wakes the player at
   the last rest with the vastei left as one pile. Bed tiers: a rented or
   owned bed adds a timed **rested** entry on the effect stack (skill
   experience ×1.05 for eight game hours, owned ×1.08); a camp adds
   nothing beyond the sitting, so the wild camper is never punished. The hidden suspend-save
   for browser interruption is the only other save and is 2.13's; no
   manual or quick save exists (confirms [0031](0031-workstream-s-round1-shape.md)).
3. **Birthsigns are permanent effect-stack entries, filled now.** The
   effect stack and its stat-effect field list are 2.8's; birthsigns, race
   packages and other permanent entries apply through it in 2.8, all
   thirteen signs authored as table data (a wide load). 2.9 adds timed
   spell effects to the same stack. Nothing about birthsigns waits for
   Part 4.
4. **Crafting is a slice system, not depth.** Alchemy, smithing crafting
   and tempering, enchanting, their stations and the resource nodes the
   slice places need form a new chunk, [2.9b](../phases/2-slice/2.9b-crafting.md),
   after magic. 2.8 leaves the hooks (Smithing and Alchemy experience, the
   station interaction, the effect-stack shape); soul gems, Soultrap and
   the bound dagger are 2.9's and gem charging is 2.9b's
   ([0146](0146-magic-ships-whole-skyrim-hands-one-effect-family-system-folk-sellers.md));
   4.5 keeps only cooking, spellmaking and summoning creatures.
5. **Tool wear sits with its reader.** 2.8 authors the repair hammer's
   wear and the Smithing repair ceiling; 2.10 authors pick and probe wear
   when it builds locks; both on 2.3's condition shape, numbers against
   Morrowind recorded as a dossier.
6. **Loops are small and seam-shaped; the owner plays finished work.**
   A progression phase proves itself with one small loop per subset and
   one per seam between systems, each a number beside a capture closed by
   a reader, each iteration fast; balance by short targeted simulations
   tied to a real moment of play, never a long simulated playthrough; no
   end-to-end journey run inside a loop. The owner's check is one studio
   play of work every loop has already closed, never QA.
7. **The crafting fortify loop is allowed and priced by rarity.** Crafting
   reads effective skills and attributes, so fortifying Alchemy, Smithing
   or Enchanting does strengthen the next craft (reverses the base-values
   bound of [0033](0033-workstream-s-design-and-numbers.md) item 9). The
   loop is bounded by supply: every source of a fortify effect on a
   crafting skill or a crafting input attribute, spell, scroll,
   ingredient or soul, is rare or expensive, with few placed sources, no
   common spell merchant and no restock of the rare ones; 2.9 flags them
   in the spell catalogue, 2.9b in the ingredient table, and the
   integrity gate keeps them scarce.

**Why.** The brief as written deferred what the player meets (birthsigns,
crafting) against the plan's third rule, claimed work other chunks own
(the suspend-save, capability speeds, every tool's wear), carried an
owner test recorded nowhere else, and planned one long sweep with the
owner playing its outliers. The owner's standing rulings are that every
NPC shares the player's system and is authored for quick retuning, that
iterations are fast and watched, and that the owner plays only what is
finished. Crafting designs exist in full in world/76 §124 and the brew
formula is already coded; leaving them to Part 4 would ship a slice in
which the Smithing and Alchemy skills exist but nothing can be made. The
owner likes the Morrowind crafting climb as a hard-won thing; pricing it
by rarity keeps the pleasure and removes the grocer-grind exploit.
