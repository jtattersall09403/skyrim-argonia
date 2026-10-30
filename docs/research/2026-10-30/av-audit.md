# Actor-value audit for the seven attributes (1.3 §a, G14.1), on paper

Lane 1.3-av-audit, 2026-10-30. Level L1 (data scan). Question: which obsolete actor values (AVs) and
`Variable01`–`Variable10` are read or written by vanilla and by the dependency stack, so the seven attributes
(Strength, Intelligence, Willpower, Agility, Speed, Endurance, Personality) can sit in reserved AVs
([native-map §3.5](../native-map.md), P1 carrier rule).

## Answer

- **Use seven obsolete AVs with 0 hits in every plugin and every script scanned.** Strength = Fame (60), Intelligence =
  Infamy (61), Willpower = LastFlattered (91), Agility = FavorPointsBonus (89), Speed = FavorsPerDay (80), Endurance =
  FavorsPerDayTimer (81), Personality = IgnoreCrippledLimbs (59). Order is by safety; any of the seven can swap with a
  reserve below if its L4 check fails.
- **Reserve, same 0-hit class:** VoicePoints (37), VoiceRate (38), Energy (2), the seven limb/condition AVs (46–52),
  WardDeflection (67), DEPRECATED05 (162, if a condition can name it), and the 18 `*SkillAdvance` AVs (114–131). That is
  about 35 further slots for P1 carriers before any `Variable` is touched.
- **Do not use `Variable01`–`10`.** All ten are read by vanilla; 620+ condition and MGEF rows and 250+ vanilla scripts (table).
  If ever needed, Variable04, 05, 08, 10 are the least used (6, 4, 4, 5 rows).
- **Do not use** LastBribedIntimidated (read by 10 persuasion INFO rows), FavorActive (two vanilla scripts), Mood,
  Morality, Assistance, Mass, Aggression, Confidence (read or written by records or scripts).
- **Actor Value Generator (AVG) is not needed and not adopted for 1.3.** It does not add AV indices; it aliases an
  existing AV (see below). It cannot remove the need to borrow, only to isolate a borrow. Kept as a fallback only if
  an L4 check finds an engine effect on a chosen AV. Last fallback unchanged: co-save canonical plus mirrored globals.
- Caveat: engine-native readers or writers of an AV are invisible to a data scan. Hence the owed L4 list below.

## Method and scope

- Candidates from CommonLibSSE `RE/A/ActorValues.h` (164 values, 0–163; a clone sits in the scratchpad), marked
  obsolete where no Skyrim record or script uses them, plus `Variable01`–`10` (68–77).
- Plugins (43): Skyrim.esm, Update.esm, Dawnguard.esm, HearthFires.esm, Dragonborn.esm and all 38 plugins in
  `Data/argonia-plugins.txt` (the stack load order, including Black Marsh.esm, King of the Murkmire, HTBM and
  Cipactli, Tropical Skyrim, Magic.esp, TKDodgeAddon, XPMSE, Precision, TrueDirectionalMovement, SkyUI). Not scanned: the
  Creation Club masters in Data (not in the load order file).
- Records: a throwaway Mutagen 0.54.4 console project (scratchpad, not committed) opens each plugin as a binary overlay,
  one plugin per process, and walks every major record's object graph by reflection. Every property typed `ActorValue`
  is counted, keyed by record type, property and, inside a condition, the condition function. This covers CTDA on INFO,
  PACK, QUST, SCEN, IDLE, SPEL, ENCH, MGEF, PERK, and MGEF `ActorValue`/`SecondActorValue`/`ResistValue`, PERK
  entry-point AVs, RACE skill rows, BPTD, WEAP and AVIF-typed fields. NPC_ records hold skill arrays, not AV enums,
  so they cannot hold a candidate. Cross-check: Dawnguard INFO rows with `Variable09` = 42, matching the first run.
- Papyrus: only compiled `.pex` exist on this machine for vanilla (extracted from `Skyrim - Misc.bsa`: 14,026 scripts,
  which include the Dawnguard, Dragonborn and HearthFires scripts) and for the stack (`~/.argonia/stack/MO2/mods`: 254
  `.pex`, plus `.psc` for SKSE, CSF, EVG, MCM Helper, ConsoleUtil). So the Papyrus scan is a **strings scan of the
  `.pex` string tables** for the exact AV name (case-insensitive, whole entry), noted by whether the same file also
  holds an AV call name (`GetAV`, `SetAV`, `ModAV`, `ForceAV`, `DamageAV`, `RestoreAV`, `GetBaseAV`, `GetActorValue`...).
  A hit proves the name is a string constant; it does not prove which call uses it. The `.psc` grep of the stack
  found AV calls only in SKSE's own `Actor.psc`/`Game.psc` wrappers (no candidate name anywhere).
