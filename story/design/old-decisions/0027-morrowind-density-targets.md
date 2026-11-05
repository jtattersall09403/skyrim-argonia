<!-- imported unchanged from elder-souls-argonia docs/decisions/0027-morrowind-density-targets.md @ b581910f0f87d8da88eaa9876d238cdc5d709e78 (0.1 §f) -->
# 0027 — Content density matched to Morrowind; quest briefs gate a packet; sourceable specifics only

**Status** accepted · **Scope** `docs/quests/`, the place catalogue,
[morrowind-content-density](../research/placement-settlements/morrowind-content-density.md)

## Density targets

The owner's directive: the same quests per km², places per km² and quests per
city as Morrowind. Measured from UESP and OpenMW cells (evidence in the
research above): Vvardenfell is about 20 km² of land with about 410 named
places and 400 base-game quests, the quests concentrated at settlements
(Vivec about 90–100, Balmora and Ald'ruhn 45–55, villages 3–8) and the
wilderness carrying places rather than quests. Our province is about 37 km² of
land.

- **18–22 named places per km²** in D0–D3 land; **8–12** in D4–D5
  (landmark-heavy, quest-light); about 550–750 named places at maturity.
- **Route spacing**: something named within 300 m of travel along every road
  and boat lane; a new visible landmark about every minute of walking.
- **Quests per settlement by magnitude**: M5 35–60, M4 10–20, M3 3–8, M2 1–3,
  M1 0–2; about 450–550 finite quests at maturity. Summed over the settlement
  register the ladder agrees with the per-km² figure.
- **Every settlement structure is enterable and every settlement NPC named**,
  Morrowind's standard.
- **Diegetic discovery**: with no quest markers, every unmarked place needs at
  least one in-world pointer (rumour, note, corpse, grave-stake, sightline).

## The co-design loop is a completion gate

A region packet without its quest-brief set and density budget is not done
([quests 90](../quests/90-production-sequence.md) §65b). One agent may wear both
hats in sequence or spawn a reader; the artefacts and the gate are what is
mandatory.

## Quests specify only what can be sourced

Every co-design brief passes the asset five-question check
([quests 70](../quests/70-assets.md) §51), citing an asset code or sourcing
job per physical element, else `ASSET-RISK` with a staging fallback. The
delivering world agent may amend a quest's physical specifics when sourcing
fails: it preserves the quest's function (sockets, approaches, stakes,
choice), protects canon-defining forms (stilt and reed, mud and wattle,
xanmeers, grave-stakes: sourcing obligations or owner escalations, never
silent swaps), writes the amendment into `docs/quests/` in the same packet
and credits substituted assets
([20-world-provisions](../quests/20-world-provisions.md)).

## Mod assets before vanilla

Skyrim's assets were built for a cold Nordic province; setting mods were built
for ours. The order ([world/90](../world/90-asset-strategy.md) §71):

1. the Black Marsh half of Black Marsh & Valenwood and the Argonian Xanmeer
   Tileset, the house style;
2. other Argonia-appropriate mod sources;
3. vanilla, first choice only for culturally neutral props and where skeleton
   or animation compatibility is the point.

A vanilla asset in an Argonian-reading role carries a one-line note on why no
mod source served; those notes are the backlog for an upgrade pass.
