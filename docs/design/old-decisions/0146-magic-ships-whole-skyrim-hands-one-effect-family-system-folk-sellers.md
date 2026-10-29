<!-- imported unchanged from elder-souls-argonia docs/decisions/0146-magic-ships-whole-skyrim-hands-one-effect-family-system-folk-sellers.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0146 Magic ships whole: Skyrim hands, one effect-family system, folk sellers, souls in the slice

**Decision (owner, 2.9 kickoff review).**

1. **The whole system, a representative slice.** 2.9 builds the full
   magic system in its scaled shape and authors every effect and every
   Morrowind spell (UESP, tuned to [world/76](../world/76-stats-progression.md)
   §123) as a wide load. Only a representative set is implemented with
   visuals: at least one spell per school and at least one per visual
   family, so every mechanism is proved once and Part 4 adds spells as
   data rows.
2. **Skyrim's hands and casting.** A spell occupies a hand. Each hand
   takes a weapon, a spell, a torch or a shield, mixed freely; the same
   spell in both hands dual-casts. Hold to charge, release to fire;
   stream spells run while held. A hit that breaks poise interrupts a
   cast; a hit that does not, does not. All five Skyrim cast styles
   (aimed, stream, self, ward, dual) are sourced from vanilla for the
   shared rig. Fire, frost and shock resist separately. Powers are once a
   day. Scrolls are single-use and teach nothing.
3. **One effect-family system, Skyrim's textures as the art.** Spell
   visuals are a config-driven set of families (projectile, hit flash,
   self glow, area ring, stream, light orb, summon flash), each taking a
   colour, a sprite and a size from the effect's school and kind, built
   like the fire system ([0107](0107-one-config-driven-fire-system-replaces-sprite-flames.md)).
   Sprites and shapes come from the vault's magic and effects pools; no
   Skyrim particle mesh is converted wholesale. The recipe for a new
   family or effect is written so Part 4 adds effects as parameters.
4. **Folk sellers, stock from the sheet.** The slice's tree-minders
   (Vees-Wai at Greenspring, Swims-The-Channel-Twice at Nine Bends) sell
   spells, blessings and cures. A seller's stock derives from the spells
   their own compiled skills could cast plus a signature list on their
   record; no order or guild record exists. General traders stock common
   scrolls; scrolls drop as loot; a non-seller may teach a spell
   informally through dialogue; starting spells come from the compiled
   sheet. Every route writes to one known-spells record.
5. **Casters and a disease from the roster.** The Teeth of Sithis's
   Nisswo and priest are the slice's enemy casters, through the enemy
   brain's caster seam, with stock by the same rule. One common disease
   rides on one slice bite (giant leech or bog-dog) so the cure is bought
   for a reason; the staged disease set stays Part 4.
6. **Scope moves.** Levitation gets visuals and a movement mode;
   water walking is catalogue only. Conjuration's slice spell is a bound
   dagger. Soul gems and Soultrap enter Part 2: 2.9 owns the spell and
   the capture on a creature's death, 2.9b owns charging an enchantment
   from a gem (amends [0144](0144-progression-ships-whole-one-stat-schema-compiled-for-every-actor.md)
   item 4). Summoning creatures, spellmaking and Hist communion stay 4.5.
7. **Every implied screen is 2.9's.** Spell entries in the belt and
   hands, the cast charge meter, the spell-seller screen, the disease
   line and notice, known spells on the sheet, with ui-lab fixtures on
   the three viewports.
8. **Loops are small and seam-shaped** ([0144](0144-progression-ships-whole-one-stat-schema-compiled-for-every-actor.md)
   item 6): one per subset and one per seam, a number beside a capture
   closed by a reader; no end-to-end walk inside a loop.

**Why.** The brief as written promised a playable mage on a slice with
no seller, no caster and no sourced clip or effect, and left the casting
model to a kickoff note. The owner's view, checked against the counts
(three Morrowind cast clips, five Skyrim styles, about a dozen visual
families, about 140 Morrowind effects that reduce to a handful of
operations), is that the whole system is table work plus one visual
system, so it ships whole with a thin proof. Skyrim's hands are the
owner's preferred feel: mixing weapon, spell, torch and shield. Folk
sellers follow the lore dossier (`world/sources/lore/topics/magic-practice.md`):
spells are bought, found, traded and taught informally, scroll magic is
common and cheap, and vendors exist without a guild. Souls move into
Part 2 because enchanting without a charge source is a station that
cannot be used.