- Run: `DOTNET_gcServer=0`, `DOTNET_GCHeapHardLimit=0xC0000000`, each plugin under `systemd-run --user --scope -p MemoryMax=3G`
  and `/usr/bin/time -v`. **Peak RSS 453,896 KB (Skyrim.esm, 869,687 records, 19 s)**; next Dragonborn 270,516 KB;
  all 38 stack plugins 117,520–248,680 KB. Total wall about 2.5 min.

## Counts per candidate AV

Record hits are totals per plugin (type/function split, first example FormID local to that plugin). The Papyrus column
counts vanilla `.pex` files naming the AV. The stack mods' 254 `.pex` name none of these AVs (0 hits; only the 6 SKSE
wrapper scripts hold any AV call at all). Plugins not listed for an AV have 0 hits.

| AV (index) | Record hits per plugin (count; record type/function; first example) | Papyrus: vanilla .pex files naming it with an AV call (stack mods: 0) |
|---|---|---|
| Fame (60) | 0 hits in all 43 plugins | 0 files (0 hits) |
| Infamy (61) | 0 hits in all 43 plugins | 0 files (0 hits) |
| FavorsPerDay (80) | 0 hits in all 43 plugins | 0 files (0 hits) |
| FavorsPerDayTimer (81) | 0 hits in all 43 plugins | 0 files (0 hits) |
| FavorPointsBonus (89) | 0 hits in all 43 plugins | 0 files (0 hits) |
| LastFlattered (91) | 0 hits in all 43 plugins | 0 files (0 hits) |
| IgnoreCrippledLimbs (59) | 0 hits in all 43 plugins | 0 files (0 hits) |
| VoicePoints (37) | 0 hits in all 43 plugins | 0 files (0 hits) |
| VoiceRate (38) | 0 hits in all 43 plugins | 0 files (0 hits) |
| Energy (2) | 0 hits in all 43 plugins | 0 files (0 hits) |
| PerceptionCondition (46) | 0 hits in all 43 plugins | 0 files (0 hits) |
| EnduranceCondition (47) | 0 hits in all 43 plugins | 0 files (0 hits) |
| LeftAttackCondition (48) | 0 hits in all 43 plugins | 0 files (0 hits) |
| RightAttackCondition (49) | 0 hits in all 43 plugins | 0 files (0 hits) |
| LeftMobilityCondition (50) | 0 hits in all 43 plugins | 0 files (0 hits) |
| RightMobilityCondition (51) | 0 hits in all 43 plugins | 0 files (0 hits) |
| BrainCondition (52) | 0 hits in all 43 plugins | 0 files (0 hits) |
| WardDeflection (67) | 0 hits in all 43 plugins | 0 files (0 hits) |
| DEPRECATED05 (162) | 0 hits in all 43 plugins | 0 files (0 hits) |
| FavorActive (79) | 0 hits in all 43 plugins | 2 files: favorquestscript.pex, qf_da11favor_0007d949.pex |
| LastBribedIntimidated (90) | Dawnguard.esm 3 (DialogResponses/GetActorValue 3; e.g. 006948:Dawnguard.esm); Skyrim.esm 7 (DialogResponses/GetActorValue 7; e.g. 0B0EED:Skyrim.esm) | 0 files (0 hits) |
| Mood (4) | Update.esm 7 (MagicEffect/(field ActorValue) 7; e.g. 002EE9:Update.esm:Survival_FireCloakFreezingWaterDesc) | 0 files (0 hits) |
| Morality (3) | Skyrim.esm 2 (Quest/GetActorValue 2; e.g. 01BE4D:Skyrim.esm:WIRemoveItem03) | 0 files (0 hits) |
| Assistance (5) | Magic.esp 1 (MagicEffect/(field ActorValue) 1; e.g. 000A50:Magic.esp:aaaPhantomFormEffect) | 3 files: qf_mq206_00036193.pex, qf_mq201_00035d5f.pex, da02script.pex |
| Mass (36) | Magic.esp 2 (MagicEffect/(field ActorValue) 2; e.g. 00095B:Magic.esp:aaaSlowfallFFSelf01) | 1 files: mq304tsunscript.pex |
| Variable01 (68) | Dawnguard.esm 7 (DialogResponses/GetActorValue 5, Package/GetActorValue 2; e.g. 016843:Dawnguard.esm); Dragonborn.esm 14 (DialogResponses/GetActorValue 7, Package/GetActorValue 5, Scene/GetActorValue 2; e.g. 035AED:Dragonborn.esm); Skyrim.esm 149 (Package/GetActorValue 96, DialogResponses/GetActorValue 53; e.g. 06B1A7:Skyrim.esm); TKDodgeAddon.esp 2 (MagicEffect/(field ActorValue) 2; e.g. 00080B:TKDodgeAddon.esp:StyyLowerDodgeCostPotionEffect) | 43 files: pf_dunblackreachshoutstrafe1_000fcbfa.pex, qf_ms13_00039645.pex, carriagesystemscript.pex, qf_mq304_00046ef1.pex, ... |
| Variable02 (69) | Dragonborn.esm 2 (DialogResponses/GetActorValue 2; e.g. 01F9C0:Dragonborn.esm); Skyrim.esm 16 (DialogResponses/GetActorValue 14, ObjectEffect/GetActorValue 2; e.g. 0CDF5E:Skyrim.esm) | 3 files: dlc2_tif__02035aed.pex, da08ebonybladealerteffectscript.pex, cartdriverscript.pex |
| Variable03 (70) | Dragonborn.esm 2 (DialogResponses/GetActorValue 2; e.g. 02C085:Dragonborn.esm); King of the Murkmire.esp 2 (DialogResponses/GetActorValue 2; e.g. 8D67B0:King of the Murkmire.esp); Skyrim.esm 6 (DialogResponses/GetActorValue 2, IdleAnimation/GetActorValue 2, Package/GetActorValue 2; e.g. 0CD9E9:Skyrim.esm) | 5 files: webdestructiblescript.pex, ms13webdestructiblescript.pex, spiderwebanimationsscript.pex, crimeguardsscript.pex, ... |
| Variable04 (71) | Skyrim.esm 6 (Package/GetActorValue 6; e.g. 06BE33:Skyrim.esm:dunValthumeValdarDefaultMaster) | 2 files: defaultnpcruntotrig.pex, dialoguefollowerscript.pex |
| Variable05 (72) | Dragonborn.esm 4 (Spell/GetActorValue 3, MagicEffect/(field ActorValue) 1; e.g. 03D2B4:Dragonborn.esm:DLC2TTR4aAbCheckWater) | 1 files: dlc2ttr4aplayerscript.pex |
| Variable06 (73) | Dawnguard.esm 12 (Package/GetActorValue 11, Spell/GetActorValue 1; e.g. 0138C4:Dawnguard.esm:DLC1dunHarkonWaitForTeleportDeath); Dragonborn.esm 11 (DialogResponses/GetActorValue 5, Package/GetActorValue 5, MagicEffect/GetActorValue 1; e.g. 035AF2:Dragonborn.esm); HearthFires.esm 124 (DialogResponses/GetActorValue 108, Package/GetActorValue 16; e.g. 003EB0:HearthFires.esm); Skyrim.esm 31 (Package/GetActorValue 29, Quest/GetActorValue 2; e.g. 107259:Skyrim.esm:dunKatariahFlutePlayerMoveToCustom02) | 49 files: dlc2_tif__02035e1f.pex, qf_dunbloatedmansgrottoqst_000955cf.pex, dlc2dunkolbjorndeathtrackingscript.pex, dunknifepointridgepollpulllever.pex, ... |
| Variable07 (74) | Dawnguard.esm 6 (DialogResponses/GetActorValue 4, ObjectEffect/GetActorValue 1, Package/GetActorValue 1; e.g. 01682B:Dawnguard.esm); Dragonborn.esm 11 (Package/GetActorValue 11; e.g. 03D3B6:Dragonborn.esm:DLC2MQ06DragonCombatOverrideNoLandingTameDragon); HearthFires.esm 120 (DialogResponses/GetActorValue 106, Package/GetActorValue 14; e.g. 007F35:HearthFires.esm); Skyrim.esm 23 (Package/GetActorValue 13, DialogResponses/GetActorValue 7, Perk/GetActorValue 1; e.g. 02B732:Skyrim.esm) | 98 files: byoh_tif__01016412.pex, tif__02000c92.pex, byoh_tif__01013ed6.pex, tif__02000c93.pex, ... |
| Variable08 (75) | Skyrim.esm 4 (Package/GetActorValue 4; e.g. 0EE39E:Skyrim.esm:dunRobbersGorgeSentyToSouthPositionWeaponSheathed) | 4 files: byohrelationshipadoptionscript.pex, qf_dunrobbersgorgeqst_000b8c9f.pex, c03rampagequest.pex, dunrobbersgorgereset.pex |
| Variable09 (76) | Dawnguard.esm 46 (DialogResponses/GetActorValue 42, Scene/GetActorValue 4; e.g. 016049:Dawnguard.esm); King of the Murkmire.esp 13 (DialogResponses/GetActorValue 13; e.g. 69C694:King of the Murkmire.esp); Skyrim.esm 8 (DialogResponses/GetActorValue 8; e.g. 0453EE:Skyrim.esm) | 46 files: rentroomscript.pex, dlc1_tif__01016066.pex, dlc1_tif__0101604d.pex, dlc1_tif__01016052.pex, ... |
| Variable10 (77) | Dawnguard.esm 2 (Package/GetActorValue 2; e.g. 0138C4:Dawnguard.esm:DLC1dunHarkonWaitForTeleportDeath); Skyrim.esm 3 (Package/GetActorValue 3; e.g. 0EB247:Skyrim.esm:DefaultMasterPackageWeaponDrawnAllowWander) | 3 files: defaultmasterpackageweapondrawnscript.pex, dlc1dunharkonbatteleport.pex, dlc1dunharkonbossbattle.pex |

