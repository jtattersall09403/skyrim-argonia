# Phase 4a: talk to everyone in BM&V

Status: [PROGRESS.md](../PROGRESS.md). The plan: [PLAN.md](../PLAN.md). Edit this file as the phase goes; it is the phase's whole brief.
The design: [talk.md](../design/talk.md). Owner ruling 2026-11-07 ([owner-rulings](../owner-rulings.md)).

**What it is.** Every person BM&V places who can be talked to gets a light backstory and three to five topics of
their own, every fact backed by a record or a lore line. Block W-talk (Phase 3) is proved on Lilmoth's 12; this
phase copies it to the rest. It runs beside Phase 4 (it needs no quest), and quest rumours are added to a
settlement's talkers when Phase 4 builds a quest that can start there.

## The census (`bmv_talker`, `python3 -m tools.argonia_world.talk_census build`)

725 enabled placed people: 553 silent (E opens nothing), 50 service (a vanilla trade menu only), 3 with vanilla
lines, 42 hostile, 77 corpses. Talkable: 603; Lilmoth's 12 are done, **591 to go**. By settlement (silent +
service): Blackrose 66, Elden Root 61, Murkmire 48, Murkwood 35, Thorn 33, Haven 30, no settlement 29,
Woodhearth 22, Alten Meirhall 21, AyRuin1 17, Greenheart 16, Capital 14, Arenthi 13, Barracks 12, BANDITCAMP1 12,
Hereguard Plantation 11, Helstrom 11, Village5 10, DWARVEN 10, 26 smaller groups with 1 to 9 each.

**First pass per settlement:** read its rows and drop any that are hostile in game though not by faction
(BANDITCAMP1's 12, Barracks' Thalmor, ruin dwellers): they stay silent and the census marks them hostile.

## The order

Black Marsh first, nearest the opening outward (the player meets them first): Hereguard Plantation, Murkmire,
Blackrose, Helstrom, Thorn, Alten Meirhall, Arenthi, the Black Marsh villages and sites; then Valenwood: Elden Root,
Haven, Woodhearth, Greenheart, Falinesti, the rest. One settlement is one commit and one build.

## Per settlement (the loop)

1. Scan the settlement's refs (containers, flora, loose ingredients, corpses, map markers, doors) into `talk_fact`
   rows with their form keys and positions; add its lore facts from `story/lore/` with the line.
2. Write each talker's `talker` row (backstory format in talk.md) and `talker_topic` rows (directions and
   distances measured from their own spot).
3. `talk_brief.py brief` per person; one `dialogue-writer` agent per person (own context, words band); `talk_brief.py
   load`.
4. `plugin.sh seed`, `plugin.sh check`, and the read-back: every talker's topics are in the ESP, gated to their ref.
   Fix and repeat until it matches. Then commit (`lane_commit.sh`), and deploy with the next batch.

## Cost (measured on Lilmoth, 2026-11-07)

12 writer runs: 23,000 to 36,000 tokens each (the two with corpus-find children 36,000; without, about 24,000),
about 30 seconds to 2 minutes each, all in parallel. About $0.30 to $0.40 a person; the scan and backstories about
$4 a settlement. **591 people in about 45 groups: about $230 + $180 ≈ $410, about 22% of a week's allowance.**
Build: seed and check under 3 minutes each.

## Acceptance

- Every `bmv_talker` row with status silent or service has a `talker` row with status built, or is re-marked hostile
  with a reason.
- The read-back finds each talker's topics in the ESP; `make check` green.
- One owner walk per region (Black Marsh, Valenwood): talk to three people the owner picks; every fact checked
  where it says.
