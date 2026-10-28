# P9: Content buildout in region packets

**Goal.** Build the whole province to Morrowind density, region by region, using the slice's proven pipeline:
every catalogue place built or deliberately deferred, every NPC living, every quest line playable, the main
quest complete with its three endings, every creature placed, every book written, each region passing the same
checks the slice passed.

**Starting state.** P7 and P8 passed. The P9 packet template (written at P7's close) and measured per-item costs
exist. Owner call O-2 (move to the 20x plan) answered.

**Read first.** The P9 packet template (`docs/phases/P9-packet-template.md`, written in WP7.6); imported
`docs/design/world/00-core.md`, `20-province-design.md`, `97-placement-principles.md`, `docs/design/quests/` in full;
old decisions 0026–0030, 0041, 0098, 0099, 0102, 0103, 0128, 0132, 0133, 0138–0143, 0153; the catalogue
`world/sources/catalogue/places-*.json`.

## The inventory to build (from the import; re-count at start)

| Kind | Count in the import | Target |
|---|---|---|
| Catalogue places | 827 (567 sited; statuses active ~419, deferred ~243, ruined/abandoned/drowned/cut the rest) | every active place built; deferred reviewed with the owner |
| Dungeon-kind interiors | 327 | built as interiors from source-plugin interiors or kit assembly |
| Settlements | 132 (8 majors: Gideon, Stormhold, Thorn, Blackrose, Lilmoth, Soulrest, Archon (M5), Helstrom (M4); Alten Corimont M4) | every building enterable, every NPC named |
| People | 782 (505 generated, 140 resident, 91 occupant, 46 cast) | all placed with schedules, faces, dialogue |
| Creatures | 177 placements, 42 species (22 mod-sourced, 15 vanilla, 4 with no source, 1 sourceable) | all placed by danger band; the 4 unsourced redesigned or replaced |
| Quests | 733 rows: 24 main, 102 faction, 46 standalone (+4 concept), 18 proposed, 527 local skeletons; 38 staged | milestone M1 170–210 journaled quests; maturity 450–550 (old 0027; the quest docs' 550–740 is a stretch figure, owner to confirm) |
| Factions | 32 | every line playable to its top rank |
| Items | 508 | all reachable through loot, merchants or quests |
| Books and documents | per `documents.json` | all written to the style guide |

Density targets (old 0027): 18–22 named places per km² in low-danger land, 8–12 in deep land, something named
within 300 m of travel on every road, a landmark about every minute of walking.

## Region order

1. **The slice region** (already done in P7) extended to its full packet.
2. **pirate-freeholds** (60 places; Alten Corimont) and **dunmer-north** (141; Stormhold, Thorn, Tearmouth,
   Hissmir, Crystalgate, Wolk Market): the main quest's first act.
3. **imperial-fringe** (128; Gideon, Glenbridge, Fig Market, Claywater Station).
4. **hist-heartland** (117; Helstrom, Greenspring): the main quest's middle; Helstrom is a city.
5. **mercantile-coast** (140; Lilmoth, Soulrest, Alten Meerhleel, Chasepoint).
6. **saxhleel-coast** (101; Archon).
7. **imperial-penal-south** (73; Blackrose).
8. **naga-kur-deeps** (67): deep land, the climax approach to the Lost City.

The planner may reorder by the main quest's needs; the order is recorded in PROGRESS.

## The packet (what one region packet contains and the steps it runs)

Each region is split into **packets** of about 20–40 places (a district for cities). One packet is one lane's
brief at a time; on 20x, up to 4 packets run in parallel in **different regions**, sharing the one GPU box
through the `job_guard.sh --gpu` lock (never two builders on one
place or district: the Helstrom lesson, old 0133).

1. **Plan** (L1): from the catalogue, list the packet's places, their classes (settlement, ruin, lair, works,
   lone, transit, sacred, camp, civic, martial), danger bands, cultures, siting, relations, loot tables; the NPCs
   who live there; the quests anchored there; the creatures; the books. Check against density targets.
2. **Kit and asset check** (L1): every mesh each place needs exists in a cleared dependency (sourcing register);
   substitutions recorded; selection order per decision 0006 §8.
3. **Build places** (`world-builder` skill, L1→L4): layouts from the placement principles; a place carries its
   own ground; every building enterable via the plugin's interior or an assembled interior; sockets fulfilled
   (old 0104: promises are fulfilled by placed interactables); cities hand-built by district in 3D (old 0133).
4. **People** (L1→L4): NPC records, faces (P1 solution), outfits, schedules on the lamp clock, services, factions.
5. **Quests** (decision 0017): each quest anchored here is written or rebuilt through `quest-write` (routed to
   its shape's principles), reviewed by `quest-review`, and its `new` things handed to step 3's builder; then
   stage graphs (L1→L4), directions validated against the route graph, fail-forward for dead NPCs.
6. **Dialogue round** (`dialogue-write` on Sonnet, from generated briefs): greetings, place topics, quest topics,
   barks, journal text, for every person in the packet.
7. **Encounters and loot** (L1): creatures and hostiles by band; roaming band table; fixed loot.
8. **Books and signs** (L1): written to the style guide, text-review.
9. **Immersion** (gate): every new element enters the inventory compliant.
10. **Navmesh and LOD:** regenerate navmesh for every cell the packet touched (and its neighbours' edge links)
    in the packet; rebuild LOD once at **region close** on the temporary 64 GiB instance (budget in decision 0008).
11. **Checks** (L4): a packet scenario walks every place, enters every building, talks to every NPC once, runs
    every quest; frame-time sample per place.
12. **Owner walk** (L6): one packet per region (not per packet): a route through the region's new places and
    its quests; blocker/polish triage.

## Main quest, factions, endings

- The main quest "The Eye and the Root" (23–24 core quests, 25–35 hours, stakes legible in the first two hours,
  three endings CUT / CLAIM / MEND; old 0026/0028) is built across packets in story order, each quest staged when
  its region packet lands; tier protection (main > faction > side; old 0030).
- The 8 major faction lines (Shadowscales, Night-Reed, Nisswo, Many-Root; Marsh Charter, Sunken Archive,
  Reed-Sail Compact, League of Open Water), the **detectives' line** (decision 0018: cases built in the packets
  that host them, the finale when its region lands) and the compact lines, with allegiance reward tracks (old 0028).
- The climax expedition Helstrom → Lost City with the Wamasu guardian (P5 boss) and the named antagonist (duel
  or words).

## Milestones

- **M1 (first complete playthrough):** the main quest end to end with all three endings, 170–210 journaled
  quests, every region at least at its slice density along the main quest's route. Owner playthrough. Possible
  early-access release (P10 may run here).
- **M2 (maturity):** every active catalogue place built, 450–550 quests, all factions complete. Owner sign-off.

## Exit gate
M2 reached, or the owner declares the content complete; all region walk packets closed; the gate green.

## Risks and fallbacks
- **Volume vs quality**: packets are small and judged at the cheapest level; the owner sees regions, not
  packets; reader panels catch sameness (old 0098: variety is measured per settlement).
- **Asset gaps per region** (e.g. no Kothringi remains asset): redesign around what exists (old rule) before
  any Fal or retexture work.
- **Cost**: 20x usage is measured weekly against the plan's cap; if lanes queue on the GPU box, add a second
  GPU box only after costing it against the budget.

## Deliberately out of scope
New systems (any system gap found here goes back to its phase as a decision); new meshes; regions outside the
province (the apron stays unreachable).
