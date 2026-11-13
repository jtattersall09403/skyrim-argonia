# Argonia.esp: every record, read back from the built plugin

Written by `make plugin-check` (tools/ArgoniaPlugin `list`) from `out/Argonia.esp`; masters: Skyrim.esm, Update.esm, Dawnguard.esm, HearthFires.esm, Dragonborn.esm, ccBGSSSE001-Fish.esm, ccBGSSSE025-AdvDSGS.esm, unofficial skyrim special edition patch.esp, Black Marsh.esm, Black Marsh North.esp, Valenwood.esp, RimExecutionHitSA.esp. 2524 records. Quest overrides keep the winning record (aliases, stages, scripts) with Start Game Enabled off and their player-visible text removed; story-manager overrides gain a first condition `GetGlobalValue ARG_VanillaStoryManager == 1` (the global is 0), so nothing under the node starts. The why is in `tools/ArgoniaPlugin/shutdown.json` and `mods/allowed-quests.json`.

| Group | Kind | Change | Records (editor id, form id) |
|---|---|---|---|
| ours | global | new | ARG_N_flag_mq03_tasted `8000E4:Argonia.esp` |
| ours | global | new | ARG_N_flag_tg01_desk_dead `80001E:Argonia.esp` |
| ours | global | new | ARG_N_flag_mq05_minders_hold `8000FD:Argonia.esp` |
| ours | global | new | ARG_N_number_test_counter `80003F:Argonia.esp` |
| ours | global | new | ARG_N_flag_mq01_reed_joined `8000DF:Argonia.esp` |
| ours | global | new | ARG_N_flag_bc02_settled `80023A:Argonia.esp` |
| ours | global | new | ARG_N_flag_main_thread_severed `8000E1:Argonia.esp` |
| ours | global | new | ARG_VanillaStoryManager `000800:Argonia.esp` |
| ours | global | new | ARG_N_flag_bc03_settled `800249:Argonia.esp` |
| ours | global | new | ARG_N_flag_mq04_reconciled `8000F3:Argonia.esp` |
| ours | global | new | ARG_N_flag_mq04_jars_to_reed `8000F4:Argonia.esp` |
| ours | global | new | ARG_N_flag_bc01_settled `80022B:Argonia.esp` |
| ours | global | new | ARG_N_flag_tg02_fence_dead `80002A:Argonia.esp` |
| ours | global | new | ARG_N_flag_tg01_fence_dead `80001F:Argonia.esp` |
| ours | global | new | ARG_N_flag_mq05_nisswo_read `8000FE:Argonia.esp` |
| ours | Faction | new | ARG_F_faction_veiled_reed `8000E0:Argonia.esp` |
| ours | Faction | new | ARG_F_faction_test_dock_hands `800040:Argonia.esp` |
| ours | Faction | new | ARG_F_faction_chainbreakers `80022C:Argonia.esp` |
| ours | Faction | new | ARG_VendorLooksAtBooks `000BCA:Argonia.esp` |
| ours | Faction | new | ARG_F_faction_night_reed_chapter `80001D:Argonia.esp` |
| ours | MagicEffect | new | ARG_NoHealthRegenEffect `000C16:Argonia.esp` |
| ours | Spell | new | ARG_NoHealthRegen `000C17:Argonia.esp` |
| ours | Armor | new | ARG_I_item_glass_bead_strand `800020:Argonia.esp` |
| ours | Armor | new | ARG_I_item_tg01_jasper_necklace `800010:Argonia.esp` |
| ours | Armor | new | ARG_I_thing_bc03_tokens `800248:Argonia.esp` |
| ours | Armor | new | ARG_I_item_tg02_neesak_charm `800022:Argonia.esp` |
| ours | Book | new | ARG_I_thing_bc01_her_leaf `800227:Argonia.esp` |
| ours | Book | new | ARG_I_thing_bc02_leaves `800237:Argonia.esp` |
| ours | Book | new | ARG_I_thing_bc01_false_leaf `80022A:Argonia.esp` |
| ours | Book | new | ARG_I_thing_bc03_book `800242:Argonia.esp` |
| ours | Book | new | ARG_I_thing_mq03_page `8000E3:Argonia.esp` |
| ours | Book | new | ARG_I_thing_bc03_list `800247:Argonia.esp` |
| ours | Book | new | ARG_I_thing_bc01_keeper_leaf `800228:Argonia.esp` |
| ours | Container | new | ARG_R_thing_tg01_strongbox_Cont `800218:Argonia.esp` |
| ours | Container | new | ARG_R_thing_mq03_sack_Cont `800216:Argonia.esp` |
| ours | Container | new | ARG_R_thing_bc02_strongbox_Cont `800239:Argonia.esp` |
| ours | Container | new | ARG_R_thing_tg02_lockbox_Cont `800219:Argonia.esp` |
| ours | Container | new | ARG_R_thing_bc01_count_box_Cont `800226:Argonia.esp` |
| ours | Container | new | ARG_VendorLooksAtBooksChest `000BCB:Argonia.esp` |
| ours | Container | new | ARG_R_thing_bc03_chest_Cont `800244:Argonia.esp` |
| ours | Container | new | ARG_R_thing_mq04_gum_box_Cont `800217:Argonia.esp` |
| ours | MiscItem | new | ARG_I_thing_mq04_sap_jars `8000F2:Argonia.esp` |
| ours | MiscItem | new | ARG_I_item_tg02_bone_figurine `800021:Argonia.esp` |
| ours | MiscItem | new | ARG_I_thing_lq25_bait `8000C9:Argonia.esp` |
| ours | MiscItem | new | ARG_I_thing_mq03_sap_jar `8000E2:Argonia.esp` |
| ours | MiscItem | new | ARG_I_thing_mq04_gum_pot `8000F0:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934C1 `000BEB:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7250 `000BF1:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCEE `000BB0:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCF0 `000BB1:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7253 `000BF4:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01512B `000BA3:Argonia.esp` |
| ours | Npc | new | ARG_Talker_015193 `000BA7:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934C4 `000BEE:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A204 `000BBF:Argonia.esp` |
| ours | Npc | new | ARG_Talker_084A87 `000BD6:Argonia.esp` |
| ours | Npc | new | ARG_R_person_test_crab_Base `80000B:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCE0 `000BAB:Argonia.esp` |
| ours | Npc | new | ARG_Talker_166BC1 `000C15:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C724F `000BF0:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934BE `000BE8:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_mercantile_coast_low_reed_village_root_herald_Base `8000EE:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C72A4 `000C06:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCFE `000BB7:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A208 `000BC2:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_mercantile_coast_soulrest_tg01_thief_Base `80001B:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7255 `000BF5:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5EA `000BDD:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01512C `000BA4:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5F1 `000BE3:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_hist_heartland_helstrom_lq30_youth_Base `8000CF:Argonia.esp` |
| ours | Npc | new | ARG_Talker_141539 `000C0D:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_pirate_freeholds_opening_work_barge_npc_opening_roll_reader_Base `8000D9:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_hist_heartland_helstrom_nisswo_interpreter_debating_house_Base `8000FC:Argonia.esp` |
| ours | Npc | new | ARG_R_creature_mq05_wasp_1_Base `8000F6:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A1E9 `000BBB:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5EF `000BE1:Argonia.esp` |
| ours | Npc | new | ARG_Talker_084A8F `000BD7:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5EC `000BDF:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934C5 `000BEF:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_mercantile_coast_soulrest_tg01_friend_Base `800019:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_imperial_penal_south_blackrose_post_gatekeeper_Base `800236:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_imperial_penal_south_blackrose_estate_debtor_Base `800220:Argonia.esp` |
| ours | Npc | new | ARG_Talker_1454F3 `000C11:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CD01 `000BB8:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CD04 `000BB9:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CD0A `000BBA:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_imperial_penal_south_blackrose_held_mother_Base `800232:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCFC `000BB6:Argonia.esp` |
| ours | Npc | new | ARG_Talker_1454F5 `000C13:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7263 `000BFE:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C72A8 `000C09:Argonia.esp` |
| ours | Npc | new | ARG_Talker_141561 `000C0F:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_imperial_penal_south_blackrose_held_speaker_Base `800234:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934BD `000BE7:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A206 `000BC1:Argonia.esp` |
| ours | Npc | new | ARG_Talker_1454F4 `000C12:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCE2 `000BAC:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCDE `000BAA:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_pirate_freeholds_opening_work_barge_npc_opening_overseer_Base `8000D7:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A1ED `000BBC:Argonia.esp` |
| ours | Npc | new | ARG_Talker_084A91 `000BD9:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_mercantile_coast_low_reed_village_egg_tender_Base `8000EC:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_mercantile_coast_lilmoth_broker_buys_the_months_Base `8000D1:Argonia.esp` |
| ours | Npc | new | ARG_Talker_00AC8E `000BA0:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_mercantile_coast_low_reed_village_cell_man_2_Base `8000E8:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_pirate_freeholds_opening_work_camp_n1_2_Base `8000DB:Argonia.esp` |
| ours | Npc | new | ARG_Talker_037E04 `000BC6:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5EE `000BE0:Argonia.esp` |
| ours | Npc | new | ARG_Talker_015195 `000BA8:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5E9 `000BDC:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7258 `000BF6:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01512D `000BA5:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5E3 `000BDA:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_mercantile_coast_soulrest_keeper_harbour_den_Base `800015:Argonia.esp` |
| ours | Npc | new | ARG_Talker_03E413 `000BC7:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCF2 `000BB2:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_hist_heartland_helstrom_grove_s_senior_tree_Base `8000FA:Argonia.esp` |
| ours | Npc | new | ARG_Talker_1454F2 `000C10:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0616E8 `000BD3:Argonia.esp` |
| ours | Npc | new | ARG_Talker_084A86 `000BD5:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934BA `000BE4:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934C2 `000BEC:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934C3 `000BED:Argonia.esp` |
| ours | Npc | new | ARG_R_creature_mq05_wasp_2_Base `8000F8:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_mercantile_coast_lilmoth_tg02_clutch_client_Base `800028:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_mercantile_coast_soulrest_khajiit_caravan_factor_Base `800017:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C725B `000BF9:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C72A6 `000C07:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7CD `000BD2:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_imperial_penal_south_blackrose_held_killer_Base `800230:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCE9 `000BAE:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_mercantile_coast_low_reed_village_chime_tuner_Base `8000EA:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7CA `000BCF:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5E8 `000BDB:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_imperial_penal_south_blackrose_estate_steward_Base `800224:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934BF `000BE9:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A1F2 `000BBE:Argonia.esp` |
| ours | Npc | new | ARG_R_person_test_keeper_Base `800008:Argonia.esp` |
| ours | Npc | new | ARG_R_creature_at_hist_heartland_helstrom_lq25_river_beast_Base `8000C7:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCD9 `000BA9:Argonia.esp` |
| ours | Npc | new | ARG_R_creature_at_hist_heartland_helstrom_lq30_basin_beast_Base `8000CB:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934BC `000BE6:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCF6 `000BB4:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCF4 `000BB3:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C729E `000C04:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_imperial_penal_south_blackrose_estate_fetcher_Base `800222:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C725D `000BFA:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7264 `000BFF:Argonia.esp` |
| ours | Npc | new | ARG_Talker_037E00 `000BC5:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C725E `000BFB:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCE5 `000BAD:Argonia.esp` |
| ours | Npc | new | ARG_R_person_test_walker_Base `800005:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7252 `000BF3:Argonia.esp` |
| ours | Npc | new | ARG_Talker_03E415 `000BC8:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7CC `000BD1:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_mercantile_coast_soulrest_berth_master_Base `80023E:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7269 `000C03:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7251 `000BF2:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7267 `000C01:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_mercantile_coast_soulrest_crew_boss_Base `800240:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCFA `000BB5:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7C8 `000BCD:Argonia.esp` |
| ours | Npc | new | ARG_Talker_14153A `000C0E:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7268 `000C02:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_imperial_penal_south_blackrose_chainbreaker_patron_Base `80021E:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C725F `000BFC:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7266 `000C00:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7260 `000BFD:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01CCEA `000BAF:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7C9 `000BCE:Argonia.esp` |
| ours | Npc | new | ARG_Talker_130789 `000C0C:Argonia.esp` |
| ours | Npc | new | ARG_Talker_01512E `000BA6:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934BB `000BE5:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A209 `000BC3:Argonia.esp` |
| ours | Npc | new | ARG_R_creature_bc02_lamia_Base `80022E:Argonia.esp` |
| ours | Npc | new | ARG_Talker_130773 `000C0A:Argonia.esp` |
| ours | Npc | new | ARG_Talker_00FF4E `000BA1:Argonia.esp` |
| ours | Npc | new | ARG_Talker_037DFE `000BC4:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A1F1 `000BBD:Argonia.esp` |
| ours | Npc | new | ARG_Talker_00FF4F `000BA2:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_mercantile_coast_lilmoth_tg02_beads_client_Base `800024:Argonia.esp` |
| ours | Npc | new | ARG_Talker_084A90 `000BD8:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5F0 `000BE2:Argonia.esp` |
| ours | Npc | new | ARG_Talker_08D5EB `000BDE:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C72A3 `000C05:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C725A `000BF8:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C7259 `000BF7:Argonia.esp` |
| ours | Npc | new | ARG_Talker_1454FC `000C14:Argonia.esp` |
| ours | Npc | new | ARG_Talker_02A205 `000BC0:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_mercantile_coast_lilmoth_tg02_charm_client_Base `800026:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0C72A7 `000C08:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_mercantile_coast_lilmoth_divers_yard_night_reed_fence_Base `800013:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_mercantile_coast_lilmoth_fish_trader_house_Base `8000D3:Argonia.esp` |
| ours | Npc | new | ARG_Talker_03E418 `000BC9:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_hist_heartland_helstrom_lq30_kin_Base `8000CD:Argonia.esp` |
| ours | Npc | new | ARG_Talker_084A85 `000BD4:Argonia.esp` |
| ours | Npc | new | ARG_Talker_0934C0 `000BEA:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_imperial_penal_south_blackrose_prison_chainbreaker_envoy_camped_causeway_Base `80023C:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_nesh_deeka_Base `8000D5:Argonia.esp` |
| ours | Npc | new | ARG_Talker_05D7CB `000BD0:Argonia.esp` |
| ours | Npc | new | ARG_Talker_130780 `000C0B:Argonia.esp` |
| ours | Npc | new | ARG_R_npc_mercantile_coast_low_reed_village_cell_man_1_Base `8000E6:Argonia.esp` |
| ours | Key | new | ARG_I_item_tg01_strongbox_key `800011:Argonia.esp` |
| ours | Key | new | ARG_I_thing_bc01_key `800229:Argonia.esp` |
| ours | Key | new | ARG_I_thing_bc03_key `800245:Argonia.esp` |
| ours | Key | new | ARG_I_thing_mq03_sack_key `8000DE:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_person_test_crab `80000A:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_mercantile_coast_lilmoth_divers_yard_night_reed_fence `800012:Argonia.esp` |
| ours | XMarker reference | new | ARG_Opening_StartMarker `000F23:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_pirate_freeholds_opening_work_barge_npc_opening_overseer `8000D6:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_pirate_freeholds_opening_work_barge_npc_opening_roll_reader `8000D8:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_pirate_freeholds_opening_work_camp_n1_2 `8000DA:Argonia.esp` |
| ours | XMarker reference | new | ARG_R_thing_mq03_lockpicks `8000DC:Argonia.esp` |
| ours | XMarker reference | new | ARG_R_thing_mq03_sack `8000DD:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_mercantile_coast_soulrest_keeper_harbour_den `800014:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_imperial_penal_south_blackrose_prison_chainbreaker_envoy_camped_causeway `80023B:Argonia.esp` |
| ours | XMarker reference | new | ARG_R_thing_bc03_book `800241:Argonia.esp` |
| ours | XMarker reference | new | ARG_R_thing_bc03_chest `800243:Argonia.esp` |
| ours | XMarker reference | new | ARG_R_thing_bc03_list `800246:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_mercantile_coast_lilmoth_fish_trader_house `8000D2:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_nesh_deeka `8000D4:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_imperial_penal_south_blackrose_chainbreaker_patron `80021D:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_creature_at_hist_heartland_helstrom_lq25_river_beast `8000C6:Argonia.esp` |
| ours | XMarker reference | new | ARG_R_thing_lq25_bait `8000C8:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_creature_at_hist_heartland_helstrom_lq30_basin_beast `8000CA:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_hist_heartland_helstrom_lq30_kin `8000CC:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_hist_heartland_helstrom_lq30_youth `8000CE:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_creature_mq05_wasp_1 `8000F5:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_creature_mq05_wasp_2 `8000F7:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_hist_heartland_helstrom_grove_s_senior_tree `8000F9:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_hist_heartland_helstrom_nisswo_interpreter_debating_house `8000FB:Argonia.esp` |
| ours | XMarker reference | new | ARG_OpeningMarker `000802:Argonia.esp` |
| ours | XMarker reference | new | ARG_VendorLooksAtBooksChestRef `000BCC:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_person_test_walker `800004:Argonia.esp` |
| ours | XMarker reference | new | ARG_R_marker_test_bollard `800006:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_person_test_keeper `800007:Argonia.esp` |
| ours | XMarker reference | new | ARG_R_thing_test_barrel `800009:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_mercantile_coast_soulrest_khajiit_caravan_factor `800016:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_mercantile_coast_soulrest_tg01_friend `800018:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_mercantile_coast_soulrest_tg01_thief `80001A:Argonia.esp` |
| ours | XMarker reference | new | ARG_R_thing_tg01_strongbox `80001C:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_mercantile_coast_lilmoth_tg02_beads_client `800023:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_mercantile_coast_lilmoth_tg02_charm_client `800025:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_mercantile_coast_lilmoth_tg02_clutch_client `800027:Argonia.esp` |
| ours | XMarker reference | new | ARG_R_thing_tg02_lockbox `800029:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_mercantile_coast_lilmoth_broker_buys_the_months `8000D0:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_mercantile_coast_low_reed_village_cell_man_1 `8000E5:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_mercantile_coast_low_reed_village_cell_man_2 `8000E7:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_mercantile_coast_low_reed_village_chime_tuner `8000E9:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_mercantile_coast_low_reed_village_egg_tender `8000EB:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_mercantile_coast_low_reed_village_root_herald `8000ED:Argonia.esp` |
| ours | XMarker reference | new | ARG_R_thing_mq04_gum_box `8000EF:Argonia.esp` |
| ours | XMarker reference | new | ARG_R_thing_mq04_sap_jars `8000F1:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_imperial_penal_south_blackrose_estate_debtor `80021F:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_imperial_penal_south_blackrose_estate_fetcher `800221:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_imperial_penal_south_blackrose_estate_steward `800223:Argonia.esp` |
| ours | XMarker reference | new | ARG_R_thing_bc01_count_box `800225:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_creature_bc02_lamia `80022D:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_imperial_penal_south_blackrose_held_killer `80022F:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_imperial_penal_south_blackrose_held_mother `800231:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_imperial_penal_south_blackrose_held_speaker `800233:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_imperial_penal_south_blackrose_post_gatekeeper `800235:Argonia.esp` |
| ours | XMarker reference | new | ARG_R_thing_bc02_strongbox `800238:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_mercantile_coast_soulrest_berth_master `80023D:Argonia.esp` |
| ours | PlacedNpc | new | ARG_R_npc_mercantile_coast_soulrest_crew_boss `80023F:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG01_Hello `80009F:Argonia.esp` |
| ours | DialogResponses | new |  `8000A0:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ04_T_d1a5b71c `8001D8:Argonia.esp` |
| ours | DialogResponses | new |  `8001DA:Argonia.esp` |
| ours | DialogResponses | new |  `8001DB:Argonia.esp` |
| ours | DialogTopic | new | ARG_BlockTest_HelloAfter `800059:Argonia.esp` |
| ours | DialogResponses | new |  `80005A:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_T_3d3e1113 `800152:Argonia.esp` |
| ours | DialogResponses | new |  `800154:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ30_HelloAfter `800134:Argonia.esp` |
| ours | DialogResponses | new |  `800135:Argonia.esp` |
| ours | DialogResponses | new |  `800137:Argonia.esp` |
| ours | DialogResponses | new |  `800136:Argonia.esp` |
| ours | DialogResponses | new |  `800138:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ04_T_2ff641c2 `8001C7:Argonia.esp` |
| ours | DialogResponses | new |  `8001C9:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Self `000A92:Argonia.esp` |
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
| ours | DialogResponses | new |  `000B08:Argonia.esp` |
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
| ours | DialogResponses | new |  `000B09:Argonia.esp` |
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
| ours | DialogTopic | new | ARG_TG02_T_f1f2ab72 `8000AF:Argonia.esp` |
| ours | DialogResponses | new |  `8000B2:Argonia.esp` |
| ours | DialogResponses | new |  `8000B4:Argonia.esp` |
| ours | DialogResponses | new |  `8000B3:Argonia.esp` |
| ours | DialogResponses | new |  `8000B1:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG01_T_1c3bdc3b `800065:Argonia.esp` |
| ours | DialogResponses | new |  `800068:Argonia.esp` |
| ours | DialogResponses | new |  `800067:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ30_T_9fa3394c `800121:Argonia.esp` |
| ours | DialogResponses | new |  `800123:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_7441b8c7 `800256:Argonia.esp` |
| ours | DialogResponses | new |  `800258:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_T_e017d919 `800178:Argonia.esp` |
| ours | DialogResponses | new |  `80017A:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_T_3845ae9d `800184:Argonia.esp` |
| ours | DialogResponses | new |  `80018B:Argonia.esp` |
| ours | DialogResponses | new |  `800187:Argonia.esp` |
| ours | DialogResponses | new |  `800186:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ04_T_3845ae9d `8001AB:Argonia.esp` |
| ours | DialogResponses | new |  `8001AE:Argonia.esp` |
| ours | DialogResponses | new |  `8001DD:Argonia.esp` |
| ours | DialogResponses | new |  `8001CC:Argonia.esp` |
| ours | DialogResponses | new |  `8001CA:Argonia.esp` |
| ours | DialogResponses | new |  `8001DC:Argonia.esp` |
| ours | DialogResponses | new |  `8001B0:Argonia.esp` |
| ours | DialogResponses | new |  `8001AF:Argonia.esp` |
| ours | DialogResponses | new |  `8001AD:Argonia.esp` |
| ours | DialogResponses | new |  `8001CB:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ25_T_2e4f6289 `800207:Argonia.esp` |
| ours | DialogResponses | new |  `800109:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_A_47138b74 `80018C:Argonia.esp` |
| ours | DialogResponses | new |  `80018E:Argonia.esp` |
| ours | DialogResponses | new |  `80018D:Argonia.esp` |
| ours | DialogTopic | new | ARG_BlockTestTwo_T_e0977919 `80002B:Argonia.esp` |
| ours | DialogResponses | new |  `80002D:Argonia.esp` |
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
| ours | DialogTopic | new | ARG_BlockTest_T_25ea342a `800038:Argonia.esp` |
| ours | DialogResponses | new |  `80003B:Argonia.esp` |
| ours | DialogResponses | new |  `80003A:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_6a8cce7e `800371:Argonia.esp` |
| ours | DialogResponses | new |  `800373:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_T_5c207ac9 `80013D:Argonia.esp` |
| ours | DialogResponses | new |  `800140:Argonia.esp` |
| ours | DialogResponses | new |  `80013F:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_5d837c8f `80039C:Argonia.esp` |
| ours | DialogResponses | new |  `80039E:Argonia.esp` |
| ours | DialogTopic | new | ARG_BlockTest_T_84ed37ec `800034:Argonia.esp` |
| ours | DialogResponses | new |  `800036:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_e63801a1 `800389:Argonia.esp` |
| ours | DialogResponses | new |  `80038C:Argonia.esp` |
| ours | DialogResponses | new |  `80038B:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_425a2291 `800319:Argonia.esp` |
| ours | DialogResponses | new |  `80031B:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_07966bc6 `8002C4:Argonia.esp` |
| ours | DialogResponses | new |  `8002C6:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_5f22f242 `8002F2:Argonia.esp` |
| ours | DialogResponses | new |  `8002F4:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ05_T_3c6803ab `8001EC:Argonia.esp` |
| ours | DialogResponses | new |  `8001EE:Argonia.esp` |
| ours | DialogResponses | new |  `8001EF:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_8873f82b `800369:Argonia.esp` |
| ours | DialogResponses | new |  `80036E:Argonia.esp` |
| ours | DialogResponses | new |  `80036D:Argonia.esp` |
| ours | DialogResponses | new |  `80036B:Argonia.esp` |
| ours | DialogResponses | new |  `80036C:Argonia.esp` |
| ours | DialogResponses | new |  `800370:Argonia.esp` |
| ours | DialogResponses | new |  `80036F:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ05_T_f957c0c4 `8001FA:Argonia.esp` |
| ours | DialogResponses | new |  `8001FC:Argonia.esp` |
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
| ours | DialogTopic | new | ARG_MQ05_T_8b43ea5e `8001F0:Argonia.esp` |
| ours | DialogResponses | new |  `8001F2:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ30_T_c95d6ca2 `80011D:Argonia.esp` |
| ours | DialogResponses | new |  `80011F:Argonia.esp` |
| ours | DialogResponses | new |  `800120:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_06258fe9 `800293:Argonia.esp` |
| ours | DialogResponses | new |  `800295:Argonia.esp` |
| ours | DialogResponses | new |  `800298:Argonia.esp` |
| ours | DialogResponses | new |  `800297:Argonia.esp` |
| ours | DialogResponses | new |  `800296:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_T_ecd2c000 `800082:Argonia.esp` |
| ours | DialogResponses | new |  `8000A6:Argonia.esp` |
| ours | DialogResponses | new |  `8000A5:Argonia.esp` |
| ours | DialogResponses | new |  `8000A1:Argonia.esp` |
| ours | DialogResponses | new |  `8000A2:Argonia.esp` |
| ours | DialogResponses | new |  `8000A3:Argonia.esp` |
| ours | DialogResponses | new |  `8000A4:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_T_32a136e6 `80014F:Argonia.esp` |
| ours | DialogResponses | new |  `800151:Argonia.esp` |
| ours | DialogTopic | new | ARG_BlockTest_T_5b312054 `8000FF:Argonia.esp` |
| ours | DialogResponses | new |  `800043:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_769b24d5 `8002EC:Argonia.esp` |
| ours | DialogResponses | new |  `8002EF:Argonia.esp` |
| ours | DialogResponses | new |  `8002F0:Argonia.esp` |
| ours | DialogResponses | new |  `8002F1:Argonia.esp` |
| ours | DialogResponses | new |  `8002EE:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG01_T_e16794f7 `80006D:Argonia.esp` |
| ours | DialogResponses | new |  `800070:Argonia.esp` |
| ours | DialogResponses | new |  `80009D:Argonia.esp` |
| ours | DialogResponses | new |  `80006F:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_5727e8cd `8002E6:Argonia.esp` |
| ours | DialogResponses | new |  `8002EB:Argonia.esp` |
| ours | DialogResponses | new |  `8002E8:Argonia.esp` |
| ours | DialogResponses | new |  `8002EA:Argonia.esp` |
| ours | DialogResponses | new |  `8002E9:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_1c24a985 `8002CD:Argonia.esp` |
| ours | DialogResponses | new |  `8002CF:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ04_T_633300f4 `8001A5:Argonia.esp` |
| ours | DialogResponses | new |  `8001A7:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_e86b4b18 `8002D9:Argonia.esp` |
| ours | DialogResponses | new |  `8002DB:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_37f913ba `80031C:Argonia.esp` |
| ours | DialogResponses | new |  `80031E:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_a561438e `800253:Argonia.esp` |
| ours | DialogResponses | new |  `800255:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_T_7605f2c4 `800164:Argonia.esp` |
| ours | DialogResponses | new |  `800166:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG01_T_d12103c8 `800071:Argonia.esp` |
| ours | DialogResponses | new |  `80009E:Argonia.esp` |
| ours | DialogResponses | new |  `80009C:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_fe0f680a `800350:Argonia.esp` |
| ours | DialogResponses | new |  `800355:Argonia.esp` |
| ours | DialogResponses | new |  `800353:Argonia.esp` |
| ours | DialogResponses | new |  `800357:Argonia.esp` |
| ours | DialogResponses | new |  `800352:Argonia.esp` |
| ours | DialogResponses | new |  `800356:Argonia.esp` |
| ours | DialogResponses | new |  `800354:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_ab1fc3b1 `8002E0:Argonia.esp` |
| ours | DialogResponses | new |  `8002E2:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ25_Hello `800114:Argonia.esp` |
| ours | DialogResponses | new |  `800115:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_3e303c46 `800335:Argonia.esp` |
| ours | DialogResponses | new |  `800337:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_6568248a `8002B8:Argonia.esp` |
| ours | DialogResponses | new |  `8002BA:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ25_T_1ed95258 `800209:Argonia.esp` |
| ours | DialogResponses | new |  `80010E:Argonia.esp` |
| ours | DialogResponses | new |  `80010C:Argonia.esp` |
| ours | DialogResponses | new |  `80010F:Argonia.esp` |
| ours | DialogResponses | new |  `80010D:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ04_T_f366a7c0 `8001A8:Argonia.esp` |
| ours | DialogResponses | new |  `8001AA:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_T_03930597 `80007D:Argonia.esp` |
| ours | DialogResponses | new |  `80007F:Argonia.esp` |
| ours | DialogResponses | new |  `800080:Argonia.esp` |
| ours | DialogResponses | new |  `800081:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ30_Hello `80012D:Argonia.esp` |
| ours | DialogResponses | new |  `80012E:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_0219476b `800399:Argonia.esp` |
| ours | DialogResponses | new |  `80039B:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_T_8dccb2ff `800077:Argonia.esp` |
| ours | DialogResponses | new |  `800079:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_9cd405e4 `80038D:Argonia.esp` |
| ours | DialogResponses | new |  `800390:Argonia.esp` |
| ours | DialogResponses | new |  `80038F:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_T_f15977f3 `80016D:Argonia.esp` |
| ours | DialogResponses | new |  `80016F:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_aa80ca41 `8002A9:Argonia.esp` |
| ours | DialogResponses | new |  `8002AB:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ04_T_2c3e5ca3 `80020E:Argonia.esp` |
| ours | DialogResponses | new |  `8001B3:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ30_A_520eee36 `80020D:Argonia.esp` |
| ours | DialogResponses | new |  `800133:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ05_T_5967412a `8001E6:Argonia.esp` |
| ours | DialogResponses | new |  `8001E8:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_a1302c62 `80031F:Argonia.esp` |
| ours | DialogResponses | new |  `800322:Argonia.esp` |
| ours | DialogResponses | new |  `800323:Argonia.esp` |
| ours | DialogResponses | new |  `800321:Argonia.esp` |
| ours | DialogTopic | new | ARG_BlockTest_T_a52b437c `800044:Argonia.esp` |
| ours | DialogResponses | new |  `800047:Argonia.esp` |
| ours | DialogResponses | new |  `800046:Argonia.esp` |
| ours | DialogTopic | new | ARG_BlockTest_T_e3b31068 `800048:Argonia.esp` |
| ours | DialogResponses | new |  `80004B:Argonia.esp` |
| ours | DialogResponses | new |  `80004A:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_f72eda2d `800376:Argonia.esp` |
| ours | DialogResponses | new |  `800379:Argonia.esp` |
| ours | DialogResponses | new |  `80037C:Argonia.esp` |
| ours | DialogResponses | new |  `80037D:Argonia.esp` |
| ours | DialogResponses | new |  `80037B:Argonia.esp` |
| ours | DialogResponses | new |  `800378:Argonia.esp` |
| ours | DialogResponses | new |  `80037A:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_3730f329 `800286:Argonia.esp` |
| ours | DialogResponses | new |  `80028C:Argonia.esp` |
| ours | DialogResponses | new |  `80028F:Argonia.esp` |
| ours | DialogResponses | new |  `80028B:Argonia.esp` |
| ours | DialogResponses | new |  `800290:Argonia.esp` |
| ours | DialogResponses | new |  `800291:Argonia.esp` |
| ours | DialogResponses | new |  `80028A:Argonia.esp` |
| ours | DialogResponses | new |  `800289:Argonia.esp` |
| ours | DialogResponses | new |  `800288:Argonia.esp` |
| ours | DialogResponses | new |  `80028D:Argonia.esp` |
| ours | DialogResponses | new |  `80028E:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_c5be3433 `8002E3:Argonia.esp` |
| ours | DialogResponses | new |  `8002E5:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_4431ef00 `8002FC:Argonia.esp` |
| ours | DialogResponses | new |  `8002FE:Argonia.esp` |
| ours | DialogResponses | new |  `8002FF:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_2b6dd5e3 `80039F:Argonia.esp` |
| ours | DialogResponses | new |  `8003A3:Argonia.esp` |
| ours | DialogResponses | new |  `8003A2:Argonia.esp` |
| ours | DialogResponses | new |  `8003A1:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Rumours `000A7B:Argonia.esp` |
| ours | DialogResponses | new |  `000A82:Argonia.esp` |
| ours | DialogResponses | new |  `000A84:Argonia.esp` |
| ours | DialogResponses | new |  `000F2D:Argonia.esp` |
| ours | DialogResponses | new |  `000F27:Argonia.esp` |
| ours | DialogResponses | new |  `000A81:Argonia.esp` |
| ours | DialogResponses | new |  `000F2E:Argonia.esp` |
| ours | DialogResponses | new |  `000F2B:Argonia.esp` |
| ours | DialogResponses | new |  `000A7D:Argonia.esp` |
| ours | DialogResponses | new |  `000A7E:Argonia.esp` |
| ours | DialogResponses | new |  `000A83:Argonia.esp` |
| ours | DialogResponses | new |  `000A86:Argonia.esp` |
| ours | DialogResponses | new |  `000F29:Argonia.esp` |
| ours | DialogResponses | new |  `000A7F:Argonia.esp` |
| ours | DialogResponses | new |  `000A7C:Argonia.esp` |
| ours | DialogResponses | new |  `000F2C:Argonia.esp` |
| ours | DialogResponses | new |  `000A80:Argonia.esp` |
| ours | DialogResponses | new |  `000A85:Argonia.esp` |
| ours | DialogResponses | new |  `000F2A:Argonia.esp` |
| ours | DialogResponses | new |  `000F26:Argonia.esp` |
| ours | DialogResponses | new |  `000F25:Argonia.esp` |
| ours | DialogResponses | new |  `000F24:Argonia.esp` |
| ours | DialogResponses | new |  `000F28:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_49af4ccf `80026E:Argonia.esp` |
| ours | DialogResponses | new |  `800277:Argonia.esp` |
| ours | DialogResponses | new |  `800273:Argonia.esp` |
| ours | DialogResponses | new |  `800275:Argonia.esp` |
| ours | DialogResponses | new |  `800272:Argonia.esp` |
| ours | DialogResponses | new |  `800279:Argonia.esp` |
| ours | DialogResponses | new |  `800274:Argonia.esp` |
| ours | DialogResponses | new |  `800276:Argonia.esp` |
| ours | DialogResponses | new |  `800271:Argonia.esp` |
| ours | DialogResponses | new |  `800278:Argonia.esp` |
| ours | DialogResponses | new |  `800270:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_HelloAfter `8001A0:Argonia.esp` |
| ours | DialogResponses | new |  `8001A1:Argonia.esp` |
| ours | DialogResponses | new |  `8001A2:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ04_T_744e3fd7 `8001BA:Argonia.esp` |
| ours | DialogResponses | new |  `8001BE:Argonia.esp` |
| ours | DialogResponses | new |  `8001BF:Argonia.esp` |
| ours | DialogResponses | new |  `8001BD:Argonia.esp` |
| ours | DialogResponses | new |  `8001BC:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_fc621a33 `8002B5:Argonia.esp` |
| ours | DialogResponses | new |  `8002B7:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_T_952fcb5f `800181:Argonia.esp` |
| ours | DialogResponses | new |  `800183:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_8aa699ed `800259:Argonia.esp` |
| ours | DialogResponses | new |  `80025B:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_T_84516bd8 `8000B8:Argonia.esp` |
| ours | DialogResponses | new |  `8000BB:Argonia.esp` |
| ours | DialogResponses | new |  `8000BA:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_b73068ed `80035E:Argonia.esp` |
| ours | DialogResponses | new |  `800360:Argonia.esp` |
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
| ours | DialogTopic | new | ARG_BC03_T_b0f19f27 `800396:Argonia.esp` |
| ours | DialogResponses | new |  `800398:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ25_T_a0d773bf `80020B:Argonia.esp` |
| ours | DialogResponses | new |  `800113:Argonia.esp` |
| ours | DialogResponses | new |  `800112:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_T_677f6e10 `8000BC:Argonia.esp` |
| ours | DialogResponses | new |  `8000BF:Argonia.esp` |
| ours | DialogResponses | new |  `8000BE:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_3e303c46 `8002C7:Argonia.esp` |
| ours | DialogResponses | new |  `8002C9:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ04_T_955a8628 `8001CD:Argonia.esp` |
| ours | DialogResponses | new |  `8001CF:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_T_52b4b715 `80017E:Argonia.esp` |
| ours | DialogResponses | new |  `800180:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ05_T_aeef371a `8001E3:Argonia.esp` |
| ours | DialogResponses | new |  `8001E5:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG01_T_ca106a9a `800062:Argonia.esp` |
| ours | DialogResponses | new |  `800064:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_HelloAfter `800095:Argonia.esp` |
| ours | DialogResponses | new |  `800096:Argonia.esp` |
| ours | DialogResponses | new |  `800097:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_7f60290f `80024D:Argonia.esp` |
| ours | DialogResponses | new |  `80024F:Argonia.esp` |
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
| ours | DialogTopic | new | ARG_MQ04_T_665a16fe `8001D4:Argonia.esp` |
| ours | DialogResponses | new |  `8001D6:Argonia.esp` |
| ours | DialogResponses | new |  `8001D7:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_a1d959fd `8002AC:Argonia.esp` |
| ours | DialogResponses | new |  `8002AE:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_d63d54b2 `800316:Argonia.esp` |
| ours | DialogResponses | new |  `800318:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_62e0f989 `800299:Argonia.esp` |
| ours | DialogResponses | new |  `80029D:Argonia.esp` |
| ours | DialogResponses | new |  `80029E:Argonia.esp` |
| ours | DialogResponses | new |  `80029B:Argonia.esp` |
| ours | DialogResponses | new |  `80029C:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_HelloAfter `8003A4:Argonia.esp` |
| ours | DialogResponses | new |  `8003AA:Argonia.esp` |
| ours | DialogResponses | new |  `8003A9:Argonia.esp` |
| ours | DialogResponses | new |  `8003A6:Argonia.esp` |
| ours | DialogResponses | new |  `8003A8:Argonia.esp` |
| ours | DialogResponses | new |  `8003A5:Argonia.esp` |
| ours | DialogResponses | new |  `8003A7:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_T_9f2ee7f5 `80015B:Argonia.esp` |
| ours | DialogResponses | new |  `80015D:Argonia.esp` |
| ours | DialogTopic | new | ARG_BlockTest_T_cf09a8f9 `80004C:Argonia.esp` |
| ours | DialogResponses | new |  `80004F:Argonia.esp` |
| ours | DialogResponses | new |  `80004E:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Someone `000B14:Argonia.esp` |
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
| ours | DialogResponses | new |  `000B80:Argonia.esp` |
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
| ours | DialogResponses | new |  `000B7F:Argonia.esp` |
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
| ours | DialogResponses | new |  `000B63:Argonia.esp` |
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
| ours | DialogTopic | new | ARG_BlockTestTwo_T_37c8386d `800031:Argonia.esp` |
| ours | DialogResponses | new |  `800033:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_Hello `800173:Argonia.esp` |
| ours | DialogResponses | new |  `800174:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_d7c71ee9 `8002D0:Argonia.esp` |
| ours | DialogResponses | new |  `8002D2:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_3bf6c1fc `80027A:Argonia.esp` |
| ours | DialogResponses | new |  `800284:Argonia.esp` |
| ours | DialogResponses | new |  `80027C:Argonia.esp` |
| ours | DialogResponses | new |  `800280:Argonia.esp` |
| ours | DialogResponses | new |  `80027E:Argonia.esp` |
| ours | DialogResponses | new |  `800281:Argonia.esp` |
| ours | DialogResponses | new |  `80027D:Argonia.esp` |
| ours | DialogResponses | new |  `800283:Argonia.esp` |
| ours | DialogResponses | new |  `800282:Argonia.esp` |
| ours | DialogResponses | new |  `80027F:Argonia.esp` |
| ours | DialogResponses | new |  `800285:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_07966bc6 `800332:Argonia.esp` |
| ours | DialogResponses | new |  `800334:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG01_HelloAfter `800075:Argonia.esp` |
| ours | DialogResponses | new |  `800203:Argonia.esp` |
| ours | DialogResponses | new |  `800076:Argonia.esp` |
| ours | DialogResponses | new |  `800202:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_0aca202e `8002A2:Argonia.esp` |
| ours | DialogResponses | new |  `8002A8:Argonia.esp` |
| ours | DialogResponses | new |  `8002A5:Argonia.esp` |
| ours | DialogResponses | new |  `8002A6:Argonia.esp` |
| ours | DialogResponses | new |  `8002A7:Argonia.esp` |
| ours | DialogResponses | new |  `8002A4:Argonia.esp` |
| ours | DialogTopic | new | ARG_BlockTest_SF_ead80562 `800053:Argonia.esp` |
| ours | DialogResponses | new |  `800055:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_A_cd02a9b0 `80018F:Argonia.esp` |
| ours | DialogResponses | new |  `800190:Argonia.esp` |
| ours | DialogResponses | new |  `800191:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_A_35ee247e `8001A3:Argonia.esp` |
| ours | DialogResponses | new |  `8001A4:Argonia.esp` |
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
| ours | DialogTopic | new | ARG_BC01_T_7920a4b1 `800265:Argonia.esp` |
| ours | DialogResponses | new |  `800268:Argonia.esp` |
| ours | DialogResponses | new |  `800267:Argonia.esp` |
| ours | DialogTopic | new | ARG_BlockTest_T_58651bd7 `80003C:Argonia.esp` |
| ours | DialogResponses | new |  `80003E:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ05_T_27b6f161 `800210:Argonia.esp` |
| ours | DialogResponses | new |  `8001F5:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_a145d133 `800269:Argonia.esp` |
| ours | DialogResponses | new |  `80026B:Argonia.esp` |
| ours | DialogResponses | new |  `80026C:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Loot `000A19:Argonia.esp` |
| ours | DialogResponses | new |  `000A1D:Argonia.esp` |
| ours | DialogResponses | new |  `000A1A:Argonia.esp` |
| ours | DialogResponses | new |  `000A1B:Argonia.esp` |
| ours | DialogResponses | new |  `000A1C:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_bc946ca8 `800338:Argonia.esp` |
| ours | DialogResponses | new |  `80033A:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG01_T_6e367228 `80009A:Argonia.esp` |
| ours | DialogResponses | new |  `80006C:Argonia.esp` |
| ours | DialogResponses | new |  `80006B:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_f77d67ea `80029F:Argonia.esp` |
| ours | DialogResponses | new |  `8002A1:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_55740835 `8002B2:Argonia.esp` |
| ours | DialogResponses | new |  `8002B4:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG01_T_24c18a85 `80005E:Argonia.esp` |
| ours | DialogResponses | new |  `800060:Argonia.esp` |
| ours | DialogResponses | new |  `800061:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_T_73b14da4 `800167:Argonia.esp` |
| ours | DialogResponses | new |  `800169:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ04_T_aef146d9 `8001C4:Argonia.esp` |
| ours | DialogResponses | new |  `8001C6:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_3e303c46 `80025C:Argonia.esp` |
| ours | DialogResponses | new |  `80025E:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ25_HelloAfter `800116:Argonia.esp` |
| ours | DialogResponses | new |  `80011B:Argonia.esp` |
| ours | DialogResponses | new |  `80011C:Argonia.esp` |
| ours | DialogResponses | new |  `80011A:Argonia.esp` |
| ours | DialogResponses | new |  `800118:Argonia.esp` |
| ours | DialogResponses | new |  `800119:Argonia.esp` |
| ours | DialogResponses | new |  `800117:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_3998e621 `800347:Argonia.esp` |
| ours | DialogResponses | new |  `800349:Argonia.esp` |
| ours | DialogResponses | new |  `80034A:Argonia.esp` |
| ours | DialogResponses | new |  `80034B:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_4ee7a9c6 `8002CA:Argonia.esp` |
| ours | DialogResponses | new |  `8002CC:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ05_T_ffe2c41a `8001E9:Argonia.esp` |
| ours | DialogResponses | new |  `8001EB:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_T_628d5dba `800188:Argonia.esp` |
| ours | DialogResponses | new |  `80018A:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ05_T_4150bea9 `8001F6:Argonia.esp` |
| ours | DialogResponses | new |  `8001F8:Argonia.esp` |
| ours | DialogResponses | new |  `8001F9:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ04_HelloAfter `8001DE:Argonia.esp` |
| ours | DialogResponses | new |  `8001DF:Argonia.esp` |
| ours | DialogResponses | new |  `8001E0:Argonia.esp` |
| ours | DialogResponses | new |  `8001E2:Argonia.esp` |
| ours | DialogResponses | new |  `8001E1:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_T_a4d5fa15 `8000A9:Argonia.esp` |
| ours | DialogResponses | new |  `8000AC:Argonia.esp` |
| ours | DialogResponses | new |  `8000AD:Argonia.esp` |
| ours | DialogResponses | new |  `8000AE:Argonia.esp` |
| ours | DialogResponses | new |  `8000AB:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_T_1bc650ae `80007A:Argonia.esp` |
| ours | DialogResponses | new |  `80007C:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_T_2d9326df `800139:Argonia.esp` |
| ours | DialogResponses | new |  `80013B:Argonia.esp` |
| ours | DialogResponses | new |  `80013C:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_6ee41b3c `800304:Argonia.esp` |
| ours | DialogResponses | new |  `800306:Argonia.esp` |
| ours | DialogResponses | new |  `800307:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_e6f5743d `8002D6:Argonia.esp` |
| ours | DialogResponses | new |  `8002D8:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Services `000B0B:Argonia.esp` |
| ours | DialogResponses | new |  `000B0F:Argonia.esp` |
| ours | DialogResponses | new |  `000B11:Argonia.esp` |
| ours | DialogResponses | new |  `000B0D:Argonia.esp` |
| ours | DialogResponses | new |  `000B12:Argonia.esp` |
| ours | DialogResponses | new |  `000B0E:Argonia.esp` |
| ours | DialogResponses | new |  `000B0C:Argonia.esp` |
| ours | DialogResponses | new |  `000B10:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_a383d1bd `800308:Argonia.esp` |
| ours | DialogResponses | new |  `800314:Argonia.esp` |
| ours | DialogResponses | new |  `80030B:Argonia.esp` |
| ours | DialogResponses | new |  `80030E:Argonia.esp` |
| ours | DialogResponses | new |  `800313:Argonia.esp` |
| ours | DialogResponses | new |  `80030F:Argonia.esp` |
| ours | DialogResponses | new |  `80030D:Argonia.esp` |
| ours | DialogResponses | new |  `80030A:Argonia.esp` |
| ours | DialogResponses | new |  `80030C:Argonia.esp` |
| ours | DialogResponses | new |  `800311:Argonia.esp` |
| ours | DialogResponses | new |  `800312:Argonia.esp` |
| ours | DialogResponses | new |  `800310:Argonia.esp` |
| ours | DialogResponses | new |  `800315:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Secret `000A88:Argonia.esp` |
| ours | DialogResponses | new |  `000A90:Argonia.esp` |
| ours | DialogResponses | new |  `000A8C:Argonia.esp` |
| ours | DialogResponses | new |  `000A8E:Argonia.esp` |
| ours | DialogResponses | new |  `000A8D:Argonia.esp` |
| ours | DialogResponses | new |  `000A8B:Argonia.esp` |
| ours | DialogResponses | new |  `000A89:Argonia.esp` |
| ours | DialogResponses | new |  `000A8A:Argonia.esp` |
| ours | DialogResponses | new |  `000A8F:Argonia.esp` |
| ours | DialogTopic | new | ARG_BlockTest_Hello `800056:Argonia.esp` |
| ours | DialogResponses | new |  `800057:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ04_T_316b9879 `8001C0:Argonia.esp` |
| ours | DialogResponses | new |  `8001C3:Argonia.esp` |
| ours | DialogResponses | new |  `8001C2:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_0be36d62 `800341:Argonia.esp` |
| ours | DialogResponses | new |  `800344:Argonia.esp` |
| ours | DialogResponses | new |  `800346:Argonia.esp` |
| ours | DialogResponses | new |  `800345:Argonia.esp` |
| ours | DialogResponses | new |  `800343:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_2d233477 `80033E:Argonia.esp` |
| ours | DialogResponses | new |  `800340:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_3845ae9d `80033B:Argonia.esp` |
| ours | DialogResponses | new |  `800374:Argonia.esp` |
| ours | DialogResponses | new |  `80033D:Argonia.esp` |
| ours | DialogResponses | new |  `800375:Argonia.esp` |
| ours | DialogResponses | new |  `80035D:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ30_T_b8e72cf6 `800128:Argonia.esp` |
| ours | DialogResponses | new |  `80012A:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_HelloAfter `800329:Argonia.esp` |
| ours | DialogResponses | new |  `80032E:Argonia.esp` |
| ours | DialogResponses | new |  `800330:Argonia.esp` |
| ours | DialogResponses | new |  `80032A:Argonia.esp` |
| ours | DialogResponses | new |  `80032F:Argonia.esp` |
| ours | DialogResponses | new |  `80032D:Argonia.esp` |
| ours | DialogResponses | new |  `80032C:Argonia.esp` |
| ours | DialogResponses | new |  `800331:Argonia.esp` |
| ours | DialogResponses | new |  `80032B:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ30_T_2750ee8b `800124:Argonia.esp` |
| ours | DialogResponses | new |  `800126:Argonia.esp` |
| ours | DialogResponses | new |  `80012C:Argonia.esp` |
| ours | DialogResponses | new |  `80012B:Argonia.esp` |
| ours | DialogResponses | new |  `800127:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_e0f6b40a `80024A:Argonia.esp` |
| ours | DialogResponses | new |  `80024C:Argonia.esp` |
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
| ours | DialogTopic | new | ARG_BC01_T_8aefbdc5 `800250:Argonia.esp` |
| ours | DialogResponses | new |  `800252:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_T_31c6171c `800212:Argonia.esp` |
| ours | DialogResponses | new |  `8000A7:Argonia.esp` |
| ours | DialogResponses | new |  `8000A8:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_T_e043fb1a `800155:Argonia.esp` |
| ours | DialogResponses | new |  `800157:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_3845ae9d `80025F:Argonia.esp` |
| ours | DialogResponses | new |  `800261:Argonia.esp` |
| ours | DialogResponses | new |  `800292:Argonia.esp` |
| ours | DialogResponses | new |  `80026D:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_7b75483d `800300:Argonia.esp` |
| ours | DialogResponses | new |  `800303:Argonia.esp` |
| ours | DialogResponses | new |  `800302:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_A_236ebe34 `800192:Argonia.esp` |
| ours | DialogResponses | new |  `800195:Argonia.esp` |
| ours | DialogResponses | new |  `800197:Argonia.esp` |
| ours | DialogResponses | new |  `800194:Argonia.esp` |
| ours | DialogResponses | new |  `800198:Argonia.esp` |
| ours | DialogResponses | new |  `800193:Argonia.esp` |
| ours | DialogResponses | new |  `800196:Argonia.esp` |
| ours | DialogResponses | new |  `80019A:Argonia.esp` |
| ours | DialogResponses | new |  `800199:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_T_3845ae9d `800141:Argonia.esp` |
| ours | DialogResponses | new |  `80014B:Argonia.esp` |
| ours | DialogResponses | new |  `800147:Argonia.esp` |
| ours | DialogResponses | new |  `800146:Argonia.esp` |
| ours | DialogResponses | new |  `80014C:Argonia.esp` |
| ours | DialogResponses | new |  `80014E:Argonia.esp` |
| ours | DialogResponses | new |  `80014D:Argonia.esp` |
| ours | DialogResponses | new |  `800143:Argonia.esp` |
| ours | DialogResponses | new |  `800145:Argonia.esp` |
| ours | DialogResponses | new |  `800144:Argonia.esp` |
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
| ours | DialogTopic | new | ARG_MQ01_SF_fa1bcdd7 `800170:Argonia.esp` |
| ours | DialogResponses | new |  `800172:Argonia.esp` |
| ours | DialogTopic | new | ARG_Talk_Trade `000B82:Argonia.esp` |
| ours | DialogResponses | new |  `000B99:Argonia.esp` |
| ours | DialogResponses | new |  `000B8B:Argonia.esp` |
| ours | DialogResponses | new |  `000B9A:Argonia.esp` |
| ours | DialogResponses | new |  `000B9E:Argonia.esp` |
| ours | DialogResponses | new |  `000B94:Argonia.esp` |
| ours | DialogResponses | new |  `000B84:Argonia.esp` |
| ours | DialogResponses | new |  `000B8A:Argonia.esp` |
| ours | DialogResponses | new |  `000B83:Argonia.esp` |
| ours | DialogResponses | new |  `000B89:Argonia.esp` |
| ours | DialogResponses | new |  `000B9C:Argonia.esp` |
| ours | DialogResponses | new |  `000B96:Argonia.esp` |
| ours | DialogResponses | new |  `000B85:Argonia.esp` |
| ours | DialogResponses | new |  `000B97:Argonia.esp` |
| ours | DialogResponses | new |  `000B8D:Argonia.esp` |
| ours | DialogResponses | new |  `000B93:Argonia.esp` |
| ours | DialogResponses | new |  `000B98:Argonia.esp` |
| ours | DialogResponses | new |  `000B91:Argonia.esp` |
| ours | DialogResponses | new |  `000B95:Argonia.esp` |
| ours | DialogResponses | new |  `000B88:Argonia.esp` |
| ours | DialogResponses | new |  `000B90:Argonia.esp` |
| ours | DialogResponses | new |  `000B8C:Argonia.esp` |
| ours | DialogResponses | new |  `000B9F:Argonia.esp` |
| ours | DialogResponses | new |  `000B9B:Argonia.esp` |
| ours | DialogResponses | new |  `000B92:Argonia.esp` |
| ours | DialogResponses | new |  `000B9D:Argonia.esp` |
| ours | DialogResponses | new |  `000B87:Argonia.esp` |
| ours | DialogResponses | new |  `000B86:Argonia.esp` |
| ours | DialogResponses | new |  `000B8F:Argonia.esp` |
| ours | DialogResponses | new |  `000B8E:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ30_A_85e9a1fd `80012F:Argonia.esp` |
| ours | DialogResponses | new |  `800130:Argonia.esp` |
| ours | DialogResponses | new |  `800131:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_f33f4595 `80034C:Argonia.esp` |
| ours | DialogResponses | new |  `80034F:Argonia.esp` |
| ours | DialogResponses | new |  `80034E:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_T_c6b5b34f `800148:Argonia.esp` |
| ours | DialogResponses | new |  `80014A:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_T_f4438851 `800158:Argonia.esp` |
| ours | DialogResponses | new |  `80015A:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_T_b6b60993 `80015E:Argonia.esp` |
| ours | DialogResponses | new |  `800160:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ05_HelloAfter `8001FD:Argonia.esp` |
| ours | DialogResponses | new |  `800201:Argonia.esp` |
| ours | DialogResponses | new |  `8001FE:Argonia.esp` |
| ours | DialogResponses | new |  `8001FF:Argonia.esp` |
| ours | DialogResponses | new |  `800200:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_95ce292b `800361:Argonia.esp` |
| ours | DialogResponses | new |  `800365:Argonia.esp` |
| ours | DialogResponses | new |  `800364:Argonia.esp` |
| ours | DialogResponses | new |  `800368:Argonia.esp` |
| ours | DialogResponses | new |  `800363:Argonia.esp` |
| ours | DialogResponses | new |  `800367:Argonia.esp` |
| ours | DialogResponses | new |  `800366:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_T_2d4b48d9 `800161:Argonia.esp` |
| ours | DialogResponses | new |  `800163:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_Hello `800324:Argonia.esp` |
| ours | DialogResponses | new |  `800327:Argonia.esp` |
| ours | DialogResponses | new |  `800326:Argonia.esp` |
| ours | DialogResponses | new |  `800328:Argonia.esp` |
| ours | DialogResponses | new |  `800325:Argonia.esp` |
| ours | DialogTopic | new | ARG_BlockTestTwo_T_65596e18 `80002E:Argonia.esp` |
| ours | DialogResponses | new |  `800030:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ04_T_09915509 `8001B4:Argonia.esp` |
| ours | DialogResponses | new |  `8001B9:Argonia.esp` |
| ours | DialogResponses | new |  `8001B6:Argonia.esp` |
| ours | DialogResponses | new |  `8001B7:Argonia.esp` |
| ours | DialogResponses | new |  `8001B8:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG01_T_83aeeed8 `80005B:Argonia.esp` |
| ours | DialogResponses | new |  `80005D:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_4eedd22d `800358:Argonia.esp` |
| ours | DialogResponses | new |  `80035C:Argonia.esp` |
| ours | DialogResponses | new |  `80035A:Argonia.esp` |
| ours | DialogResponses | new |  `80035B:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_3845ae9d `8002DC:Argonia.esp` |
| ours | DialogResponses | new |  `8002DE:Argonia.esp` |
| ours | DialogResponses | new |  `8002F5:Argonia.esp` |
| ours | DialogResponses | new |  `8002F7:Argonia.esp` |
| ours | DialogResponses | new |  `8002DF:Argonia.esp` |
| ours | DialogResponses | new |  `8002F6:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_A_c4475fb3 `80019B:Argonia.esp` |
| ours | DialogResponses | new |  `80019F:Argonia.esp` |
| ours | DialogResponses | new |  `80019D:Argonia.esp` |
| ours | DialogResponses | new |  `80019E:Argonia.esp` |
| ours | DialogResponses | new |  `80019C:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_901a2612 `800262:Argonia.esp` |
| ours | DialogResponses | new |  `800264:Argonia.esp` |
| ours | DialogTopic | new | ARG_TG02_T_e5c77b4b `800214:Argonia.esp` |
| ours | DialogResponses | new |  `8000B7:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_T_7f842221 `8002AF:Argonia.esp` |
| ours | DialogResponses | new |  `8002B1:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC01_HelloAfter `8002BB:Argonia.esp` |
| ours | DialogResponses | new |  `8002C0:Argonia.esp` |
| ours | DialogResponses | new |  `8002BD:Argonia.esp` |
| ours | DialogResponses | new |  `8002C1:Argonia.esp` |
| ours | DialogResponses | new |  `8002C2:Argonia.esp` |
| ours | DialogResponses | new |  `8002C3:Argonia.esp` |
| ours | DialogResponses | new |  `8002BC:Argonia.esp` |
| ours | DialogResponses | new |  `8002BE:Argonia.esp` |
| ours | DialogResponses | new |  `8002BF:Argonia.esp` |
| ours | DialogTopic | new | ARG_LQ25_T_a6231052 `800205:Argonia.esp` |
| ours | DialogResponses | new |  `800105:Argonia.esp` |
| ours | DialogResponses | new |  `800106:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ03_T_1117a83c `80017B:Argonia.esp` |
| ours | DialogResponses | new |  `80017D:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_3c081190 `800391:Argonia.esp` |
| ours | DialogResponses | new |  `800394:Argonia.esp` |
| ours | DialogResponses | new |  `800395:Argonia.esp` |
| ours | DialogResponses | new |  `800393:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_HelloAfter `800176:Argonia.esp` |
| ours | DialogResponses | new |  `800177:Argonia.esp` |
| ours | DialogTopic | new | ARG_BlockTest_T_957ac1dd `800101:Argonia.esp` |
| ours | DialogResponses | new |  `800052:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_cf1e9cd7 `800386:Argonia.esp` |
| ours | DialogResponses | new |  `800388:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ01_T_4581b4d8 `80016A:Argonia.esp` |
| ours | DialogResponses | new |  `80016C:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC03_T_61e03436 `80037E:Argonia.esp` |
| ours | DialogResponses | new |  `800381:Argonia.esp` |
| ours | DialogResponses | new |  `800385:Argonia.esp` |
| ours | DialogResponses | new |  `800383:Argonia.esp` |
| ours | DialogResponses | new |  `800380:Argonia.esp` |
| ours | DialogResponses | new |  `800384:Argonia.esp` |
| ours | DialogResponses | new |  `800382:Argonia.esp` |
| ours | DialogTopic | new | ARG_MQ04_T_98f66550 `8001D0:Argonia.esp` |
| ours | DialogResponses | new |  `8001D2:Argonia.esp` |
| ours | DialogResponses | new |  `8001D3:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_545d9b56 `8002D3:Argonia.esp` |
| ours | DialogResponses | new |  `8002D5:Argonia.esp` |
| ours | DialogTopic | new | ARG_BC02_T_134e61ff `8002F8:Argonia.esp` |
| ours | DialogResponses | new |  `8002FB:Argonia.esp` |
| ours | DialogResponses | new |  `8002FA:Argonia.esp` |
| ours | quest | new | ARG_BC02 `80021B:Argonia.esp` |
| ours | quest | new | ARG_TG02 `800003:Argonia.esp` |
| ours | quest | new | ARG_BC01 `80021A:Argonia.esp` |
| ours | quest | new | ARG_BlockTestTwo `800000:Argonia.esp` |
| ours | quest | new | ARG_LQ30 `8000C1:Argonia.esp` |
| ours | quest | new | ARG_MQ04 `8000C4:Argonia.esp` |
| ours | quest | new | ARG_BlockTest `800001:Argonia.esp` |
| ours | quest | new | ARG_MortalWatch `800098:Argonia.esp` |
| ours | quest | new | ARG_MQ03 `8000C3:Argonia.esp` |
| ours | quest | new | ARG_Opening `000801:Argonia.esp` |
| ours | quest | new | ARG_MQ05 `8000C5:Argonia.esp` |
| ours | quest | new | ARG_Talk `000833:Argonia.esp` |
| ours | quest | new | ARG_MQ01 `8000C2:Argonia.esp` |
| ours | quest | new | ARG_BC03 `80021C:Argonia.esp` |
| ours | quest | new | ARG_LQ25 `8000C0:Argonia.esp` |
| ours | quest | new | ARG_TG01 `800002:Argonia.esp` |
| ours | Package | new | ARG_BlockTest_ForceGreet `800058:Argonia.esp` |
| ours | Package | new | ARG_MQ01_ForceGreet `800175:Argonia.esp` |
| ours | VoiceType | new | ARG_TalkSilentVoice `000834:Argonia.esp` |
| ours | Message | new | ARG_BlockTest_Msg_063e07 `80000C:Argonia.esp` |
| ours | Message | new | ARG_BlockTest_Msg_5d8ada `80000D:Argonia.esp` |
| ours | Message | new | ARG_BlockTest_Msg_fe1380 `80000E:Argonia.esp` |
| ours | Message | new | ARG_BlockTest_Msg_46f5de `80000F:Argonia.esp` |
| ours | Message | new | ARG_MortalWatchFaction `800099:Argonia.esp` |
| ours | Message | new | ARG_BlockTest_Msg_d0c82a `800037:Argonia.esp` |
| ours | Message | new | ARG_MortalWatchMain `800204:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_B_8dccb2ff `800078:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_DangerBranch `000931:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_5f22f242 `8002F3:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_7f842221 `8002B0:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ05_B_3c6803ab `8001ED:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_0219476b `80039A:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_cf1e9cd7 `800387:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_e0f6b40a `80024B:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_3e303c46 `800336:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_B_03930597 `80007E:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_SFB_fa1bcdd7 `800171:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_134e61ff `8002F9:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_B_84516bd8 `8000B9:Argonia.esp` |
| ours | DialogBranch | new | ARG_LQ25_B_1ed95258 `80020A:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_B_73b14da4 `800168:Argonia.esp` |
| ours | DialogBranch | new | ARG_BlockTest_B_58651bd7 `80003D:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_SecretBranch `000A87:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_3c081190 `800392:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_B_f15977f3 `80016E:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_55740835 `8002B3:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_B_3d3e1113 `800153:Argonia.esp` |
| ours | DialogBranch | new | ARG_LQ30_B_2750ee8b `800125:Argonia.esp` |
| ours | DialogBranch | new | ARG_BlockTestTwo_B_e0977919 `80002C:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_DirectionsBranch `00093C:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_f33f4595 `80034D:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ05_B_8b43ea5e `8001F1:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_e63801a1 `80038A:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_e86b4b18 `8002DA:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_B_31c6171c `800213:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_0be36d62 `800342:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ04_B_955a8628 `8001CE:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_LootBranch `000A18:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_B_ecd2c000 `800083:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_2b6dd5e3 `8003A0:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ04_B_665a16fe `8001D5:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_B_1bc650ae `80007B:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG01_B_83aeeed8 `80005C:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_B_32a136e6 `800150:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_d7c71ee9 `8002D1:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_3bf6c1fc `80027B:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_06258fe9 `800294:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_2d233477 `80033F:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_fe0f680a `800351:Argonia.esp` |
| ours | DialogBranch | new | ARG_BlockTest_B_25ea342a `800039:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ03_B_52b4b715 `80017F:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_B_b6b60993 `80015F:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_5d837c8f `80039D:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ04_B_633300f4 `8001A6:Argonia.esp` |
| ours | DialogBranch | new | ARG_LQ30_B_b8e72cf6 `800129:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ04_B_d1a5b71c `8001D9:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ05_B_4150bea9 `8001F7:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_HarvestBranch `000999:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_B_5c207ac9 `80013E:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ03_B_952fcb5f `800182:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_B_677f6e10 `8000BD:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_B_7605f2c4 `800165:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_769b24d5 `8002ED:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ04_B_f366a7c0 `8001A9:Argonia.esp` |
| ours | DialogBranch | new | ARG_BlockTestTwo_B_37c8386d `800032:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ04_B_744e3fd7 `8001BB:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_B_c6b5b34f `800149:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_a145d133 `80026A:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_4ee7a9c6 `8002CB:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_B_f4438851 `800159:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_SomeoneBranch `000B13:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_SelfBranch `000A91:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ04_B_09915509 `8001B5:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_3998e621 `800348:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_8873f82b `80036A:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ05_B_ffe2c41a `8001EA:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG01_B_ca106a9a `800063:Argonia.esp` |
| ours | DialogBranch | new | ARG_BlockTest_B_84ed37ec `800035:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_4eedd22d `800359:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_B_2d4b48d9 `800162:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_bc946ca8 `800339:Argonia.esp` |
| ours | DialogBranch | new | ARG_BlockTestTwo_B_65596e18 `80002F:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_37f913ba `80031D:Argonia.esp` |
| ours | DialogBranch | new | ARG_BlockTest_SFB_ead80562 `800054:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_B_4581b4d8 `80016B:Argonia.esp` |
| ours | DialogBranch | new | ARG_LQ25_B_a6231052 `800206:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ04_B_316b9879 `8001C1:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_7f60290f `80024E:Argonia.esp` |
| ours | DialogBranch | new | ARG_LQ25_B_a0d773bf `80020C:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_6568248a `8002B9:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_07966bc6 `8002C5:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG01_B_1c3bdc3b `800066:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ04_B_aef146d9 `8001C5:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_AdviceBranch `000924:Argonia.esp` |
| ours | DialogBranch | new | ARG_BlockTest_B_e3b31068 `800049:Argonia.esp` |
| ours | DialogBranch | new | ARG_BlockTest_B_957ac1dd `800102:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_07966bc6 `800333:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_8aa699ed `80025A:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_4431ef00 `8002FD:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG01_B_e16794f7 `80006E:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ05_B_aeef371a `8001E4:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_425a2291 `80031A:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ04_B_2ff641c2 `8001C8:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_3e303c46 `80025D:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_e6f5743d `8002D7:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_7b75483d `800301:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_b73068ed `80035F:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_7920a4b1 `800266:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_a383d1bd `800309:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_f77d67ea `8002A0:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_aa80ca41 `8002AA:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_3845ae9d `8002DD:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ04_B_3845ae9d `8001AC:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_901a2612 `800263:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ03_B_628d5dba `800189:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_3845ae9d `80033C:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_HereBranch `0009AC:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_a561438e `800254:Argonia.esp` |
| ours | DialogBranch | new | ARG_BlockTest_B_5b312054 `800100:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_3e303c46 `8002C8:Argonia.esp` |
| ours | DialogBranch | new | ARG_LQ30_B_c95d6ca2 `80011E:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_62e0f989 `80029A:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ05_B_5967412a `8001E7:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_c5be3433 `8002E4:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ03_B_3845ae9d `800185:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_f72eda2d `800377:Argonia.esp` |
| ours | DialogBranch | new | ARG_BlockTest_B_a52b437c `800045:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ03_B_e017d919 `800179:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_a1d959fd `8002AD:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_6a8cce7e `800372:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_8aefbdc5 `800251:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_LoreBranch `000A1E:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_B_a4d5fa15 `8000AA:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG01_B_d12103c8 `800072:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_B_e043fb1a `800156:Argonia.esp` |
| ours | DialogBranch | new | ARG_LQ25_B_2e4f6289 `800208:Argonia.esp` |
| ours | DialogBranch | new | ARG_BlockTest_B_cf09a8f9 `80004D:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_95ce292b `800362:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_0aca202e `8002A3:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_3730f329 `800287:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_61e03436 `80037F:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ05_B_27b6f161 `800211:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_7441b8c7 `800257:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_B_9f2ee7f5 `80015C:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_ab1fc3b1 `8002E1:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG01_B_24c18a85 `80005F:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_d63d54b2 `800317:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_545d9b56 `8002D4:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_TradeBranch `000B81:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_b0f19f27 `800397:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_B_2d9326df `80013A:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ03_B_1117a83c `80017C:Argonia.esp` |
| ours | DialogBranch | new | ARG_LQ30_B_9fa3394c `800122:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_5727e8cd `8002E7:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_B_f1f2ab72 `8000B0:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_3845ae9d `800260:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_a1302c62 `800320:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC03_B_9cd405e4 `80038E:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ04_B_2c3e5ca3 `80020F:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_ServicesBranch `000B0A:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG02_B_e5c77b4b `800215:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_49af4ccf `80026F:Argonia.esp` |
| ours | DialogBranch | new | ARG_Talk_RumoursBranch `000A7A:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC01_B_fc621a33 `8002B6:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_6ee41b3c `800305:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ05_B_f957c0c4 `8001FB:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ04_B_98f66550 `8001D1:Argonia.esp` |
| ours | DialogBranch | new | ARG_MQ01_B_3845ae9d `800142:Argonia.esp` |
| ours | DialogBranch | new | ARG_BC02_B_1c24a985 `8002CE:Argonia.esp` |
| ours | DialogBranch | new | ARG_TG01_B_6e367228 `80009B:Argonia.esp` |
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
| openings-held | quest | Start Game Enabled off | AANEWQuestM `0F0F3E`, 01Captain `03B21E`, 0MainQuest1 `0BCC51` |
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
