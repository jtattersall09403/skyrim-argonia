# Mod 60199 (E.S.L.A.) as the sheet's foundation: evaluated 2026-10-29

Written by the planner from the research lane's return (the lane could not write files). Archive read from source
(psc included; SWFs not decompiled, 0003).

**What it is.** "E.S.L.A. - Elder Scrolls Levelling and Attributes" by Fallen01135, v2.03 (2023-08-31) + Willpower
Fix (2024-01-17); unmaintained ~21 months. **Oblivion-styled**: 8 attributes including Luck, the 18 vanilla skills,
21 Oblivion classes, 13 birthsigns, Oblivion levelling (+1–+5 attribute multipliers).

**How.** ESL-flagged ESP, Papyrus, 6 compiled AS2 SWFs (no source). Needs Actor Value Generator (84743, a DLL
that aliases the attributes onto obsolete AVs via a TOML), po3 Papyrus Extender, MCM Helper, PapyrusUtil, SkyUI. A
2 s Papyrus loop overwrites Health, Magicka, Stamina, their rates, SpeedMult, JumpingBonus and CarryWeight with
hard-coded formulas (`ftaSCR_TES4Sys_updateCharacter.psc:55-84`); skill gain is vanilla's skill-up event; levels
from 10 major-skill increments; level-up on sleep through its own SWF. Runtime support on 1.7.104 unverified.

**Against Argonia's sheet (1.3 §a, 1.5).** 7 attributes without Luck: partial. 27 skills: not covered. Score,
k(s), burden tiers, mitigation, ladder, StatEffect stack: not covered. Derived values: different, hard-coded
formulas. Use-based gain, vastei, rank curve: not covered. Level only at rest: partial (bed only). The sitting:
not covered. Death pile, rest-only save: not covered.

**Conflicts.** Its 2 s overwrite fights ArgoniaCore's native writes; it rewrites vanilla perks; it drives vanilla
XP; it replaces TweenMenu with its own SWF and edits Oghma and the Black Doors.

**Recommendation (research).** Pattern only; do not depend on or fork it. Take **Actor Value Generator (84743)**
alone into 1.3 §a's actor-value audit as a route-2 candidate for naming our 7 attributes as condition-readable AVs
(check it on 1.7.104 first). Keep every `skse/core` module as the formulas ArgoniaCore calls.

**Open with the owner.** The owner named 60199 as the foundation for "Morrowind attributes and skills"; it is
Oblivion's system. Asked on 2026-10-29 whether a different mod was meant, or the AV approach.
