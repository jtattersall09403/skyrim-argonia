---
name: talk-write
description: Give every BM&V person in one settlement a name, a light backstory, a personality, true topics and written lines (Phase 4a's recipe v2). Use per settlement, before its build.
---

# Talk for one settlement

Design: `docs/design/talk.md` (the tables, the topic catalogue). The four rules below are the owner's (walk 3,
2026-11-08); `talk_check` enforces each. `S` is the settlement id (`bmv.lilmoth`).

## The rules

1. **Directions are routes.** Every `talk.directions` fact is made by `talk_route` from the speaker's ref: legs
   (walk, follow the path, follow the shore, cross the bridge, along the boards, swim, climb) ending at real
   landmarks, each with its form key in `source`. A place in sight (under 60 m, near straight) is paces and a
   compass point. The writer retells the legs in the person's voice; never adds a landmark.
2. **Address follows standing.** Topic replies are said to a stranger: neutral or cool by temperament. Two
   greetings a person, `talk.greet-stranger` and `talk.greet-friend` (Talk.cs gates them on GetRelationshipRank
   with the player, < 1 and >= 1, Skyrim's Hello way). At most two warm address terms in all of a person's lines,
   none to a stranger (lint B11). A `manner` never says the person calls strangers "friend".
3. **Facts are BM&V's.** A fact cites a ref (form key) in the loaded world, or is a lore line making no physical
   claim (ship, dock, wall, tree, ruin, beast, crop...) the world does not show or contradicts; where they
   disagree the world wins and the lore line is dropped. Places by the names the player sees (`world_edit`
   `name_place`: the Docks are Soulrest).
4. **Names** (`story/design/quests/35-cast.md` §54, `86-never-reuse-names.md`): the five forms by who carries them
   (Jel for the marsh-born, translated for city and outward-facing work, nickname for the notorious, chosen,
   foreign); at most a third of a settlement Verb-the-Noun; an image (water, reed, root, stone, shadow, sky,
   boat, blade, eye, hand) once a settlement; no canon or lore name unless BM&V's base carries it; nothing Nordic.

## The loop

1. **Rows.** `python3 -m tools.argonia_world.db query "SELECT * FROM bmv_talker WHERE settlement='S' AND status IN
   ('silent','service')"`. Drop clean-up targets that are Nord, Thalmor, Imperial officials or undead (Phase 4
   part B's rule; a kept talker leaves the clean-up); mark the hostile-in-game ones hostile.
2. **Ref scan.** `python3 -m tools.argonia_world.talk_route cache` once (out/talk_route/); landmarks and refs near
   each speaker come from the same cache (`talk_route.World().refs`, each with `lm`). Place, danger, loot,
   harvest and someone facts: one row each, `source` the form key and position.
3. **Routes.** Write each directions fact with `source` naming `speaker <ref6>` and `target <key6>` (a map marker,
   a talker or a ref), then `python3 -m tools.argonia_world.talk_route facts --settlement S --write`. Check a
   route by hand with `talk_route route --from REF --to KEY`.
4. **Lore facts**: from `story/lore`, rule 3; cite a ref where the claim is physical.
5. **Talkers.** One author pass for the settlement (so opinions agree): `talker` rows (name by rule 4, trade,
   spot, two-to-three-sentence backstory citing lore, the seven personality columns) and `talker_topic` rows:
   `talk.self`, both greetings, three to five place or trade topics drawn from facts near the person's own spot;
   each person has one fact no one else has; a widely known thing is known by two or three at most.
6. **Data check.** `python3 -m tools.argonia_world.talk_check --lines-only --settlement S`: facts and names 0.
7. **Briefs.** `python3 .claude/skills/dialogue-write/talk_brief.py brief --talker REF --out BRIEF.md` per person.
8. **Lines.** One `dialogue-writer` agent per person, in parallel, each given its brief and an output path
   (TSV `<topic>\t<text>`), lint run with `--race`. Then `talk_brief.py load LINES.tsv --talker REF`.
9. **Reader.** One `reader` pass over all the settlement's lines (style guide, bans); fix and reload.
10. **Build.** `tools/ArgoniaPlugin/plugin.sh seed`, `plugin.sh check`, then `python3 -m
    tools.argonia_world.talk_check` (lines, facts, names, the ESP read-back) to 0 problems; set the talkers
    `built`; commit the story data (never `plugin/Argonia/`; the integrator re-seeds).

Cost on Lilmoth's 30: see `docs/design/talk.md` § Cost.
