# World registries

One framework for every id-linked **vocabulary** in the world: the things place
records, quests and (later) the runtime point *at* rather than contain.

Loader/validator: `tooling/world-generation/worldgen/registries.py`
(`python3 -m worldgen.registries --check`). Rationale: [decision 0044](../../../docs/decisions/0044-world-registries.md).

## The shape (all files identical)

```json
{ "schemaVersion": 1, "domain": "faction", "entries": [
  { "id": "faction.naga-kur", "name": "The Naga-Kur", "kind": "tribal-power",
    "status": "canon", "sources": ["UESP:Lore:Naga"], "notes": "one line", ... }
]}
```

- **id** — `<domain>.<slug>`, lower kebab, globally unique across *all*
  registries, never reused. These are vocabulary ids, not placed-object ids, so
  the two-segment form is legal (engineering standard 2's three-segment shape is
  relaxed per-source by `"idShape": "flat"` in `tooling/repo-standards/id-registry.json`).
- **status** — `canon` (in the lore, and `sources` must prove it), `derived`
  (project extrapolation with a written basis), `placeholder` (the id is in use
  or reserved; the brief is not written yet).
- **assetAvailability** — on `item` and `npc` entries (creatures carry the same block as `sourcing`, plus a `redesign` line): can we
  actually put this on screen? `{status, via, notes}` where status is
  `vanilla` (vanilla Skyrim actor/prop), `sourced` (mesh already in the
  vault), `sourceable` (a named Nexus mod would supply a rigged mesh with
  its own animations; not downloaded, licence unchecked) or `none` (nothing
  can deliver it as an actor, so it is staged as an effect or dropped).
  **No new animations, ever**: a creature needs a mesh that ships its own
  animation set or sits on a vanilla skeleton. Verdicts and the sourcing
  shortlist: [docs/research/lore/creature-asset-availability.md](../../../docs/research/lore/creature-asset-availability.md).
  An item's optional `records` lists the plugin base editor ids it stands
  for: `loot_fill --cell` fills a cell's item socket by its base first,
  then by model stem (`worldgen.plugin_items` reads those records' weight,
  value and name).
- **notes** — one line, always. Domain fields (`code`, `tier`, `milestone`,
  `line`, `faction`, `mergeCandidate`, …) sit alongside.

## The registries

