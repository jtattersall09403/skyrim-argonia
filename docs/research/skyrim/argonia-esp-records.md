# Argonia.esp: every record, read back from the built plugin

Written by `make plugin-check` (tools/ArgoniaPlugin `list`) from `out/Argonia.esp`; masters: Skyrim.esm, Update.esm, Dawnguard.esm, HearthFires.esm, Dragonborn.esm, ccBGSSSE001-Fish.esm, ccBGSSSE025-AdvDSGS.esm, unofficial skyrim special edition patch.esp, Black Marsh.esm, Black Marsh North.esp, Valenwood.esp, RimExecutionHitSA.esp. 2359 records. Quest overrides keep the winning record (aliases, stages, scripts) with Start Game Enabled off and their player-visible text removed; story-manager overrides gain a first condition `GetGlobalValue ARG_VanillaStoryManager == 1` (the global is 0), so nothing under the node starts. The why is in `tools/ArgoniaPlugin/shutdown.json` and `mods/allowed-quests.json`.

| Group | Kind | Change | Records (editor id, form id) |
|---|---|---|---|
| ours | global | new | ARG_MQ01_SavedDeesh `000E1A:Argonia.esp` |
| ours | global | new | ARG_BT_RaceHits `000816:Argonia.esp` |
| ours | global | new | ARG_MQ05_MindersHold `000DE3:Argonia.esp` |
| ours | global | new | ARG_BT_Global `000815:Argonia.esp` |
| ours | global | new | ARG_MQ04_Adopted `000DB2:Argonia.esp` |
| ours | global | new | ARG_HistHearing `000E7D:Argonia.esp` |
| ours | global | new | ARG_MQ03_NightTold `000E7A:Argonia.esp` |
| ours | global | new | ARG_VanillaStoryManager `000800:Argonia.esp` |
| ours | global | new | ARG_MQ03_ReedDeclined `000E7C:Argonia.esp` |
| ours | global | new | ARG_MQ01_SavedSal `000E19:Argonia.esp` |
| ours | global | new | ARG_MQ03_AttackTold `000E79:Argonia.esp` |
| ours | global | new | ARG_MQ04_LowReedStanding `000DB3:Argonia.esp` |
| ours | global | new | ARG_MQ01_Answered `000E18:Argonia.esp` |
| ours | global | new | ARG_MQ04_Reconciled `000DB1:Argonia.esp` |
| ours | global | new | ARG_BT_RaceRuns `000817:Argonia.esp` |
| ours | global | new | ARG_BC03_SeasonHeard `000D5F:Argonia.esp` |
| ours | global | new | ARG_MQ03_ReedSworn `000E7B:Argonia.esp` |
| ours | global | new | ARG_MQ01_RollRead `000E17:Argonia.esp` |
| ours | global | new | ARG_ChainbreakersStanding `000CDA:Argonia.esp` |
| ours | global | new | ARG_MQ05_NisswoRead `000DE4:Argonia.esp` |
| ours | Faction | new | ARG_MQ04_LowReedVillage `000DB4:Argonia.esp` |
| ours | Faction | new | ARG_UnboundRoot `000E15:Argonia.esp` |
| ours | Faction | new | ARG_VendorLooksAtBooks `000BC8:Argonia.esp` |
| ours | Faction | new | ARG_NightReedChapter `000C51:Argonia.esp` |
| ours | Faction | new | ARG_VeiledReed `000E73:Argonia.esp` |
| ours | Faction | new | ARG_BT_Faction `000818:Argonia.esp` |
| ours | MagicEffect | new | ARG_NoHealthRegenEffect `000C12:Argonia.esp` |
| ours | Spell | new | ARG_NoHealthRegen `000C13:Argonia.esp` |
| ours | Activator | new | ARG_MQ03_SpilledSap `000E77:Argonia.esp` |
| ours | Armor | new | ARG_TG01_JasperNecklace `000C5D:Argonia.esp` |
| ours | Armor | new | ARG_TG02_GlassBeads `000C5F:Argonia.esp` |
| ours | Armor | new | ARG_TG02_NeesakCharm `000C5E:Argonia.esp` |
| ours | Book | new | ARG_BC01_DebtBook `000CE1:Argonia.esp` |
| ours | Container | new | ARG_MQ03_FishTrap `000E76:Argonia.esp` |
| ours | Container | new | ARG_VendorLooksAtBooksChest `000BC9:Argonia.esp` |
| ours | Container | new | ARG_TG02_Lockbox `000C61:Argonia.esp` |
| ours | MiscItem | new | ARG_LQ25_BaitBucket `000C39:Argonia.esp` |
| ours | MiscItem | new | ARG_TG02_BoneFigurine `000C60:Argonia.esp` |
| ours | MiscItem | new | ARG_MQ03_SapPhial `000E74:Argonia.esp` |
| ours | MiscItem | new | ARG_BT_Token `000810:Argonia.esp` |
| ours | MiscItem | new | ARG_MQ03_CourierTag `000E75:Argonia.esp` |
| ours | MiscItem | new | ARG_BC03_Tokens `000D5E:Argonia.esp` |
| ours | MiscItem | new | ARG_MQ04_SapJars `000DA0:Argonia.esp` |
| ours | MiscItem | new | ARG_MQ04_GumPot `000D9F:Argonia.esp` |
| ours | Weapon | new | ARG_MQ01_SalReedKnife `000E16:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7267 `000BFD:Argonia.esp` |
| ours | Npc | new | ARG_Talker_084A86 `000BD3:Argonia.esp` |
| ours | Npc | new | ARG_Talker_084A87 `000BD4:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7269 `000BFF:Argonia.esp` |
| ours | Npc | new | ARG_LQ25_OkanZish `000C36:Argonia.esp` |
| ours | Npc | new | ARG_Talker_084A8F `000BD5:Argonia.esp` |
| ours | Npc | new | ARG_Talker_14153A `000C0A:Argonia.esp` |
| ours | Npc | new | ARG_Talker_015195 `000BA6:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934BC `000BE2:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_Tsanji `000E0D:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7266 `000BFC:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_DivesWithoutARope `000E08:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A204 `000BBD:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7253 `000BF0:Argonia.esp` |
| ours | Npc | new | ARG_TG_NeetaHaj `000C59:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_FindsTheOtherBankMarch `000E0B:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCF2 `000BB0:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7CD `000BD0:Argonia.esp` |
| ours | Npc | new | ARG_Talker_03E415 `000BC6:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5EB `000BDC:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_RootCutter `000E14:Argonia.esp` |
| ours | Npc | new | ARG_MQ04_RootHerald `000D8E:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCE0 `000BA9:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A1ED `000BBA:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7259 `000BF3:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934BF `000BE5:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C725F `000BF8:Argonia.esp` |
| ours | Npc | new | ARG_TG_ChapterLookout1 `000C57:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7263 `000BFA:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCEA `000BAD:Argonia.esp` |
| ours | Npc | new | ARG_TG_STabi `000C53:Argonia.esp` |
| ours | Npc | new | ARG_Talker_130773 `000C06:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5F0 `000BDE:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934BD `000BE3:Argonia.esp` |
| ours | Npc | new | ARG_Talker_1454F4 `000C0E:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7260 `000BF9:Argonia.esp` |
| ours | Npc | new | ARG_BC02_SaysItPlain `000D0D:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934C4 `000BEA:Argonia.esp` |
| ours | Npc | new | ARG_Talker_00FF4F `000BA0:Argonia.esp` |
| ours | Npc | new | ARG_LQ25_WuleenTaza `000C37:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5EA `000BDB:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7C8 `000BCB:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7CB `000BCE:Argonia.esp` |
| ours | Npc | new | ARG_LQ30_SeiWan `000C16:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7264 `000BFB:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01512B `000BA1:Argonia.esp` |
| ours | Npc | new | ARG_Talker_00FF4E `000B9F:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C725D `000BF6:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934C0 `000BE6:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5F1 `000BDF:Argonia.esp` |
| ours | Npc | new | ARG_MQ05_Wasp `000DD5:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_CutsTheOldKnot `000E13:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_WuleenSei `000E02:Argonia.esp` |
| ours | Npc | new | ARG_BC02_ThirdBornTsaxi `000D0B:Argonia.esp` |
| ours | Npc | new | ARG_Talker_084A91 `000BD7:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCFA `000BB3:Argonia.esp` |
| ours | Npc | new | ARG_Talker_03E413 `000BC5:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C72A7 `000C04:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01512E `000BA4:Argonia.esp` |
| ours | Npc | new | ARG_TG_ChapterLookout2 `000C58:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0616E8 `000BD1:Argonia.esp` |
| ours | Npc | new | ARG_MQ05_EiTuja `000DD4:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7CA `000BCD:Argonia.esp` |
| ours | Npc | new | ARG_MQ04_HidesHisWake `000D91:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCF0 `000BAF:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCF4 `000BB1:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C725E `000BF7:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCDE `000BA8:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_UxXeek `000E04:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934C1 `000BE7:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C72A4 `000C02:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7CC `000BCF:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_NeshNeel `000E0F:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934C2 `000BE8:Argonia.esp` |
| ours | Npc | new | ARG_Talker_084A85 `000BD2:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01512D `000BA3:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCE9 `000BAC:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A1F2 `000BBC:Argonia.esp` |
| ours | Npc | new | ARG_BC03_HeavyRope `000D5D:Argonia.esp` |
| ours | Npc | new | ARG_Talker_1454F3 `000C0D:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7252 `000BEF:Argonia.esp` |
| ours | Npc | new | ARG_MQ04_CountsTheJars `000D92:Argonia.esp` |
| ours | Npc | new | ARG_Talker_1454FC `000C10:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934C5 `000BEB:Argonia.esp` |
| ours | Npc | new | ARG_MQ03_ReedStranger `000E72:Argonia.esp` |
| ours | Npc | new | ARG_TG_DarZeel `000C5B:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A1F1 `000BBB:Argonia.esp` |
| ours | Npc | new | ARG_Talker_166BC1 `000C11:Argonia.esp` |
| ours | Npc | new | ARG_LQ30_HajWan `000C15:Argonia.esp` |
| ours | Npc | new | ARG_BC02_HidesInReeds `000D0E:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_DeeshDuun `000E11:Argonia.esp` |
| ours | Npc | new | ARG_MQ03_NeshDeeka `000E6F:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C724F `000BEC:Argonia.esp` |
| ours | Npc | new | ARG_MQ05_KaskaMeen `000DD3:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C725B `000BF5:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_DivesWithoutARopeMarch `000E09:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934BA `000BE0:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7255 `000BF1:Argonia.esp` |
| ours | Npc | new | ARG_Talker_037E04 `000BC4:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C72A6 `000C03:Argonia.esp` |
| ours | Npc | new | ARG_Talker_00AC8E `000B9E:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCD9 `000BA7:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_TiesTheLoosePlank `000E12:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7C9 `000BCC:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A205 `000BBE:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7251 `000BEE:Argonia.esp` |
| ours | Npc | new | ARG_Talker_084A90 `000BD6:Argonia.esp` |
| ours | Npc | new | ARG_BC_NeverSold `000CDB:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCF6 `000BB2:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_SalSei `000E10:Argonia.esp` |
| ours | Npc | new | ARG_LQ30_Viper `000C17:Argonia.esp` |
| ours | Npc | new | ARG_MQ03_SaltsTheCatch `000E70:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_MeeTuja `000E07:Argonia.esp` |
| ours | Npc | new | ARG_Talker_015193 `000BA5:Argonia.esp` |
| ours | Npc | new | ARG_MQ04_Leech `000D93:Argonia.esp` |
| ours | Npc | new | ARG_TG_OkanTei `000C5A:Argonia.esp` |
| ours | Npc | new | ARG_BT_Crab `000807:Argonia.esp` |
| ours | Npc | new | ARG_MQ04_TurnsTheClutch `000D90:Argonia.esp` |
| ours | Npc | new | ARG_BC02_KeepsTheOldCount `000D0F:Argonia.esp` |
| ours | Npc | new | ARG_MQ03_NeverWritesTwice `000E71:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_WuleenSeiMarch `000E03:Argonia.esp` |
| ours | Npc | new | ARG_TG_KeepsWhatFloats `000C54:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7250 `000BED:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5E9 `000BDA:Argonia.esp` |
| ours | Npc | new | ARG_TG_Tilts `000C52:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934C3 `000BE9:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C72A8 `000C05:Argonia.esp` |
| ours | Npc | new | ARG_Talker_130780 `000C07:Argonia.esp` |
| ours | Npc | new | ARG_LQ25_Crocodile `000C38:Argonia.esp` |
| ours | Npc | new | ARG_Talker_141539 `000C09:Argonia.esp` |
| ours | Npc | new | ARG_Talker_037E00 `000BC3:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C725A `000BF4:Argonia.esp` |
| ours | Npc | new | ARG_Talker_130789 `000C08:Argonia.esp` |
| ours | Npc | new | ARG_BC03_UssaRekh `000D5C:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7268 `000BFE:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCFE `000BB5:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A1E9 `000BB9:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7258 `000BF2:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A208 `000BC0:Argonia.esp` |
| ours | Npc | new | ARG_BC01_EstateMan `000CE0:Argonia.esp` |
| ours | Npc | new | ARG_Talker_1454F5 `000C0F:Argonia.esp` |
| ours | Npc | new | ARG_MQ04_GiantLeech `000D94:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_LlarviMaryon `000E0E:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C729E `000C00:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5E8 `000BD9:Argonia.esp` |
| ours | Npc | new | ARG_BC02_GateKeeper `000D0C:Argonia.esp` |
| ours | Npc | new | ARG_Talker_141561 `000C0B:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_FindsTheOtherBank `000E0A:Argonia.esp` |
| ours | Npc | new | ARG_MQ04_PaysLate `000D8F:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CD04 `000BB7:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5EC `000BDD:Argonia.esp` |
| ours | Npc | new | ARG_Talker_1454F2 `000C0C:Argonia.esp` |
| ours | Npc | new | ARG_BT_Walker `000806:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A206 `000BBF:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01512C `000BA2:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934BE `000BE4:Argonia.esp` |
| ours | Npc | new | ARG_BC01_HulmTei `000CDF:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCE2 `000BAA:Argonia.esp` |
| ours | Npc | new | ARG_TG_SitsByTheWater `000C55:Argonia.esp` |
| ours | Npc | new | ARG_BT_Keeper `000805:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CD0A `000BB8:Argonia.esp` |
| ours | Npc | new | ARG_Talker_037DFE `000BC2:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCEE `000BAE:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCE5 `000BAB:Argonia.esp` |
| ours | Npc | new | ARG_TG_BentSpine `000C56:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCFC `000BB4:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5E3 `000BD8:Argonia.esp` |
| ours | Npc | new | ARG_BC01_RowsForAnother `000CDE:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934BB `000BE1:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A209 `000BC1:Argonia.esp` |
| ours | Npc | new | ARG_Talker_03E418 `000BC7:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_BuysTheMonths `000E06:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CD01 `000BB6:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_RiSakka `000E0C:Argonia.esp` |
| ours | Npc | new | ARG_MQ01_UxXeekMarch `000E05:Argonia.esp` |
| ours | Npc | new | ARG_TG_RipperEel `000C5C:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C72A3 `000C01:Argonia.esp` |
| ours | Key | new | ARG_BT_Key `000812:Argonia.esp` |
| ours | Key | new | ARG_MQ03_HouseKey `000E78:Argonia.esp` |
| ours | PlacedNpc | new | ARG_BT_WalkerRef `00080B:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ05_ShipDoorA `000DDF:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ05_ShipDoorB `000DE0:Argonia.esp` |
| ours | PlacedNpc | new | ARG_TG_BentSpineRef `000C68:Argonia.esp` |
| ours | PlacedNpc | new | ARG_TG_ChapterLookout1Ref `000C69:Argonia.esp` |
| ours | PlacedNpc | new | ARG_TG_ChapterLookout2Ref `000C6A:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ05_Seat `000DE1:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ05_Broom `000DE2:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_StartMarker `000E1B:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_HoldParent `000E1C:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_CrewParent `000E1D:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_WuleenSeiRef `000E1E:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_UxXeekRef `000E1F:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_DivesWithoutARopeHoldRef `000E20:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_FindsTheOtherBankHoldRef `000E21:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_RiSakkaHoldRef `000E22:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_TsanjiHoldRef `000E23:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_LlarviMaryonHoldRef `000E24:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_DreamParent `000E8F:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_DreamMarker `000E90:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_DreamRoot1 `000E91:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_DreamRoot2 `000E92:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_DreamRoot3 `000E93:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_DreamRoot4 `000E94:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_DreamRoot5 `000E95:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_DreamRoot6 `000E96:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_ZoneDoor `000E97:Argonia.esp` |
| ours | PlacedNpc | new | ARG_TG_TiltsRef `000C64:Argonia.esp` |
| ours | PlacedNpc | new | ARG_NeshDeekaRef `000E89:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ03_SaltsTheCatchRef `000E8A:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_HouseMarker `000E8B:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_MatMarker `000E8C:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_Mat1 `000E8D:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_Mat2 `000E8E:Argonia.esp` |
| ours | PlacedNpc | new | ARG_BC_NeverSoldRef `000CDC:Argonia.esp` |
| ours | XMarker reference | new | ARG_LQ30_ViperParent `000C18:Argonia.esp` |
| ours | PlacedNpc | new | ARG_LQ30_HajWanRef `000C19:Argonia.esp` |
| ours | PlacedNpc | new | ARG_LQ30_SeiWanRef `000C1A:Argonia.esp` |
| ours | PlacedNpc | new | ARG_LQ30_ViperRef `000C1B:Argonia.esp` |
| ours | XMarker reference | new | ARG_LQ30_GateMarker `000C1C:Argonia.esp` |
| ours | XMarker reference | new | ARG_LQ30_GateZone `000C1D:Argonia.esp` |
| ours | XMarker reference | new | ARG_LQ25_CrocParent `000C3A:Argonia.esp` |
| ours | PlacedNpc | new | ARG_LQ25_CrocodileRef `000C3B:Argonia.esp` |
| ours | XMarker reference | new | ARG_LQ25_BaitBucketRef `000C3C:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ05_KaskaPost `000DD6:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ05_EiTujaPost `000DD7:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ05_YoungHist `000DD8:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ05_ZoneGrove `000DD9:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ05_KaskaMeenRef `000DDA:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ05_EiTujaRef `000DDB:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ05_WayParent `000DDC:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ05_Wasp1 `000DDD:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ05_Wasp2 `000DDE:Argonia.esp` |
| ours | XMarker reference | new | ARG_OpeningMarker `000802:Argonia.esp` |
| ours | XMarker reference | new | ARG_BT_TokenParent `000808:Argonia.esp` |
| ours | XMarker reference | new | ARG_BT_CrabParent `000809:Argonia.esp` |
| ours | PlacedNpc | new | ARG_BT_KeeperRef `00080A:Argonia.esp` |
| ours | PlacedNpc | new | ARG_BT_CrabRef `00080C:Argonia.esp` |
| ours | XMarker reference | new | ARG_BT_StartMarker `00080D:Argonia.esp` |
| ours | XMarker reference | new | ARG_BT_WalkerMarker `00080E:Argonia.esp` |
| ours | XMarker reference | new | ARG_BT_DoorMarker `00080F:Argonia.esp` |
| ours | XMarker reference | new | ARG_BT_TokenRef `000811:Argonia.esp` |
| ours | XMarker reference | new | ARG_BT_ZoneA `000813:Argonia.esp` |
| ours | XMarker reference | new | ARG_BT_ZoneB `000814:Argonia.esp` |
| ours | XMarker reference | new | ARG_VendorLooksAtBooksChestRef `000BCA:Argonia.esp` |
| ours | XMarker reference | new | ARG_TG01_Parent `000C62:Argonia.esp` |
| ours | XMarker reference | new | ARG_TG02_Parent `000C63:Argonia.esp` |
| ours | PlacedNpc | new | ARG_TG_STabiRef `000C65:Argonia.esp` |
| ours | PlacedNpc | new | ARG_TG_KeepsWhatFloatsRef `000C66:Argonia.esp` |
| ours | PlacedNpc | new | ARG_TG_SitsByTheWaterRef `000C67:Argonia.esp` |
| ours | PlacedNpc | new | ARG_TG_NeetaHajRef `000C6B:Argonia.esp` |
| ours | PlacedNpc | new | ARG_TG_OkanTeiRef `000C6C:Argonia.esp` |
| ours | PlacedNpc | new | ARG_TG_DarZeelRef `000C6D:Argonia.esp` |
| ours | XMarker reference | new | ARG_TG01_DayMarker `000C6E:Argonia.esp` |
| ours | XMarker reference | new | ARG_TG01_DrinkMarker `000C6F:Argonia.esp` |
| ours | XMarker reference | new | ARG_TG01_SleepMarker `000C70:Argonia.esp` |
| ours | XMarker reference | new | ARG_TG01_Bedroll `000C71:Argonia.esp` |
| ours | XMarker reference | new | ARG_TG01_ZoneBed `000C72:Argonia.esp` |
| ours | XMarker reference | new | ARG_TG02_LockboxRef `000C73:Argonia.esp` |
| ours | XMarker reference | new | ARG_TG02_FallenHouse `000C74:Argonia.esp` |
| ours | PlacedNpc | new | ARG_TG02_Eel1 `000C75:Argonia.esp` |
| ours | PlacedNpc | new | ARG_TG02_Eel2 `000C76:Argonia.esp` |
| ours | XMarker reference | new | ARG_BC01_ChestRef `000CE2:Argonia.esp` |
| ours | PlacedNpc | new | ARG_BC01_RowsForAnotherRef `000CE3:Argonia.esp` |
| ours | PlacedNpc | new | ARG_BC01_HulmTeiRef `000CE4:Argonia.esp` |
| ours | PlacedNpc | new | ARG_BC01_EstateMan1Ref `000CE5:Argonia.esp` |
| ours | PlacedNpc | new | ARG_BC01_EstateMan2Ref `000CE6:Argonia.esp` |
| ours | XMarker reference | new | ARG_BC01_LandingMarker `000CE7:Argonia.esp` |
| ours | XMarker reference | new | ARG_BC01_BlackroseMarker `000CE8:Argonia.esp` |
| ours | XMarker reference | new | ARG_BC01_ChannelEndZone `000CE9:Argonia.esp` |
| ours | XMarker reference | new | ARG_BC02_SmokeParent `000D10:Argonia.esp` |
| ours | XMarker reference | new | ARG_BC02_Smoke1 `000D11:Argonia.esp` |
| ours | XMarker reference | new | ARG_BC02_Smoke2 `000D12:Argonia.esp` |
| ours | XMarker reference | new | ARG_BC02_Smoke3 `000D13:Argonia.esp` |
| ours | XMarker reference | new | ARG_BC02_Smoke4 `000D14:Argonia.esp` |
| ours | XMarker reference | new | ARG_BC02_SpeakerParent `000D15:Argonia.esp` |
| ours | XMarker reference | new | ARG_BC02_KillerParent `000D16:Argonia.esp` |
| ours | XMarker reference | new | ARG_BC02_MotherParent `000D17:Argonia.esp` |
| ours | PlacedNpc | new | ARG_BC02_SpeakerRef `000D18:Argonia.esp` |
| ours | PlacedNpc | new | ARG_BC02_KillerRef `000D19:Argonia.esp` |
| ours | PlacedNpc | new | ARG_BC02_MotherRef `000D1A:Argonia.esp` |
| ours | PlacedNpc | new | ARG_BC02_TsaxiRef `000D1B:Argonia.esp` |
| ours | PlacedNpc | new | ARG_BC02_GateKeeperRef `000D1C:Argonia.esp` |
| ours | XMarker reference | new | ARG_BC02_InZone `000D1D:Argonia.esp` |
| ours | XMarker reference | new | ARG_BC02_OutSpeakerZone `000D1E:Argonia.esp` |
| ours | XMarker reference | new | ARG_BC02_OutKillerZone `000D1F:Argonia.esp` |
| ours | XMarker reference | new | ARG_BC02_OutMotherZone `000D20:Argonia.esp` |
| ours | PlacedNpc | new | ARG_BC03_UssaRekhRef `000D60:Argonia.esp` |
| ours | PlacedNpc | new | ARG_BC03_HeavyRopeRef `000D61:Argonia.esp` |
| ours | XMarker reference | new | ARG_BC03_ChestRef `000D62:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ04_CampParent `000D95:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ04_WithdrawnParent `000D96:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ04_ReconciledParent `000D97:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ04_CutRootMark `000D98:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ04_ReturnLeechesParent `000D99:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ04_HistWithdrawn `000D9A:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ04_HistReconciled `000D9B:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ04_CampFire `000D9C:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ04_CampTent `000D9D:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ04_CampBoat `000D9E:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ04_SapJarsRef `000DA1:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ04_RootHeraldRef `000DA2:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ04_PaysLateRef `000DA3:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ04_TurnsTheClutchRef `000DA4:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ04_HidesHisWakeRef `000DA5:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ04_CountsTheJarsRef `000DA6:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ04_LeechRoot1 `000DA7:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ04_LeechRoot2 `000DA8:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ04_LeechWater1 `000DA9:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ04_LeechWater2 `000DAA:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ04_LeechWater3 `000DAB:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ04_LeechBack1 `000DAC:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ04_LeechBack2 `000DAD:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ04_LeechBack3 `000DAE:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ04_ZoneRoot30 `000DAF:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ04_ZoneRoot91 `000DB0:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ04_SaltPile1 `000DD1:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ04_SaltPile2 `000DD2:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_BrokerParent `000E25:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_MarchParent `000E26:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_BuysTheMonthsRef `000E27:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_MeeTujaRef `000E28:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_WuleenSeiMarchRef `000E29:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_UxXeekMarchRef `000E2A:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_DivesWithoutARopeMarchRef `000E2B:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_FindsTheOtherBankMarchRef `000E2C:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_CampOrderly `000E2D:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_CampAttacked `000E2E:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_CampAftermath `000E2F:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_CellParent `000E30:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_SurvivorsParent `000E31:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_Shore93Parent `000E32:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_FireMarker `000E33:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_ShedMarker `000E34:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_HutsMarker `000E35:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_ShoreMarker `000E36:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_WaterEdgeMarker `000E37:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_SalSeiRef `000E38:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_DeeshDuunRef `000E39:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_NeshNeelRef `000E3A:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_CutsTheOldKnotRef `000E3B:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_RootCutter1Ref `000E3C:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_RootCutter2Ref `000E3D:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_TiesTheLoosePlankRef `000E3E:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_RiSakkaShoreRef `000E3F:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_TsanjiShoreRef `000E40:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ01_LlarviMaryonShoreRef `000E41:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_Campfire `000E42:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_Shed `000E43:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_Cutting `000E44:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_Hut1 `000E45:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_Hut2 `000E46:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_HutBurnt `000E47:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_Planks `000E48:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_HutFire1 `000E49:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_HutFire2 `000E4A:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_Egg9 `000E4B:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_Egg10 `000E4C:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_Egg11 `000E4D:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_ZoneFire `000E4E:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_ZoneShed `000E4F:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_ZoneHuts `000E50:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_ZoneShore90 `000E51:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_ZoneShore91 `000E52:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ01_ZoneShore93 `000E53:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_JarParent `000E7E:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_ReedParent `000E7F:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_SpilledSapRef `000E80:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_FishTrapRef `000E81:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_Lockpick1 `000E82:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_Lockpick2 `000E83:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_Lockpick3 `000E84:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_Lockpick4 `000E85:Argonia.esp` |
| ours | XMarker reference | new | ARG_MQ03_Lockpick5 `000E86:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ03_NeverWritesTwiceRef `000E87:Argonia.esp` |
| ours | PlacedNpc | new | ARG_MQ03_ReedStrangerRef `000E88:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ25_TheBeast `000C3E:Argonia.esp` |
| ours | DialogResponses | new |  `000C43:Argonia.esp` |
| ours | DialogResponses | new |  `000C40:Argonia.esp` |
| ours | DialogResponses | new |  `000C42:Argonia.esp` |
| ours | DialogResponses | new |  `000C44:Argonia.esp` |
| ours | DialogResponses | new |  `000C41:Argonia.esp` |
| ours | DialogResponses | new |  `000C3F:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_Brawl `000D76:Argonia.esp` |
| ours | DialogResponses | new |  `000D77:Argonia.esp` |
| ours | DialogResponses | new |  `000D79:Argonia.esp` |
| ours | DialogResponses | new |  `000D78:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ05_WatchTopic `000DF5:Argonia.esp` |
| ours | DialogResponses | new |  `000DF1:Argonia.esp` |
| ours | DialogResponses | new |  `000DF2:Argonia.esp` |
| ours | DialogResponses | new |  `000DF3:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_CutLoose `000CFA:Argonia.esp` |
| ours | DialogResponses | new |  `000CFE:Argonia.esp` |
| ours | DialogResponses | new |  `000CFB:Argonia.esp` |
| ours | DialogResponses | new |  `000CFF:Argonia.esp` |
| ours | DialogResponses | new |  `000CFD:Argonia.esp` |
| ours | DialogResponses | new |  `000D00:Argonia.esp` |
| ours | DialogResponses | new |  `000CFC:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_TopicSellFigurine `000CCC:Argonia.esp` |
| ours | DialogResponses | new |  `000CCD:Argonia.esp` |
| ours | DialogResponses | new |  `000CCF:Argonia.esp` |
| ours | DialogResponses | new |  `000CCE:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_TheBoat `000E99:Argonia.esp` |
| ours | DialogResponses | new |  `000E9F:Argonia.esp` |
| ours | DialogResponses | new |  `000E9B:Argonia.esp` |
| ours | DialogResponses | new |  `000E9E:Argonia.esp` |
| ours | DialogResponses | new |  `000E9C:Argonia.esp` |
| ours | DialogResponses | new |  `000E9D:Argonia.esp` |
| ours | DialogResponses | new |  `000E9A:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_AfterHello `000D51:Argonia.esp` |
| ours | DialogResponses | new |  `000D58:Argonia.esp` |
| ours | DialogResponses | new |  `000D54:Argonia.esp` |
| ours | DialogResponses | new |  `000D56:Argonia.esp` |
| ours | DialogResponses | new |  `000D57:Argonia.esp` |
| ours | DialogResponses | new |  `000D52:Argonia.esp` |
| ours | DialogResponses | new |  `000D5A:Argonia.esp` |
| ours | DialogResponses | new |  `000D55:Argonia.esp` |
| ours | DialogResponses | new |  `000D59:Argonia.esp` |
| ours | DialogResponses | new |  `000D53:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_TheWater `000E6A:Argonia.esp` |
| ours | DialogResponses | new |  `000E6B:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ05_TellNisswoTopic `000DFF:Argonia.esp` |
| ours | DialogResponses | new |  `000DFB:Argonia.esp` |
| ours | DialogResponses | new |  `000DFD:Argonia.esp` |
| ours | DialogResponses | new |  `000DFC:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ30_AfterHello `000C30:Argonia.esp` |
| ours | DialogResponses | new |  `000C33:Argonia.esp` |
| ours | DialogResponses | new |  `000C34:Argonia.esp` |
| ours | DialogResponses | new |  `000C31:Argonia.esp` |
| ours | DialogResponses | new |  `000C32:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_TheSeason `000D6C:Argonia.esp` |
| ours | DialogResponses | new |  `000D6F:Argonia.esp` |
| ours | DialogResponses | new |  `000D6D:Argonia.esp` |
| ours | DialogResponses | new |  `000D6E:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Harvest `00099A:Argonia.esp` |
| ours | DialogResponses | new |  `00099D:Argonia.esp` |
| ours | DialogResponses | new |  `0009A1:Argonia.esp` |
| ours | DialogResponses | new |  `00099E:Argonia.esp` |
| ours | DialogResponses | new |  `0009A4:Argonia.esp` |
| ours | DialogResponses | new |  `0009A9:Argonia.esp` |
| ours | DialogResponses | new |  `0009AA:Argonia.esp` |
| ours | DialogResponses | new |  `00099B:Argonia.esp` |
| ours | DialogResponses | new |  `0009A2:Argonia.esp` |
| ours | DialogResponses | new |  `0009A7:Argonia.esp` |
| ours | DialogResponses | new |  `0009A6:Argonia.esp` |
| ours | DialogResponses | new |  `0009A0:Argonia.esp` |
| ours | DialogResponses | new |  `0009A5:Argonia.esp` |
| ours | DialogResponses | new |  `0009AB:Argonia.esp` |
| ours | DialogResponses | new |  `0009A3:Argonia.esp` |
| ours | DialogResponses | new |  `0009A8:Argonia.esp` |
| ours | DialogResponses | new |  `00099C:Argonia.esp` |
| ours | DialogResponses | new |  `00099F:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ05_QuarrelTopic `000DF0:Argonia.esp` |
| ours | DialogResponses | new |  `000DEC:Argonia.esp` |
| ours | DialogResponses | new |  `000DED:Argonia.esp` |
| ours | DialogResponses | new |  `000DEE:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_TopicHandOverDar `000CC7:Argonia.esp` |
| ours | DialogResponses | new |  `000CCA:Argonia.esp` |
| ours | DialogResponses | new |  `000CC8:Argonia.esp` |
| ours | DialogResponses | new |  `000CC9:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_TakeOath `000EB9:Argonia.esp` |
| ours | DialogResponses | new |  `000EBB:Argonia.esp` |
| ours | DialogResponses | new |  `000EBC:Argonia.esp` |
| ours | DialogResponses | new |  `000EBA:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_TheEstate `000CED:Argonia.esp` |
| ours | DialogResponses | new |  `000CF0:Argonia.esp` |
| ours | DialogResponses | new |  `000CF2:Argonia.esp` |
| ours | DialogResponses | new |  `000CEF:Argonia.esp` |
| ours | DialogResponses | new |  `000CEE:Argonia.esp` |
| ours | DialogResponses | new |  `000CF1:Argonia.esp` |
| ours | DialogResponses | new |  `000CF3:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG01_TopicReturn `000C96:Argonia.esp` |
| ours | DialogResponses | new |  `000C9A:Argonia.esp` |
| ours | DialogResponses | new |  `000C9B:Argonia.esp` |
| ours | DialogResponses | new |  `000C98:Argonia.esp` |
| ours | DialogResponses | new |  `000C9C:Argonia.esp` |
| ours | DialogResponses | new |  `000C99:Argonia.esp` |
| ours | DialogResponses | new |  `000C97:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ30_ComeBack `000C2C:Argonia.esp` |
| ours | DialogResponses | new |  `000C2D:Argonia.esp` |
| ours | DialogResponses | new |  `000C2F:Argonia.esp` |
| ours | DialogResponses | new |  `000C2E:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Danger `000932:Argonia.esp` |
| ours | DialogResponses | new |  `000937:Argonia.esp` |
| ours | DialogResponses | new |  `000933:Argonia.esp` |
| ours | DialogResponses | new |  `000936:Argonia.esp` |
| ours | DialogResponses | new |  `00093A:Argonia.esp` |
| ours | DialogResponses | new |  `000935:Argonia.esp` |
| ours | DialogResponses | new |  `000938:Argonia.esp` |
| ours | DialogResponses | new |  `000934:Argonia.esp` |
| ours | DialogResponses | new |  `000939:Argonia.esp` |
| ours | DialogResponses | new |  `00093B:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Topic40 `000828:Argonia.esp` |
| ours | DialogResponses | new |  `000826:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG01_TopicTest `000C81:Argonia.esp` |
| ours | DialogResponses | new |  `000C82:Argonia.esp` |
| ours | DialogResponses | new |  `000C83:Argonia.esp` |
| ours | DialogResponses | new |  `000C84:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_AnswerSilent `000E60:Argonia.esp` |
| ours | DialogResponses | new |  `000E61:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_TopicClaimFigurine `000CAB:Argonia.esp` |
| ours | DialogResponses | new |  `000CAD:Argonia.esp` |
| ours | DialogResponses | new |  `000CAE:Argonia.esp` |
| ours | DialogResponses | new |  `000CAC:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_ComeSpeaker `000D35:Argonia.esp` |
| ours | DialogResponses | new |  `000D38:Argonia.esp` |
| ours | DialogResponses | new |  `000D37:Argonia.esp` |
| ours | DialogResponses | new |  `000D36:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_ComeMother `000D3F:Argonia.esp` |
| ours | DialogResponses | new |  `000D42:Argonia.esp` |
| ours | DialogResponses | new |  `000D40:Argonia.esp` |
| ours | DialogResponses | new |  `000D41:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_TopicSellBeads `000CD6:Argonia.esp` |
| ours | DialogResponses | new |  `000CD7:Argonia.esp` |
| ours | DialogResponses | new |  `000CD8:Argonia.esp` |
| ours | DialogResponses | new |  `000CD9:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ25_KeepQuiet `000C4B:Argonia.esp` |
| ours | DialogResponses | new |  `000C4C:Argonia.esp` |
| ours | DialogResponses | new |  `000C4E:Argonia.esp` |
| ours | DialogResponses | new |  `000C4D:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_TheFire `000D25:Argonia.esp` |
| ours | DialogResponses | new |  `000D28:Argonia.esp` |
| ours | DialogResponses | new |  `000D2B:Argonia.esp` |
| ours | DialogResponses | new |  `000D26:Argonia.esp` |
| ours | DialogResponses | new |  `000D2A:Argonia.esp` |
| ours | DialogResponses | new |  `000D29:Argonia.esp` |
| ours | DialogResponses | new |  `000D27:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Scene1 `00081A:Argonia.esp` |
| ours | DialogResponses | new |  `00081B:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_TheAttack `000EA1:Argonia.esp` |
| ours | DialogResponses | new |  `000EA5:Argonia.esp` |
| ours | DialogResponses | new |  `000EA4:Argonia.esp` |
| ours | DialogResponses | new |  `000EA3:Argonia.esp` |
| ours | DialogResponses | new |  `000EA7:Argonia.esp` |
| ours | DialogResponses | new |  `000EA6:Argonia.esp` |
| ours | DialogResponses | new |  `000EA2:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Topic50Never `00082E:Argonia.esp` |
| ours | DialogResponses | new |  `00082C:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_AnswerDefy `000E63:Argonia.esp` |
| ours | DialogResponses | new |  `000E64:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ25_TellCaptain `000C46:Argonia.esp` |
| ours | DialogResponses | new |  `000C47:Argonia.esp` |
| ours | DialogResponses | new |  `000C48:Argonia.esp` |
| ours | DialogResponses | new |  `000C49:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_BringDown `000D02:Argonia.esp` |
| ours | DialogResponses | new |  `000D03:Argonia.esp` |
| ours | DialogResponses | new |  `000D05:Argonia.esp` |
| ours | DialogResponses | new |  `000D04:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ04_CutTopic `000DD0:Argonia.esp` |
| ours | DialogResponses | new |  `000DCC:Argonia.esp` |
| ours | DialogResponses | new |  `000DCE:Argonia.esp` |
| ours | DialogResponses | new |  `000DCB:Argonia.esp` |
| ours | DialogResponses | new |  `000DC9:Argonia.esp` |
| ours | DialogResponses | new |  `000DCD:Argonia.esp` |
| ours | DialogResponses | new |  `000DCA:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Scene4 `000820:Argonia.esp` |
| ours | DialogResponses | new |  `000821:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_RefuseOath `000EBE:Argonia.esp` |
| ours | DialogResponses | new |  `000EC1:Argonia.esp` |
| ours | DialogResponses | new |  `000EC0:Argonia.esp` |
| ours | DialogResponses | new |  `000EBF:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Secret `000A86:Argonia.esp` |
| ours | DialogResponses | new |  `000A8C:Argonia.esp` |
| ours | DialogResponses | new |  `000A8E:Argonia.esp` |
| ours | DialogResponses | new |  `000A87:Argonia.esp` |
| ours | DialogResponses | new |  `000A8D:Argonia.esp` |
| ours | DialogResponses | new |  `000A88:Argonia.esp` |
| ours | DialogResponses | new |  `000A8B:Argonia.esp` |
| ours | DialogResponses | new |  `000A89:Argonia.esp` |
| ours | DialogResponses | new |  `000A8A:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_AfterHello `000D06:Argonia.esp` |
| ours | DialogResponses | new |  `000D08:Argonia.esp` |
| ours | DialogResponses | new |  `000D07:Argonia.esp` |
| ours | DialogResponses | new |  `000D09:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ04_VillageTopic `000DC0:Argonia.esp` |
| ours | DialogResponses | new |  `000DBA:Argonia.esp` |
| ours | DialogResponses | new |  `000DB8:Argonia.esp` |
| ours | DialogResponses | new |  `000DBD:Argonia.esp` |
| ours | DialogResponses | new |  `000DBC:Argonia.esp` |
| ours | DialogResponses | new |  `000DB9:Argonia.esp` |
| ours | DialogResponses | new |  `000DBE:Argonia.esp` |
| ours | DialogResponses | new |  `000DB7:Argonia.esp` |
| ours | DialogResponses | new |  `000DB6:Argonia.esp` |
| ours | DialogResponses | new |  `000DBB:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Rumours `000A7B:Argonia.esp` |
| ours | DialogResponses | new |  `000A82:Argonia.esp` |
| ours | DialogResponses | new |  `000A84:Argonia.esp` |
| ours | DialogResponses | new |  `000ED0:Argonia.esp` |
| ours | DialogResponses | new |  `000A81:Argonia.esp` |
| ours | DialogResponses | new |  `000A7D:Argonia.esp` |
| ours | DialogResponses | new |  `000ECF:Argonia.esp` |
| ours | DialogResponses | new |  `000ED7:Argonia.esp` |
| ours | DialogResponses | new |  `000A7E:Argonia.esp` |
| ours | DialogResponses | new |  `000A83:Argonia.esp` |
| ours | DialogResponses | new |  `000ED1:Argonia.esp` |
| ours | DialogResponses | new |  `000ECE:Argonia.esp` |
| ours | DialogResponses | new |  `000A7F:Argonia.esp` |
| ours | DialogResponses | new |  `000A7C:Argonia.esp` |
| ours | DialogResponses | new |  `000A80:Argonia.esp` |
| ours | DialogResponses | new |  `000ED4:Argonia.esp` |
| ours | DialogResponses | new |  `000ED3:Argonia.esp` |
| ours | DialogResponses | new |  `000ED9:Argonia.esp` |
| ours | DialogResponses | new |  `000ECD:Argonia.esp` |
| ours | DialogResponses | new |  `000ED5:Argonia.esp` |
| ours | DialogResponses | new |  `000ED2:Argonia.esp` |
| ours | DialogResponses | new |  `000ED6:Argonia.esp` |
| ours | DialogResponses | new |  `000ED8:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ30_WalkedOut `000C1F:Argonia.esp` |
| ours | DialogResponses | new |  `000C25:Argonia.esp` |
| ours | DialogResponses | new |  `000C23:Argonia.esp` |
| ours | DialogResponses | new |  `000C22:Argonia.esp` |
| ours | DialogResponses | new |  `000C21:Argonia.esp` |
| ours | DialogResponses | new |  `000C20:Argonia.esp` |
| ours | DialogResponses | new |  `000C24:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Services `000B09:Argonia.esp` |
| ours | DialogResponses | new |  `000B0F:Argonia.esp` |
| ours | DialogResponses | new |  `000B0D:Argonia.esp` |
| ours | DialogResponses | new |  `000B0E:Argonia.esp` |
| ours | DialogResponses | new |  `000B0A:Argonia.esp` |
| ours | DialogResponses | new |  `000B0B:Argonia.esp` |
| ours | DialogResponses | new |  `000B0C:Argonia.esp` |
| ours | DialogResponses | new |  `000B10:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_TheHire `000E66:Argonia.esp` |
| ours | DialogResponses | new |  `000E67:Argonia.esp` |
| ours | DialogResponses | new |  `000E68:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG01_TopicGiveBack `000C8E:Argonia.esp` |
| ours | DialogResponses | new |  `000C8F:Argonia.esp` |
| ours | DialogResponses | new |  `000C92:Argonia.esp` |
| ours | DialogResponses | new |  `000C94:Argonia.esp` |
| ours | DialogResponses | new |  `000C90:Argonia.esp` |
| ours | DialogResponses | new |  `000C93:Argonia.esp` |
| ours | DialogResponses | new |  `000C91:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ05_TellMinderTopic `000DFA:Argonia.esp` |
| ours | DialogResponses | new |  `000DF8:Argonia.esp` |
| ours | DialogResponses | new |  `000DF6:Argonia.esp` |
| ours | DialogResponses | new |  `000DF7:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Directions `00093D:Argonia.esp` |
| ours | DialogResponses | new |  `00094A:Argonia.esp` |
| ours | DialogResponses | new |  `000970:Argonia.esp` |
| ours | DialogResponses | new |  `000984:Argonia.esp` |
| ours | DialogResponses | new |  `000992:Argonia.esp` |
| ours | DialogResponses | new |  `000962:Argonia.esp` |
| ours | DialogResponses | new |  `00095A:Argonia.esp` |
| ours | DialogResponses | new |  `00096D:Argonia.esp` |
| ours | DialogResponses | new |  `000977:Argonia.esp` |
| ours | DialogResponses | new |  `00097F:Argonia.esp` |
| ours | DialogResponses | new |  `00094F:Argonia.esp` |
| ours | DialogResponses | new |  `000978:Argonia.esp` |
| ours | DialogResponses | new |  `000973:Argonia.esp` |
| ours | DialogResponses | new |  `000946:Argonia.esp` |
| ours | DialogResponses | new |  `000967:Argonia.esp` |
| ours | DialogResponses | new |  `00098B:Argonia.esp` |
| ours | DialogResponses | new |  `00098A:Argonia.esp` |
| ours | DialogResponses | new |  `000994:Argonia.esp` |
| ours | DialogResponses | new |  `00097B:Argonia.esp` |
| ours | DialogResponses | new |  `000942:Argonia.esp` |
| ours | DialogResponses | new |  `000952:Argonia.esp` |
| ours | DialogResponses | new |  `000989:Argonia.esp` |
| ours | DialogResponses | new |  `000940:Argonia.esp` |
| ours | DialogResponses | new |  `00094D:Argonia.esp` |
| ours | DialogResponses | new |  `000979:Argonia.esp` |
| ours | DialogResponses | new |  `000961:Argonia.esp` |
| ours | DialogResponses | new |  `00093E:Argonia.esp` |
| ours | DialogResponses | new |  `000955:Argonia.esp` |
| ours | DialogResponses | new |  `00095E:Argonia.esp` |
| ours | DialogResponses | new |  `000996:Argonia.esp` |
| ours | DialogResponses | new |  `00096E:Argonia.esp` |
| ours | DialogResponses | new |  `000944:Argonia.esp` |
| ours | DialogResponses | new |  `000953:Argonia.esp` |
| ours | DialogResponses | new |  `00097D:Argonia.esp` |
| ours | DialogResponses | new |  `000987:Argonia.esp` |
| ours | DialogResponses | new |  `00098F:Argonia.esp` |
| ours | DialogResponses | new |  `000954:Argonia.esp` |
| ours | DialogResponses | new |  `000974:Argonia.esp` |
| ours | DialogResponses | new |  `000998:Argonia.esp` |
| ours | DialogResponses | new |  `000947:Argonia.esp` |
| ours | DialogResponses | new |  `000943:Argonia.esp` |
| ours | DialogResponses | new |  `000995:Argonia.esp` |
| ours | DialogResponses | new |  `000968:Argonia.esp` |
| ours | DialogResponses | new |  `000981:Argonia.esp` |
| ours | DialogResponses | new |  `00095F:Argonia.esp` |
| ours | DialogResponses | new |  `000993:Argonia.esp` |
| ours | DialogResponses | new |  `000945:Argonia.esp` |
| ours | DialogResponses | new |  `000986:Argonia.esp` |
| ours | DialogResponses | new |  `000966:Argonia.esp` |
| ours | DialogResponses | new |  `000985:Argonia.esp` |
| ours | DialogResponses | new |  `00095D:Argonia.esp` |
| ours | DialogResponses | new |  `00096C:Argonia.esp` |
| ours | DialogResponses | new |  `00097A:Argonia.esp` |
| ours | DialogResponses | new |  `000951:Argonia.esp` |
| ours | DialogResponses | new |  `000971:Argonia.esp` |
| ours | DialogResponses | new |  `000969:Argonia.esp` |
| ours | DialogResponses | new |  `000964:Argonia.esp` |
| ours | DialogResponses | new |  `00097C:Argonia.esp` |
| ours | DialogResponses | new |  `000980:Argonia.esp` |
| ours | DialogResponses | new |  `000988:Argonia.esp` |
| ours | DialogResponses | new |  `000957:Argonia.esp` |
| ours | DialogResponses | new |  `000959:Argonia.esp` |
| ours | DialogResponses | new |  `000960:Argonia.esp` |
| ours | DialogResponses | new |  `00097E:Argonia.esp` |
| ours | DialogResponses | new |  `000976:Argonia.esp` |
| ours | DialogResponses | new |  `00098D:Argonia.esp` |
| ours | DialogResponses | new |  `000982:Argonia.esp` |
| ours | DialogResponses | new |  `000958:Argonia.esp` |
| ours | DialogResponses | new |  `000990:Argonia.esp` |
| ours | DialogResponses | new |  `00093F:Argonia.esp` |
| ours | DialogResponses | new |  `00095C:Argonia.esp` |
| ours | DialogResponses | new |  `000983:Argonia.esp` |
| ours | DialogResponses | new |  `00094E:Argonia.esp` |
| ours | DialogResponses | new |  `00094C:Argonia.esp` |
| ours | DialogResponses | new |  `000991:Argonia.esp` |
| ours | DialogResponses | new |  `000950:Argonia.esp` |
| ours | DialogResponses | new |  `00094B:Argonia.esp` |
| ours | DialogResponses | new |  `000963:Argonia.esp` |
| ours | DialogResponses | new |  `00096F:Argonia.esp` |
| ours | DialogResponses | new |  `00096B:Argonia.esp` |
| ours | DialogResponses | new |  `00098E:Argonia.esp` |
| ours | DialogResponses | new |  `000965:Argonia.esp` |
| ours | DialogResponses | new |  `000941:Argonia.esp` |
| ours | DialogResponses | new |  `00095B:Argonia.esp` |
| ours | DialogResponses | new |  `000997:Argonia.esp` |
| ours | DialogResponses | new |  `00096A:Argonia.esp` |
| ours | DialogResponses | new |  `000949:Argonia.esp` |
| ours | DialogResponses | new |  `000948:Argonia.esp` |
| ours | DialogResponses | new |  `000972:Argonia.esp` |
| ours | DialogResponses | new |  `00098C:Argonia.esp` |
| ours | DialogResponses | new |  `000975:Argonia.esp` |
| ours | DialogResponses | new |  `000956:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_TheBook `000CF5:Argonia.esp` |
| ours | DialogResponses | new |  `000CF6:Argonia.esp` |
| ours | DialogResponses | new |  `000CF7:Argonia.esp` |
| ours | DialogResponses | new |  `000CF8:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_TopicJob `000CA6:Argonia.esp` |
| ours | DialogResponses | new |  `000CA9:Argonia.esp` |
| ours | DialogResponses | new |  `000CA7:Argonia.esp` |
| ours | DialogResponses | new |  `000CA8:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Topic50 `00082B:Argonia.esp` |
| ours | DialogResponses | new |  `000829:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_ComeKiller `000D3A:Argonia.esp` |
| ours | DialogResponses | new |  `000D3D:Argonia.esp` |
| ours | DialogResponses | new |  `000D3B:Argonia.esp` |
| ours | DialogResponses | new |  `000D3C:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Advice `000925:Argonia.esp` |
| ours | DialogResponses | new |  `000927:Argonia.esp` |
| ours | DialogResponses | new |  `00092B:Argonia.esp` |
| ours | DialogResponses | new |  `00092E:Argonia.esp` |
| ours | DialogResponses | new |  `000930:Argonia.esp` |
| ours | DialogResponses | new |  `00092D:Argonia.esp` |
| ours | DialogResponses | new |  `000926:Argonia.esp` |
| ours | DialogResponses | new |  `00092C:Argonia.esp` |
| ours | DialogResponses | new |  `00092A:Argonia.esp` |
| ours | DialogResponses | new |  `000928:Argonia.esp` |
| ours | DialogResponses | new |  `00092F:Argonia.esp` |
| ours | DialogResponses | new |  `000929:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_TheOffer `000EB4:Argonia.esp` |
| ours | DialogResponses | new |  `000EB5:Argonia.esp` |
| ours | DialogResponses | new |  `000EB6:Argonia.esp` |
| ours | DialogResponses | new |  `000EB7:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Scene2 `00081C:Argonia.esp` |
| ours | DialogResponses | new |  `00081D:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG01_TopicDoor `000C7C:Argonia.esp` |
| ours | DialogResponses | new |  `000C7E:Argonia.esp` |
| ours | DialogResponses | new |  `000C7F:Argonia.esp` |
| ours | DialogResponses | new |  `000C7D:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ04_BoatTopic `000DC8:Argonia.esp` |
| ours | DialogResponses | new |  `000DC6:Argonia.esp` |
| ours | DialogResponses | new |  `000DC1:Argonia.esp` |
| ours | DialogResponses | new |  `000DC4:Argonia.esp` |
| ours | DialogResponses | new |  `000DC5:Argonia.esp` |
| ours | DialogResponses | new |  `000DC3:Argonia.esp` |
| ours | DialogResponses | new |  `000DC2:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_TheNight `000EA9:Argonia.esp` |
| ours | DialogResponses | new |  `000EAC:Argonia.esp` |
| ours | DialogResponses | new |  `000EAF:Argonia.esp` |
| ours | DialogResponses | new |  `000EB1:Argonia.esp` |
| ours | DialogResponses | new |  `000EAD:Argonia.esp` |
| ours | DialogResponses | new |  `000EAE:Argonia.esp` |
| ours | DialogResponses | new |  `000EB0:Argonia.esp` |
| ours | DialogResponses | new |  `000EAB:Argonia.esp` |
| ours | DialogResponses | new |  `000EB2:Argonia.esp` |
| ours | DialogResponses | new |  `000EAA:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_TopicSellCharm `000CD1:Argonia.esp` |
| ours | DialogResponses | new |  `000CD2:Argonia.esp` |
| ours | DialogResponses | new |  `000CD3:Argonia.esp` |
| ours | DialogResponses | new |  `000CD4:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ30_TheBasin `000C27:Argonia.esp` |
| ours | DialogResponses | new |  `000C28:Argonia.esp` |
| ours | DialogResponses | new |  `000C2A:Argonia.esp` |
| ours | DialogResponses | new |  `000C29:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_TheMarch `000E6D:Argonia.esp` |
| ours | DialogResponses | new |  `000E6E:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_TopicClaimCharm `000CB0:Argonia.esp` |
| ours | DialogResponses | new |  `000CB1:Argonia.esp` |
| ours | DialogResponses | new |  `000CB2:Argonia.esp` |
| ours | DialogResponses | new |  `000CB5:Argonia.esp` |
| ours | DialogResponses | new |  `000CB6:Argonia.esp` |
| ours | DialogResponses | new |  `000CB4:Argonia.esp` |
| ours | DialogResponses | new |  `000CB3:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG01_TopicWelcome `000C9E:Argonia.esp` |
| ours | DialogResponses | new |  `000CA0:Argonia.esp` |
| ours | DialogResponses | new |  `000CA1:Argonia.esp` |
| ours | DialogResponses | new |  `000CA4:Argonia.esp` |
| ours | DialogResponses | new |  `000CA3:Argonia.esp` |
| ours | DialogResponses | new |  `000CA2:Argonia.esp` |
| ours | DialogResponses | new |  `000C9F:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Here `0009AD:Argonia.esp` |
| ours | DialogResponses | new |  `0009CC:Argonia.esp` |
| ours | DialogResponses | new |  `0009E5:Argonia.esp` |
| ours | DialogResponses | new |  `0009C4:Argonia.esp` |
| ours | DialogResponses | new |  `0009CD:Argonia.esp` |
| ours | DialogResponses | new |  `0009E7:Argonia.esp` |
| ours | DialogResponses | new |  `000A0F:Argonia.esp` |
| ours | DialogResponses | new |  `0009D2:Argonia.esp` |
| ours | DialogResponses | new |  `000A15:Argonia.esp` |
| ours | DialogResponses | new |  `0009C6:Argonia.esp` |
| ours | DialogResponses | new |  `0009CE:Argonia.esp` |
| ours | DialogResponses | new |  `0009D4:Argonia.esp` |
| ours | DialogResponses | new |  `0009D0:Argonia.esp` |
| ours | DialogResponses | new |  `0009FC:Argonia.esp` |
| ours | DialogResponses | new |  `0009C0:Argonia.esp` |
| ours | DialogResponses | new |  `0009B1:Argonia.esp` |
| ours | DialogResponses | new |  `0009F1:Argonia.esp` |
| ours | DialogResponses | new |  `000A0C:Argonia.esp` |
| ours | DialogResponses | new |  `0009B5:Argonia.esp` |
| ours | DialogResponses | new |  `000A12:Argonia.esp` |
| ours | DialogResponses | new |  `0009EA:Argonia.esp` |
| ours | DialogResponses | new |  `0009D9:Argonia.esp` |
| ours | DialogResponses | new |  `0009DC:Argonia.esp` |
| ours | DialogResponses | new |  `0009E9:Argonia.esp` |
| ours | DialogResponses | new |  `0009AE:Argonia.esp` |
| ours | DialogResponses | new |  `0009FB:Argonia.esp` |
| ours | DialogResponses | new |  `000A0D:Argonia.esp` |
| ours | DialogResponses | new |  `0009BC:Argonia.esp` |
| ours | DialogResponses | new |  `000A00:Argonia.esp` |
| ours | DialogResponses | new |  `0009D3:Argonia.esp` |
| ours | DialogResponses | new |  `000A04:Argonia.esp` |
| ours | DialogResponses | new |  `0009E6:Argonia.esp` |
| ours | DialogResponses | new |  `0009D8:Argonia.esp` |
| ours | DialogResponses | new |  `000A06:Argonia.esp` |
| ours | DialogResponses | new |  `0009EC:Argonia.esp` |
| ours | DialogResponses | new |  `0009DA:Argonia.esp` |
| ours | DialogResponses | new |  `0009B4:Argonia.esp` |
| ours | DialogResponses | new |  `0009F9:Argonia.esp` |
| ours | DialogResponses | new |  `0009C9:Argonia.esp` |
| ours | DialogResponses | new |  `0009FA:Argonia.esp` |
| ours | DialogResponses | new |  `0009EB:Argonia.esp` |
| ours | DialogResponses | new |  `000A07:Argonia.esp` |
| ours | DialogResponses | new |  `0009F3:Argonia.esp` |
| ours | DialogResponses | new |  `0009C2:Argonia.esp` |
| ours | DialogResponses | new |  `0009BD:Argonia.esp` |
| ours | DialogResponses | new |  `000A14:Argonia.esp` |
| ours | DialogResponses | new |  `0009DD:Argonia.esp` |
| ours | DialogResponses | new |  `0009F2:Argonia.esp` |
| ours | DialogResponses | new |  `0009C8:Argonia.esp` |
| ours | DialogResponses | new |  `0009EF:Argonia.esp` |
| ours | DialogResponses | new |  `0009BA:Argonia.esp` |
| ours | DialogResponses | new |  `0009B3:Argonia.esp` |
| ours | DialogResponses | new |  `000A02:Argonia.esp` |
| ours | DialogResponses | new |  `0009E8:Argonia.esp` |
| ours | DialogResponses | new |  `0009FE:Argonia.esp` |
| ours | DialogResponses | new |  `0009F0:Argonia.esp` |
| ours | DialogResponses | new |  `0009B8:Argonia.esp` |
| ours | DialogResponses | new |  `000A01:Argonia.esp` |
| ours | DialogResponses | new |  `0009CF:Argonia.esp` |
| ours | DialogResponses | new |  `0009C3:Argonia.esp` |
| ours | DialogResponses | new |  `000A10:Argonia.esp` |
| ours | DialogResponses | new |  `0009D5:Argonia.esp` |
| ours | DialogResponses | new |  `0009BB:Argonia.esp` |
| ours | DialogResponses | new |  `000A16:Argonia.esp` |
| ours | DialogResponses | new |  `0009C5:Argonia.esp` |
| ours | DialogResponses | new |  `000A03:Argonia.esp` |
| ours | DialogResponses | new |  `0009C1:Argonia.esp` |
| ours | DialogResponses | new |  `0009EE:Argonia.esp` |
| ours | DialogResponses | new |  `000A05:Argonia.esp` |
| ours | DialogResponses | new |  `0009CB:Argonia.esp` |
| ours | DialogResponses | new |  `0009FF:Argonia.esp` |
| ours | DialogResponses | new |  `0009B0:Argonia.esp` |
| ours | DialogResponses | new |  `0009E1:Argonia.esp` |
| ours | DialogResponses | new |  `000A11:Argonia.esp` |
| ours | DialogResponses | new |  `000A09:Argonia.esp` |
| ours | DialogResponses | new |  `0009E0:Argonia.esp` |
| ours | DialogResponses | new |  `0009FD:Argonia.esp` |
| ours | DialogResponses | new |  `0009E3:Argonia.esp` |
| ours | DialogResponses | new |  `0009B6:Argonia.esp` |
| ours | DialogResponses | new |  `0009B2:Argonia.esp` |
| ours | DialogResponses | new |  `0009BF:Argonia.esp` |
| ours | DialogResponses | new |  `0009B9:Argonia.esp` |
| ours | DialogResponses | new |  `0009E4:Argonia.esp` |
| ours | DialogResponses | new |  `0009B7:Argonia.esp` |
| ours | DialogResponses | new |  `0009DE:Argonia.esp` |
| ours | DialogResponses | new |  `0009DB:Argonia.esp` |
| ours | DialogResponses | new |  `0009D6:Argonia.esp` |
| ours | DialogResponses | new |  `0009F5:Argonia.esp` |
| ours | DialogResponses | new |  `0009ED:Argonia.esp` |
| ours | DialogResponses | new |  `0009D1:Argonia.esp` |
| ours | DialogResponses | new |  `0009AF:Argonia.esp` |
| ours | DialogResponses | new |  `0009D7:Argonia.esp` |
| ours | DialogResponses | new |  `0009C7:Argonia.esp` |
| ours | DialogResponses | new |  `000A17:Argonia.esp` |
| ours | DialogResponses | new |  `0009F8:Argonia.esp` |
| ours | DialogResponses | new |  `0009BE:Argonia.esp` |
| ours | DialogResponses | new |  `000A0E:Argonia.esp` |
| ours | DialogResponses | new |  `0009E2:Argonia.esp` |
| ours | DialogResponses | new |  `0009F7:Argonia.esp` |
| ours | DialogResponses | new |  `000A0A:Argonia.esp` |
| ours | DialogResponses | new |  `0009DF:Argonia.esp` |
| ours | DialogResponses | new |  `000A08:Argonia.esp` |
| ours | DialogResponses | new |  `000A0B:Argonia.esp` |
| ours | DialogResponses | new |  `0009F4:Argonia.esp` |
| ours | DialogResponses | new |  `0009F6:Argonia.esp` |
| ours | DialogResponses | new |  `000A13:Argonia.esp` |
| ours | DialogResponses | new |  `0009CA:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_LastSeason `000D64:Argonia.esp` |
| ours | DialogResponses | new |  `000D66:Argonia.esp` |
| ours | DialogResponses | new |  `000D65:Argonia.esp` |
| ours | DialogResponses | new |  `000D69:Argonia.esp` |
| ours | DialogResponses | new |  `000D67:Argonia.esp` |
| ours | DialogResponses | new |  `000D68:Argonia.esp` |
| ours | DialogResponses | new |  `000D6A:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Loot `000A19:Argonia.esp` |
| ours | DialogResponses | new |  `000A1D:Argonia.esp` |
| ours | DialogResponses | new |  `000A1A:Argonia.esp` |
| ours | DialogResponses | new |  `000A1B:Argonia.esp` |
| ours | DialogResponses | new |  `000A1C:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Scene3 `00081E:Argonia.esp` |
| ours | DialogResponses | new |  `00081F:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_LetBy `000D44:Argonia.esp` |
| ours | DialogResponses | new |  `000D50:Argonia.esp` |
| ours | DialogResponses | new |  `000D4C:Argonia.esp` |
| ours | DialogResponses | new |  `000D4F:Argonia.esp` |
| ours | DialogResponses | new |  `000D47:Argonia.esp` |
| ours | DialogResponses | new |  `000D45:Argonia.esp` |
| ours | DialogResponses | new |  `000D46:Argonia.esp` |
| ours | DialogResponses | new |  `000D49:Argonia.esp` |
| ours | DialogResponses | new |  `000D4E:Argonia.esp` |
| ours | DialogResponses | new |  `000D4B:Argonia.esp` |
| ours | DialogResponses | new |  `000D48:Argonia.esp` |
| ours | DialogResponses | new |  `000D4D:Argonia.esp` |
| ours | DialogResponses | new |  `000D4A:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_TheRoll `000E5A:Argonia.esp` |
| ours | DialogResponses | new |  `000E5B:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Self `000A90:Argonia.esp` |
| ours | DialogResponses | new |  `000AB8:Argonia.esp` |
| ours | DialogResponses | new |  `000AC7:Argonia.esp` |
| ours | DialogResponses | new |  `000ABD:Argonia.esp` |
| ours | DialogResponses | new |  `000ABF:Argonia.esp` |
| ours | DialogResponses | new |  `000ADF:Argonia.esp` |
| ours | DialogResponses | new |  `000AE4:Argonia.esp` |
| ours | DialogResponses | new |  `000ACA:Argonia.esp` |
| ours | DialogResponses | new |  `000AB7:Argonia.esp` |
| ours | DialogResponses | new |  `000AA5:Argonia.esp` |
| ours | DialogResponses | new |  `000A9C:Argonia.esp` |
| ours | DialogResponses | new |  `000B00:Argonia.esp` |
| ours | DialogResponses | new |  `000A9E:Argonia.esp` |
| ours | DialogResponses | new |  `000AD9:Argonia.esp` |
| ours | DialogResponses | new |  `000B04:Argonia.esp` |
| ours | DialogResponses | new |  `000AEB:Argonia.esp` |
| ours | DialogResponses | new |  `000ADB:Argonia.esp` |
| ours | DialogResponses | new |  `000AAD:Argonia.esp` |
| ours | DialogResponses | new |  `000A92:Argonia.esp` |
| ours | DialogResponses | new |  `000B02:Argonia.esp` |
| ours | DialogResponses | new |  `000AAA:Argonia.esp` |
| ours | DialogResponses | new |  `000B03:Argonia.esp` |
| ours | DialogResponses | new |  `000AAE:Argonia.esp` |
| ours | DialogResponses | new |  `000AE8:Argonia.esp` |
| ours | DialogResponses | new |  `000AF7:Argonia.esp` |
| ours | DialogResponses | new |  `000AF8:Argonia.esp` |
| ours | DialogResponses | new |  `000AE7:Argonia.esp` |
| ours | DialogResponses | new |  `000B06:Argonia.esp` |
| ours | DialogResponses | new |  `000AEA:Argonia.esp` |
| ours | DialogResponses | new |  `000AA1:Argonia.esp` |
| ours | DialogResponses | new |  `000B07:Argonia.esp` |
| ours | DialogResponses | new |  `000AF3:Argonia.esp` |
| ours | DialogResponses | new |  `000AC0:Argonia.esp` |
| ours | DialogResponses | new |  `000AF5:Argonia.esp` |
| ours | DialogResponses | new |  `000AC3:Argonia.esp` |
| ours | DialogResponses | new |  `000AC5:Argonia.esp` |
| ours | DialogResponses | new |  `000A9B:Argonia.esp` |
| ours | DialogResponses | new |  `000AB0:Argonia.esp` |
| ours | DialogResponses | new |  `000ADC:Argonia.esp` |
| ours | DialogResponses | new |  `000ABA:Argonia.esp` |
| ours | DialogResponses | new |  `000AB5:Argonia.esp` |
| ours | DialogResponses | new |  `000ACC:Argonia.esp` |
| ours | DialogResponses | new |  `000A91:Argonia.esp` |
| ours | DialogResponses | new |  `000AD5:Argonia.esp` |
| ours | DialogResponses | new |  `000AC6:Argonia.esp` |
| ours | DialogResponses | new |  `000A96:Argonia.esp` |
| ours | DialogResponses | new |  `000AFA:Argonia.esp` |
| ours | DialogResponses | new |  `000AAC:Argonia.esp` |
| ours | DialogResponses | new |  `000AE3:Argonia.esp` |
| ours | DialogResponses | new |  `000AC2:Argonia.esp` |
| ours | DialogResponses | new |  `000ADE:Argonia.esp` |
| ours | DialogResponses | new |  `000AAF:Argonia.esp` |
| ours | DialogResponses | new |  `000AE9:Argonia.esp` |
| ours | DialogResponses | new |  `000AF0:Argonia.esp` |
| ours | DialogResponses | new |  `000AC1:Argonia.esp` |
| ours | DialogResponses | new |  `000AE1:Argonia.esp` |
| ours | DialogResponses | new |  `000AFC:Argonia.esp` |
| ours | DialogResponses | new |  `000AEC:Argonia.esp` |
| ours | DialogResponses | new |  `000AC9:Argonia.esp` |
| ours | DialogResponses | new |  `000AF4:Argonia.esp` |
| ours | DialogResponses | new |  `000B05:Argonia.esp` |
| ours | DialogResponses | new |  `000AFE:Argonia.esp` |
| ours | DialogResponses | new |  `000ABB:Argonia.esp` |
| ours | DialogResponses | new |  `000AB1:Argonia.esp` |
| ours | DialogResponses | new |  `000A98:Argonia.esp` |
| ours | DialogResponses | new |  `000AE2:Argonia.esp` |
| ours | DialogResponses | new |  `000AA0:Argonia.esp` |
| ours | DialogResponses | new |  `000AC8:Argonia.esp` |
| ours | DialogResponses | new |  `000AEF:Argonia.esp` |
| ours | DialogResponses | new |  `000AA8:Argonia.esp` |
| ours | DialogResponses | new |  `000AFB:Argonia.esp` |
| ours | DialogResponses | new |  `000AFD:Argonia.esp` |
| ours | DialogResponses | new |  `000AA6:Argonia.esp` |
| ours | DialogResponses | new |  `000A99:Argonia.esp` |
| ours | DialogResponses | new |  `000A9A:Argonia.esp` |
| ours | DialogResponses | new |  `000AA7:Argonia.esp` |
| ours | DialogResponses | new |  `000ACB:Argonia.esp` |
| ours | DialogResponses | new |  `000AE6:Argonia.esp` |
| ours | DialogResponses | new |  `000AB3:Argonia.esp` |
| ours | DialogResponses | new |  `000ADA:Argonia.esp` |
| ours | DialogResponses | new |  `000ABE:Argonia.esp` |
| ours | DialogResponses | new |  `000AF6:Argonia.esp` |
| ours | DialogResponses | new |  `000AEE:Argonia.esp` |
| ours | DialogResponses | new |  `000AD6:Argonia.esp` |
| ours | DialogResponses | new |  `000AA2:Argonia.esp` |
| ours | DialogResponses | new |  `000ACE:Argonia.esp` |
| ours | DialogResponses | new |  `000A93:Argonia.esp` |
| ours | DialogResponses | new |  `000AA3:Argonia.esp` |
| ours | DialogResponses | new |  `000A95:Argonia.esp` |
| ours | DialogResponses | new |  `000A94:Argonia.esp` |
| ours | DialogResponses | new |  `000ADD:Argonia.esp` |
| ours | DialogResponses | new |  `000ACD:Argonia.esp` |
| ours | DialogResponses | new |  `000AE0:Argonia.esp` |
| ours | DialogResponses | new |  `000ABC:Argonia.esp` |
| ours | DialogResponses | new |  `000AAB:Argonia.esp` |
| ours | DialogResponses | new |  `000AD0:Argonia.esp` |
| ours | DialogResponses | new |  `000AD2:Argonia.esp` |
| ours | DialogResponses | new |  `000AFF:Argonia.esp` |
| ours | DialogResponses | new |  `000AD7:Argonia.esp` |
| ours | DialogResponses | new |  `000A9F:Argonia.esp` |
| ours | DialogResponses | new |  `000AED:Argonia.esp` |
| ours | DialogResponses | new |  `000AD4:Argonia.esp` |
| ours | DialogResponses | new |  `000AB6:Argonia.esp` |
| ours | DialogResponses | new |  `000AA9:Argonia.esp` |
| ours | DialogResponses | new |  `000AC4:Argonia.esp` |
| ours | DialogResponses | new |  `000AD1:Argonia.esp` |
| ours | DialogResponses | new |  `000A9D:Argonia.esp` |
| ours | DialogResponses | new |  `000AF1:Argonia.esp` |
| ours | DialogResponses | new |  `000ACF:Argonia.esp` |
| ours | DialogResponses | new |  `000AE5:Argonia.esp` |
| ours | DialogResponses | new |  `000AA4:Argonia.esp` |
| ours | DialogResponses | new |  `000AB9:Argonia.esp` |
| ours | DialogResponses | new |  `000A97:Argonia.esp` |
| ours | DialogResponses | new |  `000AD8:Argonia.esp` |
| ours | DialogResponses | new |  `000AB4:Argonia.esp` |
| ours | DialogResponses | new |  `000AF2:Argonia.esp` |
| ours | DialogResponses | new |  `000AB2:Argonia.esp` |
| ours | DialogResponses | new |  `000AF9:Argonia.esp` |
| ours | DialogResponses | new |  `000AD3:Argonia.esp` |
| ours | DialogResponses | new |  `000B01:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG01_TopicBed `000C86:Argonia.esp` |
| ours | DialogResponses | new |  `000C87:Argonia.esp` |
| ours | DialogResponses | new |  `000C8A:Argonia.esp` |
| ours | DialogResponses | new |  `000C8B:Argonia.esp` |
| ours | DialogResponses | new |  `000C88:Argonia.esp` |
| ours | DialogResponses | new |  `000C8C:Argonia.esp` |
| ours | DialogResponses | new |  `000C89:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_TopicClaimBeads `000CB8:Argonia.esp` |
| ours | DialogResponses | new |  `000CBA:Argonia.esp` |
| ours | DialogResponses | new |  `000CBB:Argonia.esp` |
| ours | DialogResponses | new |  `000CB9:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_TheGate `000D2D:Argonia.esp` |
| ours | DialogResponses | new |  `000D32:Argonia.esp` |
| ours | DialogResponses | new |  `000D33:Argonia.esp` |
| ours | DialogResponses | new |  `000D31:Argonia.esp` |
| ours | DialogResponses | new |  `000D30:Argonia.esp` |
| ours | DialogResponses | new |  `000D2F:Argonia.esp` |
| ours | DialogResponses | new |  `000D2E:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Topic20 `000825:Argonia.esp` |
| ours | DialogResponses | new |  `000823:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ05_WordTopic `000ECC:Argonia.esp` |
| ours | DialogResponses | new |  `000EC7:Argonia.esp` |
| ours | DialogResponses | new |  `000ECA:Argonia.esp` |
| ours | DialogResponses | new |  `000EC3:Argonia.esp` |
| ours | DialogResponses | new |  `000EC8:Argonia.esp` |
| ours | DialogResponses | new |  `000EC6:Argonia.esp` |
| ours | DialogResponses | new |  `000EC4:Argonia.esp` |
| ours | DialogResponses | new |  `000EC9:Argonia.esp` |
| ours | DialogResponses | new |  `000EC2:Argonia.esp` |
| ours | DialogResponses | new |  `000EC5:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Trade `000B80:Argonia.esp` |
| ours | DialogResponses | new |  `000B99:Argonia.esp` |
| ours | DialogResponses | new |  `000B8B:Argonia.esp` |
| ours | DialogResponses | new |  `000B9A:Argonia.esp` |
| ours | DialogResponses | new |  `000B94:Argonia.esp` |
| ours | DialogResponses | new |  `000B84:Argonia.esp` |
| ours | DialogResponses | new |  `000B8A:Argonia.esp` |
| ours | DialogResponses | new |  `000B83:Argonia.esp` |
| ours | DialogResponses | new |  `000B89:Argonia.esp` |
| ours | DialogResponses | new |  `000B9C:Argonia.esp` |
| ours | DialogResponses | new |  `000B96:Argonia.esp` |
| ours | DialogResponses | new |  `000B85:Argonia.esp` |
| ours | DialogResponses | new |  `000B97:Argonia.esp` |
| ours | DialogResponses | new |  `000B82:Argonia.esp` |
| ours | DialogResponses | new |  `000B8D:Argonia.esp` |
| ours | DialogResponses | new |  `000B93:Argonia.esp` |
| ours | DialogResponses | new |  `000B98:Argonia.esp` |
| ours | DialogResponses | new |  `000B91:Argonia.esp` |
| ours | DialogResponses | new |  `000B95:Argonia.esp` |
| ours | DialogResponses | new |  `000B88:Argonia.esp` |
| ours | DialogResponses | new |  `000B90:Argonia.esp` |
| ours | DialogResponses | new |  `000B81:Argonia.esp` |
| ours | DialogResponses | new |  `000B8C:Argonia.esp` |
| ours | DialogResponses | new |  `000B9B:Argonia.esp` |
| ours | DialogResponses | new |  `000B92:Argonia.esp` |
| ours | DialogResponses | new |  `000B9D:Argonia.esp` |
| ours | DialogResponses | new |  `000B87:Argonia.esp` |
| ours | DialogResponses | new |  `000B86:Argonia.esp` |
| ours | DialogResponses | new |  `000B8F:Argonia.esp` |
| ours | DialogResponses | new |  `000B8E:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Lore `000A1F:Argonia.esp` |
| ours | DialogResponses | new |  `000A58:Argonia.esp` |
| ours | DialogResponses | new |  `000A2B:Argonia.esp` |
| ours | DialogResponses | new |  `000A79:Argonia.esp` |
| ours | DialogResponses | new |  `000A22:Argonia.esp` |
| ours | DialogResponses | new |  `000A31:Argonia.esp` |
| ours | DialogResponses | new |  `000A4D:Argonia.esp` |
| ours | DialogResponses | new |  `000A26:Argonia.esp` |
| ours | DialogResponses | new |  `000A23:Argonia.esp` |
| ours | DialogResponses | new |  `000A5B:Argonia.esp` |
| ours | DialogResponses | new |  `000A20:Argonia.esp` |
| ours | DialogResponses | new |  `000A5F:Argonia.esp` |
| ours | DialogResponses | new |  `000A71:Argonia.esp` |
| ours | DialogResponses | new |  `000A5D:Argonia.esp` |
| ours | DialogResponses | new |  `000A49:Argonia.esp` |
| ours | DialogResponses | new |  `000A21:Argonia.esp` |
| ours | DialogResponses | new |  `000A59:Argonia.esp` |
| ours | DialogResponses | new |  `000A47:Argonia.esp` |
| ours | DialogResponses | new |  `000A3A:Argonia.esp` |
| ours | DialogResponses | new |  `000A53:Argonia.esp` |
| ours | DialogResponses | new |  `000A3F:Argonia.esp` |
| ours | DialogResponses | new |  `000A4F:Argonia.esp` |
| ours | DialogResponses | new |  `000A6F:Argonia.esp` |
| ours | DialogResponses | new |  `000A32:Argonia.esp` |
| ours | DialogResponses | new |  `000A66:Argonia.esp` |
| ours | DialogResponses | new |  `000A6E:Argonia.esp` |
| ours | DialogResponses | new |  `000A25:Argonia.esp` |
| ours | DialogResponses | new |  `000A63:Argonia.esp` |
| ours | DialogResponses | new |  `000A48:Argonia.esp` |
| ours | DialogResponses | new |  `000A3D:Argonia.esp` |
| ours | DialogResponses | new |  `000A2C:Argonia.esp` |
| ours | DialogResponses | new |  `000A3B:Argonia.esp` |
| ours | DialogResponses | new |  `000A41:Argonia.esp` |
| ours | DialogResponses | new |  `000A69:Argonia.esp` |
| ours | DialogResponses | new |  `000A36:Argonia.esp` |
| ours | DialogResponses | new |  `000A62:Argonia.esp` |
| ours | DialogResponses | new |  `000A2A:Argonia.esp` |
| ours | DialogResponses | new |  `000A73:Argonia.esp` |
| ours | DialogResponses | new |  `000A5A:Argonia.esp` |
| ours | DialogResponses | new |  `000A3C:Argonia.esp` |
| ours | DialogResponses | new |  `000A3E:Argonia.esp` |
| ours | DialogResponses | new |  `000A6A:Argonia.esp` |
| ours | DialogResponses | new |  `000A43:Argonia.esp` |
| ours | DialogResponses | new |  `000A4E:Argonia.esp` |
| ours | DialogResponses | new |  `000A45:Argonia.esp` |
| ours | DialogResponses | new |  `000A51:Argonia.esp` |
| ours | DialogResponses | new |  `000A54:Argonia.esp` |
| ours | DialogResponses | new |  `000A50:Argonia.esp` |
| ours | DialogResponses | new |  `000A68:Argonia.esp` |
| ours | DialogResponses | new |  `000A34:Argonia.esp` |
| ours | DialogResponses | new |  `000A4C:Argonia.esp` |
| ours | DialogResponses | new |  `000A44:Argonia.esp` |
| ours | DialogResponses | new |  `000A4A:Argonia.esp` |
| ours | DialogResponses | new |  `000A5C:Argonia.esp` |
| ours | DialogResponses | new |  `000A6B:Argonia.esp` |
| ours | DialogResponses | new |  `000A42:Argonia.esp` |
| ours | DialogResponses | new |  `000A55:Argonia.esp` |
| ours | DialogResponses | new |  `000A2E:Argonia.esp` |
| ours | DialogResponses | new |  `000A64:Argonia.esp` |
| ours | DialogResponses | new |  `000A5E:Argonia.esp` |
| ours | DialogResponses | new |  `000A33:Argonia.esp` |
| ours | DialogResponses | new |  `000A38:Argonia.esp` |
| ours | DialogResponses | new |  `000A75:Argonia.esp` |
| ours | DialogResponses | new |  `000A76:Argonia.esp` |
| ours | DialogResponses | new |  `000A40:Argonia.esp` |
| ours | DialogResponses | new |  `000A78:Argonia.esp` |
| ours | DialogResponses | new |  `000A37:Argonia.esp` |
| ours | DialogResponses | new |  `000A52:Argonia.esp` |
| ours | DialogResponses | new |  `000A2D:Argonia.esp` |
| ours | DialogResponses | new |  `000A77:Argonia.esp` |
| ours | DialogResponses | new |  `000A27:Argonia.esp` |
| ours | DialogResponses | new |  `000A24:Argonia.esp` |
| ours | DialogResponses | new |  `000A56:Argonia.esp` |
| ours | DialogResponses | new |  `000A67:Argonia.esp` |
| ours | DialogResponses | new |  `000A57:Argonia.esp` |
| ours | DialogResponses | new |  `000A30:Argonia.esp` |
| ours | DialogResponses | new |  `000A28:Argonia.esp` |
| ours | DialogResponses | new |  `000A74:Argonia.esp` |
| ours | DialogResponses | new |  `000A2F:Argonia.esp` |
| ours | DialogResponses | new |  `000A6C:Argonia.esp` |
| ours | DialogResponses | new |  `000A70:Argonia.esp` |
| ours | DialogResponses | new |  `000A60:Argonia.esp` |
| ours | DialogResponses | new |  `000A46:Argonia.esp` |
| ours | DialogResponses | new |  `000A35:Argonia.esp` |
| ours | DialogResponses | new |  `000A29:Argonia.esp` |
| ours | DialogResponses | new |  `000A65:Argonia.esp` |
| ours | DialogResponses | new |  `000A39:Argonia.esp` |
| ours | DialogResponses | new |  `000A4B:Argonia.esp` |
| ours | DialogResponses | new |  `000A6D:Argonia.esp` |
| ours | DialogResponses | new |  `000A72:Argonia.esp` |
| ours | DialogResponses | new |  `000A61:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_TheTokens `000D71:Argonia.esp` |
| ours | DialogResponses | new |  `000D73:Argonia.esp` |
| ours | DialogResponses | new |  `000D74:Argonia.esp` |
| ours | DialogResponses | new |  `000D72:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_TopicHandOverOkan `000CC2:Argonia.esp` |
| ours | DialogResponses | new |  `000CC5:Argonia.esp` |
| ours | DialogResponses | new |  `000CC3:Argonia.esp` |
| ours | DialogResponses | new |  `000CC4:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_AnswerName `000E5D:Argonia.esp` |
| ours | DialogResponses | new |  `000E5E:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Topic90 `000832:Argonia.esp` |
| ours | DialogResponses | new |  `000830:Argonia.esp` |
| ours | DialogResponses | new |  `00082F:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Hello `000835:Argonia.esp` |
| ours | DialogResponses | new |  `0008EC:Argonia.esp` |
| ours | DialogResponses | new |  `0008D4:Argonia.esp` |
| ours | DialogResponses | new |  `00085D:Argonia.esp` |
| ours | DialogResponses | new |  `0008A3:Argonia.esp` |
| ours | DialogResponses | new |  `0008CE:Argonia.esp` |
| ours | DialogResponses | new |  `00089F:Argonia.esp` |
| ours | DialogResponses | new |  `000860:Argonia.esp` |
| ours | DialogResponses | new |  `0008CA:Argonia.esp` |
| ours | DialogResponses | new |  `000917:Argonia.esp` |
| ours | DialogResponses | new |  `000892:Argonia.esp` |
| ours | DialogResponses | new |  `0008FD:Argonia.esp` |
| ours | DialogResponses | new |  `00091E:Argonia.esp` |
| ours | DialogResponses | new |  `00090D:Argonia.esp` |
| ours | DialogResponses | new |  `0008A9:Argonia.esp` |
| ours | DialogResponses | new |  `0008D2:Argonia.esp` |
| ours | DialogResponses | new |  `0008BD:Argonia.esp` |
| ours | DialogResponses | new |  `0008BE:Argonia.esp` |
| ours | DialogResponses | new |  `0008F8:Argonia.esp` |
| ours | DialogResponses | new |  `0008F2:Argonia.esp` |
| ours | DialogResponses | new |  `000923:Argonia.esp` |
| ours | DialogResponses | new |  `0008E1:Argonia.esp` |
| ours | DialogResponses | new |  `0008C9:Argonia.esp` |
| ours | DialogResponses | new |  `0008B3:Argonia.esp` |
| ours | DialogResponses | new |  `0008B9:Argonia.esp` |
| ours | DialogResponses | new |  `0008B7:Argonia.esp` |
| ours | DialogResponses | new |  `000837:Argonia.esp` |
| ours | DialogResponses | new |  `0008D8:Argonia.esp` |
| ours | DialogResponses | new |  `00085B:Argonia.esp` |
| ours | DialogResponses | new |  `0008F3:Argonia.esp` |
| ours | DialogResponses | new |  `00091B:Argonia.esp` |
| ours | DialogResponses | new |  `0008FA:Argonia.esp` |
| ours | DialogResponses | new |  `00086C:Argonia.esp` |
| ours | DialogResponses | new |  `00088C:Argonia.esp` |
| ours | DialogResponses | new |  `00086F:Argonia.esp` |
| ours | DialogResponses | new |  `0008D9:Argonia.esp` |
| ours | DialogResponses | new |  `000849:Argonia.esp` |
| ours | DialogResponses | new |  `000922:Argonia.esp` |
| ours | DialogResponses | new |  `0008B8:Argonia.esp` |
| ours | DialogResponses | new |  `000841:Argonia.esp` |
| ours | DialogResponses | new |  `000878:Argonia.esp` |
| ours | DialogResponses | new |  `000909:Argonia.esp` |
| ours | DialogResponses | new |  `0008AD:Argonia.esp` |
| ours | DialogResponses | new |  `00083D:Argonia.esp` |
| ours | DialogResponses | new |  `00090F:Argonia.esp` |
| ours | DialogResponses | new |  `000857:Argonia.esp` |
| ours | DialogResponses | new |  `000879:Argonia.esp` |
| ours | DialogResponses | new |  `0008F0:Argonia.esp` |
| ours | DialogResponses | new |  `000893:Argonia.esp` |
| ours | DialogResponses | new |  `000906:Argonia.esp` |
| ours | DialogResponses | new |  `000905:Argonia.esp` |
| ours | DialogResponses | new |  `0008B1:Argonia.esp` |
| ours | DialogResponses | new |  `00087C:Argonia.esp` |
| ours | DialogResponses | new |  `00086A:Argonia.esp` |
| ours | DialogResponses | new |  `000890:Argonia.esp` |
| ours | DialogResponses | new |  `0008E7:Argonia.esp` |
| ours | DialogResponses | new |  `000865:Argonia.esp` |
| ours | DialogResponses | new |  `000901:Argonia.esp` |
| ours | DialogResponses | new |  `0008B5:Argonia.esp` |
| ours | DialogResponses | new |  `000920:Argonia.esp` |
| ours | DialogResponses | new |  `0008E4:Argonia.esp` |
| ours | DialogResponses | new |  `0008D5:Argonia.esp` |
| ours | DialogResponses | new |  `000873:Argonia.esp` |
| ours | DialogResponses | new |  `000884:Argonia.esp` |
| ours | DialogResponses | new |  `000856:Argonia.esp` |
| ours | DialogResponses | new |  `000919:Argonia.esp` |
| ours | DialogResponses | new |  `000847:Argonia.esp` |
| ours | DialogResponses | new |  `0008C0:Argonia.esp` |
| ours | DialogResponses | new |  `00088A:Argonia.esp` |
| ours | DialogResponses | new |  `0008DA:Argonia.esp` |
| ours | DialogResponses | new |  `000896:Argonia.esp` |
| ours | DialogResponses | new |  `00085C:Argonia.esp` |
| ours | DialogResponses | new |  `00084D:Argonia.esp` |
| ours | DialogResponses | new |  `000913:Argonia.esp` |
| ours | DialogResponses | new |  `0008CD:Argonia.esp` |
| ours | DialogResponses | new |  `00091F:Argonia.esp` |
| ours | DialogResponses | new |  `000854:Argonia.esp` |
| ours | DialogResponses | new |  `000904:Argonia.esp` |
| ours | DialogResponses | new |  `00088B:Argonia.esp` |
| ours | DialogResponses | new |  `0008BF:Argonia.esp` |
| ours | DialogResponses | new |  `0008A5:Argonia.esp` |
| ours | DialogResponses | new |  `000908:Argonia.esp` |
| ours | DialogResponses | new |  `00091D:Argonia.esp` |
| ours | DialogResponses | new |  `00091A:Argonia.esp` |
| ours | DialogResponses | new |  `000850:Argonia.esp` |
| ours | DialogResponses | new |  `0008EE:Argonia.esp` |
| ours | DialogResponses | new |  `000872:Argonia.esp` |
| ours | DialogResponses | new |  `0008D6:Argonia.esp` |
| ours | DialogResponses | new |  `0008EB:Argonia.esp` |
| ours | DialogResponses | new |  `0008F4:Argonia.esp` |
| ours | DialogResponses | new |  `000914:Argonia.esp` |
| ours | DialogResponses | new |  `000880:Argonia.esp` |
| ours | DialogResponses | new |  `0008AA:Argonia.esp` |
| ours | DialogResponses | new |  `000864:Argonia.esp` |
| ours | DialogResponses | new |  `000870:Argonia.esp` |
| ours | DialogResponses | new |  `0008BA:Argonia.esp` |
| ours | DialogResponses | new |  `0008FE:Argonia.esp` |
| ours | DialogResponses | new |  `0008CF:Argonia.esp` |
| ours | DialogResponses | new |  `00087B:Argonia.esp` |
| ours | DialogResponses | new |  `000861:Argonia.esp` |
| ours | DialogResponses | new |  `000863:Argonia.esp` |
| ours | DialogResponses | new |  `0008B4:Argonia.esp` |
| ours | DialogResponses | new |  `000882:Argonia.esp` |
| ours | DialogResponses | new |  `0008AB:Argonia.esp` |
| ours | DialogResponses | new |  `000844:Argonia.esp` |
| ours | DialogResponses | new |  `000867:Argonia.esp` |
| ours | DialogResponses | new |  `00083B:Argonia.esp` |
| ours | DialogResponses | new |  `000862:Argonia.esp` |
| ours | DialogResponses | new |  `0008C3:Argonia.esp` |
| ours | DialogResponses | new |  `0008A4:Argonia.esp` |
| ours | DialogResponses | new |  `00085F:Argonia.esp` |
| ours | DialogResponses | new |  `000839:Argonia.esp` |
| ours | DialogResponses | new |  `00089E:Argonia.esp` |
| ours | DialogResponses | new |  `0008B2:Argonia.esp` |
| ours | DialogResponses | new |  `000853:Argonia.esp` |
| ours | DialogResponses | new |  `0008E5:Argonia.esp` |
| ours | DialogResponses | new |  `000866:Argonia.esp` |
| ours | DialogResponses | new |  `0008AE:Argonia.esp` |
| ours | DialogResponses | new |  `0008E2:Argonia.esp` |
| ours | DialogResponses | new |  `000911:Argonia.esp` |
| ours | DialogResponses | new |  `000846:Argonia.esp` |
| ours | DialogResponses | new |  `0008C1:Argonia.esp` |
| ours | DialogResponses | new |  `00083C:Argonia.esp` |
| ours | DialogResponses | new |  `000895:Argonia.esp` |
| ours | DialogResponses | new |  `00083A:Argonia.esp` |
| ours | DialogResponses | new |  `000876:Argonia.esp` |
| ours | DialogResponses | new |  `0008F1:Argonia.esp` |
| ours | DialogResponses | new |  `0008E0:Argonia.esp` |
| ours | DialogResponses | new |  `00087A:Argonia.esp` |
| ours | DialogResponses | new |  `000842:Argonia.esp` |
| ours | DialogResponses | new |  `00084B:Argonia.esp` |
| ours | DialogResponses | new |  `0008C6:Argonia.esp` |
| ours | DialogResponses | new |  `0008B0:Argonia.esp` |
| ours | DialogResponses | new |  `0008D1:Argonia.esp` |
| ours | DialogResponses | new |  `000843:Argonia.esp` |
| ours | DialogResponses | new |  `0008C4:Argonia.esp` |
| ours | DialogResponses | new |  `0008EA:Argonia.esp` |
| ours | DialogResponses | new |  `000907:Argonia.esp` |
| ours | DialogResponses | new |  `000883:Argonia.esp` |
| ours | DialogResponses | new |  `00088E:Argonia.esp` |
| ours | DialogResponses | new |  `00086E:Argonia.esp` |
| ours | DialogResponses | new |  `0008DF:Argonia.esp` |
| ours | DialogResponses | new |  `000912:Argonia.esp` |
| ours | DialogResponses | new |  `00085E:Argonia.esp` |
| ours | DialogResponses | new |  `000859:Argonia.esp` |
| ours | DialogResponses | new |  `000915:Argonia.esp` |
| ours | DialogResponses | new |  `00083E:Argonia.esp` |
| ours | DialogResponses | new |  `000840:Argonia.esp` |
| ours | DialogResponses | new |  `0008A1:Argonia.esp` |
| ours | DialogResponses | new |  `000902:Argonia.esp` |
| ours | DialogResponses | new |  `000918:Argonia.esp` |
| ours | DialogResponses | new |  `0008D0:Argonia.esp` |
| ours | DialogResponses | new |  `0008D7:Argonia.esp` |
| ours | DialogResponses | new |  `0008E6:Argonia.esp` |
| ours | DialogResponses | new |  `0008C5:Argonia.esp` |
| ours | DialogResponses | new |  `000887:Argonia.esp` |
| ours | DialogResponses | new |  `0008D3:Argonia.esp` |
| ours | DialogResponses | new |  `000891:Argonia.esp` |
| ours | DialogResponses | new |  `0008E8:Argonia.esp` |
| ours | DialogResponses | new |  `00084F:Argonia.esp` |
| ours | DialogResponses | new |  `0008BC:Argonia.esp` |
| ours | DialogResponses | new |  `0008DD:Argonia.esp` |
| ours | DialogResponses | new |  `000852:Argonia.esp` |
| ours | DialogResponses | new |  `000868:Argonia.esp` |
| ours | DialogResponses | new |  `00089B:Argonia.esp` |
| ours | DialogResponses | new |  `0008AC:Argonia.esp` |
| ours | DialogResponses | new |  `0008CB:Argonia.esp` |
| ours | DialogResponses | new |  `0008CC:Argonia.esp` |
| ours | DialogResponses | new |  `00089C:Argonia.esp` |
| ours | DialogResponses | new |  `0008C7:Argonia.esp` |
| ours | DialogResponses | new |  `00084E:Argonia.esp` |
| ours | DialogResponses | new |  `0008DE:Argonia.esp` |
| ours | DialogResponses | new |  `00090C:Argonia.esp` |
| ours | DialogResponses | new |  `000845:Argonia.esp` |
| ours | DialogResponses | new |  `0008F5:Argonia.esp` |
| ours | DialogResponses | new |  `00083F:Argonia.esp` |
| ours | DialogResponses | new |  `0008F6:Argonia.esp` |
| ours | DialogResponses | new |  `000851:Argonia.esp` |
| ours | DialogResponses | new |  `000875:Argonia.esp` |
| ours | DialogResponses | new |  `0008DC:Argonia.esp` |
| ours | DialogResponses | new |  `0008DB:Argonia.esp` |
| ours | DialogResponses | new |  `000874:Argonia.esp` |
| ours | DialogResponses | new |  `000881:Argonia.esp` |
| ours | DialogResponses | new |  `00084C:Argonia.esp` |
| ours | DialogResponses | new |  `00087D:Argonia.esp` |
| ours | DialogResponses | new |  `0008F9:Argonia.esp` |
| ours | DialogResponses | new |  `000885:Argonia.esp` |
| ours | DialogResponses | new |  `00088D:Argonia.esp` |
| ours | DialogResponses | new |  `00087F:Argonia.esp` |
| ours | DialogResponses | new |  `0008B6:Argonia.esp` |
| ours | DialogResponses | new |  `000877:Argonia.esp` |
| ours | DialogResponses | new |  `000894:Argonia.esp` |
| ours | DialogResponses | new |  `000910:Argonia.esp` |
| ours | DialogResponses | new |  `0008FC:Argonia.esp` |
| ours | DialogResponses | new |  `0008A8:Argonia.esp` |
| ours | DialogResponses | new |  `0008C8:Argonia.esp` |
| ours | DialogResponses | new |  `000903:Argonia.esp` |
| ours | DialogResponses | new |  `000888:Argonia.esp` |
| ours | DialogResponses | new |  `00090E:Argonia.esp` |
| ours | DialogResponses | new |  `000897:Argonia.esp` |
| ours | DialogResponses | new |  `0008E9:Argonia.esp` |
| ours | DialogResponses | new |  `000871:Argonia.esp` |
| ours | DialogResponses | new |  `000855:Argonia.esp` |
| ours | DialogResponses | new |  `000858:Argonia.esp` |
| ours | DialogResponses | new |  `00089A:Argonia.esp` |
| ours | DialogResponses | new |  `000916:Argonia.esp` |
| ours | DialogResponses | new |  `0008FF:Argonia.esp` |
| ours | DialogResponses | new |  `00090A:Argonia.esp` |
| ours | DialogResponses | new |  `00086D:Argonia.esp` |
| ours | DialogResponses | new |  `000836:Argonia.esp` |
| ours | DialogResponses | new |  `00086B:Argonia.esp` |
| ours | DialogResponses | new |  `000898:Argonia.esp` |
| ours | DialogResponses | new |  `0008E3:Argonia.esp` |
| ours | DialogResponses | new |  `0008AF:Argonia.esp` |
| ours | DialogResponses | new |  `0008FB:Argonia.esp` |
| ours | DialogResponses | new |  `00084A:Argonia.esp` |
| ours | DialogResponses | new |  `000848:Argonia.esp` |
| ours | DialogResponses | new |  `0008F7:Argonia.esp` |
| ours | DialogResponses | new |  `00088F:Argonia.esp` |
| ours | DialogResponses | new |  `000900:Argonia.esp` |
| ours | DialogResponses | new |  `0008C2:Argonia.esp` |
| ours | DialogResponses | new |  `000886:Argonia.esp` |
| ours | DialogResponses | new |  `00085A:Argonia.esp` |
| ours | DialogResponses | new |  `0008A2:Argonia.esp` |
| ours | DialogResponses | new |  `00090B:Argonia.esp` |
| ours | DialogResponses | new |  `00087E:Argonia.esp` |
| ours | DialogResponses | new |  `000899:Argonia.esp` |
| ours | DialogResponses | new |  `000869:Argonia.esp` |
| ours | DialogResponses | new |  `0008EF:Argonia.esp` |
| ours | DialogResponses | new |  `0008A0:Argonia.esp` |
| ours | DialogResponses | new |  `0008A6:Argonia.esp` |
| ours | DialogResponses | new |  `000838:Argonia.esp` |
| ours | DialogResponses | new |  `000889:Argonia.esp` |
| ours | DialogResponses | new |  `00089D:Argonia.esp` |
| ours | DialogResponses | new |  `0008ED:Argonia.esp` |
| ours | DialogResponses | new |  `0008BB:Argonia.esp` |
| ours | DialogResponses | new |  `000921:Argonia.esp` |
| ours | DialogResponses | new |  `00091C:Argonia.esp` |
| ours | DialogResponses | new |  `0008A7:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Someone `000B12:Argonia.esp` |
| ours | DialogResponses | new |  `000B40:Argonia.esp` |
| ours | DialogResponses | new |  `000B24:Argonia.esp` |
| ours | DialogResponses | new |  `000B21:Argonia.esp` |
| ours | DialogResponses | new |  `000B4D:Argonia.esp` |
| ours | DialogResponses | new |  `000B1E:Argonia.esp` |
| ours | DialogResponses | new |  `000B3A:Argonia.esp` |
| ours | DialogResponses | new |  `000B75:Argonia.esp` |
| ours | DialogResponses | new |  `000B7E:Argonia.esp` |
| ours | DialogResponses | new |  `000B69:Argonia.esp` |
| ours | DialogResponses | new |  `000B4F:Argonia.esp` |
| ours | DialogResponses | new |  `000B38:Argonia.esp` |
| ours | DialogResponses | new |  `000B6E:Argonia.esp` |
| ours | DialogResponses | new |  `000B44:Argonia.esp` |
| ours | DialogResponses | new |  `000B5D:Argonia.esp` |
| ours | DialogResponses | new |  `000B4A:Argonia.esp` |
| ours | DialogResponses | new |  `000B5F:Argonia.esp` |
| ours | DialogResponses | new |  `000B57:Argonia.esp` |
| ours | DialogResponses | new |  `000B64:Argonia.esp` |
| ours | DialogResponses | new |  `000B2F:Argonia.esp` |
| ours | DialogResponses | new |  `000B20:Argonia.esp` |
| ours | DialogResponses | new |  `000B67:Argonia.esp` |
| ours | DialogResponses | new |  `000B28:Argonia.esp` |
| ours | DialogResponses | new |  `000B1F:Argonia.esp` |
| ours | DialogResponses | new |  `000B4E:Argonia.esp` |
| ours | DialogResponses | new |  `000B2B:Argonia.esp` |
| ours | DialogResponses | new |  `000B1B:Argonia.esp` |
| ours | DialogResponses | new |  `000B52:Argonia.esp` |
| ours | DialogResponses | new |  `000B2A:Argonia.esp` |
| ours | DialogResponses | new |  `000B74:Argonia.esp` |
| ours | DialogResponses | new |  `000B51:Argonia.esp` |
| ours | DialogResponses | new |  `000B6B:Argonia.esp` |
| ours | DialogResponses | new |  `000B6D:Argonia.esp` |
| ours | DialogResponses | new |  `000B6F:Argonia.esp` |
| ours | DialogResponses | new |  `000B56:Argonia.esp` |
| ours | DialogResponses | new |  `000B3D:Argonia.esp` |
| ours | DialogResponses | new |  `000B7C:Argonia.esp` |
| ours | DialogResponses | new |  `000B79:Argonia.esp` |
| ours | DialogResponses | new |  `000B3B:Argonia.esp` |
| ours | DialogResponses | new |  `000B39:Argonia.esp` |
| ours | DialogResponses | new |  `000B29:Argonia.esp` |
| ours | DialogResponses | new |  `000B45:Argonia.esp` |
| ours | DialogResponses | new |  `000B37:Argonia.esp` |
| ours | DialogResponses | new |  `000B27:Argonia.esp` |
| ours | DialogResponses | new |  `000B46:Argonia.esp` |
| ours | DialogResponses | new |  `000B3F:Argonia.esp` |
| ours | DialogResponses | new |  `000B2E:Argonia.esp` |
| ours | DialogResponses | new |  `000B1C:Argonia.esp` |
| ours | DialogResponses | new |  `000B78:Argonia.esp` |
| ours | DialogResponses | new |  `000B32:Argonia.esp` |
| ours | DialogResponses | new |  `000B34:Argonia.esp` |
| ours | DialogResponses | new |  `000B76:Argonia.esp` |
| ours | DialogResponses | new |  `000B5E:Argonia.esp` |
| ours | DialogResponses | new |  `000B25:Argonia.esp` |
| ours | DialogResponses | new |  `000B3E:Argonia.esp` |
| ours | DialogResponses | new |  `000B22:Argonia.esp` |
| ours | DialogResponses | new |  `000B71:Argonia.esp` |
| ours | DialogResponses | new |  `000B42:Argonia.esp` |
| ours | DialogResponses | new |  `000B66:Argonia.esp` |
| ours | DialogResponses | new |  `000B1D:Argonia.esp` |
| ours | DialogResponses | new |  `000B31:Argonia.esp` |
| ours | DialogResponses | new |  `000B7A:Argonia.esp` |
| ours | DialogResponses | new |  `000B35:Argonia.esp` |
| ours | DialogResponses | new |  `000B33:Argonia.esp` |
| ours | DialogResponses | new |  `000B59:Argonia.esp` |
| ours | DialogResponses | new |  `000B55:Argonia.esp` |
| ours | DialogResponses | new |  `000B53:Argonia.esp` |
| ours | DialogResponses | new |  `000B7B:Argonia.esp` |
| ours | DialogResponses | new |  `000B23:Argonia.esp` |
| ours | DialogResponses | new |  `000B4C:Argonia.esp` |
| ours | DialogResponses | new |  `000B26:Argonia.esp` |
| ours | DialogResponses | new |  `000B48:Argonia.esp` |
| ours | DialogResponses | new |  `000B18:Argonia.esp` |
| ours | DialogResponses | new |  `000B73:Argonia.esp` |
| ours | DialogResponses | new |  `000B2C:Argonia.esp` |
| ours | DialogResponses | new |  `000B77:Argonia.esp` |
| ours | DialogResponses | new |  `000B68:Argonia.esp` |
| ours | DialogResponses | new |  `000B6C:Argonia.esp` |
| ours | DialogResponses | new |  `000B30:Argonia.esp` |
| ours | DialogResponses | new |  `000B49:Argonia.esp` |
| ours | DialogResponses | new |  `000B62:Argonia.esp` |
| ours | DialogResponses | new |  `000B19:Argonia.esp` |
| ours | DialogResponses | new |  `000B1A:Argonia.esp` |
| ours | DialogResponses | new |  `000B50:Argonia.esp` |
| ours | DialogResponses | new |  `000B4B:Argonia.esp` |
| ours | DialogResponses | new |  `000B65:Argonia.esp` |
| ours | DialogResponses | new |  `000B16:Argonia.esp` |
| ours | DialogResponses | new |  `000B61:Argonia.esp` |
| ours | DialogResponses | new |  `000B60:Argonia.esp` |
| ours | DialogResponses | new |  `000B17:Argonia.esp` |
| ours | DialogResponses | new |  `000B5B:Argonia.esp` |
| ours | DialogResponses | new |  `000B70:Argonia.esp` |
| ours | DialogResponses | new |  `000B54:Argonia.esp` |
| ours | DialogResponses | new |  `000B2D:Argonia.esp` |
| ours | DialogResponses | new |  `000B43:Argonia.esp` |
| ours | DialogResponses | new |  `000B58:Argonia.esp` |
| ours | DialogResponses | new |  `000B13:Argonia.esp` |
| ours | DialogResponses | new |  `000B63:Argonia.esp` |
| ours | DialogResponses | new |  `000B14:Argonia.esp` |
| ours | DialogResponses | new |  `000B7D:Argonia.esp` |
| ours | DialogResponses | new |  `000B6A:Argonia.esp` |
| ours | DialogResponses | new |  `000B5A:Argonia.esp` |
| ours | DialogResponses | new |  `000B41:Argonia.esp` |
| ours | DialogResponses | new |  `000B5C:Argonia.esp` |
| ours | DialogResponses | new |  `000B47:Argonia.esp` |
| ours | DialogResponses | new |  `000B15:Argonia.esp` |
| ours | DialogResponses | new |  `000B36:Argonia.esp` |
| ours | DialogResponses | new |  `000B3C:Argonia.esp` |
| ours | DialogResponses | new |  `000B72:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_YieldTalk `000D80:Argonia.esp` |
| ours | DialogResponses | new |  `000D83:Argonia.esp` |
| ours | DialogResponses | new |  `000D82:Argonia.esp` |
| ours | DialogResponses | new |  `000D81:Argonia.esp` |
| ours | DialogResponses | new |  `000D86:Argonia.esp` |
| ours | DialogResponses | new |  `000D85:Argonia.esp` |
| ours | DialogResponses | new |  `000D84:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ05_BasinTopic `000DEB:Argonia.esp` |
| ours | DialogResponses | new |  `000DE7:Argonia.esp` |
| ours | DialogResponses | new |  `000DE9:Argonia.esp` |
| ours | DialogResponses | new |  `000DE8:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_YieldPay `000D88:Argonia.esp` |
| ours | DialogResponses | new |  `000D8B:Argonia.esp` |
| ours | DialogResponses | new |  `000D8A:Argonia.esp` |
| ours | DialogResponses | new |  `000D89:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_Break `000D7B:Argonia.esp` |
| ours | DialogResponses | new |  `000D7D:Argonia.esp` |
| ours | DialogResponses | new |  `000D7E:Argonia.esp` |
| ours | DialogResponses | new |  `000D7C:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_TopicHandOverNeeta `000CBD:Argonia.esp` |
| ours | DialogResponses | new |  `000CBF:Argonia.esp` |
| ours | DialogResponses | new |  `000CBE:Argonia.esp` |
| ours | DialogResponses | new |  `000CC0:Argonia.esp` |
| ours | quest | new | ARG_MQ01 `000E00:Argonia.esp` |
| ours | quest | new | ARG_BC02 `000D0A:Argonia.esp` |
| ours | quest | new | ARG_BlockTestEnd `000804:Argonia.esp` |
| ours | quest | new | ARG_MQ05 `000D8D:Argonia.esp` |
| ours | quest | new | ARG_MQ03 `000E01:Argonia.esp` |
| ours | quest | new | ARG_BC03 `000D5B:Argonia.esp` |
| ours | quest | new | ARG_TG01 `000C4F:Argonia.esp` |
| ours | quest | new | ARG_TG02 `000C50:Argonia.esp` |
| ours | quest | new | ARG_BlockTest `000803:Argonia.esp` |
| ours | quest | new | ARG_BC01 `000CDD:Argonia.esp` |
| ours | quest | new | ARG_Opening `000801:Argonia.esp` |
| ours | quest | new | ARG_Talk `000833:Argonia.esp` |
| ours | quest | new | ARG_LQ25 `000C35:Argonia.esp` |
| ours | quest | new | ARG_LQ30 `000C14:Argonia.esp` |
| ours | quest | new | ARG_MQ04 `000D8C:Argonia.esp` |
| ours | Package | new | ARG_TG01_ThiefEvening `000C78:Argonia.esp` |
| ours | Package | new | ARG_TG01_FriendBench `000C7A:Argonia.esp` |
| ours | Package | new | ARG_BC01_DebtorFollow `000CEB:Argonia.esp` |
| ours | Package | new | ARG_BC01_PatronAtLanding `000CEA:Argonia.esp` |
| ours | Package | new | ARG_MQ01_DeeshDuunFollows `000E58:Argonia.esp` |
| ours | Package | new | ARG_MQ01_CuttersLeave `000E56:Argonia.esp` |
| ours | Package | new | ARG_MQ01_MarchToFire `000E54:Argonia.esp` |
| ours | Package | new | ARG_BC02_MotherFollow `000D23:Argonia.esp` |
| ours | Package | new | ARG_BC02_SpeakerFollow `000D21:Argonia.esp` |
| ours | Package | new | ARG_BT_WalkPackage `000819:Argonia.esp` |
| ours | Package | new | ARG_MQ05_EiTujaGoPost `000DE6:Argonia.esp` |
| ours | Package | new | ARG_MQ01_SalSeiFollows `000E57:Argonia.esp` |
| ours | Package | new | ARG_MQ04_PaysLateNight `000DB5:Argonia.esp` |
| ours | Package | new | ARG_BC02_KillerFollow `000D22:Argonia.esp` |
| ours | Package | new | ARG_MQ05_KaskaGoPost `000DE5:Argonia.esp` |
| ours | Package | new | ARG_MQ01_LeaderLeaves `000E55:Argonia.esp` |
| ours | Package | new | ARG_TG01_ThiefDay `000C77:Argonia.esp` |
| ours | Package | new | ARG_TG01_ThiefSleep `000C79:Argonia.esp` |
| ours | VoiceType | new | ARG_TalkSilentVoice `000834:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_DangerBranch `000931:Argonia.esp` |
| ours | DialogBranch | new | ARG_LQ25_KeepQuietBranch `000C4A:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ03_TheAttackBranch `000EA0:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ03_TheBoatBranch `000E98:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_SomeoneBranch `000B11:Argonia.esp` |
| ours | DialogBranch | new | ARG_BT_Branch40 `000827:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ04_VillageBranch `000DBF:Argonia.esp` |
| ours | DialogBranch | new | ARG_BT_Branch50 `00082A:Argonia.esp` |
| ours | DialogBranch | new | ARG_BT_Branch90 `000831:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG01_TopicTestBranch `000C80:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_DirectionsBranch `00093C:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ05_TellNisswoBranch `000DFE:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ03_TheOfferBranch `000EB3:Argonia.esp` |
| ours | DialogBranch | new | ARG_LQ30_TheBasinBranch `000C26:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ05_BasinBranch `000DEA:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_LootBranch `000A18:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG01_TopicDoorBranch `000C7B:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_AnswerDefyBranch `000E62:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_TopicSellBeadsBranch `000CD5:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG01_TopicReturnBranch `000C95:Argonia.esp` |
| ours | DialogBranch | new | ARG_BT_Branch20 `000824:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_YieldPayBranch `000D87:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_TheTokensBranch `000D70:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_BrawlBranch `000D75:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_TopicClaimFigurineBranch `000CAA:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG01_TopicBedBranch `000C85:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_HarvestBranch `000999:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_TopicJobBranch `000CA5:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_AnswerSilentBranch `000E5F:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_SelfBranch `000A8F:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_TopicHandOverNeetaBranch `000CBC:Argonia.esp` |
| ours | DialogBranch | new | ARG_BT_Branch50Never `00082D:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ05_WordBranch `000ECB:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_AnswerNameBranch `000E5C:Argonia.esp` |
| ours | DialogBranch | new | ARG_LQ30_WalkedOutBranch `000C1E:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_AdviceBranch `000924:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_ComeMotherBranch `000D3E:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_TheFireBranch `000D24:Argonia.esp` |
| ours | DialogBranch | new | ARG_LQ30_ComeBackBranch `000C2B:Argonia.esp` |
| ours | DialogBranch | new | ARG_LQ25_TellCaptainBranch `000C45:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_YieldTalkBranch `000D7F:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_SecretBranch `000A85:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_TopicSellCharmBranch `000CD0:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ05_TellMinderBranch `000DF9:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_TheWaterBranch `000E69:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ03_TheNightBranch `000EA8:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_TopicClaimBeadsBranch `000CB7:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_TheGateBranch `000D2C:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_TheRollBranch `000E59:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ04_CutBranch `000DCF:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_BringDownBranch `000D01:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ03_RefuseOathBranch `000EBD:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_TopicSellFigurineBranch `000CCB:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_LastSeasonBranch `000D63:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_TopicHandOverOkanBranch `000CC1:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_HereBranch `0009AC:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_TradeBranch `000B7F:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_CutLooseBranch `000CF9:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_ComeKillerBranch `000D39:Argonia.esp` |
| ours | DialogBranch | new | ARG_LQ25_TheBeastBranch `000C3D:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ05_QuarrelBranch `000DEF:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ05_WatchBranch `000DF4:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_LoreBranch `000A1E:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_TheSeasonBranch `000D6B:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_TheBookBranch `000CF4:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_TopicClaimCharmBranch `000CAF:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_BreakBranch `000D7A:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ03_TakeOathBranch `000EB8:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ04_BoatBranch `000DC7:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG01_TopicGiveBackBranch `000C8D:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG01_TopicWelcomeBranch `000C9D:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_TopicHandOverDarBranch `000CC6:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_TheHireBranch `000E65:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_ComeSpeakerBranch `000D34:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_LetByBranch `000D43:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_RumoursBranch `000A7A:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_TheEstateBranch `000CEC:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_ServicesBranch `000B08:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_TheMarchBranch `000E6C:Argonia.esp` |
| ours | Scene | new | ARG_BT_Scene `000822:Argonia.esp` |
| intro | quest | replaced: one stage 0 with one empty log entry, which its fragment (ARG_QF_MQ101) binds to (no entry, no fragment: New Game stayed on the menu, 2026-11-06); the fragment moves the player to ARG_OpeningMarker, starts ARG_Opening and stops MQ101; no aliases, scenes or Helgen stages | MQ101 `03372B:Skyrim.esm` |
| opening | worldspace | BM&V's record kept, our marker in its persistent cell | BlackMarsh `23D689:Black Marsh.esm` |
| music | worldspace | ZNAM `0C76D3:Skyrim.esm`, the rest kept | BlackMarsh2 `0D6960:Black Marsh.esm` |
| map | worldspace | MNAM pan box NW(-17,16) SE(16,-15), the rest kept | BlackMarsh2 `0D6960:Black Marsh.esm` |
| music | worldspace | ZNAM `094BDD:Skyrim.esm`, the rest kept | UnderDark `0B8BDD:Black Marsh North.esp` |
| music | worldspace | ZNAM `0C76D3:Skyrim.esm`, the rest kept | BlackMarshNorth `005900:Black Marsh North.esp` |
| map | worldspace | MNAM pan box NW(-17,16) SE(16,-16), the rest kept | BlackMarshNorth `005900:Black Marsh North.esp` |
| music | worldspace | ZNAM `0C76D3:Skyrim.esm`, the rest kept | BlackMarsh `23D689:Black Marsh.esm` |
| map | worldspace | MNAM pan box NW(-18,4) SE(18,-25), the rest kept | BlackMarsh `23D689:Black Marsh.esm` |
| music | worldspace | ZNAM `06D546:Skyrim.esm`, the rest kept | Valenwood `005900:Valenwood.esp` |
| map | worldspace | MNAM pan box NW(-16,19) SE(17,-16), the rest kept | Valenwood `005900:Valenwood.esp` |
| map | map marker | name only: Lilmoth | `0934A4:Black Marsh North.esp` |
| map | map marker | name only: Southern Morrowind Pass | `083283:Black Marsh North.esp` |
| main quest | quest | Start Game Enabled off | MQ00 `01C5D9`, MQ103 `0D0800` |
| civil war | quest | Start Game Enabled off | CW `019E53`, CWObj `029940`, CW00A `0D3C5F`, CW00B `0E1B5A`, CWSiegeQuickStart `09726A`, CWMissionQuickStart `107987` |
| thieves guild | quest | Start Game Enabled off | TG00 `021556`, TGPre `0B2976`, TGCrown `09DD77`, TGCrownMisc `06D585`, TGRQueue `09EE78`, TGTQ01Handler `1093E4`, TG04EECHandler `1007FC`, TGREnablerHandler `103395` |
| dark brotherhood | quest | Start Game Enabled off | DB01 `01EA50`, DB01Misc `01EA4F`, DarkBrotherhood `01EA5C`, DBOlavaReadingTreasureObjective `02E656` |
| guild and faction openers | quest | Start Game Enabled off | MG01 `01F251`, MGRShell `028A55`, MGRArniel01 `06A086`, MGRitual01 `0A4E82`, MGRitual02 `0B3233`, MGRitual03 `099F27`, MGRitual05 `0D0755`, C00 `04B2D9`, C00GiantAttack `0C97D9`, C00JorrvaskrFight `0BC0BD`, CR00 `01CEEF`, CompanionsRejoinQuest `0880E1`, CompanionsBladeFragmentTracking `108059`, T01 `023B6C`, t02 `0211D5`, T03 `01C48E`, T01DegaineFavor `0D45F4`, VC01 `05C625`, NN01 `0C9BA0` |
| misc and daedric openers | quest | Start Game Enabled off | MS01 `018B4B`, MS01MiscObjectives `0D1958`, MS03 `01DA3C`, MS05 `053511`, MS05Start `042868`, MS05Rumor `0D789C`, MS06Start `093807`, MS06Rumor `0D789A`, MS07 `023A64`, MS07Rumor `0AA9A9`, MS08 `01CF25`, MS09 `01CF26`, MS10 `01DBFC`, MS11PreEssentializing `0AF269`, MS12 `02C258`, MS13 `039645`, MS13LucanCamillaScene `038386`, MS14 `025F3E`, DA01 `028AD6`, DA01Intro `092E25`, DA01dunIlinaltasDeepQST `089CD1`, DA03Start `0D7939`, DA04 `02D512`, DA05 `02A49A`, DA07 `0240B8`, DA08 `04A37B`, DA10MiscObjective `0DC53C`, DA11 `02C358`, DA15 `02AC68`, DA15Rumor `0D7897`, DA16 `0242AF`, DA16MiniScenes `0E16CC`, SolitudeOpening `0B2FD9`, DarkwaterCrossingDerkeethusRescueQuest `076B4A` |
| dawnguard | quest | Start Game Enabled off | DLC1Init `002C09`, DLC1VQ00 `00D90E`, DLC1Radiant `004C1C`, DLC1RadiantDisguised `01574C`, DLC1RV07Post `01434C` |
| dragonborn | quest | Start Game Enabled off | DLC2Init `016E02`, DLC2MQ00 `026242`, DLC2RRArrivalScene `02ADDA`, DLC2CultistOrdersQuestObjectHandler `038FB1` |
| hearthfire | quest | Start Game Enabled off | BYOHHouseFalkreath `00305E`, BYOHHouseHjaalmarch `00BE09`, BYOHHousePale `010BEE` |
| creation club | quest | Start Game Enabled off | ccBGSSSE001_Fish_MQ1 `0009DE`, ccBGSSSE001_Crab_MQ1 `0009D4`, ccBGSSSE001_RadiantQuests `000E56`, ccBGSSSE025_QuestA `000912`, ccBGSSSE025_StaadaQuest `198277`, ccBGSSSE025_MiscQuest_AmberMadnessGear `000C4D`, ccBGSSSE025_MiscQuest_Nerveshatter `0010BF` |
| mq01-held | quest | Start Game Enabled off, started by MQ03's ending | AANEWQuestM `0F0F3E`, 01Captain `03B21E`, 0MainQuest1 `0BCC51` |
| civil war | story-manager node | gated off | CWBranchNode `0236A1`, CWGarrisonNode `03844E`, CWActorHelloNode `06B19B`, CWActorDialogueNode `06B19D`, CWActorDialogueSoldiersNode `06B19E`, CWChangeLocationScenes `0D5176` |
| world interactions and couriers | story-manager node | gated off | WIPlayerRemoveItemNodes `018966`, WIKillActorMournerNodeSHARES `01E490`, WIKillEventsBranchNode `01E491`, WIChangeLocationThiefNode `023F1B`, WISkillIncreaseNode `02D387`, (no editor id) `0F6F1C`, WINewVoicePowerNode `02D38A`, WIAddItemNodes `035B5C`, WIAssautRememberNode `037FBE`, WIDeadBodyNode `03833E`, WICourierNodeSharesEvent `039FBD`, WIScriptEventBranchNode `06D1E6`, WICastMagicEventNode `070216`, WIActorDialogueBranchNode `070222`, WICastMagicNonHostileReactionNode `0A8ABA`, WIKillRunToCorpseSHARES `0ADC8E`, WIFlatterQuestNode `0AE003`, WIGreetingNodeSHARES `0C791B`, WITavernQuestNodeSHARES `0DEE94`, WIAssaultNode `0A39C0`, WIChangeLocationNode `0A39C6`, WICraftItemBranchNode `04F593` |
| main quest and dragons | story-manager node | gated off | MQCallDragonNode `046B8D`, MQResurrectDragonNode `0B39A5`, MQGreybeardCallNode `10EC64`, VoiceoftheSkyNode `10D9F0`, HighHrothgarTrainingNode `10C044`, SkyHavenSparringNode `1092E3`, SovngardeSparringNode `017045`, MainQuestPartyScenes `0BC3EE`, MQSovngardeBranch `108426`, MQSovngardeHallofHeroesNode `0F0A16`, SkyHavenTempleScenesNode `1092DE` |
| guilds | story-manager node | gated off | MagesGuildRadiantNode `028A4C`, MGSuspension `0B1145`, ThievesGuildRadiantNode `0609AD`, TG00QuestNode `0B882C`, TG01KillMonitor `0EAFA6`, TG03KillMonitor `0EAFA7`, TG04KillMonitor `0EAFA8`, TGHeadquartersScenes `04BCCC`, DBSuspensionAssault `02E3FF`, DBSanctuaryScenes `034D02`, DB03JailNode `08D5DC`, CompanionsNode `09002E`, CompanionsRadiantNode `0BFC76`, CompanionsSingleCombatNode `0880F2`, MG01ShoutNode `0B812F`, CompanionsJorrvaskrTheftNode `10FBF4` |
| radiant, misc and bounties | story-manager node | gated off | QuestNode `090028`, FreeformQuestsNode `09002A`, IntroScenesNode `09002B`, FavorsNode `0B2440`, FavorOrcsIntroNode `0763EC`, FavorSimpleDrunksNode `0B0274`, MakeFriendsNode `087E27`, MS08ArgueNode `07F3FD`, DA02KillFriendNodeOBSOLETE `04D918`, DA09IncreaseLevelNodeSHARES `09E1AD`, DA02IncreaseLevelNodeSHARES `09E1AF`, DA06IncreaseLevelNodeSHARES `0A0E73`, DA13IncreaseLevelNodeSHARES `0C4CC5`, MS04IncreaseLevelNodeSHARES `0BD721`, MS06IncreaseLevelNodeSHARES `0D91D2`, DA08KickerNode `0DC9E1`, DA08KillFriendNode `10FAEF`, DA10HauntingNode `0A9B1A`, DA02BluePalaceDeadBodyNode `0B48FC`, FFR09KickerNode `10EA41`, ReachcliffCaveScenes `0A71AB`, BQBranchNodeSHARES `0CBA9F`, WEQuestNode `0896A8`, WE100ObjQuestsNode `0A17B2` |
| dawnguard | story-manager node | gated off | DLC1ScoutQuestNode `0041D3`, DLC1RadiantDisguisedVampireLordQuestNode `004210`, DLC1RadiantQuestNode `004C21`, DLC1RadiantKillActorMonitorQuestNode `004C2F`, DLC1RV01AssaultMonitorQuestNode `004C31`, DLC1HunterBaseScenes `004E25`, DLC1VampireBaseScenes `004E26`, DLC1LD_AetherialItemsNode `00D00E`, DLC1VQ00Node `00D911`, DLC1VQ00VampireAttackNodePM `010DE3`, DLC1VQ00VampireAttackNodeAM `010DE4`, DLC1EclipseAttackNode `0162A0` |
| dragonborn | story-manager node | gated off | DLC2NelothRadiantQuests `01B65E`, DLC2WENode `01E7D9`, DLC2TelMithrynBranchNode `020686`, DLC2dunHaknirTreasureNodeSHARES `024003`, DLC2PillarDestroyedNode `028667`, DLC2EbonyWarriorNode `02C49F`, DLC2WEPriorityQuests `0331C1`, DLC2RRMineNode `03332D`, DLC2CultistAmbushNode `035472`, DLC2AshSpawnAttackNode `03842C` |
| hearthfire letters | story-manager node | gated off | BYOHHouseChangeLocationNode `00308C`, BYOHAdoptionQuestNode `003F7A`, BYOHHouseNode `010A49` |
| creation club | story-manager node | gated off | BGSSSE025_WEQuestNode `220E6E` |

Worldspace BlackMarsh: the winner's record (Black Marsh North.esp), a master. ARG_OpeningMarker at 30901, -2903, 3: on navmesh `07EEF8` (Black Marsh.esm, the winner) triangle 14, its height 2.7.

Compared with the load order's winners (40 plugins): stage, alias, condition and script counts, flags, parent and sibling links equal but for the change.

Read-back: every override carries its change (MQ101 one stage with its log entry; no quest named here is Start Game Enabled or keeps text; every node's first condition is the gate).
