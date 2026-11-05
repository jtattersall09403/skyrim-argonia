<!-- imported unchanged from elder-souls-argonia docs/world/92-demographics.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# Part XII — Demographics and community expectations (§81–84)

> Module of the world-generation master plan — see [README](README.md) for the router
> and [00-core.md](00-core.md) for the universal principles. Section numbers (§NN)
> preserved from the original plan; cross-doc references resolve via the README map.

## 81. Demographic fields

Demographics should be generated from:

- era;
- region and tribe territory;
- proximity to ports, borders and dependable roads;
- settlement purpose;
- faction control;
- migration and slavery history;
- disease history;
- current conflict;
- Hist access;
- local economy;
- route centrality.

```ts
interface DemographicPrior {
  id: DemographicPriorId;
  era: EraRange;
  region?: RegionId;
  settlementType?: SettlementTypeId;
  populationShares: Record<PopulationGroupId, Range>;
  confidence: SourceConfidence;
  sourceUrl: string;
  sourceImageHash?: string;
  author?: string;
  methodology?: string;
  notes?: string;
}
```

A deep Hist settlement and a port city should have different populations even at similar size.

## 82. Reddit demographic charts: supplied community priors

The referenced r/ElderScrolls demographic maps have now been supplied directly for eight population groups. They should be ingested into the source registry as **community-authored demographic priors**, not treated as canonical census data. Their strongest value is spatial: they encode a coherent fan interpretation of where outsider populations are concentrated and therefore provide useful priors for settlement populations, cultural mixing, architecture, trade, faction presence and encounter generation.

The attached charts give the following province-wide headline shares:

| Population group | Chart headline share |
|---|---:|
| Argonian | 72% |
| Dunmer | 10% |
| Imperial | 8% |
| Khajiit | 5% |
| Nord | 2% |
| Bosmer | 2% |
| Altmer | 1% |
| Redguard | 1% |

These rounded headline values total 101%, so they must be treated as approximate community estimates. No missing race should be inferred to have exactly zero population merely because a chart was not supplied.

The charts divide Black Marsh into seven broad spatial zones identifiable by their nearest labelled settlement anchors. The supplied percentages are:

| Chart zone / nearest anchors | Argonian | Dunmer | Imperial | Khajiit | Nord | Bosmer | Altmer | Redguard |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Stormhold / northern-western border | 75% | 22% | 2% | 2% | 7% | 2% | 2% | 2% |
| Thorn / northeastern-east zone | 75% | 20% | 2% | 1% | 3% | 1% | 1% | 1% |
| Helstrom / deep central interior | 97% | 1% | 1% | 1% | 1% | 1% | 1% | 1% |
| Gideon / western frontier | 70% | 3% | 22% | 6% | 1% | 1% | 1% | 3% |
| Soulrest / southwestern coast | 60% | 1% | 13% | 19% | 1% | 5% | 1% | 1% |
| Archon / southeastern-east coast | 79% | 15% | 5% | <1% | <1% | <1% | <1% | <1% |
| Blackrose–Lilmoth / southern zone | 80% | 3% | 7% | 6% | <1% | 10% | 3% | 1% |

Because the source graphics use rounded values independently by race, the rows are not expected to sum cleanly to 100%. The zone boundaries should be stored as traced community-map polygons or raster masks with source confidence metadata rather than being silently promoted into canonical political borders.

The pattern is useful and broadly reinforces the world architecture proposed here:

