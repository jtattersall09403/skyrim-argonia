# Journal: people's AI (NPC_ and PACK records, lane npc-ai)

What an NPC_ of ours needs, next to a vanilla one, to run its packages; how we measured that; and what is still
open, so the next lane does not repeat the read.

## 2026-10-30: Claywater's people run no AI (game-7 on f62ff062)

**Symptom (game-7, L4).** All four people read GetCurrentAIPackage -1. Their procedure is -1 at 12:00 and 49 at
23:00. They stand where they were placed. Livia does not move after StartCombat (she is in combat, procedure -1),
even 200 units from the player. Her 3D is loaded but she wears nothing. The bed target is persistent.

**How it was read.** `ArgoniaGen npcai --data <Data> [--plugin p] --edids a,b|auto:n|outfits` is a read-only
Mutagen dump over the binary overlay. It reads explicit NPC_ fields, its PACKs (by reflection) and the WRLD
persistent cell's actors (PackageRecords.cs). It peaks at 195-366 MB. A first version walked the whole NPC_ by
reflection and ran to 10.9 GB before the planner killed it; never reflect over an NPC_ overlay. The vanilla
comparators are Bendt (0E77CB) with his Sandbox and Sleep templated PACKs, Hefid (09400E), SailorXander (0AF523),
and the four templates our people use.

### NPC_: vanilla vs ours (before this lane)

| Field | Vanilla (Bendt / Hefid / TreasCorpseCommoner*) | Ours (ARG_Npc_N1, N13, WellKeeper...) | Verdict |
|---|---|---|---|
| ACBS flags | AutoCalcStats, Unique (Hefid: Unique, stats in DNAM 73/50/57) | Unique only; DNAM health/magicka/stamina 0 | **fixed**: AutoCalcStats on (class + level) |
| Template / flags | none (they are the templates) | TreasCorpse*/WERoadCourier, Traits only | kept: face, body, voice come from it |
| Voice (VTCK) | set (013AD7...) | null; Traits gives the template's (013AEE, 013AEF, 013ADE, 013AD1, all set) | ok by Traits |
| AIDT | Unaggressive, Average/Cowardly, **energy 50**, NoCrime, HelpsNobody | Unaggressive, Average, **energy 0** (Mutagen default), AnyCrime | **fixed**: energy 50, NoCrime, Neutral, HelpsNobody |
| CNAM class | 01326B Citizen etc. | 000806 ARG_Class_* (ours) | ok, present |
| Combat style | null for commoners (Bendt, Hefid), set for fighters | null | ok (race default, as vanilla commoners) |
| Packages (PKID) | 1-3 | 2 (Day sandbox, Sleep) | ok |
| DOFT / SOFT | DOFT always; SOFT on some | **none** (naked) | **fixed**: DOFT from `build_person.outfit_form_key` |
| Race | set | set (013744, 013740) | ok |
| Factions | 0-3 (crime, town) | none | open: no faction is needed for packages; a crime faction owes the town's |
| Sound level | Normal | Loud (Mutagen default) | **fixed**: Normal |
| Default/override package lists | null | null | same |

### PACK: vanilla templated vs ours (before this lane)

| Field | Vanilla (SolitudeBardsCollegeBendtSandbox4x18, 10DEB5 sleep, HefidSandboxHome) | Ours | Verdict |
|---|---|---|---|
| Type / PKCU template | Package, 01C254 / 019717 | same | same |
| DataInputVersion | 10 / 6 | 10 / 6 | same |
| Data inputs | 12 sandbox, 17 sleep | 12, 17 | same count, same indices |
| Input Name/Flags | **absent** (no UNAM/BNAM/PNAM of their own) | Name null, **Flags 0** (written) | **fixed**: Flags null |
| Events (OnBegin/End/Change) | empty topic + no idle, **no SCHR** | same plus the template's **SCHR** | **fixed**: SCHR dropped |
| Procedure tree | empty (0) | empty (0) | same |
| Conditions, combat style, owner quest | none | none | same |
| PKDT flags | 0 / WeaponsUnequipped (Hefid NoCombatAlert) | 0 / WeaponsUnequipped | same |
| Interrupt flags | 65279 / 65535 / 64740 | 65271 (template's) / 65535 | differs by GreetCorpse bit only; kept |
| PKDT unknown byte | 0, 63, 117, 130, 142 | 0 | CK repack noise; kept |
| Schedule | hour, minute -1, duration | hour, minute 0, duration | ok |
| Location | ref / cell / NearEditorLocation, radius | ref (persistent), 560 | ok |

### Placement

The six actors are in ArgoniaWorld.esm's persistent cell 000801 (Argonia.esm's WRLD override), with the
Persistent flag 0x400, as vanilla files exterior persistent actors. Nothing differs that the record read can see.

**Reading.** No record difference explains a total stop: an actor with energy 0, no outfit and zero DNAM would
still pick a package and fight. The differences are fixed so our records match a vanilla townsperson. The
whole-AI stop (no package, no movement in combat) points at the session or the place. Candidates for game-7:
1. AI toggled off globally: `tai` in `infra/gpu-box/smoke.py:234,239` toggles all actors' AI. If the smoke ever
   stopped between the two toggles, the session or base save ran with AI off.
2. The persistent placement.
3. The place's navmesh. Pathing would leave the package set but the procedure failing, which does not match -1.

`tests/scenes/claywater-control.txt` splits them. It places vanilla Golldir (a Sandbox PACK near his editor
location) and a temporary copy of our Livia's base at Livia's work spot.

**L1 check.** `place_build.check_people` fails the build when a person's NPC_ lacks packages, AI data, outfit or
class, or when a PACK's `inputCount` differs from `packages.TEMPLATE_INPUTS`. ArgoniaGen also refuses a PACK
whose written input count differs. It was proved failing once on the real data: Livia's outfit row blanked gave
`ARG_Npc_WellKeeper: no outfit`. The unit tests are tools/argonia_world/tests/test_people_records.py.

**Outfits are stand-ins** (`outfit_stand_in = 1`). They are King of the Murkmire's Saxhleel tunics (grey, green,
orange) and AnWamasuLeatherOutfit01 for Livia, in place of each npc's `look_outfit`, until that clothing is ours.
