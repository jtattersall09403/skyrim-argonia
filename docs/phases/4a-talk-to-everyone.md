# Phase 4a: talk to everyone in BM&V

Status: [PROGRESS.md](../PROGRESS.md). The plan: [PLAN.md](../PLAN.md). Edit this file as the phase goes; it is the phase's whole brief.
The design: [talk.md](../design/talk.md). The recipe: the skill `.claude/skills/talk-write`. Owner rulings
2026-11-07 and 2026-11-08 ([owner-rulings](../owner-rulings.md)).

**What it is.** Every person BM&V places who can be talked to gets a name, a light backstory, a personality and
three to five topics of their own, every fact true of BM&V's loaded world. Block W-talk (Phase 3) was proved on
Lilmoth's 30. The act's places come first, inside Phase 4 (its part B); this phase then copies the recipe to the
rest. Quest rumours are added to a settlement's talkers when Phase 4 builds a quest that can start there.

## Recipe v2 (owner's walk 3, 2026-11-08)

The owner found Lilmoth's 30 "much better", with four faults, each now a rule of `talk-write`:

1. **Directions are routes, as Morrowind gives them**: "walk west until you see the wrecked boat, then follow the
   small path north about 20 paces; on your left there is ...", "follow the shore round westwards until ...", "swim
   across to the island you can see south-east of here". Each route is computed from the world (navmesh, land and
   water heights, shore lines, roads and paths, named and notable refs as landmarks) by a route tool, from the
   speaker's spot to the target, and every waypoint is a real ref or feature with its form key. The format varies
   with the person and the context; paces and a compass point alone only where the place is close (in sight, under
   about 60 m).
2. **Address follows standing.** "My friend" or any warm address at most once or twice per person over all their
   lines, and only where their standing with the player warrants it: neutral or cool to a stranger by default, per
   temperament; a warmer greeting gated on the relationship rank the engine keeps (Skyrim's own way).
3. **Facts are BM&V's.** A topic fact is a ref in the loaded world or a lore line that the world does not contradict;
   where the lore and BM&V's placed world disagree on something the player can see (Lilmoth: "lighters, no big
   ships" against a big ship at the dock), the world wins and the lore line is not used. Places are called by the
   names the player will see (our renames in `world_edit`, e.g. the Docks as Soulrest).
4. **Names follow the old repo's rules** (`story/design/quests/35-cast.md` §54, `86-never-reuse-names.md`): the five
   name forms by who carries them; at most a third of a settlement's names in the Verb-the-Noun translated form; an
   image (reed, root, water, stone, shadow, ...) once per settlement; no canon person's name for a nobody; nothing
   from the never-reuse list; no Nordic element.

## The census (`bmv_talker`, `python3 -m tools.argonia_world.talk_census build`)

725 enabled placed people: 553 silent (E opens nothing), 50 service (a vanilla trade menu only), 3 with vanilla
lines, 42 hostile, 77 corpses. Talkable: 603; Lilmoth's 30 built (v1, to redo with v2); the act's places (Phase 4
part B) 89 more. By settlement (silent + service): Blackrose 66, Elden Root 61, Murkmire 48, Murkwood 35, Thorn 33,
Haven 30, no settlement 29, Woodhearth 22, Alten Meirhall 21, AyRuin1 17, Greenheart 16, Capital 14, Arenthi 13,
Barracks 12, BANDITCAMP1 12, Hereguard Plantation 11, Helstrom 11, Village5 10, DWARVEN 10, 26 smaller groups with 1
to 9 each. Clean-up targets (`we.clean.*`) get no talker row unless kept as talkers (Phase 4 part B's rule).

**First pass per settlement:** read its rows and drop any that are hostile in game though not by faction
(BANDITCAMP1's 12, Barracks' Thalmor, ruin dwellers): they stay silent and the census marks them hostile.

## The order

The act's places first (Phase 4 part B). Then Black Marsh, nearest the opening outward: Murkmire, Alten Meirhall,
Arenthi, the Black Marsh villages and sites; then Valenwood: Elden Root, Haven, Woodhearth, Greenheart, Falinesti,
the rest. One settlement is one commit and one build.

## Per settlement (the loop; the detail is in talk-write)

1. Scan the settlement's refs into `talk_fact` rows with form keys and positions; compute route directions with the
   route tool; add lore facts the world does not contradict.
2. One author agent writes the settlement's `talker` rows (name by the rules, backstory, seven personality columns,
   standing-gated address) and `talker_topic` rows.
3. `talk_brief.py brief` per person; one `dialogue-writer` per person; `talk_brief.py load`; one `reader` pass.
4. `plugin.sh seed`, `plugin.sh check`, `python3 -m tools.argonia_world.talk_check` until 0 problems; commit;
   deploy with the next batch.

## Cost (measured on Lilmoth's 30, 2026-11-08)

About $0.45 a person all in: the 573 not yet built, about $260, about 14% of a week's allowance. Build: seed and
check under 3 minutes each.

## Acceptance

- Every `bmv_talker` row with status silent or service has a `talker` row with status built, or is re-marked hostile
  or cleaned up with a reason.
- The read-back finds each talker's topics in the ESP; `make check` green.
- One owner walk per region (Black Marsh, Valenwood): talk to three people the owner picks; every fact checked
  where it says.