- **Helstrom/deep interior:** overwhelmingly Argonian. This strongly supports the deep-marsh core as culturally local, difficult for outsiders to penetrate and structurally unlike the peripheral cities.
- **Stormhold and Thorn:** large Dunmer minorities, with the northern edge also showing the strongest Nord presence. This supports a visibly Morrowind-facing northern frontier shaped by trade, migration, conflict and older slavery relationships.
- **Gideon:** the strongest Imperial concentration in the supplied set. This supports making the western fringe one of the clearest places to show imported Imperial infrastructure, estates, engineered roads/causeways and the remains or continuation of colonial institutions.
- **Soulrest:** the most mixed supplied zone and by far the strongest Khajiit concentration, alongside substantial Imperial and Bosmer minorities. Its settlement/economic grammar should therefore support maritime and overland trade, migration and mixed neighbourhoods.
- **Blackrose–Lilmoth:** still strongly Argonian but with notable Bosmer, Imperial, Khajiit and Altmer presence. This provides a basis for a cosmopolitan southern-waterway/coastal layer while retaining a Saxhleel majority.
- **Archon:** Argonian-majority with a substantial Dunmer minority and smaller Imperial presence, supporting an eastern coastal contact zone with a distinct social history from the western Imperial fringe.

These distributions should influence probability priors for ordinary NPC populations and culturally derived content, while **location-specific causal history remains authoritative**. A Dunmer trading enclave, Imperial expedition, Bosmer hunting party or Khajiit merchant flotilla can exist outside its statistically common zone when its reason for being there is explicit. Likewise a Hist-bound settlement inside a mixed region may remain almost entirely Argonian.

### 82.1 Race shares used by the roster (ten races, by place type)

Home: `world/sources/demographics/population-priors.json` (zones, `cultureZoneMap` for every catalogue region, `placeTypeOutsiderMultiplier`, `placeTypeOf`); code: `worldgen/npc_roster.py` `race_shares`. Breton and Orc are absent from the charts, so every zone row carries a derived 0.5 for each (DERIVED, not community data; grounding Lore:Lilmoth, Hereguard Plantation as one of the few Breton settlements; Lore:Orcs has no Black Marsh content, so the Orc weight is a trace).

The rule. The zone row's Argonian share is held at capital scale and the other races split the remaining share in proportion to the row's own non-Argonian values. A place type multiplies that remaining (outsider) share (capped at 100) and Argonians take the rest. The place type is read from the catalogue record's `classification` (`type`, then `class/family`, then `class`; `placeTypeOf` in the priors file). Multipliers are a modelling choice grounded in the fringe-versus-interior pattern (Lore:Black Marsh, Lore:Gideon, Lore:Stormhold, Lore:Helstrom); no source gives the numbers. The roster seed is unchanged.

| Place type | Outsider multiplier | Catalogue classification |
|---|---:|---|
| capital | 1.0 | settlement/major-city |
| port | 2.0 | `type` port-town, neutral-free-port, legal-harbour-city, island-confluence-city, rebuilt-stilt-city, contested-ex-capital; settlement/free-port |
| border-town | 1.5 | settlement/mixed-settlement, settlement/imperial-settlement |
| village | 0.4 | settlement/dry-village, tribal-village, water-village, outcast-settlement, homestead |
| camp | 0.1 | class camp |
| works | 0.8 | class works |

Table A, zone rows at capital scale (percent, ten races; Argonian as charted, the rest split as above):

| Zone | Argonian | Dunmer | Imperial | Khajiit | Nord | Bosmer | Altmer | Redguard | Breton | Orc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| stormhold | 75.0 | 13.8 | 1.2 | 1.2 | 4.4 | 1.2 | 1.2 | 1.2 | 0.3 | 0.3 |
| thorn | 75.0 | 16.7 | 1.7 | 0.8 | 2.5 | 0.8 | 0.8 | 0.8 | 0.4 | 0.4 |
| helstrom | 97.0 | 0.4 | 0.4 | 0.4 | 0.4 | 0.4 | 0.4 | 0.4 | 0.2 | 0.2 |
| gideon | 70.0 | 2.4 | 17.4 | 4.7 | 0.8 | 0.8 | 0.8 | 2.4 | 0.4 | 0.4 |
| soulrest | 60.0 | 1.0 | 12.4 | 18.1 | 1.0 | 4.8 | 1.0 | 1.0 | 0.5 | 0.5 |
| archon | 79.0 | 13.4 | 4.5 | 0.4 | 0.4 | 0.4 | 0.4 | 0.4 | 0.4 | 0.4 |
| blackrose-lilmoth | 80.0 | 1.9 | 4.4 | 3.8 | 0.3 | 6.3 | 1.9 | 0.6 | 0.3 | 0.3 |

