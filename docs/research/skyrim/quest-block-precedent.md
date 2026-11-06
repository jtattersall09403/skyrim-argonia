# Skyrim.esm precedent counts for the quest blocks

Measured 2026-11-05 for [docs/design/blocks.md](../../design/blocks.md) by a research agent with tools/argonia_world/esm.py (helpers not kept). Script categories are by script name in VMAD; fragment bodies are compiled and not read.


Source: ~/games/skyrimse/Data/Skyrim.esm read by tools/argonia_world/esm.py (869,687 records; 1,811 QUST; 31,465 INFO; masters none). Scripts parsed from VMAD (script names, not pex bodies, so a "category" is by NAME: a script called defaultsetstageonplayeracquire is assumed to do what it says; pex source not read, the Misc.bsa is compressed). CTDA function indices and QUST/alias flag bits verified against xEdit TES5Edit dev-4.1.5 Core/wbDefinitionsTES5.pas (GetStage 58, GetStageDone 59, GetGlobalValue 74, GetInFaction 71, GetFactionRank 73, GetItemCount 47, GetActorValue 14, GetCurrentTime 18, GetDead 46, GetIsID 72, GetQuestRunning 56, GetQuestCompleted 543, GetInCurrentLoc 359). Note: the Story Manager event code names for QUST ENAM are NOT in that file; CLOC/KILL/SCPT names are from memory (not verified); the brief's "LCHG" does not occur, vanilla uses CLOC. ADIA is the dominant code (784 quests, mostly dialogue/scene quests); meaning not verified.

Helper scripts: main.py, stats3.py in this folder. Script-name regexes are case-folded because vanilla mixes case (defaultSetStageTrigSCRIPT / defaultsetstagetrigscript).