| File | Domain | What it holds | Who grows it |
|---|---|---|---|
| `factions.json` | `faction` | The 32 real factions with their standing rules (`standing.join`: `how` none/open/sponsor/rite/quest, a quests/85 `requires`, `sponsor`, `entryQuest`, `refusal`, `sources`; `standing.expel`: `applies`, `causes`, `cost`, `return`, `unstated`, `sources`, gated by `registries.faction_expel_problems`; gated by `registries.faction_join_problems`) and the reaction matrix (40-factions §27a–28); a place's own community is a catalogue `localGroups` label, never an entry here | 40-factions authors; quest authors |
| `quests.json` | `quest` | Every quest and questline id, with code, tier, milestone and owning faction | Quest authors (docs/quests) |
| `creatures.json` | `creature` | **The creature species home table**: one row per species in the province with statblock (the contract's `Statblock`), band list, hostility, `fightFleeAlarm`, reaction, notice, den, territory, day blocks, habitat, diet, harvest, `whyHere`, `sourcing` and `look.modelSet`; the design and readable table is [world/74](../../../docs/world/74-ecology.md); `contents.creatures[].registerRef` points here | 2.4c1 (rows), 2.4c2 (`look.modelSet`); Part 4 packets add regions' rows |
| `npcs.json` | `npc` | **Generated.** One entry per live `notableNpcSlots` post, plus the written cast joined to their slots | `worldgen.npc_roster` (never by hand) |
| `items.json` | `item` | **The Item home table** (schemaVersion 2): one record per thing the player can hold (kind, subkind, model, icon, weight, value, pocket, verb, condition, ladder, whyHere; gear names its `set`, and `sets` carries each material set: wood, studded, iron, bronze, steel, bone, imperial, silver, dwarven, elven, orcish, falmer, forsworn, akaviri, glass, obsidian, ebony, daedric; gear whose `sources` name a plugin WEAP/ARMO record carries `materialFrom`, the plugin's material keyword or temper ingredient, and its `set` follows it, written and checked by `worldgen.items_material`) | 2.3a; the province load is Part 4's. `worldgen.item_views` derives the game view and the catalogue text |
| `locks.json` | `lock` | Lock records: level (1–100), class, the key item that opens it (a key names its lock back), spellKey, trap, opens {place, ref}, owner | Whoever places a locked container or door |
| `physical-materials.json` | `material` | The 14 module 75 §54 collider materials with their arrow `projectileResponse` (§55); `worldgen.material_views` derives the game view | 2.7a2; footstep, impact and other responses join later |
| `detection.json` | `detection` | The detection home table: a person's and each enemy archetype's profile, the defaults that complete a creature's (spot, alarm radius, search timeout), and the noise, light, sneak-attack, eye and searching tables; `worldgen.hostile_loot` copies `detection.person` into person records; `worldgen.stealth_views` derives the runtime view | 2.10a |
| `traps.json` | `trap` | Trap kinds: Morrowind's trapped-lock spells as effects.json effects | 2.10a |
| `owing.json` | `owing` | The Owing per catalogue region: assessor, rates, custody, amnesty, or the blockers that keep a row out of the view | 2.10a |
| `pickpocket.json` | `pickpocket` | The pickpocket chance rows | 2.10a |
| `creature-harvest.json` | `harvest` | One row per creature species: its `harvest` words mapped to existing item ids, genuine matches only; an empty list is a 2.3 items gap. `worldgen.hostile_loot` freezes it into a hostile creature's `loot` | 2.7b1 |
| `loot-rules.json` | `blanket` | The blanket loot rules: where each belongs, its `valueTier`, fixed item ids and counts, optional `pick`. `worldgen.loot_fill` freezes a rule on a socket at authoring time | 2.3a; 2.3c runs the fill |
| `deeds.json` | `deed` | Every `deedCounterKeys` value and every `deed.*` id a hostility flip or quest record names (gated by `registries.deed_reference_problems`) — the reputation/progress counters quest conditions read | Whoever adds a deed key to a place |
| `rumour-pools.json` | `rumour` | Every `rumourPoolKey` — the ambient talk pools; the lines live in `packages/text-catalogue` | Text workstream |

Not here, because they already validate elsewhere: **routes**
(`world/sources/routes/registry.json`), **places** (the catalogue itself),
**sockets** (`sockets.{scene,evidence,station,marks}` inside each place record),
**assets** (`worldgen.asset_registry`).

## `npcs.json` is generated — never edit it

`python3 -m worldgen.npc_roster --apply --whole-province --reason "<why>"`
writes the whole file from the catalogue's `notableNpcSlots` under the
prior-to-roster rule ([world 92 §84](../../../docs/world/92-demographics.md))
and from each reviewed place record's `life` block (2.4 a: headcount per
group, faction and its reason, depth, role exceptions, spots, one line per
person; creature groups with species, den, network and territory). Every row is a
contracts `LivingThingRecord` (`packages/contracts/src/living.ts`): people
(`npc.`) with race, sex, depth, a unique look from the premade pool
(`worldgen/data/premade-looks.json`), factions, spots and day; creatures
(`creature-at.`) with species, den, territory, `nav` (the den's network) and
their world/74 row; a creature's role and hostility default to its
`creatures.json` row. Role exceptions are `game-core/src/people/roles.json`
ids (rows carry no blocks; the runtime reads them from the registry). The same
run writes the runtime's derived view `packages/game-core/src/generated/living.json`
(the reviewed places' rows, read by `people/cast.ts`). Names
and looks are sticky: an id on disk keeps them. `--check` proves every live
slot has exactly one record, the naming caps of
[quests 35 §54](../../../docs/quests/35-cast.md) and determinism;
`python3 -m worldgen.paper_gate` (in `npm run check`) proves record and
roster agree, every slice socket is the home socket of exactly one group,
every creature den is a layout socket, and looks and names are unique.
The file carries `schemaVersion: 4` and the statuses `generated`, `cast`,
`occupant`, `resident`, `prose-referenced` and `creature`.
**Fix a name by changing a rule or a pool in `worldgen/name_forms.py` and
re-running** — a hand edit is overwritten and the stale-file check fails.

## The linking rules

1. A catalogue field that names an id must resolve into a registry. Enforced by
   `worldgen.registries.cross_check`, run by `worldgen/test_registries.py`:
   `hostility.owner`, `ownerFaction` and `contents.npcs[].faction` → `factions.json`;
   `deedCounterKeys` → `deeds.json`; `rumourPoolKey` → `rumour-pools.json`;
   `contents.creatures[].registerRef` / `npcs[].registerRef` / `loot[].registerRef`
   → `creatures.json` / `npcs.json` / `items.json`.
2. **Add the registry entry in the same change as the id.** If a catalogue edit
   leaves a gap, `python3 -m worldgen.registries --sync` appends the missing ids
   as `placeholder` entries — it never rewrites an authored one — and you then
   write the notes line.
3. Never rename an id to tidy it. Add the new one, point the old one at it with
   `mergeCandidate`, and retire the old one through
   `tooling/repo-standards/id-registry.json`'s `retired` list.
4. Player-visible text does **not** live here. `name` is an authoring label;
   the displayed string belongs in `packages/text-catalogue` keyed by the id
   (engineering standard 3). Item names and descriptions are generated into
   the catalogue from `items.json` (`worldgen.item_views`, regen row
   `item-views`), as place names are from the catalogue.