Worked example, Helstrom zone (outsiders 3.0 at capital scale): port 6.0 outsiders (Argonian 94.0), border-town 4.5 (95.5), village 1.2 (98.8), camp 0.3 (99.7), works 2.4 (97.6), shrine (every `sacred` class) 0.9 (99.1), hist-village 0.3 (99.7). The gate `roster.shares` (`place_gates.roster_gate`, `npc_roster.roster_share_errors`) fails a place whose generated residents sit more than one person from these counts, or whose whole roster (20 people or more) is more than 12 points of Argonian share from its prior. A Helstrom of about 330 residents therefore holds about ten non-Argonians, each carried by an explicit reason in the roster (the override rule above).

UESP pages behind the zone patterns: Lore:Helstrom (interior "impenetrable", never taken), Lore:Black Marsh (inland Argonian majority; tribal villages; colonial ventures outside the slave trade failed), Lore:Stormhold (House Dres foothold, Dunmer minority), Lore:Thorn, Lore:Gideon (Nibenese Imperials, Commerce Road traders), Lore:Soulrest, Lore:Blackrose, Lore:Lilmoth, Lore:Archon, Lore:Dunmer, Lore:Khajiit.

For source provenance, record the eight supplied image hashes:

| Population group | Supplied image SHA-256 |
|---|---|
| Argonian | `0b7b57ffa2034c05aa9733c75ee5a171645adaa017bf91b4b34aff3fc1b2cccb` |
| Dunmer | `73fd7908ba0f403624c7441f4d91c2ddee6a105246931bff104c200cb60c697d` |
| Imperial | `fabd0a31bbfcf295932f190f582331202efce6018b055ad66996715e528f427c` |
| Khajiit | `6f5cb1cfea7b8d5f131b28f4432980204382ffba93df75a3fcc4aef5a2c1c696` |
| Nord | `abc8974ede41c118a582ab2d8dbf8aae8b6bec1c4c3a2309c490587b4d2e1f95` |
| Bosmer | `4a35b259553f8f10ec62471f698437cd547f96bc7475368c2d0b45bbbc942679` |
| Altmer | `8812bf7375fbbecbf7f9af3a4db2656346735dfcb74b0000600d40603368470b` |
| Redguard | `c239a8ad42e812b99c11bfe211a36bd6ae016969d417ab5aaf60f045a4b340e8` |

If the original Reddit post is later located, add its author, URL, publication date, claimed era and methodology without changing the image-derived data unless the source itself corrects it.

## 83. Qualitative community themes

Available Reddit-linked discussions, fan projects and Black Marsh design discussions show recurring interest in:

- a province that feels alien and biologically distinct;
- deep Hist involvement;
- tribal and cultural variety among Argonians;
- dangerous interior marshes;
- underwater exploration;
- unusual transport and navigation;
- visible failed Imperial colonisation;
- ancient Xanmeers and lost peoples;
- varied landscapes beyond one continuous green swamp;
- the opportunity to play an Argonian in a homeland designed around amphibious capability.

This is a qualitative synthesis. It is not a representative survey. The design aligns well with those themes while retaining source confidence and fixed gameplay requirements.

## 83b. What the settlement register's size bands count

The register's per-magnitude bands (M3 12–35, M4 40–120, M5 150–400) count
**total placed objects**: buildings, structures, props and dressing together.
They are not a building count. The count a blueprint is judged on is the
Morrowind ratio — Balmora reads as a city on roughly 40 buildings and
structures, so an M5 is 50–80 of them, with the rest of the register's figure
made up of the props and dressing that make the place look inhabited
(97 D7 and C5b; implementation-lead decision, recorded in
[decision 0041](../old-decisions/0041-phase11-settlement-decisions.md)).