| block | measure | count | examples | how measured |
|---|---|---|---|---|
| Effects: quest flags | Start Game Enabled | 330 of 1811 quests | CreatureDialogueWerewolf, CWReservations, CreatureDialogueFox | QUST DNAM u16 flags, bit per xEdit wbDefinitionsTES5 (dev-4.1.5) line ~11181 |
| Effects: quest flags | Run Once | 207 of 1811 quests | dunThrowVoiceQst, DA04SeptimusSendForPlayerQuest, C00SwapVignarAndBrillOnAscension | QUST DNAM u16 flags, bit per xEdit wbDefinitionsTES5 (dev-4.1.5) line ~11181 |
| Effects: quest flags | Displayed in HUD | 0 of 1811 quests |  | QUST DNAM u16 flags, bit per xEdit wbDefinitionsTES5 (dev-4.1.5) line ~11181 |
| Effects: quest flags | Allow repeated stages | 105 of 1811 quests | TGNightingalePowerHandler, BardAudienceQuest, WEJS18 | QUST DNAM u16 flags, bit per xEdit wbDefinitionsTES5 (dev-4.1.5) line ~11181 |
| Effects: quest flags | Warn on alias fill failure | 41 of 1811 quests | CR12, CWFortSiegeFort, CidhnaMineJailEventScene | QUST DNAM u16 flags, bit per xEdit wbDefinitionsTES5 (dev-4.1.5) line ~11181 |
| Alias fill type | ref alias: unique actor (ALUA) | 2900 aliases in 1149 quests | ArenaCombatQuest00DBSpecial, BardSongStarter, BardsCollegeDrum | walk QUST subrecords ALST/ALLS..ALED; first matching fill subrecord in priority ALFR>ALUA>ALCO>ALEQ>ALFL>ALFE>ALRT>ALFA>CTDA-only |
| Alias fill type | ref alias: forced ref (ALFR) | 2687 aliases in 425 quests | ArenaWagerFighterQuest, BQ01, BQ02 | walk QUST subrecords ALST/ALLS..ALED; first matching fill subrecord in priority ALFR>ALUA>ALCO>ALEQ>ALFL>ALFE>ALRT>ALFA>CTDA-only |
| Alias fill type | ref alias: location alias ref (ALFA+ALRT) | 2036 aliases in 175 quests | ArenaCombatQuest00DBSpecial, ArenaCombatQuest00JailFight, ArenaCombatQuest00LevelTransition | walk QUST subrecords ALST/ALLS..ALED; first matching fill subrecord in priority ALFR>ALUA>ALCO>ALEQ>ALFL>ALFE>ALRT>ALFA>CTDA-only |
| Alias fill type | ref alias: from event (ALFE) | 1771 aliases in 927 quests | CWAttackCity, CWCampaign, CWDialogueSoldiers01 | walk QUST subrecords ALST/ALLS..ALED; first matching fill subrecord in priority ALFR>ALUA>ALCO>ALEQ>ALFL>ALFE>ALRT>ALFA>CTDA-only |
| Alias fill type | ref alias: find matching (conditions only) | 1266 aliases in 315 quests | ArenaCombatQuest00LevelTransition, ArenaCrowdQuest, BQ01 | walk QUST subrecords ALST/ALLS..ALED; first matching fill subrecord in priority ALFR>ALUA>ALCO>ALEQ>ALFL>ALFE>ALRT>ALFA>CTDA-only |
| Alias fill type | ref alias: no fill / filled by script or ALFI | 630 aliases in 119 quests | BardSongs, BardSongsInstrumental, C00 | walk QUST subrecords ALST/ALLS..ALED; first matching fill subrecord in priority ALFR>ALUA>ALCO>ALEQ>ALFL>ALFE>ALRT>ALFA>CTDA-only |
| Alias fill type | ref alias: created ref (ALCO) | 630 aliases in 271 quests | ArenaCombatQuest00JailFight, ArenaCombatQuest01Skeevers, ArenaCombatQuest02Wolves | walk QUST subrecords ALST/ALLS..ALED; first matching fill subrecord in priority ALFR>ALUA>ALCO>ALEQ>ALFL>ALFE>ALRT>ALFA>CTDA-only |
| Alias fill type | loc alias: from event (ALFE) | 294 aliases in 197 quests | BQ01, BQ02, BQ03 | walk QUST subrecords ALST/ALLS..ALED; first matching fill subrecord in priority ALFR>ALUA>ALCO>ALEQ>ALFL>ALFE>ALRT>ALFA>CTDA-only |
| Alias fill type | loc alias: no fill / filled by script or ALFI | 248 aliases in 86 quests | CWCampaign, CWFortSiegeCapital, CWFortSiegeFort | walk QUST subrecords ALST/ALLS..ALED; first matching fill subrecord in priority ALFR>ALUA>ALCO>ALEQ>ALFL>ALFE>ALRT>ALFA>CTDA-only |
| Alias fill type | loc alias: specific location (ALFL) | 162 aliases in 98 quests | ArenaCombatQuest00DBSpecial, ArenaCombatQuest00JailFight, ArenaCombatQuest00LevelTransition | walk QUST subrecords ALST/ALLS..ALED; first matching fill subrecord in priority ALFR>ALUA>ALCO>ALEQ>ALFL>ALFE>ALRT>ALFA>CTDA-only |
| Alias fill type | loc alias: find matching (conditions only) | 136 aliases in 90 quests | BQ01, BQ02, BQ03 | walk QUST subrecords ALST/ALLS..ALED; first matching fill subrecord in priority ALFR>ALUA>ALCO>ALEQ>ALFL>ALFE>ALRT>ALFA>CTDA-only |
| Alias fill type | ref alias: external alias (ALEQ) | 79 aliases in 27 quests | BardAudienceQuest, C06FuneralObserversQuest, CWCampaignObj | walk QUST subrecords ALST/ALLS..ALED; first matching fill subrecord in priority ALFR>ALUA>ALCO>ALEQ>ALFL>ALFE>ALRT>ALFA>CTDA-only |
| Alias fill type | loc alias: alias-relative (ALFA) | 48 aliases in 43 quests | BQ01, BQ02, BQ03 | walk QUST subrecords ALST/ALLS..ALED; first matching fill subrecord in priority ALFR>ALUA>ALCO>ALEQ>ALFL>ALFE>ALRT>ALFA>CTDA-only |
| Alias fill type | loc alias: external alias (ALEQ) | 4 aliases in 3 quests | CWCampaignObj, CWGovernment, MQ101DragonAttack | walk QUST subrecords ALST/ALLS..ALED; first matching fill subrecord in priority ALFR>ALUA>ALCO>ALEQ>ALFL>ALFE>ALRT>ALFA>CTDA-only |
| Alias flags (FNAM u16) | Reserves Location/Reference | 1143 aliases in 267 quests | BQ01, C00, C04 | FNAM flag bits per xEdit wbQUSTAliasFlags |
| Alias flags (FNAM u16) | Optional | 3707 aliases in 358 quests | ArenaCrowdQuest, ArenaWagerFighterQuest, BQ01 | FNAM flag bits per xEdit wbQUSTAliasFlags |
| Alias flags (FNAM u16) | Quest Object | 434 aliases in 196 quests | BardsCollegeDrum, BardsCollegeFlute, BardsCollegeLute | FNAM flag bits per xEdit wbQUSTAliasFlags |
| Alias flags (FNAM u16) | Allow Reuse in Quest | 2316 aliases in 906 quests | C00, C02, C03 | FNAM flag bits per xEdit wbQUSTAliasFlags |
| Alias flags (FNAM u16) | Allow Dead | 1375 aliases in 123 quests | C00, C00DebugFollowerComeHere, C03PostQuest | FNAM flag bits per xEdit wbQUSTAliasFlags |
| Alias flags (FNAM u16) | Matching Ref In Loaded Area | 157 aliases in 41 quests | BardAudienceQuest, DA02GuardWarn, DGIntimidateQuest | FNAM flag bits per xEdit wbQUSTAliasFlags |
| Alias flags (FNAM u16) | Essential | 194 aliases in 70 quests | ArenaCombatQuest00LevelTransition, C00, C00GiantAttack | FNAM flag bits per xEdit wbQUSTAliasFlags |
| Alias flags (FNAM u16) | Allow Disabled | 2073 aliases in 249 quests | BardsCollegeDrum, BardsCollegeFlute, BardsCollegeLute | FNAM flag bits per xEdit wbQUSTAliasFlags |
| Alias flags (FNAM u16) | Allow Reserved | 5598 aliases in 1047 quests | ArenaCombatQuest00DBSpecial, BQ01, BQ02 | FNAM flag bits per xEdit wbQUSTAliasFlags |
| Alias flags (FNAM u16) | Protected | 144 aliases in 42 quests | ArenaCombatQuest00DBSpecial, ArenaCombatQuest00JailFight, ArenaCombatQuest00LevelTransition | FNAM flag bits per xEdit wbQUSTAliasFlags |
| Alias flags (FNAM u16) | Forced by Aliases | 61 aliases in 27 quests | CR01, CW03, CWAttackCity | FNAM flag bits per xEdit wbQUSTAliasFlags |
| Alias flags (FNAM u16) | Allow Destroyed | 121 aliases in 14 quests | CWFortSiegeCapital, CWFortSiegeFort, CWPrepareCity | FNAM flag bits per xEdit wbQUSTAliasFlags |
| Alias flags (FNAM u16) | Matching Ref Closest | 143 aliases in 37 quests | BardAudienceQuest, DA02GuardWarn, DGIntimidateQuest | FNAM flag bits per xEdit wbQUSTAliasFlags |
| Alias flags (FNAM u16) | Initially Disabled | 61 aliases in 34 quests | BQ01, BQ02, BQ03 | FNAM flag bits per xEdit wbQUSTAliasFlags |
| Alias | total aliases | 12891 (11999 ref, 892 location) | Hero1, Hero2, Location | ALST/ALLS count |
| Effects: stages | stage entries (INDX) / quests with stages | 5220 stages in 871 quests |  | INDX subrecords |
| Effects: journal | stages with log text (CNAM after INDX) | 726 stages in 203 quests | TGRDU, dunHunterQST, MS01 | CNAM between INDX and next INDX/QOBJ (strings are localised ids, count of presence only) |
| Effects: objectives | QOBJ objectives | 1452 objectives in 396 quests | TGRDU, WICastMagic03, dunHunterQST | QOBJ subrecords |
| Effects: alias packages | ALPC package entries | 4125 in 365 quests | CRTwinsPostQuest, MQGreybeardCall, WERoad12 | ALPC subrecords in QUST |
| Effects: alias factions | ALFC faction entries | 1215 in 140 quests (all targets resolve to FACT) | MQHighHrothgarTraining3, MQHighHrothgarTraining2, MQHighHrothgarTraining1 | ALFC subrecords; target sig checked |
| Effects: alias spells | ALSP spell entries | 70 in 19 quests | dunGauldursonQST, CWFinale, C00VilkasTrainingQuest | ALSP subrecords |
| Effects: scenes | SCEN records / quests owning scenes | 1706 scenes in 1378 quests | MQ203EsbernEntrancePatrol, MQ101TorriGoesInside, BleakFallsDragonLakePatrol | SCEN PNAM = owning quest |
| Effects: packages | PACK records | 5961; 324 with PF_ fragments |  | PACK count; VMAD contains PF_ |
| Effects: enable parent | REFR/ACHR with XESP | 23239 of 703837 refs | KilkreathDarkMists, KilkreathDarkMists, KilkreathDarkMists | XESP subrecord on REFR/ACHR/ACRE |
| World edits: initially disabled | refs with record flag 0x800 | 4072 of 703837 refs (ACHR 1390) |  | record flags bit 0x800 "Initially Disabled" |
| World edits: initially disabled | of which also have XESP | 911 |  | flags & XESP |
| World edits: NPC template | NPC_ with TPLT | 3651 of 5118 | dunTransmogrifyDremora, dunTransmogrifyHare, dunTransmogrifyMudcrab | TPLT subrecord |
| World edits: NPC level | NPC_ with PC Level Mult (ACBS flag 0x80) | 454 of 5118 | MQ304LostSoulSons3, MQ304LostSoulImperial2, MQ304LostSoulSons2 | ACBS flags bit 0x80 |
| World edits: NPC level | NPC_ with fixed level (flag off) | 4664 | dunTransmogrifyDremora, dunTransmogrifyHare, dunTransmogrifyMudcrab | ACBS flags & 0x80 == 0 |
| Trigger (c): Story Manager event | QUST ENAM = ADIA | 784 quests | MQSovngardeConv2ActorDialogue, CWDialogueSoldiers02, MQSovngardeConv4 | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager event | QUST ENAM = SCPT | 188 quests | MQGreybeardCall, MQHighHrothgarTraining3, MQHighHrothgarTraining2 | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager event | QUST ENAM = CLOC | 135 quests | KingOlafsFestivalStarter, MGScrollSwap, DA04SeptimusSendForPlayerQuest | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager event | QUST ENAM = KILL | 13 quests | DA08FriendKill, MQVoiceoftheSkyMonitor, WIKill06 | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager event | QUST ENAM = CRFT | 10 quests | TutorialAlchemyHealPotion, TutorialBlacksmithingArmorTemper, TutorialBlacksmithingAmor | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager event | QUST ENAM = LEVL | 7 quests | DA08RumorPointer, FreeformRiften09, DA09 | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager event | QUST ENAM = AIPL | 5 quests | C00PlayerTheftPoke, WIAddItem07, WIAddItem03 | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager event | QUST ENAM = CAST | 5 quests | MG01ShoutUpdate, WICastMagic04, WICastMagic03 | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager event | QUST ENAM = REMP | 5 quests | WIRemoveItem05, WIRemoveItem04, WIRemoveItem03 | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager event | QUST ENAM = ASSU | 4 quests | WIAssaultRemember, DBSuspensionQuest, WIAssault02 | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager event | QUST ENAM = JAIL | 3 quests | JailQuest, EastmarchJailArenaFightQuest, DB03GetArrestedQuest | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager event | QUST ENAM = ESJA | 2 quests | EscapeJailQuest, EscapeJailAchievementQuest | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager event | QUST ENAM = SKIL | 2 quests | WISkillIncrease02, WISkillIncrease01 | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager event | QUST ENAM = CHRR | 2 quests | FavorJarlsMakeFriendsTrackEvent, RelationshipMarriageBreakUp | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager event | QUST ENAM = ARRT | 2 quests | TG00ArrestMonitor, DGArrestQuest | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager event | QUST ENAM = DEAD | 2 quests | DA02DeadBody, WIDeadBody01 | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager event | QUST ENAM = AHEL | 2 quests | CWDialogueSoldiersHellos, DialogueGenericDogHellos | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager event | QUST ENAM = NVPE | 1 quests | WINewVoicePower01 | QUST ENAM 4cc event code (code names not verified in xEdit source; CLOC=change location, KILL=kill actor, SCPT=script event, ADIA=? see note) |
| Trigger (c): Story Manager | SMEN event nodes / SMBN branch nodes / SMQN quest nodes | 24 / 99 / 448 | SovngardeSparringNode, MS05KingOlafsFestivalNode, CompanionsJorrvaskrTheftNode | record counts |
| Trigger (b): trigger boxes | ACTI bases with a *Trig* script | 256 | IvarsteadSSTrigger, defaultSetMultiAVTrigger, TG08GuildSceneTrigger | script names in ACTI VMAD, case-insensitive "trig" |
| Trigger (b): trigger boxes | REFR placed from those bases | 2966 |  | REFR NAME in the set |
| Trigger (b): trigger boxes | REFR/ACHR carrying a *Trig* script directly (instances) | 1195 | defaultsetstagetrigscript 327, traptriggerbase 166, wetriggerscript 146, wicommenttriggerscript 130, cwthreattriggerscript 129, defaultsetstagetrigspecificactor 48, defaultstartscenetrigscript 47, wordwalltriggerscript 46 | REFR VMAD; case-folded counts |
| Trigger (b)/(d): ref-level setstage scripts | refs with any *SetStage* script | 444 | defaultsetstagetrigscript 330, defaultsetstagetrigspecificactor 49, defaultsetstageactscript 13, defaultsetstageonenter 12, defaultsetstageactorrefscript 10, defaultsetstageonattacked 9, defaultsetstageondeath 4, dunbloatedmansetstageonactivate 3 | REFR/ACHR VMAD names containing setstage |
| Trigger (b)/(d): ACTI setstage scripts | ACTI bases with *SetStage* script | 16 | defaultSetStageTRIGOnLeavePlayerOnly, MQ101SetStage270Trigger, MQ101InsideHelgenTrigger | ACTI VMAD |
| Trigger (b): XPRM primitive | REFR with XPRM | 13668 | DA09Trigger, RoomMarker, RoomMarker | XPRM subrecord (bounds/primitive); examples are base editor ids |
| Trigger (b): XPRM primitive | XPRM refs that have a script (own or base ACTI) | 3345 |  | VMAD |
| Trigger (d): activate | script names matching setstage+act / OnActivate (all record types) | 178 records; names: defaultsetstagetrigspecificactor 50, defaultaoepushonactivatedoonce 33, defaultsetstageactscript 17, defaultdisableselfonactivate 16, defaultsetstageactorrefscript 10, defaultdisableotherobjectonactivate 10, defaultsetavonactivate 8, defaultonactivatedisablelinkedref 7 |  | VMAD script names (not pex bodies); includes alias scripts |
| Trigger (d): activate | alias scripts, activate | 7 quests; scripts: mdfailquestonactordeath (3), mgrdestructionbook03activatorscript (1), mgrdestructionbook01activatorscript (1), mgrdestructionbook02activatorscript (1), dunansilvundnoactivatealias (1), mq201partydoorblockactivationscript (1), maceofmolagbalactivatorscript (1) | DA10, FreeformWhiterunQuest01, FreeformWhiterunQuest03 | QUST alias VMAD script names, case-folded, regex activat/onact/setstageact |
| Trigger (f): item pickup | alias scripts, pickup/acquire | 18 quests; scripts: defaultsetstageonplayeracquire (16), freeformcidhnamineaonitemadded (1), ms01onitemaddedscript (1) | C06, CR06, CR10 | QUST alias VMAD script names, case-folded, regex acquire/pickup/onitemadded/containerchanged |
| Trigger (g): death | alias scripts, death | 98 quests; scripts: favornpcdeathscript (46), defaultsetstageondeathrefalias (20), swapaliasondeath (10), defaultaliasondeathscript (8), werjsetstageondeath (3), mdfailquestonactordeath (3), tg03aliasdeathscript (2), mq201malborndeathscript (1) | CR07, CR08, CR13 | QUST alias VMAD script names, case-folded, regex death/ondead/dead |
| Trigger (e): read a book | alias scripts, read book | 6 quests; scripts: defaultsetstageonclosebook (4), defaultonreadsetqueststage (2) | MS01, WERJ13, dunFrostmereCryptQST | QUST alias VMAD script names, case-folded, regex onread/closebook |
| Trigger (i): sleep/wait | alias scripts, sleep | 0 quests; scripts:  |  | QUST alias VMAD script names, case-folded, regex sleep |
| Trigger: alias setstage family | alias scripts, any setstage* | 157 quests; scripts: defaultsetstagealiasscript (119), defaultsetstageondeathrefalias (20), defaultsetstageonplayeracquire (16), defaultsetstageonhitaliasscript (5), defaultsetstageonclosebook (4), werjsetstageondeath (3), ms06aliassetstagetriggerplus (2), solitudeopeningsetstagescript (1) | C06, CR06, CR07 | QUST alias VMAD script names, case-folded, regex setstage |
| Trigger (g): death | all records with a *Death* script (names, incl. ACHR) | 221 records | defaultcounterincrementondeath 47, favornpcdeathscript 46, defaultsetstageondeathrefalias 20, dundustmanscairndraugrdeath 18, dunhillgrundstombdraugrdeath 11, swapaliasondeath 10 | all VMAD |
| Trigger (f): pickup | all records with acquire/pickup script | 24 records | defaultsetstageonplayeracquire 16, defaultsetstageonplayeracquireitem 8 | all VMAD |
| Trigger (i): sleep | all records with a *Sleep* script (names) | 10 records | marriagesleepabscript 1, dunsleepingtreesapdruggedeffect 1, playersleepquestscript 1, qf_playersleepquest_000fc1a2 1, qf_dunsleepingtreecampqst_000e1a9d 1, dunsleepingtreecampqstscript 1, pf_ambushsleeplinkedref_00048abc 1, pf_alvasleep8x12_00041fbf 1 | all VMAD; many are furniture/sleeping-tree scripts not quest triggers |
| Trigger (e): read a book | BOOK records with any script | 28 of 821 | duntreasmapscript 11, ms11butcherjournal2script 3, defaultsetstageonclosebooknotalias 3, defaultonreadsetqueststagenotalias 2, dbsanctuaryskillbooksscript 2, defaultsetstageonplayeracquireitem 2, weroad08letterscript 1, da04septimussignusletterscript 1, defaultaddmapmarkeronclosebooknotalias 1, ms01eltrysnotescript 1 | BOOK VMAD names |
| Trigger (e): read a book | of which setstage/OnRead/CloseBook family (BOOK-level) | 6 | Book3ValuableLostLegends, Book2CommonExplorersGuideToSkyrim, dunFrostmereCryptEisaJournal | regex setstage/onread/closebook |
| Trigger (a): dialogue fragments | INFO with TIF fragment | 5540 of 31465 INFOs; 475 owning quests | VoicePowers, DialogueGeneric, dunEldergleamT03 | INFO VMAD contains TIF_; owner = DIAL QNAM via group parent |
| Trigger (a) | INFO whose script list contains a TIF* name (parsed) | 5540 |  | parse_scripts |
| Trigger: quest stage fragments | QUST with stage fragments (QF_) | 845 of 1811 | MQSovngardeConv2ActorDialogue, KingOlafsFestivalStarter, DA15Return | QUST VMAD fragment section, fragCount>0 |
| Trigger: scene fragments | SCEN with SF_ fragment | 577 of 1706 |  | VMAD |
| Quests with any non-fragment quest script |  | 658 of 1811 | wescript 98, whiterunstablescene3script 54, favorchangelocationquestscript 24, ivarsteaddialoguequestscript 20, arenacombatquest 14 | QUST VMAD |
| Quests with any alias script |  | 521 of 1811 |  | QUST VMAD alias section |
| Conditions | GetStage (func 58) | QUST 166 uses/71 recs; INFO 6040 uses/5033 recs; PACK 1506 uses/1172 recs; SCEN 258 uses/91 recs; ALL 8029 uses/6410 recs | 0xdd7, 0xdd8, 0xe3d | CTDA u16 at bytes 8..10; index verified against xEdit TES5 table |
| Conditions | GetStageDone (func 59) | QUST 188 uses/66 recs; INFO 2848 uses/2113 recs; PACK 596 uses/422 recs; SCEN 506 uses/131 recs; ALL 4175 uses/2766 recs | 0xdd7, 0xdd8, MS03LouisLetrushWalkOffScenePackage | CTDA u16 at bytes 8..10; index verified against xEdit TES5 table |
| Conditions | GetGlobalValue (func 74) | QUST 121 uses/58 recs; INFO 1074 uses/989 recs; PACK 232 uses/113 recs; SCEN 16 uses/13 recs; ALL 1579 uses/1231 recs | 0x14105, 0x142c2, MQ101StayOnHorseQT1 | CTDA u16 at bytes 8..10; index verified against xEdit TES5 table |
| Conditions | GetInFaction (func 71) | QUST 2136 uses/206 recs; INFO 4554 uses/3539 recs; PACK 89 uses/67 recs; SCEN 1 uses/1 recs; ALL 6904 uses/3876 recs | 0xdd7, 0xdd8, 0xe3d | CTDA u16 at bytes 8..10; index verified against xEdit TES5 table |
| Conditions | GetFactionRank (func 73) | QUST 1 uses/1 recs; INFO 254 uses/230 recs; PACK 2 uses/2 recs; SCEN 0 uses/0 recs; ALL 259 uses/235 recs | 0x15490, 0x15494, 0x154b4 | CTDA u16 at bytes 8..10; index verified against xEdit TES5 table |
| Conditions | GetItemCount (func 47) | QUST 70 uses/25 recs; INFO 576 uses/519 recs; PACK 3 uses/3 recs; SCEN 0 uses/0 recs; ALL 678 uses/571 recs | 0x13629, 0x1362b, 0x13630 | CTDA u16 at bytes 8..10; index verified against xEdit TES5 table |
| Conditions | GetActorValue (func 14) | QUST 21 uses/14 recs; INFO 318 uses/312 recs; PACK 169 uses/157 recs; SCEN 21 uses/5 recs; ALL 543 uses/500 recs | 0x17efe, 0x185d8, 0x185da | CTDA u16 at bytes 8..10; index verified against xEdit TES5 table |
| Conditions | GetCurrentTime (func 18) | QUST 16 uses/8 recs; INFO 26 uses/13 recs; PACK 0 uses/0 recs; SCEN 78 uses/6 recs; ALL 518 uses/226 recs | MUSExploreDay09, _MUSExploreSILENT15TypeSpacerNIGHT, 0x2094a | CTDA u16 at bytes 8..10; index verified against xEdit TES5 table |
| Conditions | GetDead (func 46) | QUST 234 uses/55 recs; INFO 585 uses/499 recs; PACK 103 uses/53 recs; SCEN 78 uses/32 recs; ALL 1028 uses/660 recs | DialogueMarkarthKeepStormcloakCourtScene04, DialogueMarkarthTreasuryHouseThonarBetridScene01, 0x176a6 | CTDA u16 at bytes 8..10; index verified against xEdit TES5 table |
| Conditions | GetIsID (func 72) | QUST 3595 uses/842 recs; INFO 15347 uses/14743 recs; PACK 32 uses/31 recs; SCEN 3 uses/2 recs; ALL 19169 uses/15768 recs | 0xe3d, WinterholdHousecarlSleepLonghouse23x7, 0x130da | CTDA u16 at bytes 8..10; index verified against xEdit TES5 table |
| Conditions | GetQuestRunning (func 56) | QUST 25 uses/10 recs; INFO 174 uses/170 recs; PACK 85 uses/80 recs; SCEN 1 uses/1 recs; ALL 316 uses/289 recs | 0xdd7, 0xdd8, 0x1c488 | CTDA u16 at bytes 8..10; index verified against xEdit TES5 table |
| Conditions | GetQuestCompleted (func 543) | QUST 21 uses/20 recs; INFO 387 uses/376 recs; PACK 35 uses/35 recs; SCEN 4 uses/3 recs; ALL 470 uses/457 recs | MS05KingOlafsFestivalNode, DA11VerulusStandOutsideHallofDeadPackage, FaendalMS13VisitCamilla7x2 | CTDA u16 at bytes 8..10; index verified against xEdit TES5 table |
| Conditions | location functions 359/360/444/562/563/565/567/603/604/605/610 (GetInCurrentLoc, GetInCurrentLocAlias, GetInCurrentLocFormList, LocationHasKeyword, LocationHasRefType, GetIsEditorLocation, GetIsEditorLocAlias, IsInSameCurrentLocAsRef, IsInSameCurrentLocAsRefAlias, LocAliasIsLocation, LocAliasHasKeyword) | QUST 1162 uses/187 recs; INFO 987 uses/927 recs; PACK 73 uses/57 recs; SCEN 14 uses/6 recs; ALL 2650 uses/1460 recs | dunBrokenFangCaveNode, 0x153b8, 0x153b9 | CTDA func in set; indices verified in xEdit table (359,360,444,562,563,565,567,603-605,610) |
| Conditions |   GetInCurrentLoc (359) all records | 1058 uses/826 recs |  | CTDA |
| Conditions |   GetInCurrentLocAlias (360) all records | 260 uses/102 recs |  | CTDA |
| Conditions |   GetInCurrentLocFormList (444) all records | 8 uses/7 recs |  | CTDA |
| Conditions |   LocationHasKeyword (562) all records | 512 uses/383 recs |  | CTDA |
| Conditions |   LocationHasRefType (563) all records | 70 uses/53 recs |  | CTDA |
| Conditions |   GetIsEditorLocation (565) all records | 94 uses/68 recs |  | CTDA |
| Conditions |   GetIsEditorLocAlias (567) all records | 416 uses/29 recs |  | CTDA |
| Conditions |   IsInSameCurrentLocAsRef (603) all records | 0 uses/0 recs |  | CTDA |
| Conditions |   IsInSameCurrentLocAsRefAlias (604) all records | 7 uses/3 recs |  | CTDA |
| Conditions |   LocAliasIsLocation (605) all records | 201 uses/147 recs |  | CTDA |
| Conditions |   LocAliasHasKeyword (610) all records | 24 uses/16 recs |  | CTDA |
| Conditions | GetActorValue on a skill (AV 6..23, xEdit enum) | 150 uses/126 recs; by sig INFO 121, SCEN 18, QUST 11 | 0xc4202, 0xc4206, 0xc0809 | CTDA param1 at bytes 12..16 |
| Trigger (h): another quest stage | QUST with GetStage/GetStageDone CTDA on a different quest | 86 of 1811 | CW, MG07, TG07 | param1 != own formid; QUST fragment bodies opaque (fragments setting other quests not counted) |
| Trigger (h): another quest stage | INFO with GetStage/GetStageDone on a quest other than its owner | 1596 |  | owner = DIAL QNAM |
| Trigger (h) | QUST with GetStage/GetStageDone on itself | 44 |  |  |
| Trigger (i): wait days | records with GetGlobalValue(GameDaysPassed) CTDA | 8 records (7 QUST; by sig {'QUST': 7, 'SMQN': 1}) | WICommentCollegeRobes, WICommentNaked, WICommentSneaking | GLOB GameDaysPassed formid ['0x39'] |
| Conditions | GetGlobalValue top globals |  | HirelingCommentNextAllowed 247, GameHour 188, TGTalkGate 121, CWBattlePhase 117, TGRFailVex 68, TRUEGlobal 60 | CTDA param1 |