Other candidates, all **0 hits** in the 43 plugins and in 14,280 `.pex`: the 18 skill-advance AVs (114–131, `OneHandedSkillAdvance`
to `EnchantingSkillAdvance`) and LastFlattered/DEPRECATED05 as listed above. Every other AV hit in the scan is a live AV
(skills, resists, rates, `WaitingForPlayer` for followers, etc.) and is not a candidate.

### Who uses `Variable01`–`10` (vanilla scripts and records)

- Variable01: carts and ferries (carriagesystemscript, cartdriverscript, rpdefault_ferrysystem), Blackreach and DLC
  dragons (dlc2tamedragonscript, dlc1vqdragonscript), 53+7+5 INFO conditions, 96+2+5 package conditions.
- Variable02: cartdriverscript, Ebony Blade (da08ebonybladealerteffectscript); Variable03: webs, crime guards.
- Variable04: **dialoguefollowerscript** (followers) and defaultnpcruntotrig. Variable05: only dlc2ttr4aplayerscript (one
  Dragonborn water check, also an MGEF). Variable06: Hearthfires adoption and children (108 INFO + 16 package rows),
  resurrect-dragon quest. Variable07: Hearthfires adoption TIFs (106 INFO + 14 package rows), spriggan perk (one Perk
  condition), vampire bats amulet. Variable08: robbers-gorge, c03rampage. Variable09: Dawnguard Harkon/Soul Cairn (42 INFO)
  and rentroomscript. Variable10: defaultmasterpackageweapondrawnscript, Harkon.