## 83c. Population caps

How many people the province holds, set against the base games (the
numbers and their UESP pages are in the dossier
[population-and-creature-parity](../../../world/sources/lore/topics/population-and-creature-parity.md)).
Fish, insects and birds are ambient scenery, never counted.

| Scope | People |
|---|---|
| Helstrom | target 300, cap 320 (under Vivec's 326), at least 100 named |
| Each other city | cap 120 (no more than Ald'ruhn) |
| Town | 25–35 |
| Village, camp | 3–12 |
| Province | 2,400–2,700 (*Morrowind* with its expansions; *Skyrim*'s ~860 is the floor) |
| Creature species | 48–52 (the base games' count plus 6–10, never their add-on totals) |

## 84. Demographic design implications, and the prior→roster rule (16g)

**The prior→roster rule.** The roster in `world/sources/registries/npcs.json`
is built by `worldgen.npc_roster` from two sources and never hand-written.
Every `notableNpcSlots` entry on a live place record becomes one roster
record. A place's blueprint occupants (`kind` `person`, the default) then join
the record their slotId names or become `occupant` records (named, guards
among them), and its `generated` occupants become unnamed `resident` records
whose race is the place's `race_shares` split by largest remainder.
`creature` and `group` occupants are not roster people. Each occupant record
carries a `post` naming its blueprint occupant, parcels and npc socket. The
slot clauses:

1. **Id** `npc.<region>.<place-slug>.<slot-slug>`, permanent (engineering
   standard 2). A slot that the cast roster of quests 36 already names takes
   that cast member's id and name, never a second identity.
2. **Race and sex** are drawn deterministically (seeded by the id) from the
   zone's population priors (§82) restricted by the place's `culture` and
   any race the slot text names; sex is even unless the slot or the cast
   says otherwise (decision 0054: sex is an axis).
3. **Name** by the culture register's form for that race and region
   (quests 35 §54; style guide §1.5): Jel or translated Tamrielic for
   Argonians by region idiom, Latinate Imperial, Dunmer given + house,
   Khajiit prefix or epithet. Caps checked mechanically per region roster:
   at most one third Verb-the-Noun, no repeated imagery within a place,
   no name reused province-wide. The whole roster is text-reviewed in bulk.
4. **Faction, home and role**: the matching `contents.npcs[]` slot's
   faction, else the record's `ownerFaction`; home is the place id and the
   slot index (a socket id once the blueprint has one); role is the slot's
   own words.
5. **Shape**: the 10b `NpcRecord` field list (identity, race, sex, factionIds,
   home, role, then typed empty slots `statblock`, `archetype`,
   `hostility`, `fightFleeAlarm`, `marks`, `schedules`, `patrols`,
   `dialogueTopics`, `services`, `crime`, `standing`), `status: generated`,
   so 10c extends the record without renaming it.

Every slot resolves to a record and every generated record to a live slot
(`test_npc_roster`).

**Where a slot stands in a built place.** Each roster slot of a place built
in the 16k loop has an `npc` socket (decision 0103 decision 5) whose
`rosterSlotId` is the slot id and whose schedule names a `work` and a `home`
`idle` socket. The compile's `sockets.roster` gate (`worldgen/sockets.py`)
fails a slot with no `npc` socket. It also fails an `npc` socket whose
schedule lacks a `work` or `home` entry naming an `idle` socket.

**Design implications.**

- Deep rootlands should be overwhelmingly Saxhleel and culturally local in eras where lore supports that state.
- Ports and border cities can have mixed populations shaped by trade, occupation, slavery, migration and political history.
- Current tribes require distinct demographic and social rules.
- Historical peoples appear through archaeology after their disappearance.
- Small outsider expeditions need visible logistical support and motives.
- Demographic fields should affect architecture, language, services, factions, clothing, boats, food, religion and quest structure.

---

