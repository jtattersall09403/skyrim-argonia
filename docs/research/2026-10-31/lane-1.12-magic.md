# Lane 1.12-magic: Magic Expanded in Black Marsh and in Wind UI's magic pane

Owner, 2026-10-31: Magic Expanded (Nexus 133435, 5.1, dependency row `magic-expanded`) in the stack and in the magic
pane, Morrowind's schools included. Route: data (world db `mod_form`) then our SKSE at data load. Its plugin is never
edited or mastered.

## What the mod holds (L1, read in place from the player's Magic.esp and Magic.bsa; nothing copied)
152 SPEL, 191 MGEF (19 hidden in the UI), 140 BOOK (tomes, no body text), 55 SCRL, 40 WEAP (staves, bound weapons),
10 ARMO (bound armour), 9 MESG, 4 PERK, 1 QUST (the MCM), 7 MCM strings (its English translation file), 23 scripts.
MGEF magic skills: Alteration 39, Conjuration 25, Destruction 43, Illusion 25, Restoration 46, none 13.

## The Nordic review (0012)
603 rows written to `data/immersion/verdicts.jsonl` (`<local id>:Magic.esp`, plus `mcm:Magic.esp`): 591 keep,
12 replace. The replaced, restated at data load by `mod_form` rows (our words):
- the force effects named after the shout (000AC1-AC3 "Unrelenting Force ...") -> Slight Force, Force, Powerful Force;
- the Storm Call snowstorm spell (SPEL 000972, 000975; MGEF 000973, 000974; tome 00089D) -> Marsh Squall, cold rain;
- Arctic Blow (SPEL 000A19, MGEF 000A11, tome 00088E) -> Numbing Blow ("a numbing hand");
- Resurrection's description reworded (a misspelling), name kept.
Reader pass (independent, 548 distinct visible lines after the renames): first pass found 4 tells (the first
rename, Hailstorm) and 3 borderline (Arctic Blow); both fixed as above. A second pass on the final list is owed.
No Skyrim place, person, Nord, dragon, shout, Thu'um, Dawnguard or Alduin word is in any visible string. The two
"CG Dragon Storm Call" effects are hidden in the UI. Shout-built spells (Force, Slow Time, Disarm, Throw Noise,
Twister/Cyclone, Phantom Form/Etherialize, the storms) all read as plain spells once renamed: none withheld.

## Schools in Wind UI (evidence: WindUI.dll strings)
Wind UI's magic window groups by literal headings in its DLL: Alteration, Conjuration, Destruction, Illusion,
Restoration and **Other** (plus Powers, Shouts); none is a translation key. No data route gives a Mysticism heading:
an effect on any other actor value can only land under "Other". Per the brief, Mysticism's effects (21 rows: Soul
Trap, Spell Absorption, Reflect, Dispel x3, Absorb x6, Analyze, Telekinetic Grip, Mark, Recall, Teleportation x4)
are recorded with `school = mysticism` and stay under the school the mod gave them (Alteration/Restoration/
Conjuration). When a route to a sixth heading exists (a Wind UI setting, or the author), set Mysticism's actor value
in `skyrim_units.SKILL_AV` plus life.cpp's kSkillMirrors row and the same rows apply. Poison (8 effects: Viperbolt
x3, Toxic Cloud, Poison Cloak x2, Poison Spray, Poisonous Touch) moves from Restoration to Destruction (Morrowind's).

## Reach in Black Marsh
The mod's script adds its tomes, scrolls and staves to vanilla leveled lists (LItemSpellTomes*, LItemScroll*,
staff lists: its aaaTargetList* FLSTs). Argonia's only merchant chest (ARG_Cont_MerchantChestWellKeeper) lists items
directly and no Argonia leveled list holds those vanilla lists; `trade_class` has only `trade-class.general`. So
none of its spells reach the player in Black Marsh today. Wiring needs a spell-selling trade class (economy, 2.10):
not built here (no merchant to give it to).

## Built
world/schema.sql `mod_form` + world/db/mod_form.jsonl (41 rows); tools/argonia_world/core_tables.py -> 
skse/core/generated/argonia/core/tables_magic.h; skyrim_units.MAGIC_SCHOOL_AVS; skse/core magic.h/.cpp +
tests/test_magic.cpp (core.magic); skse/ArgoniaCore/src/magic.cpp (MagicDataLoaded from main.cpp's OnDataLoaded);
tests/journeys/magic-pane.yaml; tests/journeys/batches/lane-1.12-magic.sh (deploy + journey + still).

## In game (L4)
Job `l112magic` on argonia-play-ie: see the status line in the lane report back; stills stay in out/l112magic.