- No dog or horse script names a Variable. Followers and mounts do not touch the chosen seven.
- Stack plugins: TKDodgeAddon's `StyyLowerDodgeCostPotionEffect` MGEF **writes** Variable01 (2 rows); King of the
  Murkmire has 15 rows copied from vanilla INFO (Variable03, 09). No other stack plugin touches one.

## Actor Value Generator (Nexus 84743)

- **What it is** (GitHub NoahBoddie/actor-value-generator, `LEGACY.md` docs; Nexus page returned 403 to the fetch tool, so
  its description and file notes were not read): an SKSE DLL that reads TOML files from
  `Data/SKSE/Plugins/ActorValueData/*_AVG.toml` and defines "Extra Values": Adaptive (per-actor store, with regen and a
  default formula), Functional (value computed by a formula or a plugin function). An Extra Value declares `alias = "<existing AV>"`;
  uses of that AV in the listed plugins (and plugins that inherit from them) are replaced by the Extra Value. Plugins are named in
  the TOML or an include list. So AVG **does not create new AV indices**: a condition in our plugin reading "Fame"
  reads our value, vanilla reading Fame reads the engine's.
- **Evidence it borrows slots:** the E.S.L.A. TOML (`x60199/.../ESLAAttributes_AVG.toml`) aliases its eight attributes onto Fame,
  Infamy, FavorActive, FavorPointsBonus, FavorsPerDay, FavorsPerDayTimer, LastBribedIntimidated, LastFlattered. Six of those
  are our zero-hit set; one mod ran them on an Oblivion-style 2 s Papyrus loop.
- **Licence:** GPL-3.0 (repo). We would only depend on it as a DLL, never ship its code, but a GPL-3 DLL in the
  sourcing register needs the usual note.
- **Runtime support: unverified.** Repo `vcpkg.json` version 2.0.0.0, last push 2026-09-13; Nexus page is an old (about 3.7
  years) post with no stated game-version range, requires SKSE and Address Library. A dependent mod
  (Magic Fixes and Tweaks) states 1.6.1130+. Nothing found on 1.6.1170 or 1.7.104. Decision 0002 leaves the pin to the 0.2
  smoke run; it would need a DLL load test on the pinned runtime before use.
