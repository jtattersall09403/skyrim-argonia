# Argonia.esp: every record, read back from the built plugin

Written by `make plugin-check` (tools/ArgoniaPlugin `list`) from `out/Argonia.esp`; masters: Skyrim.esm, Update.esm, Dawnguard.esm, HearthFires.esm, Dragonborn.esm, ccBGSSSE001-Fish.esm, ccBGSSSE025-AdvDSGS.esm, unofficial skyrim special edition patch.esp, Black Marsh.esm, Black Marsh North.esp, Valenwood.esp, RimExecutionHitSA.esp, Magic.esp, Magistrate Levitate.esp. 722 records. Quest overrides keep the winning record (aliases, stages, scripts) with Start Game Enabled off and their player-visible text removed; story-manager overrides gain a first condition `GetGlobalValue ARG_VanillaStoryManager == 1` (the global is 0), so nothing under the node starts. The why is in `tools/ArgoniaPlugin/shutdown.json` and `mods/allowed-quests.json`.

| Group | Kind | Change | Records (editor id, form id) |
|---|---|---|---|
| ours | global | new | ARG_BT_RaceHits `000816:Argonia.esp` |
| ours | global | new | ARG_BT_Global `000815:Argonia.esp` |
| ours | global | new | ARG_VanillaStoryManager `000800:Argonia.esp` |
| ours | global | new | ARG_BT_RaceRuns `000817:Argonia.esp` |
| ours | Faction | new | ARG_BT_Faction `000818:Argonia.esp` |
| ours | Faction | new | ARG_VendorLooksAtBooks `0008ED:Argonia.esp` |
| ours | MagicEffect | new | ARG_NoHealthRegenEffect `0008F7:Argonia.esp` |
| ours | Spell | new | ARG_NoHealthRegen `0008F8:Argonia.esp` |
| ours | Container | new | ARG_VendorLooksAtBooksChest `0008EE:Argonia.esp` |
| ours | MiscItem | new | ARG_BT_Token `000810:Argonia.esp` |
| ours | Npc | new | ARG_Talker_03E418 `0008EC:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7C9 `0008F1:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A209 `0008E9:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01512D `0008DD:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0616E8 `0008F6:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7CC `0008F4:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7CD `0008F5:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A208 `0008E8:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A1F2 `0008E4:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A1E9 `0008E1:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A1ED `0008E2:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A205 `0008E6:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A204 `0008E5:Argonia.esp` |
| ours | Npc | new | ARG_Talker_00FF4E `0008D9:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01512C `0008DC:Argonia.esp` |
| ours | Npc | new | ARG_Talker_00AC8E `0008D8:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01512B `0008DB:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7C8 `0008F0:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7CA `0008F2:Argonia.esp` |
| ours | Npc | new | ARG_BT_Crab `000807:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A206 `0008E7:Argonia.esp` |
| ours | Npc | new | ARG_Talker_03E415 `0008EB:Argonia.esp` |
| ours | Npc | new | ARG_Talker_00FF4F `0008DA:Argonia.esp` |
| ours | Npc | new | ARG_Talker_015195 `0008E0:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A1F1 `0008E3:Argonia.esp` |
| ours | Npc | new | ARG_Talker_015193 `0008DF:Argonia.esp` |
| ours | Npc | new | ARG_Talker_03E413 `0008EA:Argonia.esp` |
| ours | Npc | new | ARG_BT_Walker `000806:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7CB `0008F3:Argonia.esp` |
| ours | Npc | new | ARG_BT_Keeper `000805:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01512E `0008DE:Argonia.esp` |
| ours | Key | new | ARG_BT_Key `000812:Argonia.esp` |
| ours | PlacedNpc | new | ARG_BT_WalkerRef `00080B:Argonia.esp` |
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
| ours | XMarker reference | new | ARG_VendorLooksAtBooksChestRef `0008EF:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Lore `00087D:Argonia.esp` |
| ours | DialogResponses | new |  `000884:Argonia.esp` |
| ours | DialogResponses | new |  `00088A:Argonia.esp` |
| ours | DialogResponses | new |  `00088B:Argonia.esp` |
| ours | DialogResponses | new |  `000880:Argonia.esp` |
| ours | DialogResponses | new |  `000882:Argonia.esp` |
| ours | DialogResponses | new |  `000883:Argonia.esp` |
| ours | DialogResponses | new |  `000887:Argonia.esp` |
| ours | DialogResponses | new |  `000881:Argonia.esp` |
| ours | DialogResponses | new |  `000885:Argonia.esp` |
| ours | DialogResponses | new |  `00087F:Argonia.esp` |
| ours | DialogResponses | new |  `000888:Argonia.esp` |
| ours | DialogResponses | new |  `000886:Argonia.esp` |
| ours | DialogResponses | new |  `00087E:Argonia.esp` |
| ours | DialogResponses | new |  `000889:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Loot `000877:Argonia.esp` |
| ours | DialogResponses | new |  `000878:Argonia.esp` |
| ours | DialogResponses | new |  `000879:Argonia.esp` |
| ours | DialogResponses | new |  `00087B:Argonia.esp` |
| ours | DialogResponses | new |  `00087A:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Topic40 `000828:Argonia.esp` |
| ours | DialogResponses | new |  `000826:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Self `000897:Argonia.esp` |
| ours | DialogResponses | new |  `0008A3:Argonia.esp` |
| ours | DialogResponses | new |  `00089F:Argonia.esp` |
| ours | DialogResponses | new |  `0008A9:Argonia.esp` |
| ours | DialogResponses | new |  `0008B3:Argonia.esp` |
| ours | DialogResponses | new |  `0008AD:Argonia.esp` |
| ours | DialogResponses | new |  `0008B1:Argonia.esp` |
| ours | DialogResponses | new |  `0008B5:Argonia.esp` |
| ours | DialogResponses | new |  `0008A5:Argonia.esp` |
| ours | DialogResponses | new |  `0008AA:Argonia.esp` |
| ours | DialogResponses | new |  `0008B4:Argonia.esp` |
| ours | DialogResponses | new |  `0008AB:Argonia.esp` |
| ours | DialogResponses | new |  `0008A4:Argonia.esp` |
| ours | DialogResponses | new |  `00089E:Argonia.esp` |
| ours | DialogResponses | new |  `0008B2:Argonia.esp` |
| ours | DialogResponses | new |  `0008AE:Argonia.esp` |
| ours | DialogResponses | new |  `0008B0:Argonia.esp` |
| ours | DialogResponses | new |  `0008A1:Argonia.esp` |
| ours | DialogResponses | new |  `00089B:Argonia.esp` |
| ours | DialogResponses | new |  `0008AC:Argonia.esp` |
| ours | DialogResponses | new |  `00089C:Argonia.esp` |
| ours | DialogResponses | new |  `0008A8:Argonia.esp` |
| ours | DialogResponses | new |  `00089A:Argonia.esp` |
| ours | DialogResponses | new |  `000898:Argonia.esp` |
| ours | DialogResponses | new |  `0008AF:Argonia.esp` |
| ours | DialogResponses | new |  `0008A2:Argonia.esp` |
| ours | DialogResponses | new |  `000899:Argonia.esp` |
| ours | DialogResponses | new |  `0008A0:Argonia.esp` |
| ours | DialogResponses | new |  `0008A6:Argonia.esp` |
| ours | DialogResponses | new |  `00089D:Argonia.esp` |
| ours | DialogResponses | new |  `0008A7:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Scene1 `00081A:Argonia.esp` |
| ours | DialogResponses | new |  `00081B:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Topic50Never `00082E:Argonia.esp` |
| ours | DialogResponses | new |  `00082C:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Services `0008B7:Argonia.esp` |
| ours | DialogResponses | new |  `0008B9:Argonia.esp` |
| ours | DialogResponses | new |  `0008B8:Argonia.esp` |
| ours | DialogResponses | new |  `0008BA:Argonia.esp` |
| ours | DialogResponses | new |  `0008BC:Argonia.esp` |
| ours | DialogResponses | new |  `0008BB:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Advice `000836:Argonia.esp` |
| ours | DialogResponses | new |  `000837:Argonia.esp` |
| ours | DialogResponses | new |  `000839:Argonia.esp` |
| ours | DialogResponses | new |  `000838:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Scene4 `000820:Argonia.esp` |
| ours | DialogResponses | new |  `000821:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Trade `0008D3:Argonia.esp` |
| ours | DialogResponses | new |  `0008D4:Argonia.esp` |
| ours | DialogResponses | new |  `0008D5:Argonia.esp` |
| ours | DialogResponses | new |  `0008D6:Argonia.esp` |
| ours | DialogResponses | new |  `0008D7:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Topic50 `00082B:Argonia.esp` |
| ours | DialogResponses | new |  `000829:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Scene2 `00081C:Argonia.esp` |
| ours | DialogResponses | new |  `00081D:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Harvest `000855:Argonia.esp` |
| ours | DialogResponses | new |  `00085D:Argonia.esp` |
| ours | DialogResponses | new |  `000860:Argonia.esp` |
| ours | DialogResponses | new |  `00085B:Argonia.esp` |
| ours | DialogResponses | new |  `000857:Argonia.esp` |
| ours | DialogResponses | new |  `000856:Argonia.esp` |
| ours | DialogResponses | new |  `00085C:Argonia.esp` |
| ours | DialogResponses | new |  `000861:Argonia.esp` |
| ours | DialogResponses | new |  `000862:Argonia.esp` |
| ours | DialogResponses | new |  `00085F:Argonia.esp` |
| ours | DialogResponses | new |  `00085E:Argonia.esp` |
| ours | DialogResponses | new |  `000859:Argonia.esp` |
| ours | DialogResponses | new |  `000858:Argonia.esp` |
| ours | DialogResponses | new |  `00085A:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Rumours `00088D:Argonia.esp` |
| ours | DialogResponses | new |  `000890:Argonia.esp` |
| ours | DialogResponses | new |  `00088E:Argonia.esp` |
| ours | DialogResponses | new |  `00088F:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Secret `000892:Argonia.esp` |
| ours | DialogResponses | new |  `000893:Argonia.esp` |
| ours | DialogResponses | new |  `000895:Argonia.esp` |
| ours | DialogResponses | new |  `000894:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Scene3 `00081E:Argonia.esp` |
| ours | DialogResponses | new |  `00081F:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Topic20 `000825:Argonia.esp` |
| ours | DialogResponses | new |  `000823:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Directions `000845:Argonia.esp` |
| ours | DialogResponses | new |  `000849:Argonia.esp` |
| ours | DialogResponses | new |  `000847:Argonia.esp` |
| ours | DialogResponses | new |  `00084D:Argonia.esp` |
| ours | DialogResponses | new |  `000850:Argonia.esp` |
| ours | DialogResponses | new |  `000853:Argonia.esp` |
| ours | DialogResponses | new |  `000846:Argonia.esp` |
| ours | DialogResponses | new |  `00084B:Argonia.esp` |
| ours | DialogResponses | new |  `00084F:Argonia.esp` |
| ours | DialogResponses | new |  `000852:Argonia.esp` |
| ours | DialogResponses | new |  `00084E:Argonia.esp` |
| ours | DialogResponses | new |  `000851:Argonia.esp` |
| ours | DialogResponses | new |  `00084C:Argonia.esp` |
| ours | DialogResponses | new |  `00084A:Argonia.esp` |
| ours | DialogResponses | new |  `000848:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Someone `0008BE:Argonia.esp` |
| ours | DialogResponses | new |  `0008CE:Argonia.esp` |
| ours | DialogResponses | new |  `0008CA:Argonia.esp` |
| ours | DialogResponses | new |  `0008C9:Argonia.esp` |
| ours | DialogResponses | new |  `0008C0:Argonia.esp` |
| ours | DialogResponses | new |  `0008CD:Argonia.esp` |
| ours | DialogResponses | new |  `0008BF:Argonia.esp` |
| ours | DialogResponses | new |  `0008CF:Argonia.esp` |
| ours | DialogResponses | new |  `0008C3:Argonia.esp` |
| ours | DialogResponses | new |  `0008C1:Argonia.esp` |
| ours | DialogResponses | new |  `0008C6:Argonia.esp` |
| ours | DialogResponses | new |  `0008D1:Argonia.esp` |
| ours | DialogResponses | new |  `0008C4:Argonia.esp` |
| ours | DialogResponses | new |  `0008D0:Argonia.esp` |
| ours | DialogResponses | new |  `0008C5:Argonia.esp` |
| ours | DialogResponses | new |  `0008CB:Argonia.esp` |
| ours | DialogResponses | new |  `0008CC:Argonia.esp` |
| ours | DialogResponses | new |  `0008C7:Argonia.esp` |
| ours | DialogResponses | new |  `0008C8:Argonia.esp` |
| ours | DialogResponses | new |  `0008C2:Argonia.esp` |
| ours | DialogTopic | new | ARG_BT_Topic90 `000832:Argonia.esp` |
| ours | DialogResponses | new |  `000830:Argonia.esp` |
| ours | DialogResponses | new |  `00082F:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Danger `00083B:Argonia.esp` |
| ours | DialogResponses | new |  `000841:Argonia.esp` |
| ours | DialogResponses | new |  `00083D:Argonia.esp` |
| ours | DialogResponses | new |  `00083C:Argonia.esp` |
| ours | DialogResponses | new |  `000842:Argonia.esp` |
| ours | DialogResponses | new |  `000843:Argonia.esp` |
| ours | DialogResponses | new |  `00083E:Argonia.esp` |
| ours | DialogResponses | new |  `000840:Argonia.esp` |
| ours | DialogResponses | new |  `00083F:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Here `000864:Argonia.esp` |
| ours | DialogResponses | new |  `00086C:Argonia.esp` |
| ours | DialogResponses | new |  `00086F:Argonia.esp` |
| ours | DialogResponses | new |  `00086A:Argonia.esp` |
| ours | DialogResponses | new |  `000865:Argonia.esp` |
| ours | DialogResponses | new |  `000873:Argonia.esp` |
| ours | DialogResponses | new |  `000872:Argonia.esp` |
| ours | DialogResponses | new |  `000870:Argonia.esp` |
| ours | DialogResponses | new |  `000867:Argonia.esp` |
| ours | DialogResponses | new |  `000866:Argonia.esp` |
| ours | DialogResponses | new |  `00086E:Argonia.esp` |
| ours | DialogResponses | new |  `000868:Argonia.esp` |
| ours | DialogResponses | new |  `000875:Argonia.esp` |
| ours | DialogResponses | new |  `000874:Argonia.esp` |
| ours | DialogResponses | new |  `000871:Argonia.esp` |
| ours | DialogResponses | new |  `00086D:Argonia.esp` |
| ours | DialogResponses | new |  `00086B:Argonia.esp` |
| ours | DialogResponses | new |  `000869:Argonia.esp` |
| ours | quest | new | ARG_BlockTestEnd `000804:Argonia.esp` |
| ours | quest | new | ARG_BlockTest `000803:Argonia.esp` |
| ours | quest | new | ARG_Opening `000801:Argonia.esp` |
| ours | quest | new | ARG_Talk `000833:Argonia.esp` |
| ours | Package | new | ARG_BT_WalkPackage `000819:Argonia.esp` |
| ours | VoiceType | new | ARG_TalkSilentVoice `000834:Argonia.esp` |
| ours | DialogBranch | new | ARG_BT_Branch40 `000827:Argonia.esp` |
| ours | DialogBranch | new | ARG_BT_Branch50 `00082A:Argonia.esp` |
| ours | DialogBranch | new | ARG_BT_Branch90 `000831:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_ServicesBranch `0008B6:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_RumoursBranch `00088C:Argonia.esp` |
| ours | DialogBranch | new | ARG_BT_Branch20 `000824:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_DirectionsBranch `000844:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_HarvestBranch `000854:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_AdviceBranch `000835:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_SomeoneBranch `0008BD:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_TradeBranch `0008D2:Argonia.esp` |
| ours | DialogBranch | new | ARG_BT_Branch50Never `00082D:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_SecretBranch `000891:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_LootBranch `000876:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_SelfBranch `000896:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_DangerBranch `00083A:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_HereBranch `000863:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_LoreBranch `00087C:Argonia.esp` |
| ours | Scene | new | ARG_BT_Scene `000822:Argonia.esp` |
| intro | quest | replaced: one stage 0 with one empty log entry, which its fragment (ARG_QF_MQ101) binds to (no entry, no fragment: New Game stayed on the menu, 2026-11-06); the fragment moves the player to ARG_OpeningMarker, starts ARG_Opening and stops MQ101; no aliases, scenes or Helgen stages | MQ101 `03372B:Skyrim.esm` |
| opening | worldspace | BM&V's record kept, our marker in its persistent cell | BlackMarsh `23D689:Black Marsh.esm` |
| map | worldspace | MNAM pan box NW(-17,16) SE(16,-15), the rest kept | BlackMarsh2 `0D6960:Black Marsh.esm` |
| map | worldspace | MNAM pan box NW(-17,16) SE(16,-16), the rest kept | BlackMarshNorth `005900:Black Marsh North.esp` |
| map | worldspace | MNAM pan box NW(-18,4) SE(18,-25), the rest kept | BlackMarsh `23D689:Black Marsh.esm` |
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