## Not measured
- Distinct quests targeted by each trigger-box ref (needs property object-id parsing; scripts parsed by name only).
- Quest-fragment bodies (QF_ scripts are compiled; whether they set other quests' stages is opaque).
- Script behaviour by pex body (name-based classification only).
- Story Manager event code meanings (not in the xEdit file consulted).

## Added 2026-11-06 (the slice's world edits)

| block | measure | count | examples | how measured |
|---|---|---|---|---|
| W-navmesh | interior CELLs with NAVM | 583 of 590 (1,519 NAVM in interiors; 15,966 in all) | NightingaleHall01, DragonBridgeFarm, WhiterunJail02 | CELL DATA bit 0x1; NAVM in the CELL's child group |
| W-name | CELLs with FULL; map markers with FULL | 583 (all interiors); 397 of 397 XMRK REFRs | KilkreathRuins03, TwistedRootCaveMapMarker | CELL FULL; REFR with XMRK then FULL |
| W-ref | placements initially disabled; with an enable parent | 4,072 (2,682 REFR, 1,390 ACHR); 23,239 XESP; 911 both | DA09PedestalEmptyRef, TGNightingaleBeds | record flag 0x800; XESP subrecord |


## Added 2026-11-06 (setDoorAccess: a door unlocked or its key given by a quest)

| block | measure | count | examples | how measured |
|---|---|---|---|---|
| E-item (setDoorAccess) | door REFRs with a lock (XLOC); of which name a key | 762; 398 | | REFR whose NAME is a DOOR base, XLOC present, key form id at XLOC offset 4 |
| E-item (setDoorAccess) | QUST whose QF_ fragment script has a property that is a locked door ref or a KEYM | 36 (22 a locked door, 18 a key) | HousePurchase, MQ101, MG01, DB01, TG06, MS01 | VMAD scripts parsed property by property (object and object-array values); script name starts qf_ |
| E-item (setDoorAccess) | INFO whose TIF_ fragment script has such a property | 25 INFOs (7 a door, 18 a key) in 13 quests | MS01 6, DialogueWhiterunGuardGateStop 4, DA15 3 | as above, script name starts tif_; owner is the DIAL's QNAM |
| E-item (setDoorAccess) | quests with either | 43 | | union of the two |

The stage a fragment belongs to is in the compiled fragment and is not counted; a property names what a fragment may touch, not what it does (a door may be opened, unlocked or disabled).