- **Does it remove the need to borrow?** No (above). What it adds: readable names in conditions only through the alias, an isolated
  store from engine/vanilla writers, regen and default formulas. We do not need regen or formulas because ArgoniaCore
  writes the values. So: **skip, keep as the named fallback**. Sources:
  [Nexus 84743](https://www.nexusmods.com/skyrimspecialedition/mods/84743),
  [GitHub](https://github.com/NoahBoddie/actor-value-generator).

## Recommendation

| Attribute | AV (index) | Why this one | Conflict evidence |
|---|---|---|---|
| Strength | Fame (60) | Unused Oblivion-era reputation AV | 0 record hits, 0 .pex, in 43 plugins |
| Intelligence | Infamy (61) | as Fame | 0 and 0 |
| Willpower | LastFlattered (91) | speech leftover; vanilla uses only its neighbour LastBribedIntimidated | 0 and 0 (LastBribedIntimidated has 10 INFO rows, so keep clear of it) |
| Agility | FavorPointsBonus (89) | favour system never wired | 0 and 0 |
| Speed | FavorsPerDay (80) | as above | 0 and 0 |
| Endurance | FavorsPerDayTimer (81) | as above; only one with a timer name, so a day-pass L4 check first | 0 and 0 |
| Personality | IgnoreCrippledLimbs (59) | Fallout limb leftover | 0 and 0 |

- ArgoniaCore's `stats` family stays canonical; the AV is a mirror written with `SetBaseActorValue`, read by conditions
  as `GetActorValue`/`GetBaseActorValue` (Papyrus `GetAV`) from our plugins only.
- NPCs do not need live attribute AVs (native-map: NPC numbers compiled), so no vanilla NPC script or package can see them.
- Reserve order for P1 carriers: VoicePoints, VoiceRate, Energy, the limb AVs (46–52), the skill-advance AVs (114–131),
  WardDeflection, DEPRECATED05; then Variable04, 05, 08, 10. If the budget still runs out: stepped perk rows on bands
  (the native-map fallback) or the co-save plus mirrored globals.
- AVG route stays unadopted; reopen only if an L4 check below shows an engine write on a chosen AV.

## L4 checks owed to a later game lane

Every check starts from a scene on the base save (CLAUDE.md). SkyLink and the console are the hands.

1. **Set and read back, each chosen AV and each reserve in turn:** `SetBaseActorValue` (ArgoniaCore) 10, 50, 100 on the player; read
   back by console `GetActorValue`, by Papyrus `GetAV`/`GetBaseActorValue`, and by a throwaway condition (a perk or
   MGEF conditioned `GetActorValue <AV> >= N` that visibly toggles). Prove the AV name is accepted in the condition
   parameter, including DEPRECATED05 and the `*SkillAdvance` names.
2. **Rest, wait and a fight:** with all seven set to distinct values, rest 24 game hours (incl. a day change, for FavorsPerDay
   and the Timer), fight a bandit and a draugr, take a hit, cast, swim, sprint; re-read the seven after each. Pass only
   if none moved. Include a save, quit and load round trip (are the values persisted by the engine, and is ArgoniaCore's
   mirror rewrite enough on load?).
3. **Vanilla side-effect probe:** with Personality = 100 (IgnoreCrippledLimbs) and Strength = 100 (Fame): check combat damage,
   dismemberment and crippled limb behaviour, shop prices, crime bounty and persuasion do not change vs a baseline with 0.
4. **Followers and cities:** with a follower and a Hearthfires child NPC present, re-read the seven (and Variable04/05/08/10 only
   if ever chosen) to prove the Variable scripts do not move them.
5. **Mod interaction:** load the whole stack (Papyrus-using mods: TKDodgeAddon, XPMSE, HTBM) and repeat check 2 to confirm
   TKDodgeAddon's Variable01 write is harmless to the chosen set.
6. **Console/UI stray readers:** open the stats and console views and confirm no vanilla menu shows or edits a chosen AV.
7. **If AVG is ever reopened:** DLL load on the pinned runtime from the smoke run before anything else, then check 1 on an Extra Value alias.

## Unverified

- Engine-native (non-data) readers/writers of the seven chosen AVs: checks 1–3, 6.
- `.psc` sources for vanilla and for most stack mods are absent; Papyrus evidence is a `.pex` strings scan. It does not see AV names
  built at runtime from a concatenated string.
- AVG on the pinned runtime, and its Nexus page text (403 to fetch).
- The Creation Club masters in Data were not scanned (not in the load order file).
